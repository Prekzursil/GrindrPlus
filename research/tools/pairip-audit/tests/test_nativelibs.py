"""Tests for pairip_audit.nativelibs (pure logic + synthetic zip fixture)."""

import zipfile

from fakes import build_synthetic_apk
from pairip_audit.nativelibs import filter_pairip_libs, is_pairip_lib, map_native_libs


class TestMapNativeLibs:
    def test_groups_by_abi_and_sorts(self):
        entries = [
            "lib/arm64-v8a/libz.so",
            "lib/arm64-v8a/libpairipcore.so",
            "lib/armeabi-v7a/libfoo.so",
        ]
        assert map_native_libs(entries) == {
            "arm64-v8a": ["libpairipcore.so", "libz.so"],
            "armeabi-v7a": ["libfoo.so"],
        }

    def test_deduplicates_repeated_entries(self):
        entries = ["lib/x86/liba.so", "lib/x86/liba.so", "lib/x86/libb.so"]
        assert map_native_libs(entries) == {"x86": ["liba.so", "libb.so"]}

    def test_ignores_non_lib_entries(self):
        entries = [
            "AndroidManifest.xml",
            "classes.dex",
            "assets/b4f5k.vmcode",
            "lib/notasofile.txt",
            "lib/nested/abi/libdeep.so",  # abi must be a single path segment
            "META-INF/com/foo/lib/fake.so",
            "",
            None,
        ]
        assert map_native_libs(entries) == {}

    def test_empty_and_none_inputs(self):
        assert map_native_libs([]) == {}
        assert map_native_libs(None) == {}

    def test_synthetic_zip_entries(self, tmp_path):
        apk = build_synthetic_apk(tmp_path / "app.apk")
        with zipfile.ZipFile(apk) as zf:
            names = zf.namelist()
        libs = map_native_libs(names)
        assert libs["arm64-v8a"] == ["libother.so", "libpairipcore.so"]
        assert libs["armeabi-v7a"] == ["libother.so", "libpairipcore.so"]
        assert "x86" not in libs


class TestIsPairipLib:
    def test_pairip_runtime_lib(self):
        assert is_pairip_lib("libpairipcore.so") is True

    def test_case_insensitive(self):
        assert is_pairip_lib("libPairipCore.so") is True

    def test_plain_libs(self):
        assert is_pairip_lib("libnative.so") is False
        assert is_pairip_lib("") is False
        assert is_pairip_lib(None) is False


class TestFilterPairipLibs:
    def test_keeps_only_pairip_abis(self):
        libs = {
            "arm64-v8a": ["libpairipcore.so", "libz.so"],
            "x86": ["libz.so"],
        }
        assert filter_pairip_libs(libs) == {"arm64-v8a": ["libpairipcore.so"]}

    def test_empty(self):
        assert filter_pairip_libs({}) == {}
        assert filter_pairip_libs(None) == {}
