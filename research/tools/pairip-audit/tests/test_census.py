"""Tests for pairip_audit.census (pure assembly parts)."""

import json

from fakes import FakeDEX, pairip_dex_blueprint, plain_dex_blueprint
from pairip_audit.census import (
    PAIRIP_DOTTED,
    base_notes,
    build_census,
    coerce_version_code,
    write_census,
)
from pairip_audit.dexscan import scan_dex

#: The exact census contract from the spec, in order.
CENSUS_KEYS = [
    "apk",
    "versionName",
    "versionCode",
    "pairipDetected",
    "nativeLibs",
    "pairipNativeLibs",
    "pairipClasses",
    "dexStats",
    "integrityEntryPoints",
    "notes",
]

PAIRIP_ENTRIES = [
    "AndroidManifest.xml",
    "classes.dex",
    "lib/arm64-v8a/libpairipcore.so",
    "lib/arm64-v8a/libz.so",
    "assets/b4f5k.vmcode",
]
PLAIN_ENTRIES = [
    "AndroidManifest.xml",
    "classes.dex",
    "lib/arm64-v8a/libz.so",
]


class TestCoerceVersionCode:
    def test_numeric_string_becomes_int(self):
        assert coerce_version_code("250211") == 250211

    def test_non_numeric_passthrough(self):
        assert coerce_version_code("1.2-beta") == "1.2-beta"
        assert coerce_version_code("") == ""
        assert coerce_version_code(None) is None
        assert coerce_version_code(7) == 7


def _pairip_scans():
    return [scan_dex(FakeDEX(pairip_dex_blueprint()), "classes.dex")]


class TestBuildCensus:
    def test_exact_keys_and_order(self):
        census = build_census(
            apk="app.apk",
            version_name="25.21.1",
            version_code="250211",
            entry_names=PAIRIP_ENTRIES,
            dex_scans=_pairip_scans(),
            unreadable_dex=[],
            manifest_app="com.pairip.application.Application",
        )
        assert list(census.keys()) == CENSUS_KEYS

    def test_pairip_census_values(self):
        census = build_census(
            apk="app.apk",
            version_name="25.21.1",
            version_code="250211",
            entry_names=PAIRIP_ENTRIES,
            dex_scans=_pairip_scans(),
            unreadable_dex=[],
            manifest_app="com.pairip.application.Application",
        )
        assert census["versionName"] == "25.21.1"
        assert census["versionCode"] == 250211
        assert census["pairipDetected"] is True
        assert census["nativeLibs"] == {"arm64-v8a": ["libpairipcore.so", "libz.so"]}
        assert census["pairipNativeLibs"] == {"arm64-v8a": ["libpairipcore.so"]}
        assert census["pairipClasses"] == [
            "com.pairip.SignatureCheck",
            "com.pairip.VMRunner",
            "com.pairip.application.Application",
        ]
        assert census["dexStats"]["totalMethods"] == 10
        assert census["dexStats"]["stubMethods"] == 2
        assert census["dexStats"]["stubPct"] == 20.0
        # manifest application is prepended as an entry point
        assert census["integrityEntryPoints"][0]["kind"] == "manifest-application"
        assert (
            census["integrityEntryPoints"][0]["class"]
            == "com.pairip.application.Application"
        )

    def test_detection_via_libs_only(self):
        scans = [scan_dex(FakeDEX(plain_dex_blueprint()), "classes.dex")]
        census = build_census(
            apk="a",
            version_name="",
            version_code="",
            entry_names=["lib/arm64-v8a/libpairipcore.so"],
            dex_scans=scans,
            unreadable_dex=[],
        )
        assert census["pairipDetected"] is True
        assert census["pairipClasses"] == []

    def test_detection_via_vmcode_only(self):
        scans = [scan_dex(FakeDEX(plain_dex_blueprint()), "classes.dex")]
        census = build_census(
            apk="a",
            version_name="",
            version_code="",
            entry_names=["assets/data.vmcode"],
            dex_scans=scans,
            unreadable_dex=[],
        )
        assert census["pairipDetected"] is True

    def test_no_pairip_is_false_but_still_a_census(self):
        scans = [scan_dex(FakeDEX(plain_dex_blueprint()), "classes.dex")]
        census = build_census(
            apk="plain.apk",
            version_name="1.0",
            version_code="1",
            entry_names=PLAIN_ENTRIES,
            dex_scans=scans,
            unreadable_dex=[],
            manifest_app="com.example.app.Main",
        )
        assert census["pairipDetected"] is False
        assert census["pairipNativeLibs"] == {}
        assert census["integrityEntryPoints"] == []

    def test_manifest_app_included_when_discovered_even_if_prefixed_oddly(self):
        # a relative manifest name that still resolves to a discovered pairip
        # class is included
        scans = _pairip_scans()
        census = build_census(
            apk="a",
            version_name="",
            version_code="",
            entry_names=[],
            dex_scans=scans,
            unreadable_dex=[],
            manifest_app="com.pairip.VMRunner",
        )
        assert census["integrityEntryPoints"][0] == {
            "class": "com.pairip.VMRunner",
            "method": None,
            "kind": "manifest-application",
        }

    def test_notes_document_heuristic_and_limits(self):
        census = build_census(
            apk="a",
            version_name="",
            version_code="",
            entry_names=["assets/data.vmcode"],
            dex_scans=[],
            unreadable_dex=[],
        )
        joined = "\n".join(census["notes"])
        assert "VMRunner" in joined
        assert "invoke" in joined and "executeVM" in joined
        assert "limits" in joined.lower()
        assert "data.vmcode" in joined

    def test_scan_error_and_unreadable_dex_notes(self):
        from fakes import FakeClass, FakeMethod
        from pairip_audit.dexscan import scan_dex as _scan

        broken = FakeMethod("x", "Lcom/A;", code_error=RuntimeError("bad"))
        scans = [_scan(FakeDEX([FakeClass("Lcom/A;", [broken])]), "classes2.dex")]
        census = build_census(
            apk="a",
            version_name="",
            version_code="",
            entry_names=[],
            dex_scans=scans,
            unreadable_dex=["classes5.dex"],
        )
        joined = "\n".join(census["notes"])
        assert "1 method(s) could not be disassembled" in joined
        assert "classes5.dex" in joined


class TestBaseNotes:
    def test_static_part(self):
        notes = base_notes([])
        assert any(n.startswith("Stub heuristic:") for n in notes)
        assert len(notes) == 5  # no vmcode line when no assets

    def test_pairip_dotted_prefix_constant(self):
        assert PAIRIP_DOTTED == "com.pairip."


class TestWriteCensus:
    def test_roundtrip(self, tmp_path):
        census = build_census(
            apk="x.apk",
            version_name="1",
            version_code="1",
            entry_names=[],
            dex_scans=[],
            unreadable_dex=[],
        )
        out = tmp_path / "census.json"
        write_census(census, str(out))
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded == census
