"""Instruction-level heuristic for PairIP VM stub / virtualized-method detection.

Grounding (read from the sample repositories before implementing -- see
pairip-research/samples/):

- ``samples/pairipcore-vm/docs/source/introduction.md`` (lines 21-27): to
  prevent easy circumvention of the Java-side checks, "some classes invoke
  ``VMRunner.executeVM`` instead of executing regular Java code" -- i.e.
  virtualized methods are replaced by *stubs* that delegate to the PairIP VM
  runner, and important strings are initialized at runtime.
- ``samples/pairipcore/README.md`` (lines 89-146): ``com.pairip.VMRunner``
  exposes ``public static Object invoke(String vmByteCodeFile, Object[] args)``
  which reads VM bytecode (from the assets folder) and calls
  ``public static native Object executeVM(byte[] vmCode, Object[] args)``;
  the class static initializer runs ``System.loadLibrary("pairipcore")``.
- ``samples/pairipcore/README.md`` (lines 29-43): the host application class
  (``com.pairip.application.Application``) calls
  ``SignatureCheck.verifyIntegrity(context)`` from ``attachBaseContext``.

Therefore the static marker implemented here is: **a method whose Dalvik
bytecode contains an invoke instruction whose target is
``Lcom/pairip/VMRunner;->invoke`` or ``->executeVM``**.  Calls to *other*
``com.pairip.*`` classes (e.g. ``SignatureCheck.verifyIntegrity``) are
recorded separately as integrity call sites, not as stubs.  This module is
pure logic over instruction-shaped objects (``get_name()`` / ``get_output()``
like androguard's ``Instruction``), so it is fully unit-testable with fakes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

# --- PairIP markers ---------------------------------------------------------

#: Dalvik descriptor prefix of every PairIP-injected class.
PAIRIP_CLASS_PREFIX = "Lcom/pairip/"

#: The VM runner class documented in both sample repositories.
VMRUNNER_CLASS = "Lcom/pairip/VMRunner;"

#: VM entry methods on VMRunner: the Java-side wrapper and the native entry.
VM_ENTRY_METHODS = frozenset({"invoke", "executeVM"})

#: System.loadLibrary / System.load, used to detect "pairipcore" loading.
LOADLIBRARY_CLASS = "Ljava/lang/System;"
LOADLIBRARY_METHODS = frozenset({"loadLibrary", "load"})

#: Substring identifying the PairIP native library inside a const-string.
PAIRIPCORE_LIB_TOKEN = "pairipcore"

# An invoke target as rendered by androguard's Instruction.get_output():
# e.g. "v0, v1, Lcom/pairip/VMRunner;->invoke(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/Object;"
# The method-name class must accept constructors/synthetic accessors: <init>,
# <clinit>, access$000, ...
_INVOKE_TARGET_RE = re.compile(r"(L[^;\s]+;)->([A-Za-z_$<][A-Za-z0-9_$<>]*)")


# --- findings container -----------------------------------------------------


@dataclass
class MethodFindings:
    """What one method's bytecode revealed about PairIP usage."""

    #: VM runner references, e.g. "Lcom/pairip/VMRunner;->invoke".
    vm_refs: List[str] = field(default_factory=list)

    #: Calls into other com.pairip.* classes (integrity / licensing hooks).
    pairip_refs: List[str] = field(default_factory=list)

    #: True when the method loads the "pairipcore" native library
    #: (const-string "pairipcore" + invoke System.loadLibrary/load).
    loads_pairipcore: bool = False


# --- pure helpers -----------------------------------------------------------


def extract_invoke_target(insn_output: str) -> Optional[Tuple[str, str]]:
    """Extract ``(class_descriptor, method_name)`` from an invoke output string.

    Returns ``None`` when no ``Lsome/Class;->method`` token is present.
    """
    if not insn_output:
        return None
    match = _INVOKE_TARGET_RE.search(insn_output)
    if not match:
        return None
    return match.group(1), match.group(2)


