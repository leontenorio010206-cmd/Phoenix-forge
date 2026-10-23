"""Cyclone IV bridge: project-generation contract and no implicit hardware writes."""
from pathlib import Path
import subprocess

import pytest

from app.core.project import Project
from app.integrations import quartus_bridge as q


@pytest.fixture
def demo():
    return Project(
        name="contador",
        device="cyclone_iv",
        files={
            "src/contador.v": (
                "module contador(input wire clk, output reg [1:0] leds);\n"
                "always @(posedge clk) leds <= leds + 1'b1;\nendmodule\n"
            ),
            "tb_contador.v": (
                "module tb_contador;\n"
                "initial begin $display(\"testbench\"); $finish; end\nendmodule\n"
            ),
        },
        simulation={"top": "contador", "testbench": "tb_contador", "timeout": 15},
        pins={"clk": "PIN_23", "leds[0]": "PIN_24", "leds[1]": "PIN_25"},
    )


def test_exports_real_quartus_files_and_excludes_testbench(tmp_path, demo):
    out = q.export_project(demo, tmp_path, "ep4ce6e22c8n")
    qsf = (out / "PhoenixForge_CycloneIV.qsf").read_text(encoding="utf-8")
    assert 'set_global_assignment -name FAMILY "Cyclone IV E"' in qsf
    assert "set_global_assignment -name DEVICE EP4CE6E22C8N" in qsf
    assert "set_global_assignment -name TOP_LEVEL_ENTITY contador" in qsf
    assert "set_global_assignment -name VERILOG_FILE {src/src/contador.v}" in qsf
    assert "set_location_assignment PIN_23 -to {clk}" in qsf
    assert "set_location_assignment PIN_24 -to {leds[0]}" in qsf
    assert "tb_contador.v" not in qsf
    assert not (out / "src/tb_contador.v").exists()
    assert (out / "src/src/contador.v").exists()
    assert (out / "PhoenixForge_CycloneIV.qpf").is_file()
    assert not list(out.rglob("*.sof"))
    assert "NO" in (out / "LEEME_ANTES_DE_PROGRAMAR.txt").read_text(encoding="utf-8")


def test_refuses_unknown_part_and_testbench_top(tmp_path, demo):
    for device in ("", "Cyclone IV", "EP4CE; dangerous", "EP2C5T144C8N"):
        with pytest.raises(ValueError):
            q.export_project(demo, tmp_path, device)
    with pytest.raises(ValueError):
        q.export_project(demo, tmp_path, "EP4CE6E22C8N", top="tb_contador")
    assert list(tmp_path.iterdir()) == []


def test_explicit_pinout_never_guessed(tmp_path, demo):
    demo.pins = {}
    out = q.export_project(demo, tmp_path, "EP4CGX15BF14C6")
    qsf = (out / "PhoenixForge_CycloneIV.qsf").read_text(encoding="utf-8")
    assert 'set_global_assignment -name FAMILY "Cyclone IV GX"' in qsf
    assert "set_location_assignment" not in qsf
    assert "Asignaciones de pines: 0" in (out / "LEEME_ANTES_DE_PROGRAMAR.txt").read_text(encoding="utf-8")


def test_rejects_bad_duplicate_or_injected_pins(tmp_path, demo):
    for pins in (
        {"clk": "PIN_23", "reset": "PIN_23"},
        {"clk;exec bad": "PIN_23"},
        {"clk": "PIN_23;bad"},
    ):
        with pytest.raises(ValueError):
            q.export_project(demo, tmp_path, "EP4CE6E22C8N", pins=pins)
    assert not list(tmp_path.iterdir())


def test_never_overwrites_existing_export(tmp_path, demo):
    output = q.export_project(demo, tmp_path, "EP4CE6E22C8N")
    with pytest.raises(FileExistsError):
        q.export_project(demo, tmp_path, "EP4CE6E22C8N")
    assert output.is_dir()


def test_compiler_uses_argv_and_never_invokes_programmer(tmp_path, demo):
    output = q.export_project(demo, tmp_path, "EP4CE6E22C8N")
    executable = tmp_path / "quartus_sh.exe"
    executable.write_bytes(b"fake in tests")
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "Compilation successful", "")

    result = q.compile_project(output, executable, runner=fake_run)
    assert "successful" in result
    cmd, options = calls[0]
    assert cmd == [str(executable), "--flow", "compile", q.PROJECT_NAME]
    assert options["cwd"] == str(output)
    assert options["check"] is False and options["timeout"] > 60
    assert "quartus_pgm" not in " ".join(cmd)
    with pytest.raises(ValueError):
        q.find_quartus(tmp_path / "powershell.exe")


def test_compilation_failure_is_visible(tmp_path, demo):
    output = q.export_project(demo, tmp_path, "EP4CE6E22C8N")
    executable = tmp_path / "quartus_sh.exe"
    executable.touch()

    def fail(args, **kwargs):
        return subprocess.CompletedProcess(args, 2, "", "Error: missing Quartus device support")

    with pytest.raises(RuntimeError, match="missing Quartus device support"):
        q.compile_project(output, executable, runner=fail)


@pytest.mark.gui
def test_hardware_studio_exposes_quartus_tab_and_project(qt_app, demo):
    from app.ui.hardware_studio import HardwareStudio
    panel = HardwareStudio(lambda: demo)
    panel.timer.stop()
    index = panel.tabs.count() - 2  # inserted before Arduino catalog
    assert panel.tabs.tabText(index) == "Cyclone IV / Quartus"
    tab = panel.tabs.widget(index)
    tab.sync_project()
    assert tab.top.text() == "contador"
    assert tab.part.text() == ""
    assert not tab.compile_button.isEnabled()
    panel.close()
