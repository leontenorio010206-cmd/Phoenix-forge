"""Cyclone IV local toolchain runner: internal IDE flow, official vendor binaries.

This is NOT a Quartus-free bitstream generator. Only temporary SRAM/JTAG
configuration is supported; flash writes and unknown chains are blocked.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from app.core.hdl import ports
from app.integrations import quartus_bridge

DEVICE = re.compile(r"\bEP4C(?:E|GX)\d+[A-Z0-9]*\b", re.I)
DENSITY = re.compile(r"^EP4C(?:E|GX)\d+", re.I)
CABLE = re.compile(r"^\s*(\d+)\)\s+(.+?)\s*$")
CHIP_LINE = re.compile(r"^\s*([0-9A-Fa-f]{8})\s+(.+?)\s*$")


def discover_tools(executable=None, which=shutil.which, environ=None):
    """Find installed Quartus version without launching its user interface.

    Only scans conventional install locations and trusts installed executables
    chosen by the user or present on PATH; never downloads vendor software.
    """
    env = os.environ if environ is None else environ
    choices = []
    if executable:
        choices.append(Path(executable))
    else:
        for filename in ("quartus_sh", "quartus_sh.exe"):
            value = which(filename)
            if value:
                choices.append(Path(value))
        for var in ("QUARTUS_ROOTDIR", "QUARTUS_ROOTDIR_OVERRIDE"):
            if env.get(var):
                root = Path(env[var])
                choices.extend([root / "bin64/quartus_sh.exe", root / "bin/quartus_sh.exe",
                                root / "linux64/quartus_sh", root / "bin/quartus_sh"])
        bases = [Path("C:/intelFPGA_lite"), Path("C:/intelFPGA"),
                 Path("C:/altera"), Path("C:/Program Files/Altera")]
        for base in bases:
            if base.is_dir():
                for folder in sorted(base.iterdir(), reverse=True):
                    choices.extend([folder / "quartus/bin64/quartus_sh.exe",
                                    folder / "quartus/bin/quartus_sh.exe"])
    seen = set()
    for choice in choices:
        path = choice.expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        if path.is_file() and path.name.lower() in ("quartus_sh", "quartus_sh.exe"):
            # These programs must come from the same vendor toolchain directory.
            ext = ".exe" if path.suffix.lower() == ".exe" else ""
            programmer = path.parent / ("quartus_pgm" + ext)
            scanner = path.parent / ("jtagconfig" + ext)
            if programmer.is_file() and scanner.is_file():
                return {"quartus_sh": str(path), "quartus_pgm": str(programmer),
                        "jtagconfig": str(scanner)}
    raise FileNotFoundError(
        "Necesitas instalar Quartus con soporte Cyclone IV. No hace falta abrirlo; "
        "PhœnixForge usará sus herramientas de compilación y JTAG internamente.")


def run_checked(argv, runner=subprocess.run, cwd=None, timeout=45):
    result = runner(argv, cwd=cwd, capture_output=True, text=True,
                    timeout=timeout, check=False)
    output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    if result.returncode:
        raise RuntimeError("La herramienta devolvió código %d: %s" %
                           (result.returncode, output[-2500:]))
    return output


def parse_jtag(output):
    """Parse jtagconfig output; unrecognised devices never count as verified."""
    found = []
    current = None
    for line in output.splitlines():
        cable = CABLE.match(line)
        if cable:
            if current:
                found.append(current)
            current = {"number": int(cable[1]), "name": cable[2], "devices": []}
            continue
        chip = CHIP_LINE.match(line)
        if current and chip:
            current["devices"].append({"idcode": chip[1].upper(), "label": chip[2]})
    if current:
        found.append(current)
    return found


def scan_hardware(tools, runner=subprocess.run):
    output = run_checked([tools["jtagconfig"], "-n"], runner=runner)
    cables = parse_jtag(output)
    return {"cables": cables, "raw": output}


def validate_chain(scan, part, cable_number=None):
    """Require a single chip matching the density; JTAG cannot verify package.

    Selecting a programmer via USB VID/PID alone is never sufficient.
    """
    part = quartus_bridge.validate_part(part)
    density = DENSITY.match(part)
    if not density:
        raise ValueError("No se pudo identificar la familia/densidad del chip.")
    cables = scan.get("cables", [])
    if cable_number is None:
        if len(cables) != 1:
            raise ValueError("Selecciona el cable JTAG exacto; hay cero o varios.")
        selected = cables[0]
    else:
        selected = next((c for c in cables if c["number"] == int(cable_number)), None)
        if selected is None:
            raise ValueError("El cable JTAG seleccionado ya no está conectado.")
    if len(selected["devices"]) != 1:
        raise ValueError("Solo se admite una FPGA en la cadena JTAG. Revisa el cable.")
    chip = selected["devices"][0]
    detected = DEVICE.search(chip["label"])
    if not detected or DENSITY.match(detected.group(0)).group(0).upper() != density.group(0).upper():
        raise ValueError("La FPGA JTAG (%s) no coincide con el chip seleccionado (%s)." %
                         (chip["label"], part))
    # IDCODE identifies device family/density, NOT package, voltage or pin mapping.
    return selected


def verify_pin_coverage(project, top):
    """Fail closed for unsatisfied top-level port locations before SRAM programming."""
    index = [m for m in __import__("app.core.hdl", fromlist=["modules"]).modules(project.files)
             if m["name"] == top]
    if len(index) != 1:
        raise ValueError("El módulo principal debe estar definido una sola vez.")
    definitions = ports(project.files[index[0]["file"]], top)
    expected = set()
    for entry in definitions:
        if entry["width"] == 1:
            expected.add(entry["name"])
        else:
            expected.update(entry["name"] + "[" + str(n) + "]"
                            for n in range(min(entry["msb"], entry["lsb"]),
                                           max(entry["msb"], entry["lsb"]) + 1))
    assigned = set(project.pins)
    missing = expected - assigned
    extra = assigned - expected
    if missing or extra:
        raise ValueError(
            "Pinout incompleto. Faltan: %s. Sobran: %s. Comprueba el esquema real." %
            (", ".join(sorted(missing)) or "ninguno",
             ", ".join(sorted(extra)) or "ninguno"))
    if not expected:
        raise ValueError("El módulo no contiene pines físicos verificables.")
    return expected


def find_fresh_sof(project_dir, started_at):
    """Reject absent or old bitstreams; never silently upload a stale build."""
    path = Path(project_dir) / "output_files" / (quartus_bridge.PROJECT_NAME + ".sof")
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError("Quartus no produjo un archivo .sof válido.")
    if path.stat().st_mtime < started_at - 2:
        raise RuntimeError("El archivo .sof es anterior a esta compilación.")
    return path


def compile_and_run(project, parent, part, top, cable_number=None,
                    executable=None, runner=subprocess.run, on_stage=None):
    """One click after setup: export -> build -> rescan JTAG -> SRAM configure.

    The UI must require explicit consent and manual verification of the physical
    pin mapping. No .pof/.jic/flash operations are exposed by this function.
    """
    project.validate()
    part = quartus_bridge.validate_part(part)
    verify_pin_coverage(project, top)
    notify = on_stage or (lambda msg: None)
    tools = discover_tools(executable)
    notify("Detectando cable y chip por JTAG (solo lectura)...")
    initial = scan_hardware(tools, runner)
    selected = validate_chain(initial, part, cable_number)
    cable_number = selected["number"]

    notify("Exportando proyecto Quartus con el chip y los pines confirmados...")
    folder = quartus_bridge.export_project(project, parent, part, top=top, pins=project.pins)
    notify("Compilando dentro del flujo de PhoenixForge mediante Quartus...")
    started_at = time.time()
    report = run_checked([tools["quartus_sh"], "--flow", "compile",
                          quartus_bridge.PROJECT_NAME],
                         runner=runner, cwd=str(folder), timeout=1800)
    bitstream = find_fresh_sof(folder, started_at)

    notify("Verificando de nuevo la cadena JTAG antes de configurar...")
    fresh = scan_hardware(tools, runner)
    validate_chain(fresh, part, cable_number)
    notify("Cargando .sof en la SRAM de FPGA (no Flash)...")
    # One-device JTAG chain guaranteed by validate_chain; @1 denotes device 1.
    result = run_checked([tools["quartus_pgm"], "-c", str(cable_number), "-m", "jtag",
                          "-o", "p;%s@1" % str(bitstream)],
                         runner=runner, timeout=180)
    notify("Programación SRAM finalizada. El diseño empieza a operar con alimentación.")
    return {"folder": str(folder), "bitstream": str(bitstream),
            "cable_number": cable_number, "report": report[-3000:],
            "programmer": result[-3000:]}
