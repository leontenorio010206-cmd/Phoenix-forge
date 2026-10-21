"""Linux portability contract; real frozen acceptance runs separately in CI."""
from pathlib import Path
import shutil
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_linux_port_has_no_windows_binary_runtime_dependency():
    from app.utils.paths import bundled_icarus
    if sys.platform == "linux":
        assert bundled_icarus() is None
    assert "iverilog" in (ROOT / "linux/run-phoenixforge.sh").read_text(encoding="utf-8")
    assert "vvp" in (ROOT / "linux/run-phoenixforge.sh").read_text(encoding="utf-8")


def test_linux_port_uses_frozen_self_test_not_merely_successful_import():
    source = (ROOT / "tools/build_linux.py").read_text(encoding="utf-8")
    assert "--self-test" in source
    assert "--offscreen" in source
    assert "project_roundtrip" in source
    assert "hdl_and_vcd" in source
    assert "sha256" in source


def test_linux_port_rejects_non_linux_or_missing_simulator(monkeypatch):
    import tools.build_linux as build
    monkeypatch.setattr(build.sys, "platform", "win32")
    with pytest.raises(RuntimeError, match="native Linux"):
        build.require_linux()
    monkeypatch.setattr(build.sys, "platform", "linux")
    monkeypatch.setattr(build.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(build.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="Icarus"):
        build.require_linux()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux only")
def test_linux_native_icarus_compiles_real_source(tmp_path):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus Linux not installed")
    from app.core.examples import adder_project
    from app.simulators.icarus import IcarusEngine
    result = IcarusEngine().run(adder_project(), root=tmp_path)
    assert result.success, result.output
    assert "PASS: 8" in result.output
