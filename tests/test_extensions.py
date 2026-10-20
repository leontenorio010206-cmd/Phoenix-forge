import copy
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

from app.devices.catalog import load_profiles, validate_profile
from app.core.examples import adder_project, internal_adder_result
from app.exporters.bundle import export_bundle, port_metadata
from app.core.project import Project
from app.core.hdl import ports, modules
from app.plugins.manager import PluginManager
from app.simulators.icarus import IcarusEngine


def test_profiles_and_unverified_status():
    profiles = load_profiles()
    assert len(profiles) == 10
    assert profiles['ep2c5t144c8n']['scope'] == 'device'
    for p in profiles.values():
        assert not p['compatibility']['synthesis_verified']
        assert not p['compatibility']['programming_verified']
    p = copy.deepcopy(profiles['cyclone_iv'])
    p['numeric_resources'] = {'pins': 999}
    with pytest.raises(ValueError): validate_profile(p)
    p = copy.deepcopy(profiles['ep2c5t144c8n'])
    p['compatibility']['synthesis_verified'] = True
    with pytest.raises(ValueError): validate_profile(p)


def test_exports_roundtrip_and_ports(tmp_path):
    p = adder_project()
    p.artifacts = internal_adder_result()
    export_bundle(p, tmp_path / 'export')
    assert Project.open(tmp_path / 'export/project.pforge') == p
    assert (tmp_path / 'export/src/tb_full_adder.v').exists()
    assert (tmp_path / 'export/results/adder_internal.vcd').exists()
    metadata = json.loads((tmp_path / 'export/ports.json').read_text())
    assert len(metadata['modules'][0]['ports']) == 5
    with pytest.raises(FileExistsError): export_bundle(p, tmp_path / 'export')


def test_hdl_port_subset():
    text = 'module m(input wire [7:0] data, output reg ready); endmodule'
    assert ports(text, 'm')[0]['width'] == 8
    text = 'module m(a,b); input [3:0] a; output b; endmodule'
    assert [p['name'] for p in ports(text, 'm')] == ['a', 'b']
    with pytest.raises(ValueError): ports('module m(input [N-1:0] a); endmodule', 'm')
    assert modules({'a.v':'// module fake\nmodule real; endmodule'})[0]['name'] == 'real'



def test_plugin_discovery_no_execution_and_lifecycle(tmp_path):
    folder = tmp_path / 'plugins'
    source = Path(__file__).resolve().parents[1] / 'examples/plugins/module_inventory'
    shutil.copytree(str(source), str(folder / 'inventory'))
    manager = PluginManager()
    infos = manager.discover(folder)
    assert len(infos) == 1 and infos[0].compatible
    assert not manager.loaded
    with pytest.raises(PermissionError): manager.load(infos[0])
    manager.load(infos[0], trusted=True)
    tool = next(iter(manager.registry.values()))
    assert len(tool(adder_project())) == 2
    manager.unload(infos[0].manifest['id'])
    assert not manager.loaded and not manager.registry
    # Altered code must be re-discovered and explicitly trusted again.
    with (folder / 'inventory/plugin.py').open('a') as f: f.write('\n# modified\n')
    with pytest.raises(ValueError, match='modificado'): manager.load(infos[0], trusted=True)


def test_bad_plugins_and_activation_rollback(tmp_path):
    folder = tmp_path / 'bad'
    folder.mkdir()
    manifest = {'id':'org.test.bad','name':'bad','api_version':99,'version':'1.0.0','entry_point':'plugin.py'}
    (folder / 'plugin.json').write_text(json.dumps(manifest))
    (folder / 'plugin.py').write_text("raise RuntimeError('MUST NOT RUN DURING DISCOVERY')")
    manager = PluginManager()
    assert not manager.discover(tmp_path)[0].compatible
    manifest['api_version'] = 1
    (folder / 'plugin.json').write_text(json.dumps(manifest))
    (folder / 'plugin.py').write_text("from app.plugins.sdk import Plugin\nclass Broken(Plugin):\n def activate(self,c):\n  c.register('hdl_tool','x',object())\n  raise RuntimeError('expected')\ndef create_plugin(): return Broken()\n")
    info = manager.discover(tmp_path)[0]
    with pytest.raises(RuntimeError): manager.load(info, trusted=True)
    assert not manager.registry and not manager.loaded and manager.errors


@pytest.mark.parametrize('content', ['[]', '{"id": []}', '{"id": null}'])
def test_invalid_manifest_does_not_crash_discovery(tmp_path, content):
    directory = tmp_path / 'invalid'
    directory.mkdir()
    (directory / 'plugin.json').write_text(content)
    found = PluginManager().discover(tmp_path)
    assert len(found) == 1 and not found[0].compatible

