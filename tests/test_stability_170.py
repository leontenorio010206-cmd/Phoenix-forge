"""Quality gate must fail closed even if PyInstaller produced an EXE."""
import json
from pathlib import Path
import pytest
from tools import release_gate, size_report


def _report():
    return {
        "version": "1.7.0", "success": True,
        "validation_status": "ci_accepted_windows_server_2022",
        "artifacts": [{"name": "PhoenixForge_v1.7.0_Portable.exe",
                       "sha256": "abc", "bytes": 40000000}],
        "native_acceptance": {
            "ordinary_startup": True, "development_PATH_removed": True,
            "launches": [
                {"success": True, "native_windows": True, "frozen": True,
                 "bundled_icarus": True},
                {"success": True, "native_windows": True, "frozen": True,
                 "bundled_icarus": True}
            ]
        }
    }


def test_release_gate_passes_only_two_verified_launches(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist/"PhoenixForge_v1.7.0_Portable.exe").write_bytes(b"MZ")
    monkeypatch.setattr(release_gate, "inspect_pe",
                        lambda path, minimum_size: {"sha256": "abc", "name": Path(path).name})
    report = _report()
    manifest = tmp_path/"report.json"
    manifest.write_text(json.dumps(report), encoding="utf-8")
    assert release_gate.verify_release(manifest, dist)["sha256"] == "abc"
    report["native_acceptance"]["launches"] = report["native_acceptance"]["launches"][:1]
    manifest.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="dos ejecuciones"):
        release_gate.verify_release(manifest, dist)


def test_gate_rejects_experimental_failed_or_unverified_build(tmp_path, monkeypatch):
    dist = tmp_path/"dist"
    dist.mkdir()
    (dist/"PhoenixForge_v1.7.0_Portable.exe").write_bytes(b"MZ")
    monkeypatch.setattr(release_gate, "inspect_pe",
                        lambda *a, **k: {"sha256": "abc"})
    path = tmp_path/"status.json"
    for key, value in [
        ("success", False),
        ("validation_status", "experimental_unverified"),
        ("version", "1.6.2"),
    ]:
        report = _report()
        report[key] = value
        path.write_text(json.dumps(report))
        with pytest.raises(ValueError):
            release_gate.verify_release(path, dist)


def test_gate_rejects_extra_binary_and_checksum_mismatch(tmp_path, monkeypatch):
    dist = tmp_path/"dist"
    dist.mkdir()
    original = dist/"PhoenixForge_v1.7.0_Portable.exe"
    original.write_bytes(b"MZ")
    manifest = tmp_path/"report.json"
    manifest.write_text(json.dumps(_report()))
    monkeypatch.setattr(release_gate, "inspect_pe",
                        lambda *a, **k: {"sha256":"wrong"})
    with pytest.raises(ValueError, match="Checksum"):
        release_gate.verify_release(manifest, dist)
    (dist/"PhoenixForge_EXPERIMENTAL.exe").write_bytes(b"MZ")
    with pytest.raises(ValueError, match="Artefacto"):
        release_gate.verify_release(manifest, dist)


def test_size_audit_is_measured_and_preserves_source_tree(tmp_path):
    for path, data in {
        "vendor/icarus/bin/iverilog.exe": b"1"*30,
        "vendor/sources/icarus.tar.gz": b"2"*20,
        "vendor/licenses/LICENSE": b"3"*10,
        "app/main.py": b"hello",
        "docs/README.md": b"hi",
    }.items():
        item = tmp_path/path
        item.parent.mkdir(parents=True, exist_ok=True)
        item.write_bytes(data)
    dist = tmp_path/"dist"
    dist.mkdir()
    (dist/"PhoenixForge_v1.7.0_Portable.exe").write_bytes(b"MZEXE")
    report = size_report.report_sizes(tmp_path, dist)
    assert report["parts"]["FPGA_Icarus_runtime"] == 30
    assert report["parts"]["Qt_sources_corresponding"] == 20
    assert report["parts"]["Third_party_licenses"] == 10
    assert report["artifacts"]["PhoenixForge_v1.7.0_Portable.exe"] == 5
    assert (tmp_path/"vendor/sources/icarus.tar.gz").exists()


@pytest.mark.gui
def test_small_laptop_view_and_sleeping_usb_scan(qt_app):
    from app.ui.main_window import MainWindow
    window = MainWindow()
    assert window.minimumWidth() <= 860
    assert window.minimumHeight() <= 560
    assert not window.hardware.timer.isActive()
    window.dirty = False
    window.close()
