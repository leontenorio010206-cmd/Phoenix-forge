"""Arduino 1.6.1: dynamic catalogue, accurate USB wording and library updates."""
import json
import subprocess
from app.hardware import arduino, discovery
from app.hardware.arduino_catalog import (
    BASIC_PACK, CORE_HEADERS, EXAMPLES, model_shortcuts, merge_catalog
)
import pytest


def test_original_vs_clone_not_authenticated():
    official = discovery.classify_usb("Arduino Uno (COM5)", r"USB\VID_2341&PID_0043\X")
    assert "Arduino" in official.origin
    assert "no verificable" in official.origin
    compatible = discovery.classify_usb("Arduino CH340 (COM8)", r"USB\VID_1A86&PID_7523\X")
    assert "Compatible/clon posible" in compatible.origin
    assert compatible.kind == "USB / serie"
    other = discovery.classify_usb("USB SERIAL CH340 (COM4)", r"USB\VID_1A86&PID_7523\X")
    assert "origen no verificable" in other.origin


def test_bundled_catalog_and_sketches():
    shortcuts = model_shortcuts()
    fqbn = [entry[1] for entry in shortcuts]
    assert len(fqbn) >= 20 and len(fqbn) == len(set(fqbn))
    assert "arduino:avr:uno" in fqbn
    assert "arduino:renesas_uno:unor4wifi" in fqbn
    assert "Wire.h" in CORE_HEADERS and "SPI.h" in CORE_HEADERS
    assert "ArduinoJson" in BASIC_PACK and "Servo" in BASIC_PACK
    for name, content in EXAMPLES.items():
        assert "void setup()" in content and "void loop()" in content


def test_dynamic_board_listall_adds_new_models():
    response = {"boards": [
        {"name": "New Arduino board", "fqbn": "arduino:newfamily:myboard"},
        {"name": "Uno R3 updated", "fqbn": "arduino:avr:uno"},
        {"name": "Invalid", "fqbn": "invalid"},
    ]}
    calls = []
    def runner(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(response), "")
    output = arduino.board_listall(cli="arduino-cli", runner=runner)
    assert ["arduino", "board", "listall", "--json"] == calls[0] or calls[0][1:] == ["board", "listall", "--json"]
    assert any(x[1] == "arduino:newfamily:myboard" for x in output)
    assert next(x[0] for x in output if x[1] == "arduino:avr:uno") == "Uno R3 updated"
    assert all(x[1] != "invalid" for x in output)


def test_installed_library_inventory():
    response = {"installed_libraries": [
        {"library": {"name": "Servo", "version": "1.2.2"}},
        {"library": {"name": "Wire", "version": "builtin"}},
    ]}
    def runner(args, **kwargs):
        assert args[1:] == ["lib", "list", "--all", "--json"]
        return subprocess.CompletedProcess(args, 0, json.dumps(response), "")
    assert len(arduino.library_list(cli="arduino-cli", runner=runner)) == 2


def test_library_search_and_update_call_official_cli():
    calls = []
    def runner(args, **kwargs):
        calls.append(args[1:])
        return subprocess.CompletedProcess(args, 0, "OK", "")
    assert "OK" in arduino.library_search("ArduinoJson", cli="cli", runner=runner)
    arduino.upgrade_libraries(cli="cli", runner=runner)
    assert calls == [
        ["lib", "search", "--names", "ArduinoJson"],
        ["lib", "update-index"], ["lib", "upgrade"]
    ]
    with pytest.raises(ValueError):
        arduino.library_search("")


def test_basic_pack_installs_each_name_and_reports_partial_errors():
    calls = []
    def runner(args, **kwargs):
        calls.append(args[1:])
        if args[1:4] == ["lib", "install", "Servo"]:
            return subprocess.CompletedProcess(args, 1, "", "intentional failure")
        return subprocess.CompletedProcess(args, 0, "OK", "")
    result = arduino.install_starter_pack(cli="cli", runner=runner)
    assert len([x for x in calls if x[:2] == ["lib", "update-index"]]) == 1
    assert len([x for x in calls if x[:2] == ["lib", "install"]]) == len(BASIC_PACK)
    assert len(result["failed"]) == 1
    assert result["failed"][0][0] == "Servo"


@pytest.mark.gui
def test_hardware_catalog_ui_and_examples(qt_app, monkeypatch):
    from app.ui.hardware_studio import HardwareStudio
    panel = HardwareStudio()
    panel.timer.stop()
    assert panel.tabs.count() == 5
    assert panel.tabs.tabText(3) == "Cyclone IV / Quartus"
    assert panel.models.topLevelItemCount() == len(model_shortcuts())
    panel.model_filter.setText("Uno R4")
    assert panel.models.topLevelItemCount() == 2
    item = panel.models.topLevelItem(0)
    panel.choose_model(item)
    assert panel.fqbn.currentText().startswith("arduino:renesas_uno:")
    assert panel.core.currentText() == "arduino:renesas_uno"
    panel._got_model_catalog(merge_catalog(model_shortcuts(), [
        {"name": "Future board", "fqbn": "arduino:future:board"}]))
    assert panel.fqbn.findText("arduino:future:board") >= 0
    monkeypatch.setattr(panel, "_confirm", lambda *args: True)
    panel.example.setCurrentText("Serial")
    panel.apply_example()
    assert "Serial.begin" in panel.sketch.toPlainText()
    panel.close()
