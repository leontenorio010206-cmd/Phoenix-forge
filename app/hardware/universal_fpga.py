"""Vendor-neutral *diagnostics* for FPGA hardware.

Important: recognising a JTAG chip is not discovering the PCB model, pins,
voltages, package or a valid toolchain. Physical writes are never performed.
"""
import re
import shutil

from app.hardware import fpga


# This is a feature/capability matrix, NOT a promise that all backends are
# implemented. "integrated" means the PhoenixForge adapter exists today.
FAMILIES = (
    {
        "key": "cyclone_iv", "name": "Intel/Altera Cyclone IV",
        "pattern": r"\bEP4C(?:E|GX)[A-Z0-9]+\b",
        "vendor": "Intel/Altera", "builder": "Quartus Prime con soporte Cyclone IV",
        "tools": ("quartus_sh", "quartus_pgm", "jtagconfig"),
        "integrated": True,
        "notes": "Compilación + SRAM/JTAG integrada, solo con chip completo y pines verificados.",
    },
    {
        "key": "cyclone_v", "name": "Intel/Altera Cyclone V",
        "pattern": r"\b(?:5CSE|5CEB|5CGX|5CSX|5CST)[A-Z0-9]+\b",
        "vendor": "Intel/Altera", "builder": "Quartus (versión compatible)",
        "tools": ("quartus_sh",), "integrated": False,
        "notes": "Editor y RTL disponibles; el flujo físico aún no está integrado.",
    },
    {
        "key": "ice40", "name": "Lattice iCE40",
        "pattern": r"\b(?:ICE40[A-Z0-9]+|HX(?:1|4|8)K|UP5K|LP[0-9]+K)\b",
        "vendor": "Lattice", "builder": "Yosys + nextpnr-ice40 + IceStorm",
        "tools": ("yosys", "nextpnr-ice40", "icepack"), "integrated": False,
        "notes": "Toolchain abierta compatible con ciertos chips, paquetes y pines.",
    },
    {
        "key": "ecp5", "name": "Lattice ECP5",
        "pattern": r"\bLFE5(?:U|UM|UM5G)?[-A-Z0-9]+\b",
        "vendor": "Lattice", "builder": "Yosys + nextpnr-ecp5 + Project Trellis",
        "tools": ("yosys", "nextpnr-ecp5", "ecppack"), "integrated": False,
        "notes": "Requiere chip/paquete exactos y fichero LPF verificado.",
    },
    {
        "key": "gowin", "name": "Gowin GW1N/GW2A/GW5",
        "pattern": r"\bGW(?:1N|1NR|1NSR|2A|5A|5AST)[-A-Z0-9]*\b",
        "vendor": "Gowin", "builder": "Gowin EDA o herramientas abiertas específicas",
        "tools": ("yosys", "nextpnr-himbaechel", "gowin_pack"),
        "integrated": False,
        "notes": "No todos los modelos Gowin tienen flujo abierto compatible.",
    },
    {
        "key": "xilinx7", "name": "AMD/Xilinx Serie 7",
        "pattern": r"\bXC7(?:A|S|K|V|Z)[A-Z0-9]+\b",
        "vendor": "AMD/Xilinx", "builder": "Vivado o un flujo abierto específico",
        "tools": ("vivado",), "integrated": False,
        "notes": "No se considera listo para carga automática.",
    },
    {
        "key": "spartan6", "name": "AMD/Xilinx Spartan-6",
        "pattern": r"\bXC6SLX[A-Z0-9]+\b",
        "vendor": "AMD/Xilinx", "builder": "ISE (herramienta legacy)",
        "tools": (), "integrated": False,
        "notes": "El flujo de síntesis de fabricante es antiguo; no integrado.",
    },
    {
        "key": "efinix", "name": "Efinix",
        "pattern": r"\b(?:T[0-9]+F[A-Z0-9]+|TI[0-9]+F[A-Z0-9]+)\b",
        "vendor": "Efinix", "builder": "Efinity",
        "tools": (), "integrated": False,
        "notes": "No hay integración de síntesis/programación en PhoenixForge.",
    },
)
COMPILED = tuple((row, re.compile(row["pattern"], re.I)) for row in FAMILIES)
SAFE_CABLE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,75}$")
# Do not infer model from USB VID/PID, FTDI adapter name or the cable selector.
UNKNOWN = {
    "family": "No identificada", "vendor": "Desconocido",
    "detected_part": "", "key": "unknown", "confidence": "sin verificar",
    "builder": "Por determinar", "integrated": False,
    "notes": "Se requiere leer el chip por JTAG y validar el modelo de tarjeta.",
}


