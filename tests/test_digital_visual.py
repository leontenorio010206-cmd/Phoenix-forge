"""The visual exporter must reflect the module and preserve real HDL output."""
import json
import xml.etree.ElementTree as ET
import zipfile
import pytest

from app.core.examples import adder_project
from app.exporters.digital_hdl import digital_component_files
from app.exporters.digital_symbol import build_component_svg


def test_dynamic_symbol_svg_has_real_ports():
    project = adder_project()
    package = digital_component_files(project)
    symbol = ET.fromstring(package["symbol.svg"])
    wiring = ET.fromstring(package["connections.svg"])
    assert symbol.tag.endswith("svg") and wiring.tag.endswith("svg")
    for name in ("full_adder", "a", "b", "cin", "sum", "cout"):
        assert name.encode("utf-8") in package["symbol.svg"]
    assert b"SWITCH / BUS" in package["connections.svg"]
    assert b"LED / BUS" in package["connections.svg"]
    assert b"module full_adder" in package["component.v"]
    assert "timing" in json.loads(package["ports.json"])["scope"]


def test_bus_width_and_xml_escape():
    src = build_component_svg("A&B", [
        {"name": "address", "direction": "input", "width": 12},
        {"name": "enabled", "direction": "output", "width": 1},
    ])
    ET.fromstring(src)
    assert b"A&amp;B" in src
    assert b"address [12]" in src


@pytest.mark.gui
def test_digital_visual_studio_and_export(qt_app, tmp_path, monkeypatch):
    from app.ui.qt import QtWidgets as W
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.new_adder()
    window.navigate(4)
    qt_app.processEvents()
    assert window.navigation.item(4).text() == "Exportar a Digital"
    panel = window.digital_export
    assert panel.pin_table.rowCount() == 5
    assert panel.top.currentText() == "full_adder"
    assert panel.symbol.renderer.isValid()
    assert panel.wiring.renderer.isValid()
    destination = tmp_path / "fpga_Digital.zip"
    messages = []
    monkeypatch.setattr(W.QFileDialog, "getSaveFileName", lambda *a, **k: (str(destination), ""))
    monkeypatch.setattr(W.QMessageBox, "information", lambda *a, **k: messages.append(a))
    panel.export_button.click()
    assert destination.is_file()
    assert panel.folder_button.isEnabled()
    with zipfile.ZipFile(destination) as archive:
        assert "symbol.svg" in archive.namelist()
        assert "connections.svg" in archive.namelist()
        assert "component.v" in archive.namelist()
        assert archive.read("component.v").startswith(b"// Origen:")
    assert messages
    panel.virtual_requested.emit()
    assert window.navigation.currentRow() == 2
    assert window.devices.tabs.currentIndex() == 1
    window.dirty = False
    window.close()
