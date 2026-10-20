"""Regression tests for the opt-in, non-invasive Digital bridge."""
import hashlib
import json
import os
import zipfile
from pathlib import Path
import pytest

from app.core.examples import adder_project
from app.integrations import digital_bridge as bridge


def _fake_icarus(directory):
    files = {
        "bin/iverilog.exe": b"test-compiler",
        "bin/vvp.exe": b"test-runner",
        "lib/ivl/ivl.exe": b"test-ivl",
        "lib/ivl/ivlpp.exe": b"test-ivlpp",
        "licenses/README.txt": b"sample license",
    }
    for name, data in files.items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = {
        "architecture": "AMD64", "version": "test",
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return files


def test_ports_are_computed_from_actual_hdl():
    project = adder_project()
    fields = bridge.port_config(project)
    assert fields == {
        "etiqueta": "full_adder",
        "entradas": "a,b,cin",
        "salidas": "sum,cout",
        "aplicacion": "IVerilog",
    }


def test_unpacked_export_is_usable_without_extracting_a_zip(tmp_path):
    project = adder_project()
    file = bridge.export_unpacked_component(project, root=tmp_path)
    assert file.is_file() and file.suffix == ".v"
    assert b"module full_adder" in file.read_bytes()
    assert (file.parent / "ports.json").exists()
    assert (file.parent / "symbol.svg").exists()
    assert file == bridge.export_unpacked_component(project, root=tmp_path)
    (file.parent / "user_document.txt").write_text("Do not erase!")
    with pytest.raises(FileExistsError):
        bridge.export_unpacked_component(project, root=tmp_path)
    assert (file.parent / "user_document.txt").read_text() == "Do not erase!"


def test_bundle_verification_and_safe_persistence(tmp_path, monkeypatch):
    source = tmp_path / "runtime"
    source.mkdir()
    _fake_icarus(source)
    target = tmp_path / "prepared"
    monkeypatch.setattr(bridge.sys, "platform", "win32")
    assert bridge.prepare_icarus_for_digital(source, target) == target
    assert target.is_dir()
    assert bridge.prepare_icarus_for_digital(source, target) == target
    assert (target / "licenses/README.txt").read_bytes() == b"sample license"
    (target / "bin/iverilog.exe").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="Icarus"):
        bridge.prepare_icarus_for_digital(source, target)


def test_inventory_rejects_traversal(tmp_path):
    source = tmp_path / "runtime"
    source.mkdir()
    _fake_icarus(source)
    manifest = json.loads((source / "manifest.json").read_text())
    manifest["files"]["../escape.exe"] = "0" * 64
    (source / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        bridge.verify_icarus_bundle(source)


def test_external_launcher_has_scoped_path_only(tmp_path, monkeypatch):
    jar = tmp_path / "Digital.jar"
    jar.write_bytes(b"test-jar")
    runtime = tmp_path / "icarus"
    (runtime / "bin").mkdir(parents=True)
    (runtime / "bin/iverilog.exe").write_bytes(b"test-exe")
    called = {}
    def fake_popen(args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs
        return "fake-process"
    original_path = os.environ.get("PATH", "")
    assert bridge.launch_digital(jar, runtime, java="java", popen=fake_popen) == "fake-process"
    assert called["args"] == ["java", "-jar", str(jar)]
    assert called["kwargs"]["env"]["PATH"].startswith(str(runtime.resolve() / "bin"))
    assert os.environ.get("PATH", "") == original_path
    assert called["kwargs"]["cwd"] == str(tmp_path.resolve())
    with pytest.raises(FileNotFoundError):
        bridge.launch_digital(tmp_path / "unknown.jar", runtime, java="java", popen=fake_popen)


@pytest.mark.gui
def test_digital_one_click_controls_exist(qt_app):
    from app.ui.main_window import MainWindow
    window = MainWindow()
    window.new_adder()
    window.navigate(4)
    panel = window.digital_export
    seen = []
    # Prevent the real UI handler opening a native file picker in headless CI.
    panel.bridge_requested.disconnect(window.prepare_and_open_digital)
    panel.bridge_requested.connect(seen.append)
    panel.bridge_button.click()
    assert seen == ["full_adder"]
    text = window.copy_digital_settings("full_adder")
    assert "Etiqueta: full_adder" in text
    window.dirty = False
    window.close()
