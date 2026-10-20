"""Hardware Studio checks: safe discovery, official installer, compilation and UF2."""
import hashlib
import io
import json
import os
import subprocess
import zipfile
from pathlib import Path
import pytest

from app.hardware import arduino, discovery


def test_usb_classification_conservative():
    uno = discovery.classify_usb("Arduino Uno (COM4)", r"USB\VID_2341&PID_0043\AB")
    assert uno.kind == "Arduino" and uno.port == "COM4"
    uart = discovery.classify_usb("USB Serial CH340 (COM11)", r"USB\VID_1A86&PID_7523\X")
    assert uart.kind == "USB / serie" and uart.confidence == "ambigua"
    jtag = discovery.classify_usb("Altera USB-Blaster", r"USB\VID_09FB&PID_6001\Y")
    assert jtag.kind.startswith("Programador FPGA") and "no identifica" in jtag.note
    pico = discovery.classify_usb("RP2 Boot", r"USB\VID_2E8A&PID_0003\Z")
    assert "Pico" in pico.kind


def test_device_attach_detection_without_auto_install():
    old = [discovery.classify_usb("USB serial (COM3)", r"USB\VID_1A86&PID_7523\A")]
    found = old + [discovery.classify_usb("Arduino Uno (COM4)", r"USB\VID_2341&PID_0043\B")]
    assert discovery.added_devices(old, found) == found[1:]


def test_windows_pnp_json_and_pico_volume(monkeypatch):
    monkeypatch.setattr(discovery.sys, "platform", "win32")
    payloads = [
        [{"Name": "Arduino Uno (COM5)", "PNPDeviceID": r"USB\VID_2341&PID_0043\A", "Status": "OK"}],
        [{"VolumeName": "RPI-RP2", "DeviceID": "E:"}]
    ]
    def fake_runner(cmd, **kwargs):
        assert cmd[0] == "powershell.exe" and kwargs["timeout"] <= 12
        return subprocess.CompletedProcess(cmd, 0, json.dumps(payloads.pop(0)), "")
    found = discovery.list_usb_devices(fake_runner)
    assert {d.kind for d in found} == {"Arduino", "Pico UF2"}
    assert any(d.port == "E:\\" for d in found)


def test_cli_install_pinned_checksum(tmp_path, monkeypatch):
    monkeypatch.setattr(arduino.sys, "platform", "win32")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("arduino-cli.exe", b"fake executable")
    payload = archive.getvalue()
    monkeypatch.setattr(arduino, "CLI_SHA256", hashlib.sha256(payload).hexdigest())
    seen = []
    def downloader(url, timeout=None):
        seen.append(url)
        return io.BytesIO(payload)
    dest = tmp_path / "cli"
    assert arduino.install_cli(downloader, dest) == dest / "arduino-cli.exe"
    assert dest.joinpath("arduino-cli.exe").read_bytes() == b"fake executable"
    assert len(seen) == 1
    assert arduino.install_cli(downloader, dest) == dest / "arduino-cli.exe"
    assert len(seen) == 1


def test_cli_rejects_checksum_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(arduino.sys, "platform", "win32")
    with pytest.raises(ValueError, match="SHA256"):
        arduino.install_cli(lambda *a, **k: io.BytesIO(b"untrusted"), tmp_path / "notinstalled")
    assert not (tmp_path / "notinstalled").exists()


def test_sketch_folder_and_compile_argv(tmp_path):
    folder = arduino.prepare_sketch("void setup(){} void loop(){}", root=tmp_path)
    assert (folder / (folder.name + ".ino")).is_file()
    calls = []
    def fake_runner(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "compiled OK", "")
    assert "compiled OK" in arduino.compile_sketch(folder, "arduino:avr:uno", cli="arduino-cli",
                                                    runner=fake_runner)
    assert calls[0][0][1:4] == ["compile", "--fqbn", "arduino:avr:uno"]
    with pytest.raises(ValueError):
        arduino.upload_sketch(folder, "arduino:avr:uno", "COM4 & rm", cli="arduino-cli", runner=fake_runner)
    (folder.parent / (folder.name + "-build")).mkdir(exist_ok=True)
    assert "uploaded" in arduino.upload_sketch(folder, "arduino:avr:uno", "COM4",
        cli="arduino-cli", runner=lambda args, **kwargs:
        subprocess.CompletedProcess(args, 0, "uploaded", ""))


def test_untrusted_core_and_library_rejected():
    with pytest.raises(ValueError):
        arduino.core_install("untrusted:core")
    with pytest.raises(ValueError):
        arduino.library_install("--something")
    with pytest.raises(ValueError):
        arduino.library_install("bad;shutdown")


def test_board_json_parser():
    sample = {"detected_ports": [{"port": {"address": "COM5"}, "matching_boards":
               [{"name": "Uno", "fqbn": "arduino:avr:uno"}]}]}
    def runner(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, json.dumps(sample), "")
    assert arduino.board_list(cli="arduino-cli", runner=runner)[0]["matching_boards"][0]["fqbn"] == "arduino:avr:uno"


def test_pico_uf2_requires_bootsel_marker_and_no_overwrite(tmp_path):
    firmware = tmp_path / "program.uf2"
    firmware.write_bytes(b"\x55\x46\x32\x0A" * 12)
    target = tmp_path / "pico"
    target.mkdir()
    with pytest.raises(ValueError):
        arduino.copy_uf2(firmware, target)
    (target / "INFO_UF2.TXT").write_text("RP2040")
    assert Path(arduino.copy_uf2(firmware, target)).read_bytes() == firmware.read_bytes()
    with pytest.raises(FileExistsError):
        arduino.copy_uf2(firmware, target)


@pytest.mark.gui
def test_hardware_studio_ui(qt_app):
    from app.ui.hardware_studio import HardwareStudio
    panel = HardwareStudio()
    assert panel.tabs.count() == 3
    assert panel.fqbn.currentText() == "arduino:avr:uno"
    assert "pinMode" in panel.sketch.toPlainText()
    assert panel.worker is None
    panel.timer.stop()
    panel.close()


@pytest.mark.gui
def test_hardware_studio_navigation(qt_app):
    from app.ui.main_window import MainWindow
    window = MainWindow()
    assert window.navigation.item(5).text() == "Hardware Studio"
    assert window.hardware is window.stack.widget(5)
    window.hardware.timer.stop()
    window.dirty = False
    window.close()