def infer_from_jtag(result):
    """Extract a tentative device family *only* from JTAG output.

    A string that merely mentions a family is not proof of a real read: the UI
    always labels its identification as tentative and shows the raw diagnosis.
    """
    result = str(result or "")
    for row, pattern in COMPILED:
        match = pattern.search(result)
        if match:
            return {
                "family": row["name"], "vendor": row["vendor"],
                "detected_part": match.group(0).upper(), "key": row["key"],
                "confidence": "tentativa: valida el IDCODE y el marcado físico",
                "builder": row["builder"], "integrated": row["integrated"],
                "notes": row["notes"],
            }
    return dict(UNKNOWN)


def toolchain_inventory(which=shutil.which):
    """Only inspect PATH, do not start any third-party process."""
    wanted = sorted({name for row in FAMILIES for name in row["tools"]} |
                    {"openFPGALoader"})
    found = {}
    for name in wanted:
        candidate = which(name)
        if not candidate and name == "openFPGALoader":
            candidate = which("openFPGALoader.exe")
        elif not candidate:
            candidate = which(name + ".exe")
        found[name] = str(candidate) if candidate else None
    return found


def capability_inventory(found=None):
    """Return truthful states: installed is not integrated or certified."""
    found = toolchain_inventory() if found is None else found
    items = []
    for row in FAMILIES:
        missing = [name for name in row["tools"] if not found.get(name)]
        items.append({
            "key": row["key"], "name": row["name"],
            "builder": row["builder"],
            "tools_installed": not missing and bool(row["tools"]),
            "missing_tools": missing,
            "integrated": row["integrated"],
            "ready_for_hardware": False,
            "note": row["notes"],
        })
    return items



def suggest_cable_for_usb(identity):
    """Suggest, never assert: a USB descriptor identifies only an adapter."""
    matched = fpga.VID_PID.search(str(identity or ""))
    if not matched:
        return None, ("El dispositivo seleccionado no expone un VID/PID USB "
                      "compatible. Elige el cable a partir de su documentación.")
    vid = matched.group(1).upper()
    if vid == "09FB":
        return "usb-blaster", (
            "Parece un adaptador Intel/Altera compatible con USB-Blaster. "
            "Podría ser otra revisión o una copia: verifica el modelo y, "
            "si es USB-Blaster II, elige usb-blasterII. "
            "NO identifica el chip FPGA ni los pines.")
    if vid in {"0403", "2A19"}:
        return None, ("Adaptador FTDI/Digilent detectado. Existen muchos "
                      "cables y canales con ese proveedor; consulta el modelo "
                      "y selecciona su identificador compatible con openFPGALoader.")
    return None, ("USB VID/PID no basta para reconocer un cable JTAG. "
                  "Selecciona el tipo de cable desde su documentación.")


def inspect_cable(target, loader=None, runner=None):
    """Explicit read-only probe. Never probes all interfaces without selection."""
    if not SAFE_CABLE.fullmatch(target or ""):
        raise ValueError("Selecciona un cable compatible (ejemplo: usb-blaster).")
    kwargs = {"executable": loader, "via": "cable"}
    if runner is not None:
        kwargs["runner"] = runner
    output = fpga.probe_target(target, **kwargs)
    return {"cable": target, "raw": output, "match": infer_from_jtag(output),
            "board_identified": False, "pins_identified": False,
            "programming_allowed": False}


def describe_survey(survey, tools=None):
    """Presentation text, clear about identification and safety boundaries."""
    match = survey["match"]
    lines = [
        "Cable JTAG seleccionado: " + survey["cable"],
        "Familia posible: " + match["family"],
        "Marcado detectado: " + (match["detected_part"] or "No reconocido"),
        "Confianza: " + match["confidence"],
        "Síntesis: " + match["builder"],
        "Integración física en PhoenixForge: " +
        ("Parcial (Cyclone IV)" if match["integrated"] else "No implementada"),
        "Placa exacta y asignaciones de pines: NO IDENTIFICADAS",
        "Programación: BLOQUEADA hasta conocer chip, placa y pines verificados.",
        "Notas: " + match["notes"],
        "",
        "Salida original de la herramienta (revisar antes de confiar):",
        survey["raw"][:4500],
    ]
    return "\n".join(lines)
