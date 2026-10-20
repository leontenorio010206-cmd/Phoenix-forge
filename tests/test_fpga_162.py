"""FPGA v1.6.2: driver inspection, catalog, probe and programming boundaries."""
from pathlib import Path
import subprocess
import pytest

from app.hardware import fpga


def test_probe_vendor_identification_is_not_chip_detection():
    name, note = fpga.cable_hint("USB-Blaster", r"USB\VID_09FB&PID_6001\TEST")
    assert "USB-Blaster" in name
    assert "chip FPGA" in note
    clone, clone_note = fpga.cable_hint("Clone Blaster", r"USB\VID_09FB&PID_6001&MI_00\TEST")
    assert "MI_00" in clone_note and "copias" in clone_note
    bridge, detail = fpga.cable_hint("USB UART", r"USB\VID_0403&PID_6010\TEST")
    assert "FTDI" in bridge and "not necessarily" in detail
    assert fpga.cable_hint("Unknown", r"USB\VID_1234&PID_7777\TEST")[0] == "No identificado"


def test_driver_report_reads_only_exact_interface_and_does_not_change_driver(monkeypatch):
    monkeypatch.setattr(fpga.sys, "platform", "win32")
    identity = r"USB\VID_09FB&PID_6001&MI_00\TOKEN"
    calls = []
    payloads = [
        [{"DeviceID": identity, "DeviceName": "Intel JTAG",
          "DriverProviderName": "Vendor", "DriverVersion": "1.2",
          "InfName": "oem30.inf"}],
        [{"PNPDeviceID": identity, "Name": "USB Blaster", "Service": "libusbK",
          "Status": "OK", "ConfigManagerErrorCode": 0}],
    ]
    import json
    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(payloads.pop(0)), "")
    report = fpga.driver_report(identity, runner=fake_run)
    assert report["service"] == "libusbk" and report["provider"] == "Vendor"
    assert report["inf"] == "oem30.inf" and report["problem_code"] == 0
    assert report["driver_installation"].startswith("No se instalaron")
    assert len(calls) == 2 and all("-Command" in call for call in calls)
    assert all("Get-CimInstance" in call[-1] for call in calls)


def test_driver_reports_problem_code(monkeypatch):
    monkeypatch.setattr(fpga.sys, "platform", "win32")
    identity = r"USB\VID_0403&PID_6010\FOO"
    import json
    payloads = [[{"DeviceID": identity, "DriverProviderName": "FTDI"}],
                [{"PNPDeviceID": identity, "Service": "FTDIBUS",
                  "ConfigManagerErrorCode": 28, "Status": "Error"}]]
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, json.dumps(payloads.pop(0)), "")
    result = fpga.driver_report(identity, runner=fake_run)
    assert result["problem_code"] == 28
    assert any("28" in note for note in result["alerts"])
    assert any("serie" in note for note in result["alerts"])
    with pytest.raises(ValueError):
        fpga.driver_report("FAKE;Remove-Item C:\\", runner=fake_run)


def test_tool_supports_dynamic_board_cable_chip_lists(tmp_path):
    loader = tmp_path / "openFPGALoader.exe"
    loader.write_bytes(b"fake")
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "KNOWN " + args[-1], "")
    result = fpga.catalog(loader, runner=fake_run)
    assert list(result) == ["boards", "cables", "fpga"]
    assert [call[-1] for call in calls] == ["--list-boards", "--list-cables", "--list-fpga"]
    assert all(call[0] == str(loader) for call in calls)


def test_probe_is_readonly_and_sanitizes_target(tmp_path):
    loader = tmp_path / "openFPGALoader.exe"
    loader.write_bytes(b"fake")
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "JTAG IDCODE", "")
    assert "IDCODE" in fpga.probe_target("tangnano9k", executable=loader, runner=fake_run)
    assert calls[0][1:] == ["--detect", "-b", "tangnano9k"]
    assert "IDCODE" in fpga.probe_target("usb-blaster", via="cable",
                                        executable=loader, runner=fake_run)
    assert calls[1][1:] == ["--detect", "-c", "usb-blaster"]
    with pytest.raises(ValueError):
        fpga.probe_target("bad;echo danger", executable=loader, runner=fake_run)


def test_program_firmware_requires_valid_path_and_explicit_arguments(tmp_path):
    loader = tmp_path / "openFPGALoader.exe"
    loader.write_bytes(b"fake")
    firmware = tmp_path / "Gowin.fs"
    firmware.write_bytes(b"PLACEHOLDER_TEST_ONLY")
    recorded = []
    def fake_run(args, **kwargs):
        recorded.append(args)
        return subprocess.CompletedProcess(args, 0, "Success", "")
    assert fpga.program_target("tangnano9k", firmware, executable=loader, runner=fake_run) == "Success"
    assert recorded[0][1:4] == ["-b", "tangnano9k", "-m"]
    assert recorded[0][4] == str(firmware)
    fpga.program_target("usb-blaster", firmware, via="cable", flash=True, executable=loader,
                        runner=fake_run)
    assert recorded[1][1:4] == ["-c", "usb-blaster", "-f"]
    bad = tmp_path / "bad.txt"
    bad.write_text("test")
    with pytest.raises(ValueError):
        fpga.program_target("tangnano9k", bad, executable=loader, runner=fake_run)
    with pytest.raises(ValueError):
        fpga.program_target("bad;sh", firmware, executable=loader, runner=fake_run)
    with pytest.raises(ValueError):
        fpga.find_loader(tmp_path / "not-an-fpga.exe")


def test_fpga_examples_are_quickstarts_not_claims_of_global_support():
    board_names = [x[1] for x in fpga.examples()]
    assert len(set(board_names)) == len(board_names)
    assert "tangnano9k" in board_names and "qmtechCycloneIV" in board_names


@pytest.mark.gui
def test_fpga_studio_ui_no_implicit_install(qt_app):
    from app.ui.hardware_studio import HardwareStudio
    panel = HardwareStudio()
    panel.timer.stop()
    assert panel.tabs.tabText(2) == "FPGA / Drivers"
    assert panel.fpga_via.currentIndex() == 0
    assert panel.fpga_target.findText("tangnano9k") >= 0
    panel.fpga_via.setCurrentIndex(1)
    assert panel.fpga_target.findText("usb-blaster") >= 0
    assert panel.fpga_catalog_text.isReadOnly()
    assert panel.fpga_driver_text.isReadOnly()
    assert panel.worker is None
    panel.close()
