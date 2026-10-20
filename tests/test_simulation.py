import threading
import pytest
from app.core.examples import adder_project, clock_project, internal_adder_result, internal_clock_result
from app.core.project import Project
from app.simulators.icarus import IcarusEngine
from app.simulators.vcd import parse_vcd


def engine_or_skip():
    engine = IcarusEngine()
    if not engine.available:
        pytest.skip('Icarus Verilog not installed')
    return engine


def test_missing_compiler_reports_failure(tmp_path):
    engine = IcarusEngine('/no/such/iverilog', '/no/such/vvp')
    result = engine.run(adder_project(), root=tmp_path)
    assert not result.success and 'No se encontraron' in result.reason
    assert result.commands == []


@pytest.mark.hdl
@pytest.mark.parametrize('factory,proof', [(adder_project, 'PASS: 8'), (clock_project, 'PASS: 72')])
def test_real_icarus_success(tmp_path, factory, proof):
    result = engine_or_skip().run(factory(), root=tmp_path)
    assert result.success, result.output
    assert proof in result.output
    assert any(n.endswith('.vcd') for n in result.artifacts)
    assert not [d for d in result.diagnostics if d.severity == 'error']
    for name, data in result.artifacts.items():
        if name.endswith('.vcd'):
            assert parse_vcd(data).signals


@pytest.mark.hdl
def test_real_compile_and_runtime_failures(tmp_path):
    engine = engine_or_skip()
    p = adder_project(); p.files['full_adder.v'] = 'module full_adder THIS IS BAD; endmodule'
    result = engine.run(p, root=tmp_path)
    assert not result.success and 'Compilación fallida' in result.reason
    assert result.diagnostics
    p = Project(files={'tb.v':'module tb; initial $fatal(1,"Intentional test failure"); endmodule'}, simulation={'testbench':'tb'})
    result = engine.run(p, root=tmp_path)
    assert not result.success and 'Simulación fallida' in result.reason
    p.files['tb.v'] = 'module tb; initial $stop; endmodule'
    result = engine.run(p, root=tmp_path)
    assert not result.success, '$stop must not be reported as successful completion'


@pytest.mark.hdl
def test_timeout_cancel_and_reject_include(tmp_path):
    engine = engine_or_skip()
    p = Project(files={'tb.v':'module tb; initial forever #1; endmodule'}, simulation={'testbench':'tb','timeout':1})
    result = engine.run(p, root=tmp_path)
    assert not result.success and 'Tiempo máximo' in result.reason
    cancel = threading.Event(); cancel.set()
    result = engine.run(p, root=tmp_path, cancel=cancel)
    assert not result.success and 'cancelada' in result.reason
    p.files['tb.v'] = '`include "../../outside.v"\nmodule tb; endmodule'
    result = engine.run(p, root=tmp_path)
    assert not result.success and 'Ruta insegura' in result.reason


def test_vcd_internal_and_aliases():
    for artifacts in (internal_adder_result(), internal_clock_result()):
        for name, data in artifacts.items():
            if name.endswith('.vcd'):
                trace = parse_vcd(data)
                assert trace.signals and trace.end > 0
    data = b'$timescale 1 ns $end\n$scope module x $end\n$var wire 1 ! a $end\n$var wire 1 ! alias $end\n$upscope $end\n$enddefinitions $end\n#0\n0!\n#2\n1!'
    trace = parse_vcd(data)
    assert trace.timescale == '1ns'
    assert trace.signals[0].events == trace.signals[1].events == [(0,'0'),(2,'1')]
    with pytest.raises(ValueError): parse_vcd(b'not a VCD')
    with pytest.raises(ValueError, match='cambios'): parse_vcd(data, max_events=1)

