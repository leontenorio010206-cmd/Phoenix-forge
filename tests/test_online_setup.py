"""Dependency installer release safeguards; no downloads in unit tests."""
import hashlib
import json
from pathlib import Path
import pytest

from app.integrations import digital_bridge
from tools.build_setup_windows import verify_components_manifest


def test_pinned_external_distributions_are_real_and_checksum_locked():
    root = Path(__file__).resolve().parents[1]
    manifest = verify_components_manifest(root)
    digital = manifest["components"]["digital"]
    java = manifest["components"]["java"]
    assert digital["version"] == "0.31"
    assert digital["sha256"] == digital_bridge._OPTIONAL_COMPONENTS["digital"][2]
    assert java["sha256"] == digital_bridge._OPTIONAL_COMPONENTS["java"][2]
    assert "Eclipse" not in digital["source"]
    assert "adoptium" in java["source"]
    assert digital["bytes"] == 12689882


def _receipt(root, kind, content):
    folder, filename, checksum = digital_bridge._OPTIONAL_COMPONENTS[kind]
    directory = root / folder / "runtime" / "bin"
    directory.mkdir(parents=True)
    path = directory / filename
    path.write_bytes(content)
    (root / folder / "phoenixforge-component.json").write_text(
        json.dumps({
            "component":kind, "archive_sha256":checksum,
            "relative_path":"runtime/bin/"+filename,
            "file_sha256":hashlib.sha256(content).hexdigest(),
        }), encoding="utf-8")
    return path


def test_installed_digital_and_java_are_found_from_receipts(tmp_path):
    jar = _receipt(tmp_path, "digital", b"Digital Jar fixture")
    javaw = _receipt(tmp_path, "java", b"Java fixture")
    assert digital_bridge.locate_installed_digital([tmp_path]) == str(jar)
    assert digital_bridge.locate_java([tmp_path]) == str(javaw)
    jar.write_bytes(b"modified")
    assert digital_bridge.locate_installed_digital([tmp_path]) is None


def test_setup_receipts_reject_escape_and_unknown_archives(tmp_path):
    jar = _receipt(tmp_path, "digital", b"safe fixture")
    marker = jar.parents[2] / "phoenixforge-component.json"
    payload = json.loads(marker.read_text(encoding="utf-8"))
    payload["relative_path"] = "../outside/Digital.jar"
    marker.write_text(json.dumps(payload), encoding="utf-8")
    assert digital_bridge.locate_installed_digital([tmp_path]) is None
    payload["relative_path"] = "runtime/bin/Digital.jar"
    payload["archive_sha256"] = "0" * 64
    marker.write_text(json.dumps(payload), encoding="utf-8")
    assert digital_bridge.locate_installed_digital([tmp_path]) is None


def test_nsis_offline_core_and_online_optional_are_separate():
    nsis = (Path(__file__).resolve().parents[1] / "installer/PhoenixForge.nsi").read_text(encoding="utf-8")
    assert 'RequestExecutionLevel user' in nsis
    assert 'Section "PhœnixForge (obligatorio)" Main' in nsis
    assert 'Section /o "Digital v0.31' in nsis
    assert 'Section /o "Java Eclipse Temurin' in nsis
    assert 'install_optional.ps1' in nsis
    assert 'optional-components.json' in nsis


def test_optional_installer_script_has_verification_and_no_global_path():
    text = (Path(__file__).resolve().parents[1] / "installer/install_optional.ps1").read_text(encoding="utf-8")
    for token in ("Get-FileHash", "SHA256", "Assert-TrustedZip",
                  "ExtractToDirectory", "Move-Item", "max_expanded_bytes", "Component"):
        assert token in text
    assert "SetEnvironmentVariable" not in text
    assert "pnputil" not in text
    assert "Invoke-Expression" not in text


def test_setup_release_workflow_must_be_strictly_gated():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/ci-windows.yml").read_text(encoding="utf-8")
    assert workflow.index("Validar reporte de liberación") < workflow.index("Generar Setup Windows")
    assert workflow.index("Generar Setup Windows") < workflow.index("Publicar ÚNICAMENTE EXE aceptado")
    assert "PhoenixForge_v1.7.0_Setup.exe" in workflow


def test_setup_build_manifest_disallows_untrusted_urls(tmp_path):
    root = tmp_path
    (root / "installer").mkdir()
    orig = json.loads((Path(__file__).resolve().parents[1] /
                       "installer/optional-components.json").read_text(encoding="utf-8"))
    orig["components"]["digital"]["url"] = "http://malicious.example/Digital.zip"
    (root / "installer/optional-components.json").write_text(json.dumps(orig), encoding="utf-8")
    with pytest.raises(ValueError, match="Descarga insegura"):
        verify_components_manifest(root)
