"""Quartus-free RTL synthesis. JSON/BLIF netlists are NOT FPGA bitstreams."""
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile

from app.core.hdl import identifier, modules
from app.integrations.quartus_bridge import validate_part
from app.integrations import oss_cad
from app.utils.paths import safe_relative

SOURCE = re.compile(r"^[A-Za-z0-9_./ -]+$")
SCRIPT_NAME = "phoenix_open_synthesis.ys"
EXPERIMENTAL_PART = "EP4CE6F17C8"
RESEARCH_URL = "https://github.com/14sea/Cyclone_CRAM_Mapper"


def find_yosys(executable=None, which=shutil.which):
    """Look for a signed/verified-by-packager or user-selected binary, never download."""
    if executable:
        path = Path(executable).expanduser().resolve()
        if path.name.lower() not in ("yosys", "yosys.exe") or not path.is_file():
            raise ValueError("Selecciona un ejecutable Yosys válido.")
        return str(path)
    if getattr(sys, "frozen", False):
        roots = [Path(sys.executable).resolve().parent]
        if getattr(sys, "_MEIPASS", None):
            roots.append(Path(sys._MEIPASS).resolve())
        for root in roots:
            for rel in ("tools/yosys.exe", "tools/yosys",
                        "bin/yosys.exe", "bin/yosys", "yosys.exe", "yosys"):
                candidate = root / rel
                if candidate.is_file():
                    return str(candidate)
    packaged = oss_cad.locate("yosys.exe")
    if packaged:
        return packaged
    result = which("yosys") or which("yosys.exe")
    if result:
        return str(result)
    raise FileNotFoundError(
        "No hay Yosys disponible. La versión portable aún debe empaquetar "
        "un binario verificado con sus licencias; nunca exige Quartus.")


def design_sources(project, top):
    """Keep synthesis inputs separate from testbenches and arbitrary commands."""
    project.validate()
    top = identifier(str(top or "").strip())
    if not top or top == project.simulation.get("testbench"):
        raise ValueError("El top no puede estar vacío ni ser el testbench.")
    index = modules(project.files)
    if top not in {m["name"] for m in index}:
        raise ValueError("El módulo top no existe en el proyecto.")
    result = []
    for name, body in sorted(project.files.items()):
        if not name.lower().endswith((".v", ".sv")):
            continue
        safe_relative(name)
        if not SOURCE.fullmatch(name):
            raise ValueError("Nombre de archivo HDL no admitido: " + name)
        entries = [m for m in index if m["file"] == name]
        if entries and all(m["testbench_hint"] or
                           m["name"] == project.simulation.get("testbench")
                           for m in entries):
            continue
        result.append((name, body))
    if not result:
        raise ValueError("No existen fuentes HDL sintetizables.")
    return top, result


def synthesis_script(top, sources):
    commands = ["# PhœnixForge: netlist lógico, no FPGA bitstream"]
    commands += ['read_verilog -sv -defer "src/%s"' % name for name, _ in sources]
    commands += ["hierarchy -check -top " + top,
                 "synth -top " + top + " -flatten", "check -assert", "stat",
                 'write_json "netlist.json"', 'write_blif "netlist.blif"']
    return "\n".join(commands) + "\n"


def synthesize(project, parent, top, part, executable=None,
               runner=subprocess.run, timeout=300):
    """Compile Verilog to JSON/BLIF using Yosys. Never generate or flash RBF/SOF."""
    part = validate_part(part)
    top, sources = design_sources(project, top)
    tool = find_yosys(executable)
    parent = Path(parent).expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="yosys-", dir=str(parent)))
    for name, body in sources:
        path = folder / "src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (folder / SCRIPT_NAME).write_text(
        synthesis_script(top, sources), encoding="utf-8")
    try:
        proc = runner([tool, "-s", SCRIPT_NAME], cwd=str(folder),
                      capture_output=True, text=True, timeout=timeout, check=False,
                      env=oss_cad.tool_environment(tool))
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Yosys excedió el límite de tiempo.") from exc
    log = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-40000:]
    (folder / "yosys.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise RuntimeError("Yosys falló: " + log[-4000:])
    hashes = {}
    for name in ("netlist.json", "netlist.blif"):
        path = folder / name
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError("Yosys no creó " + name)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder / "RESULTADO.txt").write_text(
        "Síntesis lógica completa SIN Quartus.\n"
        "Target previsto: " + part + "\nTop: " + top + "\n"
        "JSON/BLIF no son bitstreams. NO PROGRAMAR FPGA.\n"
        "Faltan tecnología Cyclone IV, place-and-route, bitgen y validación física.\n",
        encoding="utf-8")
    return {"folder": str(folder), "top": top, "part": part,
            "netlist": str(folder / "netlist.json"),
            "blif": str(folder / "netlist.blif"), "hashes": hashes,
            "log_tail": log[-6000:],
            "bitstream_ready": False, "programming_allowed": False}


def ep4ce6_research_status(root, part, which=shutil.which):
    """Read-only capability audit; upstream GPL integration remains separate."""
    part = validate_part(part)
    folder = Path(root).expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError("Selecciona un directorio local de Cyclone_CRAM_Mapper.")
    required = ("synth/ep4ce6_map.v", "synth/prims.v",
                "synth/np2fasm.py", "fuzz/fasm2rbf.py",
                "fuzz/chipdb_gen.py", "results/route_cells_full.json")
    return {"supported_part": part == EXPERIMENTAL_PART,
            "part": part, "reference_part": EXPERIMENTAL_PART,
            "missing": [p for p in required if not (folder / p).is_file()],
            "yosys_found": bool(which("yosys") or which("yosys.exe")),
            "nextpnr_found": bool(which("nextpnr-generic") or which("nextpnr-generic.exe")),
            "bitstream_ready": False, "programming_allowed": False,
            "url": RESEARCH_URL,
            "license": "GPL-3.0-or-later para código upstream, CC BY-SA 4.0 documentos"}
