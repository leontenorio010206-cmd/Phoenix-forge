"""Vendor-neutral read-only FPGA discovery and capability matrix."""
import subprocess

import pytest

from app.hardware import universal_fpga as universal


def test_identification_is_explicitly_tentative():
    found = universal.infer_from_jtag(
        "JTAG scan: idcode 020F30DD detected EP4CE6")
    assert found["key"] == "cyclone_iv"
    assert found["detected_part"] == "EP4CE6"
    assert "tentativa" in found["confidence"]
    assert "Quartus" in found["builder"]
    assert universal.infer_from_jtag("unknown device 0x12345678")["key"] == "unknown"
    for sample, key in (("XC7A35T", "xilinx7"),
                        ("LFE5U-25F", "ecp5"),
                        ("GW1NR-LV9", "gowin"),
                        ("iCE40HX1K", "ice40")):
        assert universal.infer_from_jtag("JTAG " + sample)["key"] == key


def test_usb_adapter_never_becomes_board_or_part():
    cable, warning = universal.suggest_cable_for_usb(
        r"USB\VID_09FB&PID_6001\DEV")
    assert cable == "usb-blaster"
    assert "NO identifica" in warning
    cable, warning = universal.suggest_cable_for_usb(
        r"USB\VID_0403&PID_6010\DEV")
    assert cable is None and "FTDI" in warning
    assert universal.suggest_cable_for_usb("unrelated")[0] is None


def test_optional_toolchains_do_not_enable_unverified_hardware():
    detected = {
        "yosys": "/fake/yosys", "nextpnr-ice40": "/fake/nextpnr",
        "icepack": "/fake/icepack", "quartus_sh": "/fake/quartus_sh",
        "quartus_pgm": "/fake/quartus_pgm", "jtagconfig": "/fake/jtagconfig",
    }
    inventory = universal.toolchain_inventory(which=lambda name: detected.get(name))
    assert inventory["icepack"] == "/fake/icepack"
    matrix = {row["key"]: row for row in universal.capability_inventory(inventory)}
    assert matrix["ice40"]["tools_installed"] is True
    assert matrix["ice40"]["integrated"] is False
    assert matrix["cyclone_iv"]["tools_installed"] is True
    assert matrix["cyclone_iv"]["integrated"] is True
    assert all(not row["ready_for_hardware"] for row in matrix.values())


def test_probe_only_issues_detect_and_never_writes(tmp_path):
    exe = tmp_path / "openFPGALoader.exe"
    exe.touch()
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(
            args, 0, "IDCODE 020F30DD part EP4CE6", "")

    survey = universal.inspect_cable(
        "usb-blaster", loader=str(exe), runner=fake_run)
    assert survey["match"]["key"] == "cyclone_iv"
    assert survey["board_identified"] is False
    assert survey["pins_identified"] is False
    assert survey["programming_allowed"] is False
    assert calls == [[str(exe), "--detect", "-c", "usb-blaster"]]
    description = universal.describe_survey(survey)
    assert "BLOQUEADA" in description
    assert "PIN" not in description or "NO IDENTIFICADAS" in description
    with pytest.raises(ValueError):
        universal.inspect_cable("usb-blaster; rm", loader=str(exe), runner=fake_run)
    assert len(calls) == 1


@pytest.mark.gui
def test_universal_tab_exists_without_usb_probe(qt_app):
    from app.ui.hardware_studio import HardwareStudio
    panel = HardwareStudio()
    panel.timer.stop()
    assert panel.tabs.tabText(3) == "FPGA universal"
    widget = panel.tabs.widget(3)
    assert widget.worker is None
    assert widget.cable.currentText() == ""
    assert widget.last_survey is None
    widget.show_capabilities()
    assert "FAMILIAS Y ESTADO REAL" in widget.capabilities.toPlainText()
    panel.close()
