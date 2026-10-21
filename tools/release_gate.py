"""Release gate: reject any Windows EXE not accepted by native frozen tests."""
import argparse
import json
from pathlib import Path
import sys

# Running `python tools/release_gate.py` puts tools/ (not the repository
# root) on sys.path on Windows. Use the same stable import root as the
# Windows builder so the release gate works both as script and module.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.verify_artifact import inspect_pe


def verify_release(report_path, directory):
    data = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if data.get("version") != "1.7.0" or not data.get("success"):
        raise ValueError("Reporte de build ausente, fallido o de versión equivocada")
    if data.get("validation_status") != "ci_accepted_windows_server_2022":
        raise ValueError("El ejecutable no superó aceptación Windows nativa")
    native = data.get("native_acceptance", {})
    if not native.get("ordinary_startup") or not native.get("development_PATH_removed"):
        raise ValueError("Faltan arranque gráfico real o independencia de PATH")
    launches = native.get("launches", [])
    if len(launches) != 2 or any(
            not all(run.get(k) for k in ("success", "native_windows", "frozen", "bundled_icarus"))
            for run in launches):
        raise ValueError("No se verificaron dos ejecuciones HDL congeladas y nativas")
    if not data.get("artifacts") or len(data["artifacts"]) != 1:
        raise ValueError("Número inesperado de artefactos Windows")
    folder = Path(directory)
    binaries = list(folder.glob("*.exe"))
    expected = "PhoenixForge_v1.7.0_Portable.exe"
    if [p.name for p in binaries] != [expected]:
        raise ValueError("Artefacto ausente o hay ejecutables no verificados en dist")
    actual = inspect_pe(folder / expected, minimum_size=20*1024*1024)
    if actual["sha256"] != data["artifacts"][0].get("sha256"):
        raise ValueError("Checksum del EXE no coincide con el reporte nativo")
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    verified = verify_release(args.report, args.directory)
    print("EXE ACEPTADO en runner Windows:", verified["name"], verified["bytes"], verified["sha256"])


if __name__ == "__main__":
    main()
