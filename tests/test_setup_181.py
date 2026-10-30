"""Safety tests for preview 1.8.1 Setup; fixtures do not download anything."""
import hashlib
import json
from pathlib import Path
import pytest

from app.integrations import oss_cad, open_cyclone
from tools.build_setup_181 import verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def fake_bundle(directory):
    root = directory / oss_cad.FOLDER
    bin_dir = root / "runtime/oss-cad-suite/bin"
    bin_dir.mkdir(parents=True)
    yosys = bin_dir / "yosys.exe"
    loader = bin_dir / "openFPGALoader.exe"
    yosys.write_bytes(b"Yosys fixture")
    loader.write_bytes(b"JTAG fixture")
    receipt = {
        "component": "osscad", "version": oss_cad.VERSION,
        "archive_sha256": oss_cad.ARCHIVE_SHA256,
        "relative_path": "runtime/oss-cad-suite/bin/yosys.exe",
        "file_sha256": hashlib.sha256(yosys.read_bytes()).hexdigest(),
        "loader_sha256": hashlib.sha256(loader.read_bytes()).hexdigest(),
    }
    (root/"phoenixforge-component.json").write_text(json.dumps(receipt))
    return yosys, loader


def test_release_is_pinned_to_official_digest():
    spec = verify_manifest(ROOT)
    assert spec["bytes"] == 603362463
    assert spec["sha256"] == oss_cad.ARCHIVE_SHA256
    assert "YosysHQ" in spec["url"]


def test_tools_discovery_needs_verified_receipt(tmp_path, monkeypatch):
    yosys, loader = fake_bundle(tmp_path)
    monkeypatch.setattr(oss_cad, "install_roots", lambda: [tmp_path])
    assert oss_cad.locate("yosys.exe") == str(yosys)
    assert oss_cad.locate("openFPGALoader.exe") == str(loader)
    assert open_cyclone.find_yosys(which=lambda n: None) == str(yosys)
    env = oss_cad.tool_environment(str(yosys), base={"PATH": "C:/Windows"})
    assert env["PATH"].startswith(str(yosys.parent))


def test_reject_modified_binary_and_forged_path(tmp_path):
    yosys, loader = fake_bundle(tmp_path)
    assert oss_cad.locate("yosys.exe", roots=[tmp_path])
    yosys.write_bytes(b"Tampered")
    assert oss_cad.locate("yosys.exe", roots=[tmp_path]) is None
    receipt = tmp_path/oss_cad.FOLDER/"phoenixforge-component.json"
    data = json.loads(receipt.read_text())
    data["relative_path"] = "../../outside.exe"
    receipt.write_text(json.dumps(data))
    assert oss_cad.locate("openFPGALoader.exe", roots=[tmp_path]) is None
    with pytest.raises(ValueError):
        oss_cad.locate("quartus_sh.exe", roots=[tmp_path])


def test_installer_requires_download_consent_and_verification():
    nsis = (ROOT/"installer/PhoenixForge_181.nsi").read_text(encoding="utf-8")
    assert "PhoenixForge_v1.8.1_Portable.exe" in nsis
    assert 'Section "OSS CAD Suite' in nsis
    assert "install_osscad_181.ps1" in nsis
    assert "RequestExecutionLevel user" in nsis
    script = (ROOT/"installer/install_osscad_181.ps1").read_text(encoding="utf-8")
    for token in ("Get-FileHash", "SHA-256", "max_entries", "tar.exe", "Move-Item"):
        assert token in script
    for forbidden in ("SetEnvironmentVariable", "pnputil", "Invoke-Expression"):
        assert forbidden not in script


def test_reject_manifest_mutation(tmp_path):
    (tmp_path/"installer").mkdir()
    spec = verify_manifest(ROOT)
    spec["url"] = "https://example.net/wrong.tgz"
    (tmp_path/"installer/osscad-181.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        verify_manifest(tmp_path)


def test_legacy_release_gate_keeps_170_default():
    from tools.release_gate import verify_release
    import inspect
    assert inspect.signature(verify_release).parameters["expected_version"].default == "1.7.0"
