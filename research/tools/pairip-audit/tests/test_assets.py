"""Tests for pairip_audit.assets (pure logic + synthetic zip fixture)."""

import zipfile

from fakes import build_synthetic_apk
from pairip_audit.assets import find_vmcode_assets


def test_finds_vmcode_assets_sorted_and_deduped():
    entries = [
        "assets/zeta.vmcode",
        "assets/alpha.vmcode",
        "assets/alpha.vmcode",
        "assets/nested/deep.vmcode",
    ]
    assert find_vmcode_assets(entries) == [
        "assets/alpha.vmcode",
        "assets/nested/deep.vmcode",
        "assets/zeta.vmcode",
    ]


def test_ignores_non_vmcode_entries():
    entries = [
        "assets/readme.txt",
        "assets/data.bin",
        "lib/arm64-v8a/data.vmcode",  # must live under assets/
        "assets/vmcode",  # not the suffix
        "",
        None,
    ]
    assert find_vmcode_assets(entries) == []


def test_empty_and_none_inputs():
    assert find_vmcode_assets([]) == []
    assert find_vmcode_assets(None) == []


def test_synthetic_zip_entries(tmp_path):
    apk = build_synthetic_apk(tmp_path / "app.apk")
    with zipfile.ZipFile(apk) as zf:
        names = zf.namelist()
    assert find_vmcode_assets(names) == ["assets/b4f5k.vmcode", "assets/other.vmcode"]
