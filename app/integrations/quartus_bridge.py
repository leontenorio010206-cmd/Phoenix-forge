"""Conservative Cyclone IV / Quartus project export and external compilation.

No device is inferred from an attached USB cable. Nothing is programmed here.
The user must supply the exact chip marking and verified board pinout.
"""
import re
import shutil
import subprocess
from pathlib import Path

from app.core.hdl import identifier, modules
from app.utils.paths import safe_relative

DEVICE_RE = re.compile(r"^EP4C(?:E|GX)[A-Z0-9]{4,22}$")
PIN_RE = re.compile(r"^PIN_[A-Z0-9]{1,8}$")
PORT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*(?:\[[0-9]+\])?$")
SOURCE_RE = re.compile(r"^[A-Za-z0-9_./ -]+$")
PROJECT_NAME = "PhoenixForge_CycloneIV"


def validate_part(part):
    """Validate syntax only: Quartus must verify the exact part is supported."""
    part = str(part or "").strip().upper()
    if not DEVICE_RE.fullmatch(part):
        raise ValueError("Introduce el código COMPLETO del chip Cyclone IV (EP4CE... o EP4CGX...).")
    return part


def find_quartus(executable=None):
    """Locate a user-selected Quartus executable or one already on PATH."""
    if executable:
        path = Path(executable).expanduser().resolve()
        if path.name.lower() not in ("quartus_sh", "quartus_sh.exe") or not path.is_file():
            raise ValueError("Selecciona un ejecutable quartus_sh válido de Quartus.")
        return str(path)
    found = shutil.which("quartus_sh") or shutil.which("quartus_sh.exe")
    if not found:
        raise FileNotFoundError("No se encontró quartus_sh. Selecciónalo desde Quartus Prime Lite.")
    return found


def export_project(project, parent, part, top=None, pins=None):
    """Export a new self-contained .qpf/.qsf folder; never overwrite old projects.

    Physical pin assignments require an exact board schematic, and are never
    guessed from a generic device profile or a USB-Blaster identification.
    """
    project.validate()
    part = validate_part(part)
    top = identifier(top or project.simulation.get("top", ""))
    if top == project.simulation.get("testbench"):
        raise ValueError("El módulo principal no puede ser el testbench.")
    index = modules(project.files)
    if top not in {entry["name"] for entry in index}:
        raise ValueError("No se encontró el módulo principal en las fuentes Verilog.")

    source_files = []
    for filename, content in sorted(project.files.items()):
        if not filename.lower().endswith((".v", ".sv")):
            continue
        safe_relative(filename)
        if not SOURCE_RE.fullmatch(filename):
            raise ValueError("Renombra el archivo HDL: ruta incompatible con Quartus: " + filename)
        entries = [m for m in index if m["file"] == filename]
        # Exclude files that contain testbenches only; keep files with design modules.
        if entries and all(m["testbench_hint"] or
                           m["name"] == project.simulation.get("testbench") for m in entries):
            continue
        source_files.append((filename, content))
    if not source_files:
        raise ValueError("El proyecto no contiene fuentes sintetizables.")

    # Explicit override allows a verified physical pinout, never a guessed one.
    physical_pins = project.pins if pins is None else pins
    if not isinstance(physical_pins, dict):
        raise ValueError("Las asignaciones de pines deben ser un diccionario.")
    checked_pins = []
    seen = set()
    for signal, location in sorted(physical_pins.items()):
        if not PORT_RE.fullmatch(str(signal)) or not PIN_RE.fullmatch(str(location).upper()):
            raise ValueError("Pin inválido: %r -> %r. Usa 'clk': 'PIN_23'." % (signal, location))
        location = str(location).upper()
        if location in seen:
            raise ValueError("Un pin físico no puede asignarse a dos señales: " + location)
        seen.add(location)
        checked_pins.append((signal, location))

    parent = Path(parent).expanduser().resolve()
    if not parent.is_dir():
        raise FileNotFoundError("Selecciona una carpeta de destino existente.")
    output = parent / (PROJECT_NAME + "_" + project.project_id[:8])
    if output.exists():
        raise FileExistsError("La carpeta ya existe: " + str(output))
    output.mkdir()

    qsf = [
        '# Generado por PhœnixForge: NO implica compatibilidad física certificada.',
        'set_global_assignment -name FAMILY "Cyclone IV GX"' if part.startswith("EP4CGX")
            else 'set_global_assignment -name FAMILY "Cyclone IV E"',
        'set_global_assignment -name DEVICE ' + part,
        'set_global_assignment -name TOP_LEVEL_ENTITY ' + top,
    ]
    for filename, content in source_files:
        destination = output / "src" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        kind = "SYSTEMVERILOG_FILE" if filename.lower().endswith(".sv") else "VERILOG_FILE"
        qsf.append("set_global_assignment -name %s {src/%s}" % (kind, filename))
    for signal, location in checked_pins:
        qsf.append("set_location_assignment %s -to {%s}" % (location, signal))

    (output / (PROJECT_NAME + ".qpf")).write_text(
        'PROJECT_REVISION = "' + PROJECT_NAME + '"\n', encoding="utf-8")
    (output / (PROJECT_NAME + ".qsf")).write_text("\n".join(qsf) + "\n", encoding="utf-8")
    (output / "LEEME_ANTES_DE_PROGRAMAR.txt").write_text(
        "El proyecto puede sintetizarse en Quartus si el dispositivo exacto existe.\n"
        "No se ha comprobado la placa física, el reloj, voltajes o el pinout.\n"
        "Chip seleccionado: " + part + "\n"
        "Asignaciones de pines: " + str(len(checked_pins)) + "\n"
        "Antes de programar: verifica TODAS las señales, restricciones de reloj,\n"
        "estándares I/O, diagrama de la tarjeta y dispositivo detectado por JTAG.\n"
        "La compilación NO implica que la placa sea segura de programar.\n",
        encoding="utf-8")
    return output


def compile_project(folder, executable=None, runner=subprocess.run, timeout=1800):
    """Compile externally through quartus_sh; no JTAG/write operations."""
    folder = Path(folder).expanduser().resolve()
    if not (folder / (PROJECT_NAME + ".qsf")).is_file():
        raise FileNotFoundError("No existe un proyecto Quartus exportado en esta carpeta.")
    cmd = [find_quartus(executable), "--flow", "compile", PROJECT_NAME]
    result = runner(cmd, cwd=str(folder), capture_output=True, text=True,
                    timeout=timeout, check=False)
    output = ((result.stdout or "") + "\n" + (result.stderr or ""))[-20000:]
    if result.returncode:
        raise RuntimeError("Quartus terminó con código %d:\n%s" %
                           (result.returncode, output[-5000:]))
    return output.strip()
