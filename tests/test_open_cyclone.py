"""Quartus-free RTL synthesis, intentionally not physical bitstream compilation."""
import subprocess
from pathlib import Path
import pytest

from app.core.project import Project
from app.integrations import open_cyclone


@pytest.fixture
def demo():
    return Project(
        name="Prueba", device="cyclone_iv",
        files={
            "main.v": "module led(input clk, output reg q); always @(posedge clk) q <= ~q; endmodule",
            "tb.v": "module tb; endmodule",
            "time.sdc": "create_clock -period 20 [get_ports clk]",
        },
        simulation={"top": "led", "testbench": "tb", "timeout": 15},
        pins={"clk": "PIN_E1", "q": "PIN_G15"})


def test_yosys_script_excludes_testbench(demo):
    top, sources = open_cyclone.design_sources(demo, "led")
    assert top == "led"
    assert [name for name, _ in sources] == ["main.v"]
    script = open_cyclone.synthesis_script(top, sources)
    assert "hierarchy -check -top led" in script
    assert 'write_json "netlist.json"' in script
    assert "quartus_sh" not in script
    assert "quartus_pgm" not in script


def test_yosys_outputs_logic_netlist_only(demo, tmp_path):
    yosys = tmp_path / "yosys.exe"
    yosys.touch()
    calls = []

    def fake(argv, **kwargs):
        calls.append(argv)
        folder = Path(kwargs["cwd"])
        (folder / "netlist.json").write_text('{"modules": {}}')
        (folder / "netlist.blif").write_text(".model led\n.end\n")
        return subprocess.CompletedProcess(argv, 0, "Yosys complete", "")

    result = open_cyclone.synthesize(
        demo, tmp_path, "led", "EP4CE6F17C8", executable=yosys, runner=fake)
    assert calls == [[str(yosys), "-s", open_cyclone.SCRIPT_NAME]]
    assert Path(result["netlist"]).is_file()
    assert Path(result["blif"]).is_file()
    assert result["programming_allowed"] is False
    assert result["bitstream_ready"] is False
    assert not list(Path(result["folder"]).glob("*.rbf"))
    assert not list(Path(result["folder"]).glob("*.sof"))
    assert "NO PROGRAMAR" in (Path(result["folder"]) / "RESULTADO.txt").read_text()


def test_yosys_fail_closed(demo, tmp_path):
    yosys = tmp_path / "yosys.exe"
    yosys.touch()
    bad = lambda argv, **k: subprocess.CompletedProcess(argv, 3, "", "Syntax error")
    with pytest.raises(RuntimeError, match="Syntax error"):
        open_cyclone.synthesize(
            demo, tmp_path, "led", "EP4CE6F17C8", executable=yosys, runner=bad)
    no_outputs = lambda argv, **k: subprocess.CompletedProcess(argv, 0, "", "")
    with pytest.raises(RuntimeError, match="netlist.json"):
        open_cyclone.synthesize(
            demo, tmp_path, "led", "EP4CE6F17C8",
            executable=yosys, runner=no_outputs)


def test_only_ep4ce6_experimental_research_profile(demo, tmp_path):
    with pytest.raises(ValueError):
        open_cyclone.design_sources(demo, "tb")
    with pytest.raises(ValueError):
        open_cyclone.design_sources(demo, "not_a_module")
    state = open_cyclone.ep4ce6_research_status(
        tmp_path, "EP4CE10F17C8", which=lambda key: None)
    assert state["supported_part"] is False
    assert "fuzz/fasm2rbf.py" in state["missing"]
    assert not state["bitstream_ready"]
    assert not state["programming_allowed"]


@pytest.mark.gui
def test_open_cyclone_tab_has_yosys_action(qt_app):
    from app.ui.hardware_studio import HardwareStudio
    studio = HardwareStudio()
    studio.timer.stop()
    names = [studio.tabs.tabText(i) for i in range(studio.tabs.count())]
    assert "Cyclone IV / Libre" in names
    tab = studio.tabs.widget(names.index("Cyclone IV / Libre"))
    assert tab.worker is None
    assert tab.start_button.text().startswith("Sintetizar")
    studio.close()
