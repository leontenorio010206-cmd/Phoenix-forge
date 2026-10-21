"""Build the optional online NSIS Setup only AFTER strict native EXE acceptance."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.release_gate import verify_release
from tools.verify_artifact import inspect_pe

VERSION = "1.7.0"


def find_nsis():
    candidates = [shutil.which("makensis"), shutil.which("makensis.exe")]
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(variable)
        if base:
            candidates.append(str(Path(base) / "NSIS" / "makensis.exe"))
    return next((str(p) for p in candidates if p and Path(p).is_file()), None)


def verify_components_manifest(root):
    doc = json.loads((Path(root) / "installer/optional-components.json").read_text(encoding="utf-8"))
    if doc.get("schema_version") != 1 or set(doc["components"]) != {"java", "digital"}:
        raise ValueError("Manifiesto del instalador incompatible")
    for name, spec in doc["components"].items():
        from urllib.parse import urlparse
        url = urlparse(spec["url"])
        if (url.scheme != "https" or url.hostname != "github.com" or
                len(spec["sha256"]) != 64 or not all(c in "0123456789abcdef" for c in spec["sha256"])):
            raise ValueError("Descarga insegura o hash inválido: " + name)
        if not 10_000 < int(spec["bytes"]) < 150_000_000:
            raise ValueError("Tamaño de descarga fuera de rango: " + name)
    return doc


def build_setup(root=ROOT, nsis=None, runner=subprocess.run):
    root = Path(root).resolve()
    verify_components_manifest(root)
    exe = root / "dist" / f"PhoenixForge_v{VERSION}_Portable.exe"
    verify_release(root / "build/windows-build-report.json", exe.parent)
    tool = nsis or find_nsis()
    if not tool:
        raise FileNotFoundError("NSIS makensis.exe no está instalado")
    args = [str(tool), "/INPUTCHARSET", "UTF8", "/DPF_ROOT=" + str(root),
            str(root / "installer/PhoenixForge.nsi")]
    runner(args, cwd=str(root), check=True)
    output = root / "dist" / f"PhoenixForge_v{VERSION}_Setup.exe"
    info = inspect_pe(output, minimum_size=20 * 1024 * 1024, machine=None)
    sha_file = output.parent / "SHA256SUMS.txt"
    existing = sha_file.read_text(encoding="ascii") if sha_file.exists() else ""
    if output.name in existing:
        raise ValueError("Checksum duplicado en SHA256SUMS")
    with sha_file.open("a", encoding="ascii") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(info["sha256"] + "  " + info["name"] + "\n")
    report = {
        "version": VERSION, "exe": info,
        "components": list(verify_components_manifest(root)["components"]),
        "result": "installer_generated_after_strict_native_acceptance",
        "qualification": "NSIS packaging verified; optional downloads/installed apps require end-user checks",
    }
    (root / "build/setup-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nsis")
    options = parser.parse_args()
    print(json.dumps(build_setup(nsis=options.nsis), indent=2))
