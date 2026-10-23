"""Tests for pairip_audit.stubs: the instruction-level stub heuristic."""

import pytest
from fakes import (
    LOADLIBRARY_OUTPUT,
    VM_EXECUTE_OUTPUT,
    VM_INVOKE_OUTPUT,
    VERIFY_INVOKE_OUTPUT,
    BrokenInsn,
    FakeInsn,
    RaisingIterator,
    abstract_method,
)
from pairip_audit import stubs
from pairip_audit.stubs import (
    MethodFindings,
    classify_invoke,
    extract_invoke_target,
    is_const_string_insn,
    is_invoke_insn,
    is_pairip_class_name,
    is_stub,
    method_instructions,
    scan_instructions,
    scan_method,
)


class TestExtractInvokeTarget:
    def test_regular_invoke_output(self):
        assert extract_invoke_target(
            "v0, v1, Lcom/pairip/VMRunner;->invoke(Ljava/lang/String;)Ljava/lang/Object;"
        ) == ("Lcom/pairip/VMRunner;", "invoke")

    def test_no_registers_prefix(self):
        assert extract_invoke_target(
            "Lcom/example/Foo;->bar()V"
        ) == ("Lcom/example/Foo;", "bar")

    def test_ctor_and_synthetic_names(self):
        assert extract_invoke_target("v0, Lcom/a/B;-><init>()V") == ("Lcom/a/B;", "<init>")
        assert extract_invoke_target("v0, Lcom/a/B;->access$000(I)J") == ("Lcom/a/B;", "access$000")

    def test_ctor_into_pairip_class_is_a_pairip_call(self):
        # regression: invoke-direct of a com.pairip constructor must be
        # classifiable (integrity call site), not silently dropped.
        target = extract_invoke_target(
            "v1, Lcom/pairip/license/LicenseManager;-><init>()V"
        )
        assert target == ("Lcom/pairip/license/LicenseManager;", "<init>")
        assert classify_invoke(*target) == "pairip"

    def test_no_target(self):
        assert extract_invoke_target("v0, v1") is None
        assert extract_invoke_target("") is None
        assert extract_invoke_target(None) is None

    def test_range_invoke_output(self):
        assert extract_invoke_target(
            "v1 .. v3, Lcom/x/Y;->run([Ljava/lang/Object;)V"
        ) == ("Lcom/x/Y;", "run")


class TestInstructionNamePredicates:
    def test_is_invoke_insn(self):
        for name in (
            "invoke-virtual",
            "invoke-super",
            "invoke-direct",
            "invoke-static",
            "invoke-interface",
            "invoke-static/range",
        ):
            assert is_invoke_insn(name), name
        assert not is_invoke_insn("const-string")
        assert not is_invoke_insn("")
        assert not is_invoke_insn(None)

    def test_is_const_string_insn(self):
        assert is_const_string_insn("const-string")
        assert is_const_string_insn("const-string/jumbo")
        assert not is_const_string_insn("const/4")
        assert not is_const_string_insn("")
        assert not is_const_string_insn(None)


class TestClassifyInvoke:
    def test_vm_entries(self):
        assert classify_invoke("Lcom/pairip/VMRunner;", "invoke") == "vm"
        assert classify_invoke("Lcom/pairip/VMRunner;", "executeVM") == "vm"

    def test_other_pairip_classes(self):
        assert classify_invoke("Lcom/pairip/SignatureCheck;", "verifyIntegrity") == "pairip"
        # non-entry VMRunner members are still pairip-internal calls
        assert classify_invoke("Lcom/pairip/VMRunner;", "setContext") == "pairip"

    def test_non_pairip(self):
        assert classify_invoke("Ljava/lang/System;", "loadLibrary") is None
        assert classify_invoke("Lcom/example/Foo;", "bar") is None

    def test_prefix_is_package_scoped(self):
        # com.pairipfoo must NOT match the com/pairip/ package prefix
        assert classify_invoke("Lcom/pairipfoo/X;", "invoke") is None


class TestIsPairipClassName:
    def test_shapes(self):
        assert is_pairip_class_name("Lcom/pairip/VMRunner;")
        assert is_pairip_class_name("Lcom/pairip/application/Application;")
        assert not is_pairip_class_name("Lcom/pairipfoo/X;")
        assert not is_pairip_class_name("")
        assert not is_pairip_class_name(None)