def is_invoke_insn(insn_name: str) -> bool:
    """True for invoke-virtual / invoke-super / invoke-direct / invoke-static /
    invoke-interface (and their /range, /jumbo variants)."""
    return bool(insn_name) and insn_name.startswith("invoke")


def is_const_string_insn(insn_name: str) -> bool:
    """True for const-string / const-string/jumbo instructions."""
    return bool(insn_name) and "const-string" in insn_name


def classify_invoke(class_ref: str, method_name: str) -> Optional[str]:
    """Classify an invoke target against PairIP markers.

    Returns ``"vm"`` for the documented VM entry points, ``"pairip"`` for
    other com.pairip.* targets, ``None`` otherwise.
    """
    if class_ref == VMRUNNER_CLASS and method_name in VM_ENTRY_METHODS:
        return "vm"
    if class_ref.startswith(PAIRIP_CLASS_PREFIX):
        return "pairip"
    return None


def is_pairip_class_name(class_ref: str) -> bool:
    """True when a Dalvik class descriptor belongs to com.pairip.*."""
    return bool(class_ref) and class_ref.startswith(PAIRIP_CLASS_PREFIX)


# --- instruction scan -------------------------------------------------------


def scan_instructions(instructions: Iterable) -> MethodFindings:
    """Scan instruction-shaped objects (androguard ``Instruction`` or fakes).

    Never raises for a single bad instruction: instructions whose
    ``get_name()``/``get_output()`` raise are skipped.  Exceptions raised by
    the iterator itself (broken disassembly) propagate to the caller so the
    method can be counted as a scan error.
    """
    findings = MethodFindings()
    saw_pairipcore_string = False
    saw_load_call = False
    for insn in instructions:
        try:
            name = insn.get_name() or ""
            output = insn.get_output() or ""
        except Exception:  # best-effort: skip unreadable instructions
            continue
        if is_invoke_insn(name):
            target = extract_invoke_target(output)
            if target is None:
                continue
            class_ref, method_name = target
            kind = classify_invoke(class_ref, method_name)
            if kind == "vm":
                findings.vm_refs.append(f"{class_ref}->{method_name}")
            elif kind == "pairip":
                findings.pairip_refs.append(f"{class_ref}->{method_name}")
            elif class_ref == LOADLIBRARY_CLASS and method_name in LOADLIBRARY_METHODS:
                saw_load_call = True
        elif is_const_string_insn(name):
            if PAIRIPCORE_LIB_TOKEN in output:
                saw_pairipcore_string = True
    findings.loads_pairipcore = saw_pairipcore_string and saw_load_call
    return findings


def method_instructions(method):
    """Return the instruction iterable of an androguard-shaped method.

    Returns ``None`` when the method has no code item (abstract / native).
    """
    code = method.get_code()
    if code is None:
        return None
    return code.get_bc().get_instructions()


def scan_method(method) -> Tuple[Optional[MethodFindings], Optional[str]]:
    """Scan one method-shaped object.

    Returns ``(findings, error)``:

    - ``(None, None)`` -- method has no code item (nothing to scan);
    - ``(findings, None)`` -- scanned (possibly empty findings);
    - ``(None, error)`` -- disassembly failed; *error* describes the failure.
    """
    try:
        instructions = method_instructions(method)
    except Exception as exc:  # broken code item access
        return None, f"{type(exc).__name__}: {exc}"
    if instructions is None:
        return None, None
    try:
        return scan_instructions(instructions), None
    except Exception as exc:  # iterator blew up mid-disassembly
        return None, f"{type(exc).__name__}: {exc}"


def is_stub(class_ref: str, findings: Optional[MethodFindings]) -> bool:
    """Stub verdict for a method.

    A method is a PairIP VM stub candidate when it carries a VM-runner
    delegation *and* is not itself part of the PairIP runtime: methods
    declared inside ``com.pairip.*`` (e.g. ``VMRunner.invoke``, which calls
    ``executeVM``) are the runtime, not virtualized app code.
    """
    if is_pairip_class_name(class_ref):
        return False
    return bool(findings and findings.vm_refs)
