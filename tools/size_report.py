"""Record release size by category; keep all runtime and LGPL/GPL sources.

Never strip binaries or remove license/source obligations automatically.
"""
import argparse
import json
from pathlib import Path


def total_bytes(path):
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def report_sizes(root, dist):
    base = Path(root)
    target = Path(dist)
    components = {
        "FPGA_Icarus_runtime": "vendor/icarus",
        "Qt_sources_corresponding": "vendor/sources",
        "Third_party_licenses": "vendor/licenses",
        "Application_code": "app",
        "Examples": "examples",
        "Documentation": "docs",
    }
    measured = {label: total_bytes(base / rel) for label, rel in components.items()}
    outputs = {p.name: p.stat().st_size for p in target.glob("*")
               if p.is_file() and p.suffix in {".exe", ".zip"}}
    return {
        "format": 1, "measurement": "bytes_uncompressed_source_and_artifacts",
        "parts": measured, "artifacts": outputs,
        "observations": [
            "PyInstaller onefile comprime sus dependencias; el tamaño no es la suma de los componentes.",
            "No se elimina Icarus ni Qt ni fuentes/licencias correspondientes para ahorrar espacio.",
            "Un portable de archivo único se extrae al ejecutar; en HDD el arranque puede ser más lento.",
            "Comparar tiempos de inicio y peso en un Windows 10 físico antes de declarar mejoras."
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--dist", default="dist")
    p.add_argument("--output", default="build/size-report.json")
    args = p.parse_args()
    result = report_sizes(args.root, args.dist)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
