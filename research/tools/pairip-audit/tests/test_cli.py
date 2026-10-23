"""End-to-end CLI tests: synthetic zip APK + mocked androguard layer.

The androguard adapter (pairip_audit.apksource) is monkeypatched with fakes
that read a real synthetic zip (stdlib zipfile), so the whole pipeline --
entry names -> native libs / assets -> dex blueprint scan -> census JSON --
runs without any real APK.
"""

import json
import sys

import pytest
from fakes import (
    FakeAPK,
    FakeDEX,
    build_synthetic_apk,
    pairip_dex_blueprint,
    plain_dex_blueprint,
)

import pairip_audit.apksource as apksource
import run_audit


@pytest.fixture
def patched_androguard(monkeypatch):
    """Replace the androguard APK/DEX symbols used by the adapter."""

    def install(tmp_path, *, blueprint=None, with_pairip_libs=True,
                with_vmcode_assets=True, app_class="com.pairip.application.Application",
                open_error=False):
        apk_path = build_synthetic_apk(
            tmp_path / "app.apk",
            with_pairip_libs=with_pairip_libs,
            with_vmcode_assets=with_vmcode_assets,
        )
        blueprint = blueprint if blueprint is not None else pairip_dex_blueprint()

        holder = {}

        def fake_apk(path):
            holder["apk"] = FakeAPK(
                path,
                app_class=app_class,
                dex_blueprints=[blueprint],
                open_error=open_error,
            )
            return holder["apk"]

        monkeypatch.setattr(apksource, "APK", fake_apk)
        monkeypatch.setattr(apksource, "DEX", lambda blob: FakeDEX(blueprint))
        return apk_path

    return install


class TestHappyPath:
    def test_pairip_apk_exit_zero_and_census(self, tmp_path, patched_androguard, capsys):
        apk = patched_androguard(tmp_path)
        out = tmp_path / "census.json"
        code = run_audit.main([apk, "--out", str(out)])
        assert code == 0
        census = json.loads(out.read_text(encoding="utf-8"))
        assert list(census.keys()) == [
            "apk", "versionName", "versionCode", "pairipDetected",
            "nativeLibs", "pairipNativeLibs", "pairipClasses", "dexStats",
            "integrityEntryPoints", "notes",
        ]
        assert census["pairipDetected"] is True
        assert census["versionName"] == "25.21.1"
        assert census["versionCode"] == 250211
        assert census["nativeLibs"]["arm64-v8a"] == [
            "libother.so", "libpairipcore.so",
        ]
        assert census["pairipNativeLibs"] == {
            "arm64-v8a": ["libpairipcore.so"],
            "armeabi-v7a": ["libpairipcore.so"],
        }
        assert "com.pairip.VMRunner" in census["pairipClasses"]
        assert census["dexStats"]["stubMethods"] == 2
        assert census["dexStats"]["totalMethods"] == 10
        assert census["dexStats"]["perDex"][0]["dex"] == "classes.dex"
        kinds = [e["kind"] for e in census["integrityEntryPoints"]]
        assert kinds[0] == "manifest-application"
        assert "load-pairipcore" in kinds and "pairip-call" in kinds
        # summary line printed
        captured = capsys.readouterr()
        assert "pairipDetected=True" in captured.out
        assert str(out) in captured.out

    def test_pairip_free_apk_still_exit_zero(self, tmp_path, patched_androguard):
        apk = patched_androguard(
            tmp_path,
            blueprint=plain_dex_blueprint(),
            with_pairip_libs=False,
            with_vmcode_assets=False,
            app_class="com.example.app.Main",
        )
        out = tmp_path / "census.json"
        code = run_audit.main([apk, "--out", str(out)])
        assert code == 0
        census = json.loads(out.read_text(encoding="utf-8"))
        assert census["pairipDetected"] is False
        assert census["pairipNativeLibs"] == {}
        assert census["pairipClasses"] == []
        assert census["dexStats"]["stubMethods"] == 0


class TestErrorPaths:
    def test_missing_file_exits_1(self, tmp_path, capsys):
        code = run_audit.main([str(tmp_path / "nope.apk"), "--out", str(tmp_path / "o.json")])
        assert code == 1
        assert "no such file" in capsys.readouterr().err

    def test_unreadable_zip_exits_1(self, tmp_path, patched_androguard, capsys):
        apk = patched_androguard(tmp_path, open_error=True)
        code = run_audit.main([apk, "--out", str(tmp_path / "o.json")])
        assert code == 1
        assert "failed to open APK" in capsys.readouterr().err

    def test_unwritable_out_exits_1(self, tmp_path, patched_androguard, capsys):
        apk = patched_androguard(tmp_path)
        bad_out = tmp_path / "missing-dir" / "census.json"
        code = run_audit.main([apk, "--out", str(bad_out)])
        assert code == 1
        assert "cannot write" in capsys.readouterr().err

    def test_usage_error_exits_2(self, capsys):
        with pytest.raises(SystemExit) as exc:
            run_audit.main([])
        assert exc.value.code == 2


class TestParser:
    def test_flags(self):
        parser = run_audit.build_parser()
        args = parser.parse_args(["x.apk", "--out", "y.json"])
        assert args.apk == "x.apk"
        assert args.out == "y.json"

    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc:
            run_audit.main(["--version"])
        assert exc.value.code == 0
        assert run_audit.__version__ in capsys.readouterr().out


def test_sys_path_bootstrap():
    # run_audit must be importable and place its own dir on sys.path
    assert "pairip_audit" in sys.modules
    assert any(p.endswith("pairip-audit") for p in sys.path)
