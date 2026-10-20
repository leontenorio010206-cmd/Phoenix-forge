"""Portable RTL simulation associated with one of ten device profiles."""
from app.core.hdl import modules
from app.core.project import Project
from app.devices.catalog import load_profiles


def rtl_readiness(project, catalog=None):
    catalog = catalog if catalog is not None else load_profiles()
    profile = catalog.get(project.device)
    errors, warnings = [], []
    if not profile:
        return ["Perfil FPGA desconocido: seleccione uno de los diez perfiles."], warnings
    if not profile["compatibility"]["logical_simulation"]:
        errors.append("Este perfil no admite simulación lógica RTL.")
    names = {item["name"] for item in modules(project.files)}
    if not names:
        errors.append("Añada un módulo Verilog (.v/.sv) para simular.")
    top = project.simulation.get("top", "")
    root = project.simulation.get("testbench") or top
    if not root or root not in names:
        errors.append("Seleccione un módulo raíz/testbench existente en Estudio HDL.")
    elif root == top and not project.simulation.get("testbench"):
        warnings.append("Sin testbench: el diseño puede terminar sin estímulos útiles.")
    if profile["scope"] == "family":
        warnings.append("Perfil de familia: no identifica encapsulado ni capacidad de un chip concreto.")
    if project.pins:
        warnings.append("Los pines son metadatos; no se validan eléctricamente ni afectan el resultado RTL.")
    warnings.append("Simulación funcional RTL genérica: NO modela tiempos, PLL, primitivas del fabricante ni programación física.")
    return errors, warnings


def device_demo_project(device_id, catalog=None):
    """A real Icarus RTL test on any of the ten profiles."""
    catalog = catalog if catalog is not None else load_profiles()
    if device_id not in catalog:
        raise ValueError("Perfil FPGA desconocido")
    profile = catalog[device_id]
    if not profile["compatibility"]["logical_simulation"]:
        raise ValueError("Simulación lógica no disponible en este perfil")
    design = '''module fpga_demo(input clk, input reset, output reg [3:0] leds);
  always @(posedge clk) begin
    if (reset) leds <= 4'b0000;
    else leds <= leds + 4'b0001;
  end
endmodule
'''
    bench = '''module tb_fpga_demo;
  reg clk = 0;
  reg reset = 1;
  wire [3:0] leds;
  integer i;
  fpga_demo dut(.clk(clk), .reset(reset), .leds(leds));
  initial begin
    $dumpfile("fpga_demo.vcd"); $dumpvars(0, tb_fpga_demo);
    #5; clk = 1; #1;
    if (leds !== 4'b0000) $fatal(1, "Reset incorrecto");
    #4; clk = 0; reset = 0;
    for (i = 1; i <= 12; i = i + 1) begin
      #5; clk = 1; #1;
      if (leds !== (i & 15)) $fatal(1, "Contador incorrecto en %0d", i);
      #4; clk = 0;
    end
    $display("PASS: 12 FPGA RTL vectors"); $finish;
  end
endmodule
'''
    return Project(name="Demo RTL · " + profile["name"], device=device_id,
                   files={"fpga_demo.v": design, "tb_fpga_demo.v": bench},
                   simulation={"top": "fpga_demo", "testbench": "tb_fpga_demo", "timeout": 15},
                   metadata={"example": "fpga_rtl_demo", "simulation_scope": "generic_rtl_not_device_emulation",
                             "profile_scope": profile["scope"]})
