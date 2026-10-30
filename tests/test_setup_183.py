"""1.8.3 setup regression: versioned artifacts and no Quartus dependency."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_versioned_installer_references_real_files():
    nsis = (ROOT / "installer/PhoenixForge_183.nsi").read_text(encoding="utf-8")
    assert "PhoenixForge_v1.8.3_Portable.exe" in nsis
    assert "PhoenixForge_v1.8.3_Setup.exe" in nsis
    assert 'DisplayVersion" "1.8.3"' in nsis
    assert "install_osscad_181.ps1" in nsis
    assert "osscad-181.json" in nsis
    assert "RequestExecutionLevel user" in nsis
    assert "quartus_sh.exe" not in nsis


def test_release_gate_checks_183_and_keeps_stable_default():
    from inspect import signature
    from tools.release_gate import verify_release
    from tools.build_setup_183 import VERSION, verify_manifest
    assert signature(verify_release).parameters["expected_version"].default == "1.7.0"
    assert VERSION == "1.8.3"
    manifest = verify_manifest(ROOT)
    assert manifest["version"] == "2026-10-27"
    assert manifest["bytes"] == 603362463


def test_release_workflow_matches_builder():
    workflow = (ROOT / ".github/workflows/ci-windows-183.yml").read_text(encoding="utf-8")
    assert "PF_BUILD_VERSION: '1.8.3'" in workflow
    assert "python tools/release_gate.py --version 1.8.3" in workflow
    assert "python tools/build_setup_183.py" in workflow
    assert "build/setup-183-report.json" in workflow
    script = (ROOT / "tools/build_setup_183.py").read_text(encoding="utf-8")
    assert "build/setup-183-report.json" in script
    assert "installer/osscad-181.json" in script


@pytest.mark.gui
def test_free_fpga_gui_resets_programming_consent(qt_app):
    from app.ui.open_cyclone_panel import OpenCyclonePanel
    panel = OpenCyclonePanel()
    assert not panel.cable.currentText()
    assert not panel.deploy_button.isEnabled()
    for box in (panel.board_ok, panel.external_ok, panel.sram_ok):
        box.setChecked(True)
    panel.clear_deploy_authorization()
    assert not any(box.isChecked() for box in (
        panel.board_ok, panel.external_ok, panel.sram_ok))
    assert hasattr(panel, "detect_yosys")
    panel.close()
