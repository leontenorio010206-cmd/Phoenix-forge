"""Interactive, bounded RTL probing on a virtual FPGA panel.

No chip-specific gate/timing model: all ten profile selections run the user's
actual Verilog with Icarus. Ports are HDL signals, not electrically mapped pads.
"""
import copy
import re
from app.core.hdl import modules, ports, identifier
from app.devices.catalog import load_profiles

PROBE_MODULE = "pf_virtual_probe"
PROBE_FILE = "__phoenix_virtual_probe.v"
MAX_WIDTH = 16
MAX_PORTS = 40
OUTPUT_PATTERN = re.compile(r"^PF_OUT:([A-Za-z_][\w$]*)=([01xXzZ]+)\r?$", re.M)


def select_ports(project, top=None):
    """Identify plain Verilog ports, explicitly reject unsupported constructs."""
    if project.device not in load_profiles():
        raise ValueError("Seleccione un perfil FPGA compatible del catálogo")
    top = identifier(top or project.simulation.get("top", ""))
    found = [item for item in modules(project.files) if item["name"] == top]
    if len(found) != 1:
        raise ValueError("El módulo HDL principal debe existir una sola vez")
    pinout = ports(project.files[found[0]["file"]], top)
    if len(pinout) > MAX_PORTS:
        raise ValueError("El banco virtual admite hasta 40 puertos HDL")
    for port in pinout:
        if port["direction"] not in ("input", "output"):
            raise ValueError("Los puertos inout no son compatibles con el banco inicial")
        if not 1 <= port["width"] <= MAX_WIDTH:
            raise ValueError("Se admiten buses de 1 a 16 bits con anchura literal")
    if not any(p["direction"] == "output" for p in pinout):
        raise ValueError("El módulo necesita al menos una salida para observar")
    return top, pinout


def make_probe_project(project, inputs, clock=None, cycles=0, top=None):
    """Build a disposable project with generated driving testbench.

    Never alters original project, pins, sources or saved artifacts.
    """
    top, pinout = select_ports(project, top)
    if not isinstance(inputs, dict):
        raise ValueError("Las entradas deben proporcionarse como un diccionario")
    by_name = {p["name"]: p for p in pinout}
    if any(name not in by_name or by_name[name]["direction"] != "input" for name in inputs):
        raise ValueError("Entrada no perteneciente al módulo")
    if PROBE_FILE in project.files or any(m["name"] == PROBE_MODULE for m in modules(project.files)):
        raise ValueError("Nombre interno de prueba reservado; renombre el módulo o archivo")
    if type(cycles) is not int or not 0 <= cycles <= 100:
        raise ValueError("Se admiten entre 0 y 100 pulsos de reloj")
    if clock and (clock not in by_name or by_name[clock]["direction"] != "input"
                  or by_name[clock]["width"] != 1):
        raise ValueError("Seleccione una señal de reloj de entrada de 1 bit")
    if cycles and not clock:
        raise ValueError("Para pulsos de reloj, seleccione un pin HDL de reloj")
    lines = ['`timescale 1ns/1ps', 'module ' + PROBE_MODULE + ';']
    for p in pinout:
        declaration = "reg" if p["direction"] == "input" else "wire"
        vector = "[%d:%d] " % (p["msb"], p["lsb"]) if p["width"] > 1 else ""
        lines.append("  %s %s%s;" % (declaration, vector, p["name"]))
    connections = ", ".join(".%s(%s)" % (p["name"], p["name"]) for p in pinout)
    lines.append("  %s dut(%s);" % (top, connections))
    lines.append("  integer pf_cycle;")
    lines.append("  initial begin")
    lines.append('    $dumpfile("virtual_fpga.vcd"); $dumpvars(0, ' + PROBE_MODULE + ');')
    for p in pinout:
        if p["direction"] != "input":
            continue
        name = p["name"]
        value = 0 if name == clock else inputs.get(name, 0)
        if type(value) is not int or value < 0 or value >= (1 << p["width"]):
            raise ValueError("Valor fuera de rango en " + name)
        lines.append("    %s = %d'd%d;" % (name, p["width"], value))
    lines.append("    #2;")
    if clock and cycles:
        lines.append("    for (pf_cycle = 0; pf_cycle < %d; pf_cycle = pf_cycle + 1) begin" % cycles)
        lines.append("      %s = 1'b1; #2; %s = 1'b0; #2;" % (clock, clock))
        lines.append("    end")
    for p in pinout:
        if p["direction"] == "output":
            lines.append('    $display("PF_OUT:%s=%%b", %s);' % (p["name"], p["name"]))
    lines += ["    $finish;", "  end", "endmodule"]
    trial = copy.deepcopy(project)
    trial.files[PROBE_FILE] = "\n".join(lines) + "\n"
    trial.simulation = {"top": top, "testbench": PROBE_MODULE, "timeout": 30}
    trial.artifacts = {}
    trial.validate()
    return trial


def outputs_from_result(result, expected_ports):
    if not result.success:
        raise RuntimeError(result.reason + ": " + result.output[:300])
    outputs = {m.group(1): m.group(2).lower() for m in OUTPUT_PATTERN.finditer(result.output)}
    names = {p["name"] for p in expected_ports if p["direction"] == "output"}
    if set(outputs) != names:
        raise ValueError("No se pudieron recuperar todas las señales de salida del HDL")
    return outputs
