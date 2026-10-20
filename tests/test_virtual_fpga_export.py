"""Native Icarus tests for virtual FPGA inputs and Digital HDL packages."""
import json
import zipfile
import pytest

from app.core.examples import adder_project
from app.devices.catalog import load_profiles
from app.devices.simulation import device_demo_project
from app.exporters.digital_hdl import digital_component_files, export_digital_component
from app.simulators.icarus import IcarusEngine
from app.simulators.virtual_fpga import (
    PROBE_FILE, make_probe_project, outputs_from_result, select_ports,
)


@pytest.mark.parametrize("device", list(load_profiles()))
def test_virtual_probe_for_ten_profiles(device):
    project = device_demo_project(device)
    original = dict(project.files)
    trial = make_probe_project(project, {"reset": 1}, clock="clk", cycles=2)
    assert project.files == original
    assert trial.device == device
    assert trial.simulation["testbench"] == "pf_virtual_probe"
    assert "$dumpfile" in trial.files[PROBE_FILE]
    assert "PF_OUT:leds=%b" in trial.files[PROBE_FILE]


def test_virtual_probe_checks_port_values():
    project = adder_project()
    top, pins = select_ports(project)
    assert top == "full_adder" and len(pins) == 5
    with pytest.raises(ValueError, match="rango"):
        make_probe_project(project, {"a": 2})
    with pytest.raises(ValueError, match="Entrada"):
        make_probe_project(project, {"fake_pin": 1})
    with pytest.raises(ValueError, match="reloj"):
        make_probe_project(project, {}, cycles=2)
    trial = make_probe_project(project, {"a": 1, "b": 1, "cin": 0})
    assert "pf_virtual_probe" in trial.files[PROBE_FILE]


@pytest.mark.hdl
def test_virtual_probe_runs_real_iverilog(tmp_path):
    engine = IcarusEngine()
    if not engine.available:
        pytest.skip("Icarus no disponible")
    project = adder_project()
    top, pins = select_ports(project)
    result = engine.run(make_probe_project(project, {"a": 1, "b": 1, "cin": 0}), root=tmp_path)
    assert result.success, result.output
    assert outputs_from_result(result, pins) == {"sum": "0", "cout": "1"}
    assert any(n.endswith(".vcd") for n in result.artifacts)


@pytest.mark.hdl
def test_virtual_fpga_clocked_counter(tmp_path):
    engine = IcarusEngine()
    if not engine.available:
        pytest.skip("Icarus no disponible")
    project = device_demo_project("ice40_up5k")
    _, pins = select_ports(project)
    result = engine.run(make_probe_project(project, {"reset": 1}, clock="clk", cycles=2), root=tmp_path)
    assert result.success, result.output
    assert outputs_from_result(result, pins)["leds"] == "0000"



def test_windows_crlf_probe_output_parser():
    from app.simulators.icarus import SimulationResult
    result = SimulationResult(True, "", output="PF_OUT:sum=0\r\nPF_OUT:cout=1\r\n")
    _, pins = select_ports(adder_project())
    assert outputs_from_result(result, pins) == {"sum": "0", "cout": "1"}



def test_export_digital_component_real_hdl(tmp_path):
    project = adder_project()
    files = digital_component_files(project)
    assert set(files) == {"component.v", "ports.json", "LEEME_DIGITAL.txt", "symbol.svg", "connections.svg"}
    assert b"module full_adder" in files["component.v"]
    assert b"module tb_full_adder" not in files["component.v"]
    manifest = json.loads(files["ports.json"])
    assert manifest["top"] == "full_adder"
    assert len(manifest["ports"]) == 5
    assert manifest["symbol_preview"] == "symbol.svg"
    assert manifest["wiring_preview"] == "connections.svg"
    archive = tmp_path / "digital.zip"
    export_digital_component(project, archive)
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.read("component.v") == files["component.v"]
    with pytest.raises(FileExistsError):
        export_digital_component(project, archive)
    assert not (tmp_path / "plugin.jar").exists()


def test_export_digital_rejects_unsafe_include():
    project = adder_project()
    project.files["full_adder.v"] += '\n`include "../external.vh"\n'
    with pytest.raises(ValueError):
        digital_component_files(project)


@pytest.mark.gui
def test_virtual_fpga_gui_attached(qt_app):
    from app.ui.main_window import MainWindow
    window = MainWindow()
    window.devices.tabs.setCurrentIndex(1)
    assert window.devices.bench is not None
    window.open_device_demo("ice40_up5k")
    assert window.devices.bench.module.currentText() == "fpga_demo"
    assert {"clk", "reset"} == set(window.devices.bench.inputs)
    assert "leds" in window.devices.bench.outputs
    window.dirty = False
    window.close()
