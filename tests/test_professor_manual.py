"""Teacher tutorial assets must open unchanged in the stable .pforge format."""
import json
from pathlib import Path

from app.core.project import Project
from app.exporters.digital_hdl import digital_component_files
from app.simulators.icarus import IcarusEngine

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples/fpga_demo_profesor/Ejemplo_Contador_FPGA_4bits.pforge"


def test_teacher_example_can_open_and_export_digital():
    project = Project.open(SAMPLE)
    assert project.simulation["top"] == "fpga_demo"
    assert project.simulation["testbench"] == "tb_fpga_demo"
    assert project.files["fpga_demo.v"] == (SAMPLE.parent / "fpga_demo.v").read_text(encoding="utf-8")
    assert project.files["tb_fpga_demo.v"] == (SAMPLE.parent / "tb_fpga_demo.v").read_text(encoding="utf-8")
    package = digital_component_files(project, "fpga_demo")
    assert {"component.v", "ports.json", "LEEME_DIGITAL.txt", "symbol.svg", "connections.svg"} == set(package)
    assert b"module fpga_demo" in package["component.v"]
    assert b"module tb_fpga_demo" not in package["component.v"]
    manifest = json.loads(package["ports.json"])
    assert manifest["top"] == "fpga_demo"
    assert {p["name"] for p in manifest["ports"]} == {"clk", "reset", "leds"}
    assert manifest["scope"].startswith("RTL functional")


def test_teacher_example_follows_real_icarus_when_available(tmp_path):
    import pytest
    engine = IcarusEngine()
    if not engine.available:
        pytest.skip("Requires native iverilog and vvp installed on this runner")
    result = engine.run(Project.open(SAMPLE), root=tmp_path)
    assert result.success, result.output
    assert "PASS: 12 FPGA RTL vectors" in result.output
    assert any(k.endswith("fpga_demo.vcd") for k in result.artifacts)


def test_teacher_manual_has_no_obsolete_v11_header():
    text = (ROOT / "docs/USER_MANUAL.md").read_text(encoding="utf-8")
    assert "Manual de usuario — PhœnixForge v1.7.0" in text
    assert "FPGA" in text and "Digital" in text
    assert "no genera bitstreams" not in text or ".dig" in text
