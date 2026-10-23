"""Local Cyclone IV flow: discover -> compile -> re-detect -> temporary SRAM only."""
from pathlib import Path
import subprocess

import pytest

from app.core.project import Project
from app.integrations import cyclone_runner as runner


@pytest.fixture
def design():
    return Project(
        name="LED",
        device="cyclone_iv",
        files={"blink.v":
               "module blink(input wire clk, output reg led);\n"
               "always @(posedge clk) led <= ~led;\nendmodule\n",
               "timing.sdc": "create_clock -period 20.000 [get_ports {clk}]\n"},
        simulation={"top": "blink", "testbench": "", "timeout": 15},
        pins={"clk": "PIN_23", "led": "PIN_24"},
    )


def test_parse_jtag_chain_and_density_validation():
    raw = "1) USB-Blaster [USB-0]\n 020F30DD EP4CE6\n + Node 0C001\n"
    scan = {"cables": runner.parse_jtag(raw)}
    c = runner.validate_chain(scan, "EP4CE6E22C8N")
    assert c["number"] == 1
    assert c["devices"][0]["idcode"] == "020F30DD"
    with pytest.raises(ValueError, match="no coincide"):
        runner.validate_chain(scan, "EP4CE10E22C8N")
    with pytest.raises(ValueError):
        runner.validate_chain({"cables": []}, "EP4CE6E22C8N")
    with pytest.raises(ValueError):
        runner.validate_chain({"cables": runner.parse_jtag(
            raw + "2) Other USB-Blaster\n 020F30DD EP4CE6\n")},
            "EP4CE6E22C8N")


def test_jtag_rejects_unknown_and_multichip():
    unknown = runner.parse_jtag("1) USB-Blaster\n 01234567 UNKNOWN_01234567\n")
    with pytest.raises(ValueError):
        runner.validate_chain({"cables": unknown}, "EP4CE6E22C8N")
    multi = runner.parse_jtag(
        "1) USB-Blaster\n 020F30DD EP4CE6\n 020F30DD EP4CE6\n")
    with pytest.raises(ValueError, match="una FPGA"):
        runner.validate_chain({"cables": multi}, "EP4CE6E22C8N")


def test_find_quartus_requires_all_tools(tmp_path):
    root = tmp_path / "quartus"
    root.mkdir()
    compiler = root / "quartus_sh.exe"
    compiler.touch()
    with pytest.raises(FileNotFoundError):
        runner.discover_tools(compiler)
    (root / "quartus_pgm.exe").touch()
    (root / "jtagconfig.exe").touch()
    toolchain = runner.discover_tools(compiler)
    assert toolchain["quartus_sh"] == str(compiler)


def test_pinout_full_coverage_before_writing(tmp_path, design):
    assert runner.verify_pin_coverage(design, "blink") == {"clk", "led"}
    design.pins.pop("led")
    with pytest.raises(ValueError, match="Faltan"):
        runner.verify_pin_coverage(design, "blink")


def test_oneclick_scans_compiles_scans_programs_sram_only(tmp_path, design, monkeypatch):
    tools = {"quartus_sh": "/fake/quartus_sh.exe",
             "quartus_pgm": "/fake/quartus_pgm.exe",
             "jtagconfig": "/fake/jtagconfig.exe"}
    monkeypatch.setattr(runner, "discover_tools", lambda path: tools)
    calls, progress = [], []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        if argv[0] == tools["jtagconfig"]:
            return subprocess.CompletedProcess(
                argv, 0, "1) USB-Blaster [USB-0]\n 020F30DD EP4CE6\n", "")
        if argv[0] == tools["quartus_sh"]:
            folder = Path(kwargs["cwd"])
            path = folder / "output_files" / "PhoenixForge_CycloneIV.sof"
            path.parent.mkdir()
            path.write_bytes(b"fake-configuration-for-tests-only")
            return subprocess.CompletedProcess(argv, 0, "Quartus compilation: successful", "")
        return subprocess.CompletedProcess(argv, 0, "Programming successful", "")

    result = runner.compile_and_run(
        design, tmp_path, "EP4CE6E22C8N", "blink",
        runner=fake_run, on_stage=progress.append)
    assert result["cable_number"] == 1
    assert [call[0] for call in calls] == [
        tools["jtagconfig"], tools["quartus_sh"],
        tools["jtagconfig"], tools["quartus_pgm"]]
    assert calls[1][1:] == ["--flow", "compile", "PhoenixForge_CycloneIV"]
    assert calls[3][1:4] == ["-c", "1", "-m"]
    assert calls[3][4] == "jtag" and calls[3][5] == "-o"
    assert calls[3][6].startswith("p;") and calls[3][6].endswith(".sof@1")
    assert all("pof" not in " ".join(call).lower() for call in calls)
    assert any("SRAM" in text for text in progress)
    qsf = (Path(result["folder"]) / "PhoenixForge_CycloneIV.qsf").read_text()
    assert "SDC_FILE" in qsf


def test_wrong_fpga_prevents_programming_or_compiling(tmp_path, design, monkeypatch):
    monkeypatch.setattr(runner, "discover_tools",
                        lambda path: {"jtagconfig": "scan", "quartus_sh": "compile",
                                      "quartus_pgm": "program"})
    calls = []

    def wrong(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0,
                                           "1) USB-Blaster\n 020F30DD EP4CE10\n", "")

    with pytest.raises(ValueError, match="no coincide"):
        runner.compile_and_run(design, tmp_path, "EP4CE6E22C8N", "blink", runner=wrong)
    assert len(calls) == 1 and calls[0][0] == "scan"
    assert list(tmp_path.iterdir()) == []
