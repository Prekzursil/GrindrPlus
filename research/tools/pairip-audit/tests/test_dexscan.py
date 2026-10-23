"""Tests for pairip_audit.dexscan over fake androguard dex objects."""

from fakes import (
    FakeClass,
    FakeDEX,
    FakeInsn,
    FakeMethod,
    LOADLIBRARY_OUTPUT,
    VM_INVOKE_OUTPUT,
    VERIFY_INVOKE_OUTPUT,
    pairip_dex_blueprint,
    plain_dex_blueprint,
)
from pairip_audit.dexscan import (
    MAX_ENTRY_POINTS,
    DexScan,
    combine,
    scan_dex,
    to_dotted,
)


class TestToDotted:
    def test_class_descriptor(self):
        assert to_dotted("Lcom/pairip/VMRunner;") == "com.pairip.VMRunner"

    def test_nested(self):
        assert to_dotted("Lcom/pairip/application/Application;") == (
            "com.pairip.application.Application"
        )

    def test_non_class_passes_through(self):
        assert to_dotted("com.example.Foo") == "com.example.Foo"
        assert to_dotted("[Ljava/lang/Object;") == "[Ljava/lang/Object;"


class TestScanDex:
    def test_pairip_blueprint_counts(self):
        scan = scan_dex(FakeDEX(pairip_dex_blueprint()), "classes.dex")
        # 5 classes in the blueprint
        assert scan.classes == 5
        # VMRunner: <clinit>, invoke, executeVM, setContext
        # SignatureCheck: verifyIntegrity
        # Application: attachBaseContext
        # GameLogic: virtualizedSecret, plainJava, onAbstract
        # Helper: callExecuteVMDirectly
        assert scan.methods == 10
        # stubs: GameLogic.virtualizedSecret + Helper.callExecuteVMDirectly
        # (VMRunner.invoke delegates to executeVM but lives in com.pairip.*)
        assert scan.stub_methods == 2
        assert scan.scan_errors == 0

    def test_pairip_classes_listed_dotted(self):
        scan = scan_dex(FakeDEX(pairip_dex_blueprint()), "classes.dex")
        # per-dex order follows class declaration order; the census-level
        # sorted list is asserted separately in test_census.
        assert sorted(scan.pairip_classes) == [
            "com.pairip.SignatureCheck",
            "com.pairip.VMRunner",
            "com.pairip.application.Application",
        ]

    def test_entry_points(self):
        scan = scan_dex(FakeDEX(pairip_dex_blueprint()), "classes.dex")
        kinds = {(e["kind"]) for e in scan.entry_points}
        assert kinds == {"pairip-call", "load-pairipcore"}
        by_class_method = {(e["class"], e["method"]) for e in scan.entry_points}
        assert (
            "com.pairip.application.Application",
            "attachBaseContext",
        ) in by_class_method
        assert ("com.pairip.VMRunner", "<clinit>") in by_class_method
        load_entry = next(
            e for e in scan.entry_points if e["kind"] == "load-pairipcore"
        )
        assert load_entry["library"] == "pairipcore"
        verify_entry = next(
            e for e in scan.entry_points if e["kind"] == "pairip-call"
        )
        assert verify_entry["targets"] == [
            "Lcom/pairip/SignatureCheck;->verifyIntegrity"
        ]

    def test_plain_dex_has_no_markers(self):
        scan = scan_dex(FakeDEX(plain_dex_blueprint()), "classes.dex")
        assert scan.classes == 1
        assert scan.methods == 1
        assert scan.stub_methods == 0
        assert scan.pairip_classes == []
        assert scan.entry_points == []
        assert scan.dropped_entry_points == 0

    def test_scan_error_counted_not_fatal(self):
        method = FakeMethod(
            "broken",
            "Lcom/example/A;",
            code_error=RuntimeError("bad code item"),
        )
        scan = scan_dex(FakeDEX([FakeClass("Lcom/example/A;", [method])]), "d.dex")
        assert scan.methods == 1
        assert scan.scan_errors == 1
        assert scan.stub_methods == 0

    def test_stub_is_not_an_entry_point(self):
        # A pure VM stub delegates to VMRunner.invoke: counted as stub, but it
        # is not an integrity call site.
        method = FakeMethod(
            "stubbed", "Lcom/app/X;", [FakeInsn("invoke-static", VM_INVOKE_OUTPUT)]
        )
        scan = scan_dex(FakeDEX([FakeClass("Lcom/app/X;", [method])]), "d.dex")
        assert scan.stub_methods == 1
        assert scan.entry_points == []

    def test_entry_point_cap(self):
        # MAX_ENTRY_POINTS + 2 methods each calling a pairip class.
        methods = [
            FakeMethod(
                f"m{i}", "Lcom/app/Y;", [FakeInsn("invoke-static", VERIFY_INVOKE_OUTPUT)]
            )
            for i in range(MAX_ENTRY_POINTS + 2)
        ]
        scan = scan_dex(FakeDEX([FakeClass("Lcom/app/Y;", methods)]), "d.dex")
        assert len(scan.entry_points) == MAX_ENTRY_POINTS
        assert scan.dropped_entry_points == 2

    def test_empty_dex(self):
        scan = scan_dex(FakeDEX([]), "classes.dex")
        assert scan == DexScan(name="classes.dex")


class TestCombine:
    def test_totals_and_pct(self):
        a = DexScan(name="classes.dex", classes=2, methods=10, stub_methods=1)
        b = DexScan(name="classes2.dex", classes=3, methods=30, stub_methods=3)
        stats = combine([a, b])
        assert stats["totalMethods"] == 40
        assert stats["stubMethods"] == 4
        assert stats["stubPct"] == 10.0
        assert stats["perDex"] == [
            {"dex": "classes.dex", "classes": 2, "methods": 10, "stubMethods": 1},
            {"dex": "classes2.dex", "classes": 3, "methods": 30, "stubMethods": 3},
        ]

    def test_pct_rounding(self):
        stats = combine([DexScan(name="d", classes=1, methods=3, stub_methods=1)])
        assert stats["stubPct"] == 33.33

    def test_no_methods(self):
        stats = combine([])
        assert stats == {
            "totalMethods": 0,
            "stubMethods": 0,
            "stubPct": 0.0,
            "perDex": [],
        }

    def test_blueprint_end_to_end_counts(self):
        stats = combine([scan_dex(FakeDEX(pairip_dex_blueprint()), "classes.dex")])
        assert stats["totalMethods"] == 10
        assert stats["stubMethods"] == 2
