"""1.8.3 regression coverage: fail closed before every FPGA write."""
from pathlib import Path
import json
import subprocess
import pytest

from app.core.project import Project
from app.integrations import cyclone_deploy, oss_cad


@pytest.fixture
def project():
    return Project(
        name="test", device="cyclone_iv",
        files={"top.v": "module top(input a,output y);assign y=a;endmodule"},
        simulation={"top": "top", "testbench": "", "timeout": 15},
        pins={"a": "PIN_E1", "y": "PIN_G15"})


def stage(project, tmp_path):
    rbf = tmp_path / "input.rbf"
    rbf.write_bytes(bytes(range(256)) * 300)
    root = tmp_path / "package"
    cyclone_deploy.stage_external_rbf(
        project, rbf, root, "EP4CE6F17C8", "AX301 revision A",
        pins_confirmed=True, voltage_confirmed=True)
    return root, rbf


@pytest.mark.parametrize("output", [
    "Found EP4CE6F17C8\nIDCODE: 0x020830DD\nIDCODE: 0x020830DD",
    "Found EP4CE6F17C8\nIDCODE: 0x020830DD\nEP4CE10F17C8",
    "Unknown JTAG device IDCODE: 0x020830DD",
    "No device found IDCODE: 0x020830DD",
    "Chain length: 2 IDCODE: 0x020830DD",
])
def test_jtag_ambiguous_always_rejected(output):
    with pytest.raises(RuntimeError):
        cyclone_deploy.jtag_preflight(output, "EP4CE6F17C8")


def test_rbf_modified_during_scan_is_rejected_without_programming(project, tmp_path):
    package, original = stage(project, tmp_path)
    calls = []
    loader = tmp_path / "openFPGALoader.exe"
    loader.write_bytes(b"stand-in")

    def run(args, **kwargs):
        calls.append(list(args))
        if "--detect" in args:
            image = package / "firmware.rbf"
            content = bytearray(image.read_bytes())
            content[99] ^= 0xFF
            image.write_bytes(content)
            return subprocess.CompletedProcess(args, 0, "Found EP4CE6F17C8 IDCODE: 0x020830DD", "")
        raise AssertionError("Unexpected write attempt")

    with pytest.raises(ValueError, match="SHA256"):
        cyclone_deploy.deploy_sram(
            package, "usb-blaster", "EP4CE6F17C8",
            confirmed_board=True, confirmed_external_bitstream=True,
            confirmed_sram_only=True, loader=loader, runner=run)
    assert len(calls) == 1
    assert "--detect" in calls[0]


def test_sram_writes_only_a_private_copy(project, tmp_path):
    package, original = stage(project, tmp_path)
    calls = []
    loader = tmp_path / "openFPGALoader.exe"
    loader.write_bytes(b"stand-in")

    def run(args, **kwargs):
        calls.append(list(args))
        if "--detect" in args:
            return subprocess.CompletedProcess(args, 0, "Found EP4CE6F17C8 IDCODE: 0x020830DD", "")
        assert "-m" in args and "-f" not in args
        assert args[-1] != str(package / "firmware.rbf")
        assert Path(args[-1]).read_bytes() == (package / "firmware.rbf").read_bytes()
        return subprocess.CompletedProcess(args, 0, "FPGA configured SRAM", "")

    result = cyclone_deploy.deploy_sram(
        package, "usb-blaster", "EP4CE6F17C8",
        confirmed_board=True, confirmed_external_bitstream=True,
        confirmed_sram_only=True, loader=loader, runner=run)
    assert result["flash_written"] is False
    assert len(calls) == 2
    assert not Path(calls[-1][-1]).exists()


def test_staging_rejects_symlink_firmware(project, tmp_path):
    package, firmware = stage(project, tmp_path)
    link = tmp_path / "linked.rbf"
    try:
        link.symlink_to(firmware)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks disabled on this host")
    with pytest.raises(ValueError, match="simbólicos"):
        cyclone_deploy.stage_external_rbf(
            project, link, tmp_path / "other", "EP4CE6F17C8", "AX301 A",
            pins_confirmed=True, voltage_confirmed=True)


def test_manifest_rejects_duplicate_or_forged_pins(project, tmp_path):
    package, source = stage(project, tmp_path)
    marker = package / "manifest.json"
    data = json.loads(marker.read_text(encoding="utf-8"))
    data["pins"] = {"a": "PIN_G15", "y": "PIN_G15"}
    marker.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicados"):
        cyclone_deploy.inspect_staged(package)
    data["pins"] = {"a": "FIRMWARE_OUTSIDE"}
    marker.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="inválida"):
        cyclone_deploy.inspect_staged(package)


def test_all_oss_cad_tools_must_match_receipt(tmp_path):
    root = tmp_path / oss_cad.FOLDER
    bin_dir = root / "runtime" / "oss-cad-suite" / "bin"
    bin_dir.mkdir(parents=True)
    import hashlib
    names = ["yosys.exe", "openFPGALoader.exe", "nextpnr-generic.exe"]
    digests = {}
    for name in names:
        exe = bin_dir / name
        exe.write_bytes(name.encode("utf-8"))
        digests[name] = hashlib.sha256(exe.read_bytes()).hexdigest()
    receipt = {"component": "osscad", "version": oss_cad.VERSION,
               "archive_sha256": oss_cad.ARCHIVE_SHA256,
               "relative_path": "runtime/oss-cad-suite/bin/yosys.exe",
               "file_sha256": digests["yosys.exe"],
               "loader_sha256": digests["openFPGALoader.exe"],
               "nextpnr_sha256": digests["nextpnr-generic.exe"]}
    (root / "phoenixforge-component.json").write_text(json.dumps(receipt))
    assert oss_cad.locate("nextpnr-generic.exe", roots=[tmp_path])
    (bin_dir / "yosys.exe").write_bytes(b"tampered")
    assert oss_cad.locate("nextpnr-generic.exe", roots=[tmp_path]) is None
    assert oss_cad.locate("openFPGALoader.exe", roots=[tmp_path]) is None