class TestScanInstructions:
    def test_full_stub_body(self):
        findings = scan_instructions(
            [
                FakeInsn("const-string", 'v0, "b4f5k.vmcode"'),
                FakeInsn("invoke-static", VM_INVOKE_OUTPUT),
                FakeInsn("return-object", "v0"),
            ]
        )
        assert findings.vm_refs == ["Lcom/pairip/VMRunner;->invoke"]
        assert findings.pairip_refs == []
        assert findings.loads_pairipcore is False

    def test_executevm_delegation_counts(self):
        findings = scan_instructions([FakeInsn("invoke-static", VM_EXECUTE_OUTPUT)])
        assert findings.vm_refs == ["Lcom/pairip/VMRunner;->executeVM"]

    def test_pairip_call_and_loadlibrary(self):
        findings = scan_instructions(
            [
                FakeInsn("const-string", 'v0, "pairipcore"'),
                FakeInsn("invoke-static", LOADLIBRARY_OUTPUT),
                FakeInsn("const-string", 'v1, "unrelated"'),
                FakeInsn("invoke-static", VERIFY_INVOKE_OUTPUT),
            ]
        )
        assert findings.vm_refs == []
        assert findings.pairip_refs == [
            "Lcom/pairip/SignatureCheck;->verifyIntegrity"
        ]
        assert findings.loads_pairipcore is True

    def test_loadlibrary_without_pairipcore_string(self):
        findings = scan_instructions(
            [
                FakeInsn("const-string", 'v0, "somelib"'),
                FakeInsn("invoke-static", LOADLIBRARY_OUTPUT),
            ]
        )
        assert findings.loads_pairipcore is False

    def test_pairipcore_string_without_loadlibrary(self):
        findings = scan_instructions(
            [FakeInsn("const-string", 'v0, "libpairipcore.so"')]
        )
        assert findings.loads_pairipcore is False

    def test_invoke_without_resolvable_target_is_ignored(self):
        findings = scan_instructions([FakeInsn("invoke-static", "v0, v1")])
        assert findings.vm_refs == [] and findings.pairip_refs == []

    def test_broken_instructions_are_skipped(self):
        findings = scan_instructions(
            [BrokenInsn(), FakeInsn("invoke-static", VM_INVOKE_OUTPUT), BrokenInsn()]
        )
        assert findings.vm_refs == ["Lcom/pairip/VMRunner;->invoke"]

    def test_plain_method_yields_empty_findings(self):
        findings = scan_instructions(
            [FakeInsn("const/4", "v0, 1"), FakeInsn("return-void", "")]
        )
        assert findings == MethodFindings()

    def test_iterator_failure_propagates(self):
        with pytest.raises(ValueError):
            scan_instructions(RaisingIterator(FakeInsn("return-void", "")))


class TestMethodScan:
    def _method(self, instructions=None, code_error=None):
        from fakes import FakeMethod

        return FakeMethod("m", "Lcom/example/A;", instructions, code_error=code_error)

    def test_abstract_method_has_no_code(self):
        method = abstract_method("onAbstract", "Lcom/example/A;")
        assert method_instructions(method) is None
        findings, error = scan_method(method)
        assert findings is None and error is None

    def test_normal_scan(self):
        findings, error = scan_method(
            self._method([FakeInsn("invoke-static", VM_INVOKE_OUTPUT)])
        )
        assert error is None
        assert findings.vm_refs == ["Lcom/pairip/VMRunner;->invoke"]

    def test_get_code_raising_is_reported_as_error(self):
        method = self._method(code_error=RuntimeError("corrupt code item"))
        findings, error = scan_method(method)
        assert findings is None
        assert error is not None and "RuntimeError" in error

    def test_disassembly_failure_mid_stream_is_reported(self):
        method = self._method(RaisingIterator(FakeInsn("return-void", "")))
        findings, error = scan_method(method)
        assert findings is None
        assert error is not None and "ValueError" in error


class TestIsStub:
    def test_app_method_delegating_to_vm_is_stub(self):
        findings = MethodFindings(vm_refs=["Lcom/pairip/VMRunner;->invoke"])
        assert is_stub("Lcom/example/game/GameLogic;", findings) is True

    def test_pairip_runtime_methods_are_never_stubs(self):
        findings = MethodFindings(vm_refs=["Lcom/pairip/VMRunner;->executeVM"])
        assert is_stub("Lcom/pairip/VMRunner;", findings) is False

    def test_no_findings_no_stub(self):
        assert is_stub("Lcom/example/A;", None) is False
        assert is_stub("Lcom/example/A;", MethodFindings()) is False


def test_module_documents_grounding():
    # The heuristic constants must match the documented marker.
    assert stubs.VMRUNNER_CLASS == "Lcom/pairip/VMRunner;"
    assert stubs.VM_ENTRY_METHODS == {"invoke", "executeVM"}
    assert stubs.PAIRIP_CLASS_PREFIX == "Lcom/pairip/"
