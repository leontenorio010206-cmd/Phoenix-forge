"""Verified per-user OSS CAD Suite receipt for PhœnixForge 1.8.1 preview.

Never accepts unpinned archives, traverses paths or modifies global PATH.
The presence of an FPGA compiler does not imply Cyclone IV bitstream support.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

VERSION = "2026-10-27"
FOLDER = "OSS-CAD-Suite-20261027"
ARCHIVE_SHA256 = "aadcf3ff1b7cc8720509fde6c57ca84249f3beb45ddd14fd492c608241a12bb8"
ALLOWED = {"yosys.exe", "openFPGALoader.exe", "nextpnr-generic.exe"}


def install_roots():
    """Include portable executable location and usual per-user install path."""
    roots = [Path(sys.executable).resolve().parent / "Integrations"]
    if os.environ.get("LOCALAPPDATA"):
        roots.append(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "PhoenixForge" / "Integrations")
    return roots


def _digest(path):
    obj = hashlib.sha256()
    with path.open("rb") as inp:
        for block in iter(lambda: inp.read(1024 * 1024), b""):
            obj.update(block)
    return obj.hexdigest()


def _installed(roots, name):
    if name not in ALLOWED:
        raise ValueError("Herramienta OSS CAD no permitida")
    for root in roots:
        directory = Path(root) / FOLDER
        marker = directory / "phoenixforge-component.json"
        if not marker.is_file() or marker.is_symlink():
            continue
        try:
            info = json.loads(marker.read_text(encoding="utf-8-sig"))
            if (info.get("component") != "osscad" or info.get("version") != VERSION or
                    info.get("archive_sha256") != ARCHIVE_SHA256 or
                    info.get("relative_path") != "runtime/oss-cad-suite/bin/yosys.exe"):
                continue
            bin_dir = directory / "runtime" / "oss-cad-suite" / "bin"
            exe = bin_dir / name
            if not exe.is_file() or exe.is_symlink():
                continue
            if not exe.resolve().is_relative_to(directory.resolve()):
                continue
            if name == "yosys.exe":
                expected = info.get("file_sha256")
            elif name == "openFPGALoader.exe":
                expected = info.get("loader_sha256")
            else:
                expected = info.get("nextpnr_sha256")
            if (not isinstance(expected, str) or len(expected) != 64 or
                    _digest(exe) != expected):
                continue
            # A compatible install must still have intact mandatory tools.
            core = {"yosys.exe": info.get("file_sha256"),
                    "openFPGALoader.exe": info.get("loader_sha256")}
            for core_name, core_hash in core.items():
                target = bin_dir / core_name
                if (not target.is_file() or target.is_symlink() or
                        not isinstance(core_hash, str) or len(core_hash) != 64 or
                        _digest(target) != core_hash):
                    break
            else:
                return exe
            continue
            return exe
        except (OSError, ValueError, TypeError):
            continue
    return None


def locate(name, roots=None):
    found = _installed(install_roots() if roots is None else roots, name)
    return str(found) if found else None


def tool_environment(executable, base=None):
    """Activate only for a child process, preserving global/user environment."""
    env = dict(os.environ if base is None else base)
    bin_dir = Path(executable).resolve().parent
    if bin_dir.name.lower() == "bin" and bin_dir.parent.name == "oss-cad-suite":
        root = bin_dir.parent
        # Mirror the relevant entries from upstream environment.bat,
        # scoped only to our Yosys/JTAG child process (never global PATH).
        env["PATH"] = os.pathsep.join(
            (str(bin_dir), str(root / "lib"), env.get("PATH", "")))
        env["YOSYSHQ_ROOT"] = str(root) + os.sep
        env["PYTHON_EXECUTABLE"] = str(root / "lib" / "python3.exe")
        env["SSL_CERT_FILE"] = str(root / "etc" / "cacert.pem")
        env["OPENFPGALOADER_SOJ_DIR"] = str(root / "share" / "openFPGALoader")
    return env
