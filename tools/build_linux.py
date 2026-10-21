"""Build and validate an experimental x86_64 Linux desktop archive (never Windows)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
NAME = "PhoenixForge-Linux-x86_64"
ARCHIVE = "PhoenixForge_Linux_x86_64_v1.7.0-preview.tar.gz"


def require_linux():
    if not sys.platform.startswith("linux") or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise RuntimeError("This preview requires a native Linux x86_64 builder.")
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        raise RuntimeError("Install the native Linux Icarus Verilog (iverilog and vvp) before building.")


def command(argv, *, env=None, timeout=300):
    return subprocess.run(
        [str(a) for a in argv],
        cwd=str(ROOT), env=env, timeout=timeout,
        shell=False, check=True,
    )


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def build():
    require_linux()
    dist = ROOT / "dist"
    report_path = ROOT / "build/linux-preview-report.json"
    report = {"version": "1.7.0", "platform": platform.platform(),
              "architecture": platform.machine(),
              "linux_preview": True, "success": False}
    try:
        environment = os.environ.copy()
        environment["PHOENIXFORGE_QT"] = "pyside6"
        environment["QT_QPA_PLATFORM"] = "offscreen"

        command([sys.executable, "-m", "compileall", "-q", "app", "tools", "tests"], env=environment)
        command([sys.executable, "-m", "pytest", "-q", "-m", "not packaged",
                 "--junitxml=build/linux-tests.xml"], env=environment, timeout=300)
        command([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
                 "--distpath", "dist", "--workpath", "build/work-linux",
                 "build/PhoenixForgeLinux.spec"], env=environment, timeout=600)
        bundle = dist / "PhoenixForge-Linux"
        app = bundle / "PhoenixForge"
        if not app.is_file() or app.stat().st_size < 1024 * 1024:
            raise RuntimeError("Missing or suspicious frozen Linux application.")

        shutil.copy2(ROOT / "linux/run-phoenixforge.sh", bundle / "run-phoenixforge.sh")
        (bundle / "run-phoenixforge.sh").chmod(0o755)
        for item in ("LICENSE", "THIRD_PARTY_NOTICES.md", "LEGAL.md", "CREDITS.md"):
            shutil.copy2(ROOT / item, bundle / item)
        shutil.copy2(ROOT / "docs/LINUX_PORT.md", bundle / "LEEME-LINUX.md")

        acceptance_dir = ROOT / "build/linux-packaged-acceptance"
        if acceptance_dir.exists():
            shutil.rmtree(acceptance_dir)
        isolated = environment.copy()
        isolated.pop("PYTHONHOME", None)
        isolated.pop("PYTHONPATH", None)
        isolated.pop("QT_PLUGIN_PATH", None)
        isolated.pop("QML2_IMPORT_PATH", None)
        with tempfile.TemporaryDirectory(prefix="phoenix-linux-preview-") as home:
            isolated["HOME"] = home
            isolated["XDG_DATA_HOME"] = str(Path(home) / ".local" / "share")
            command([bundle / "run-phoenixforge.sh", "--doctor"], env=isolated, timeout=30)
            command([bundle / "run-phoenixforge.sh", "--self-test",
                     acceptance_dir, "--offscreen"], env=isolated, timeout=180)
        result = json.loads((acceptance_dir / "acceptance.json").read_text(encoding="utf-8"))
        checks = set(result.get("checks", {}))
        required = {"resources", "window_visible", "editor", "hdl_and_vcd",
                    "project_roundtrip", "plugin", "all_navigation",
                    "hardware_and_digital_ui"}
        if (not result.get("success") or not result.get("frozen")
                or result.get("native_windows")
                or result.get("qt_binding") != "PySide6"
                or not required.issubset(checks)):
            raise RuntimeError("Frozen Linux UI/HDL acceptance incomplete: " + str(result))

        target = dist / NAME
        if target.exists():
            shutil.rmtree(target)
        bundle.rename(target)
        artifact = dist / ARCHIVE
        if artifact.exists():
            artifact.unlink()
        with tarfile.open(artifact, "w:gz", format=tarfile.PAX_FORMAT) as tar:
            tar.add(target, arcname=NAME, recursive=True)
        report.update({"success": True, "archive": artifact.name,
                       "bytes": artifact.stat().st_size,
                       "sha256": digest(artifact),
                       "acceptance": {"success": True, "checks": sorted(checks),
                                      "qt_binding": result["qt_binding"]},
                       "external_iverilog_required": True,
                       "qualification": "Ubuntu 22.04 CI x86_64 preview, not field-certified"})
        (dist / (artifact.name + ".sha256")).write_text(
            report["sha256"] + "  " + artifact.name + "\n", encoding="ascii")
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    if args.report_only:
        print((ROOT / "build/linux-preview-report.json").read_text(encoding="utf-8"))
    else:
        print(json.dumps(build(), indent=2, ensure_ascii=False))
