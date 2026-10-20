"""Regression for resource lifetime, packaged commands, and source cleanup."""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import threading
import zipfile
import pytest

from app.core.examples import clock_project
from app.core.project import Project
from app.simulators.icarus import IcarusEngine
from app.utils import paths
from tools.verify_artifact import inspect_pe, verify_vendor


def test_frozen_resources_and_persistent_paths(tmp_path, monkeypatch):
    frozen, persistent = tmp_path / '_MEI-test', tmp_path / 'perfil'
    monkeypatch.setattr(sys, '_MEIPASS', str(frozen), raising=False)
    monkeypatch.setenv('PHOENIXFORGE_DATA', str(persistent))
    assert paths.resource_root() == frozen
    assert paths.assets_dir() == frozen / 'app/assets'
    project_folder = paths.user_projects_dir()
    assert project_folder == persistent / 'projects'
    assert frozen not in project_folder.parents
    assert project_folder.is_dir()


def test_packaged_command_resolution_and_error_propagation(tmp_path, monkeypatch):
    # Empty fixtures only test argument routing. No real compiler success is asserted.
    bundle = tmp_path / 'Prueba Fénix'
    (bundle / 'bin').mkdir(parents=True)
    for n in ('iverilog.exe', 'vvp.exe'):
        (bundle / 'bin' / n).touch()
    monkeypatch.setattr('app.simulators.icarus.bundled_icarus', lambda: bundle)
    monkeypatch.setenv('PATH', '')
    engine = IcarusEngine()
    assert engine.bundle == bundle and engine.available
    def compile_error(command, cwd, log, timeout, cancel):
        assert command[0] == str(bundle / 'bin/iverilog.exe')
        assert command[command.index('-B') + 1] == str(bundle / 'lib/ivl')
        Path(log).write_text('intentional compiler error')
        return 3
    monkeypatch.setattr(engine, '_execute', compile_error)
    result = engine.run(clock_project(), root=tmp_path / 'run')
    assert not result.success and 'código 3' in result.reason
    assert len(result.commands) == 1
    override = IcarusEngine('/does-not-exist', '/does-not-exist')
    assert override.bundle is None and not override.available


def test_child_environment_is_local(tmp_path, monkeypatch):
    engine = IcarusEngine('/missing', '/missing')
    engine.bundle = tmp_path / 'Icarus runtime'
    monkeypatch.setenv('PATH', 'original-path')
    captured = {}
    class CompletedProcess:
        returncode = 0
        def poll(self): return 0
    def launch(command, **kwargs):
        captured.update(kwargs)
        return CompletedProcess()
    monkeypatch.setattr('app.simulators.icarus.subprocess.Popen', launch)
    assert engine._execute(['iverilog.exe'], tmp_path, tmp_path / 'test.log', 1, threading.Event()) == 0
    assert captured['shell'] is False
    assert captured['env']['PATH'].startswith(str(engine.bundle / 'bin') + os.pathsep)
    assert os.environ['PATH'] == 'original-path'


def test_version_100_project_preserves_data(tmp_path):
    p = clock_project()
    p.metadata['user-data'] = {'note': 'Conservar íntegro'}
    p.pins = {'red': 'PIN_1'}
    p.export_state = {'history': [1, 2, 3]}
    p.artifacts['result.txt'] = b'previous result'
    original = p.save(tmp_path / 'current.pforge')
    legacy = tmp_path / 'previous.pforge'
    with zipfile.ZipFile(original) as src, zipfile.ZipFile(legacy, 'w') as dest:
        for info in src.infolist():
            content = src.read(info.filename)
            if info.filename == 'manifest.json':
                manifest = json.loads(content)
                manifest['app_version'] = '1.0.0'
                content = json.dumps(manifest).encode()
            dest.writestr(info, content)
    loaded = Project.open(legacy)
    assert loaded == p
    again = loaded.save(tmp_path / 'updated.pforge')
    assert Project.open(again) == p
    assert loaded.manifest()['schema_version'] == 1
    assert loaded.manifest()['app_version'] == '1.6.1'


@pytest.mark.parametrize('payload', [b'', b'#!/bin/sh\necho not-windows\n', b'MZ'+b'\0'*126])
def test_invalid_executable_rejected(tmp_path, payload):
    target = tmp_path / 'fixture.bin'
    target.write_bytes(payload)
    with pytest.raises(ValueError):
        inspect_pe(target, minimum_size=64)


def test_wrong_architecture_and_console_rejected(tmp_path):
    data = bytearray(256)
    data[:2] = b'MZ'; struct.pack_into('<I', data, 0x3c, 0x40)
    data[0x40:0x44] = b'PE\0\0'
    struct.pack_into('<H', data, 0x44, 0x14c)
    target = tmp_path / 'header-fixture.bin'; target.write_bytes(data)
    with pytest.raises(ValueError, match='architecture'): inspect_pe(target, minimum_size=128)
    struct.pack_into('<H', data, 0x44, 0x8664)
    struct.pack_into('<H', data, 0x40+24+68, 3)
    target.write_bytes(data)
    with pytest.raises(ValueError, match='GUI'): inspect_pe(target, minimum_size=128)


def test_vendor_corruption_rejected(tmp_path):
    file = tmp_path / 'payload'; file.write_bytes(b'changed')
    manifest = {'architecture': 'AMD64', 'files': {'payload': hashlib.sha256(b'original').hexdigest()}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='integrity'): verify_vendor(tmp_path)


def test_removed_exercise_absent_from_distribution():
    root = Path(__file__).resolve().parents[1]
    forbidden = ('car' + 'rito', 'práctica ' + '5', 'practica' + '5')
    candidates = [p for d in ('app', 'examples', 'docs') for p in (root / d).rglob('*')]
    candidates += [root / n for n in ('README.md', 'CHANGELOG.md', 'INFORME_ENTREGA.md', 'THIRD_PARTY_NOTICES.md')]
    for path in candidates:
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        assert not any(term in path.name.lower() for term in forbidden), str(path)
        if path.suffix in ('.py', '.v', '.md', '.json', '.txt', '.dig'):
            assert not any(term in path.read_text(encoding='utf-8').lower() for term in forbidden), str(path)
        elif path.suffix == '.pforge':
            with zipfile.ZipFile(path) as archive:
                assert not any(term in b'\n'.join(archive.read(n) for n in archive.namelist()).decode('utf-8').lower()
                               for term in forbidden)


def test_component_source_export(tmp_path):
    from app.exporters.components import export_components
    folder = export_components(tmp_path / 'components')
    assert (folder / 'THIRD_PARTY_NOTICES.md').is_file()
    assert (folder / 'sources/iverilog-12.0.tar.gz').is_file()
    with pytest.raises(FileExistsError): export_components(folder)


@pytest.mark.packaged
def test_real_packaged_windows_acceptance(tmp_path):
    executable = os.environ.get('PHOENIXFORGE_EXE')
    if not executable:
        pytest.skip('Windows executable not built/selected; packaged acceptance NOT verified')
    from tools.test_packaged import verify
    result = verify(Path(executable), tmp_path)
    assert result['ordinary_startup'] and len(result['launches']) == 2
