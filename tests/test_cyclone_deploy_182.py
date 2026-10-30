"""1.8.2: external RBF provenance and SRAM-only programming safety."""
import json
from pathlib import Path
import subprocess
import pytest

from app.core.project import Project
from app.integrations import cyclone_deploy


@pytest.fixture
def project():
    return Project(
        name="FPGA board demo", device="cyclone_iv",
        files={"main.v": "module led(input clk, output y); assign y=clk; endmodule"},
        simulation={"top": "led", "testbench": "", "timeout": 15},
        pins={"clk": "PIN_E1", "y": "PIN_G15"})


def firmware(path):
    result = path / "external.rbf"
    result.write_bytes(bytes(range(256)) * 400)
    return result


def stage(project, tmp_path):
    root = tmp_path / "staged"
    result = cyclone_deploy.stage_external_rbf(
        project, firmware(tmp_path), root, "EP4CE6F17C8", "AX301 rev 2",
        pins_confirmed=True, voltage_confirmed=True)
    return root, result


def test_rbf_package_stores_real_sha256_and_unverified_origin(project, tmp_path):
    root, data = stage(project, tmp_path)
    record, binfile = cyclone_deploy.inspect_staged(root)
    assert data["source"] == "EXTERNAL_RBF_UNVERIFIED"
    assert record["rbf_sha256"] == cyclone_deploy.digest(binfile)
    assert binfile.read_bytes() == (bytes(range(256)) * 400)
    assert record["part"] == "EP4CE6F17C8"
    assert record["pins"] == {"clk": "PIN_E1", "y": "PIN_G15"}
    assert record["programming_automatic"] is False
    with pytest.raises(FileExistsError):
        cyclone_deploy.stage_external_rbf(
            project, binfile, root, "EP4CE6F17C8", "AX301 rev 2",
            pins_confirmed=True, voltage_confirmed=True)


def test_rejects_unverified_board_and_pins(project, tmp_path):
    file = firmware(tmp_path)
    with pytest.raises(ValueError, match="Confirma"):
        cyclone_deploy.stage_external_rbf(
            project, file, tmp_path/"bad", "EP4CE6F17C8", "AX301 rev 2")
    project.pins = {}
    with pytest.raises(ValueError, match="pines físicos"):
        cyclone_deploy.stage_external_rbf(
            project, file, tmp_path/"bad", "EP4CE6F17C8", "AX301 rev 2",
            pins_confirmed=True, voltage_confirmed=True)


def test_modified_rbf_never_reaches_jtag(project, tmp_path):
    root, data = stage(project, tmp_path)
    (root/"firmware.rbf").write_bytes(b"broken")
    with pytest.raises(ValueError, match="Tamaño"):
        cyclone_deploy.inspect_staged(root)
    with pytest.raises(ValueError):
        cyclone_deploy.deploy_sram(root, "usb-blaster", "EP4CE6F17C8",
                                  confirmed_board=True,
                                  confirmed_external_bitstream=True,
                                  confirmed_sram_only=True)


def test_jtag_requires_one_recognized_id_and_no_conflicting_part():
    allowed = cyclone_deploy.jtag_preflight(
        "Found EP4CE6F17C8\nIDCODE: 0x020830DD", "EP4CE6F17C8")
    assert allowed["jtag_idcode"] == "020830DD"
    assert allowed["jtag_exact_part_verified"] is False
    for text in ("Unknown device with IDCODE: 0x020830DD",
                 "No cable found",
                 "IDCODE: 0x020830DD\nIDCODE: 0x020840DD",
                 "Found EP4CE10F17C8 IDCODE: 0x020830DD"):
        with pytest.raises(RuntimeError):
            cyclone_deploy.jtag_preflight(text, "EP4CE6F17C8")


def test_deployment_rechecks_jtag_and_writes_sram_only(project, tmp_path):
    root, data = stage(project, tmp_path)
    loader = tmp_path / "openFPGALoader.exe"
    loader.write_bytes(b"stub")
    calls = []

    def fake(argv, **kwargs):
        calls.append(list(argv))
        assert kwargs.get("env") is not None
        if "--detect" in argv:
            return subprocess.CompletedProcess(argv, 0, "Found EP4CE6F17C8\nIDCODE: 0x020830DD", "")
        if "-m" in argv:
            return subprocess.CompletedProcess(argv, 0, "RAM configured", "")
        return subprocess.CompletedProcess(argv, 1, "", "Unexpected command")

    with pytest.raises(PermissionError):
        cyclone_deploy.deploy_sram(
            root, "usb-blaster", "EP4CE6F17C8",
            confirmed_board=True, confirmed_external_bitstream=False,
            confirmed_sram_only=True, loader=loader, runner=fake)
    assert calls == []
    with pytest.raises(ValueError, match="marcado"):
        cyclone_deploy.deploy_sram(
            root, "usb-blaster", "EP4CE10F17C8",
            confirmed_board=True, confirmed_external_bitstream=True,
            confirmed_sram_only=True, loader=loader, runner=fake)
    assert calls == []
    result = cyclone_deploy.deploy_sram(
        root, "usb-blaster", "EP4CE6F17C8",
        confirmed_board=True, confirmed_external_bitstream=True,
        confirmed_sram_only=True, loader=loader, runner=fake)
    assert result["status"] == "sram_configuration_sent"
    assert result["flash_written"] is False
    assert result["verification_on_silicon"] is False
    assert len(calls) == 2
    assert "--detect" in calls[0]
    assert "-m" in calls[1] and "-f" not in calls[1]
    assert calls[1][-1].endswith("firmware.rbf")


def test_unknown_jtag_or_error_prevents_write(project, tmp_path):
    root, data = stage(project, tmp_path)
    loader = tmp_path/"openFPGALoader.exe"
    loader.touch()
    calls = []
    def fake(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(
            argv, 1, "", "Unknown device with IDCODE: 0x020830DD")
    with pytest.raises(RuntimeError):
        cyclone_deploy.deploy_sram(
            root, "usb-blaster", "EP4CE6F17C8",
            confirmed_board=True, confirmed_external_bitstream=True,
            confirmed_sram_only=True, loader=loader, runner=fake)
    assert len(calls) == 1
    assert "-m" not in calls[0]


@pytest.mark.gui
def test_ui_does_not_enable_deployment_without_provenance(qt_app):
    from app.ui.open_cyclone_panel import OpenCyclonePanel
    panel = OpenCyclonePanel()
    assert panel.staged_folder is None
    assert not panel.deploy_button.isEnabled()
    assert not panel.board_ok.isChecked()
    assert not panel.sram_ok.isChecked()
    assert "SRAM" in panel.deploy_button.text()
    panel.close()
