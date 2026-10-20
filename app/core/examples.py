"""Factories shared by GUI, CLI and integration tests."""
import json
from app.core.project import Project
from app.simulators.clock import TrafficLight, PulseDivider, SquareDivider
from app.simulators.vcd import digital_vcd
from app.utils.paths import assets_dir


def adder_project():
    """Portable one-bit full adder and exhaustive self-checking testbench."""
    design = '''`timescale 1ns/1ps
module full_adder(input a, b, cin, output sum, cout);
  assign {cout,sum} = {1'b0,a} + {1'b0,b} + {1'b0,cin};
endmodule
'''
    bench = '''`timescale 1ns/1ps
module tb_full_adder;
reg a,b,cin;
wire sum,cout;
integer i;
full_adder dut(a,b,cin,sum,cout);
initial begin
  $dumpfile("full_adder.vcd"); $dumpvars(0,tb_full_adder);
  for (i=0;i<8;i=i+1) begin
    {a,b,cin}=i; #10;
    if ({cout,sum} !== ({1'b0,a}+{1'b0,b}+{1'b0,cin})) $fatal(1,"Adder mismatch");
  end
  $display("PASS: 8 full-adder vectors"); $finish;
end
endmodule
'''
    return Project("Sumador de 1 bit", files={"full_adder.v":design,"tb_full_adder.v":bench},
                   simulation={"top":"full_adder","testbench":"tb_full_adder","timeout":15},
                   metadata={"example":"full_adder"})


def internal_adder_result():
    samples = []
    for n in range(8):
        a,b,c = (n >> 2) & 1, (n >> 1) & 1, n & 1
        total = a+b+c
        samples.append((n*10, dict(a=a,b=b,cin=c,sum=total&1,cout=total>>1)))
    return {"adder_internal.vcd": digital_vcd(("a","b","cin","sum","cout"),samples)}


def clock_project(red=5, green=5, yellow=2, clock_hz=50000000, period=50000000, half_period=25000000, modulus=5208):
    from app.simulators.clock import Counter
    TrafficLight(red, green, yellow, clock_hz)
    PulseDivider(period); SquareDivider(half_period); Counter(modulus)
    if any(v > 2147483647 for v in (red, green, yellow, clock_hz, period, half_period, modulus)):
        raise ValueError("Los parámetros HDL de v1.0 deben caber en un entero positivo de 32 bits")
    names = ("pulse_generator.v", "square_divider.v", "modulo_counter.v", "traffic_light.v", "tb_clock.v")
    files = {name: (assets_dir() / "templates" / name).read_text(encoding="utf-8") for name in names}
    files["traffic_light.v"] = files["traffic_light.v"].replace("RED_SECONDS=5", "RED_SECONDS=%d" % red).replace("GREEN_SECONDS=5", "GREEN_SECONDS=%d" % green).replace("YELLOW_SECONDS=2", "YELLOW_SECONDS=%d" % yellow)
    files["traffic_light.v"] = files["traffic_light.v"].replace("CLOCK_HZ=50000000", "CLOCK_HZ=%d" % clock_hz)
    files["pulse_generator.v"] = files["pulse_generator.v"].replace("CYCLES=50000000", "CYCLES=%d" % period)
    files["square_divider.v"] = files["square_divider.v"].replace("HALF_CYCLES=25000000", "HALF_CYCLES=%d" % half_period)
    files["modulo_counter.v"] = files["modulo_counter.v"].replace("MODULUS=5208", "MODULUS=%d" % modulus)
    # Self-checking testbench intentionally uses fixed 3/2/1 durations to cover boundaries.
    return Project("Semáforo · Práctica 6", files=files,
                   simulation={"top": "traffic_light", "testbench": "tb_clock", "timeout": 15, "clock_hz": clock_hz,
                               "red": red, "green": green, "yellow": yellow, "period": period,
                               "half_period": half_period, "modulus": modulus},
                   metadata={"exercise": "clock", "source": "Práctica 6.0.pdf, páginas 12-25",
                             "added_design": "Rojo → verde → amarillo, reset síncrono activo alto; tiempos configurables"})


def internal_clock_result(red=5, green=5, yellow=2):
    model = TrafficLight(red, green, yellow, clock_hz=4)
    pulse, square = PulseDivider(4), SquareDivider(2)
    samples = [(0, dict(model.outputs, CLK=0, PULSE=0, SQUARE=0))]
    trace_cycles = min(4096, 8 * sum(model.durations))
    for i in range(1, trace_cycles + 1):
        model.advance(); pulse.advance(); square.advance()
        values = dict(model.outputs, CLK=1, PULSE=pulse.pulse, SQUARE=square.output)
        samples.append((i * 10 - 5, values))
        samples.append((i * 10, dict(values, CLK=0)))
    return {"clock_internal.vcd": digital_vcd(("CLK", "PULSE", "SQUARE") + model.STATES, samples),
            "internal_result.json": json.dumps({"engine": "Internal event-driven model", "reduced_clock_hz": 4,
                                                 "hardware_reference_hz": 50000000, "durations": model.durations,
                                                 "trace_cycles": trace_cycles, "trace_limit_cycles": 4096}, indent=2).encode("utf-8")}

