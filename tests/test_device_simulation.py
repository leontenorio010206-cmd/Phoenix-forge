"""All ten FPGA profiles have a vendor-independent RTL demonstration."""
import pytest
from app.devices.catalog import load_profiles
from app.devices.simulation import device_demo_project, rtl_readiness
from app.core.project import Project
from app.simulators.icarus import IcarusEngine


@pytest.mark.parametrize('device_id', list(load_profiles()))
def test_device_profiles_prepare_rtl_demo(device_id):
    project = device_demo_project(device_id)
    errors, warnings = rtl_readiness(project)
    assert not errors
    assert any('NO modela' in message for message in warnings)
    assert project.device == device_id
    assert 'fpga_demo.v' in project.files
    assert 'tb_fpga_demo.v' in project.files
    assert project.simulation['testbench'] == 'tb_fpga_demo'


def test_bad_device_and_missing_verilog():
    with pytest.raises(ValueError, match='desconocido'):
        device_demo_project('inventado')
    project = Project(device='cyclone_iv')
    errors, warnings = rtl_readiness(project)
    assert errors and any('Verilog' in error for error in errors)
    assert any('familia' in warning for warning in warnings)


@pytest.mark.hdl
@pytest.mark.parametrize('device_id', list(load_profiles()))
def test_real_verilog_demo_on_ten_profiles(device_id, tmp_path):
    engine = IcarusEngine()
    if not engine.available:
        pytest.skip('Icarus no disponible')
    result = engine.run(device_demo_project(device_id), root=tmp_path)
    assert result.success, result.output
    assert 'PASS: 12 FPGA RTL vectors' in result.output
    assert any(name.endswith('.vcd') for name in result.artifacts)
