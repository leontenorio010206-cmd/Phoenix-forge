"""FPGA programmer discovery and diagnostics for Windows.

USB hardware IDs generally identify the cable/interface, NOT the attached FPGA.
No driver installation, INF modification or registry changes are permitted here.
Optional openFPGALoader operations always require explicit UI confirmation.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import sys

from app.hardware.discovery import VID_PID, _ps

# Quickstart only. The installed tool provides the complete supported lists.
# These are examples of manufacturer *families*; no country-of-origin guesses.
FPGA_EXAMPLES = (
    ("Sipeed Tang Nano", "tangnano", "Gowin GW1N"),
    ("Sipeed Tang Nano 4K", "tangnano4k", "Gowin GW1NSR"),
    ("Sipeed Tang Nano 9K", "tangnano9k", "Gowin GW1NR"),
    ("Sipeed Tang Nano 20K", "tangnano20k", "Gowin GW2A"),
    ("QMTech Cyclone IV", "qmtechCycloneIV", "Intel Cyclone IV"),
    ("QMTech Cyclone V", "qmtechCycloneV", "Intel Cyclone V"),
    ("ULX3S", "ulx3s", "Lattice ECP5"),
    ("iCEBreaker", "icebreaker", "Lattice iCE40"),
    ("Digilent Arty A7", "arty", "AMD/Xilinx Artix-7"),
    ("OrangeCrab", "orangeCrab", "Lattice ECP5"),
    ("Terasic DE10-Nano", "de10nano", "Intel Cyclone V"),
    ("Efinix FireAnt", "fireant", "Efinix Trion"),
)
PROBES = {
    # Manufacturer-assigned identifier indicates adapter only. Clones can spoof it.
    "09FB": ("USB-Blaster / Intel-Altera compatible", "JTAG cable; FPGA not identified"),
    "0403": ("FTDI USB adapter (possibly JTAG)", "Generic FTDI VID; not necessarily FPGA"),
    "2A19": ("Digilent USB adapter (possible)", "Check device interface and model"),
    "1366": ("SEGGER USB probe (possible JTAG)", "J-Link is not automatically FPGA-compatible"),
}
INTERFACE_RE = re.compile(r"&MI_([0-9A-F]{2})", re.I)
VALID_TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,75}$")
VALID_FILENAME = {".bit", ".bin", ".fs", ".svf", ".jed", ".pof", ".rbf", ".hex", ".mcs"}

SIGNED_DRIVERS_PS = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
@(
  Get-CimInstance Win32_PnPSignedDriver |
    Where-Object { $_.DeviceID -like 'USB*' } |
    Select-Object DeviceID, DeviceName, DriverProviderName, DriverVersion, InfName
) | ConvertTo-Json -Depth 4 -Compress
"""
DEVICE_STATUS_PS = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
@(
  Get-CimInstance Win32_PnPEntity |
    Where-Object { $_.PNPDeviceID -like 'USB*' } |
    Select-Object PNPDeviceID, Name, Service, Status, ConfigManagerErrorCode
) | ConvertTo-Json -Depth 4 -Compress
"""


def cable_hint(name, identity):
    """Return cautious identification with interface-level warnings."""
    match = VID_PID.search(identity or "")
    vid = match.group(1).upper() if match else ""
    candidate = PROBES.get(vid)
    if not candidate:
        return ("No identificado", "No se reconoce un programador FPGA por este ID USB.")
    group, detail = candidate
    interface = INTERFACE_RE.search(identity or "")
    if interface:
        detail += "; interfaz USB MI_" + interface.group(1).upper() + ". No cambies su driver sin confirmar la función."
    if vid == "09FB":
        detail += "; hay cables USB-Blaster originales y copias con los mismos IDs."
    return group, detail + ". Nunca identifica automáticamente el chip FPGA."


def driver_report(identity, runner=subprocess.run):
    """Read driver identity and Windows problem code from static, non-mutating WMI.

    Explicitly match the full PnP interface ID, not merely VID/PID.
    """
    if sys.platform != "win32":
        raise OSError("Diagnóstico de driver disponible en Windows")
    if not isinstance(identity, str) or not identity.startswith("USB") or len(identity) > 280:
        raise ValueError("Selecciona una interfaz USB de la lista")
    normalized = identity.casefold()
    drivers = _ps(SIGNED_DRIVERS_PS, runner)
    devices = _ps(DEVICE_STATUS_PS, runner)
    driver = next((d for d in drivers if isinstance(d, dict) and
                   str(d.get("DeviceID", "")).casefold() == normalized), {})
    status = next((d for d in devices if isinstance(d, dict) and
                   str(d.get("PNPDeviceID", "")).casefold() == normalized), {})
    service = str(status.get("Service") or "").lower()
    issue = status.get("ConfigManagerErrorCode")
    label, warning = cable_hint(str(status.get("Name") or ""), identity)
    try:
        code = int(issue) if issue is not None else -1
    except (TypeError, ValueError):
        code = -1
    alerts = []
    if code not in (-1, 0):
        alerts.append("Windows informa código de problema %d; revisa Administrador de dispositivos." % code)
    if not driver:
        alerts.append("Windows no devolvió un driver firmado para esta interfaz.")
    if service in {"ftdibus", "ftser2k"}:
        alerts.append("Controlador FTDI: cambiarlo por WinUSB puede desconectar funciones serie.")
    elif service in {"winusb", "libusbk", "libusb0"}:
        alerts.append("Driver USB genérico detectado; la compatibilidad depende del programador y de la interfaz.")
    elif not service:
        alerts.append("No se detectó servicio de driver activo.")
    else:
        alerts.append("Servicio Windows '" + service + "': no se verificó compatibilidad con openFPGALoader.")
    return {
        "usb_id": identity, "probe": label, "description": warning,
        "device_name": str(status.get("Name") or driver.get("DeviceName") or ""),
        "service": service or "Desconocido",
        "provider": str(driver.get("DriverProviderName") or "Sin identificar"),
        "version": str(driver.get("DriverVersion") or ""),
        "inf": str(driver.get("InfName") or ""),
        "windows_status": str(status.get("Status") or "Desconocido"),
        "problem_code": code, "alerts": alerts,
        "driver_installation": "No se instalaron ni reemplazaron controladores.",
    }


def find_loader(path=None):
    if path:
        candidate = Path(path).expanduser().resolve()
        if candidate.name.lower() not in {"openfpgaloader.exe", "openfpgaloader"}:
            raise ValueError("Selecciona el ejecutable openFPGALoader oficial")
        if not candidate.is_file():
            raise FileNotFoundError("No se encontró openFPGALoader")
        return str(candidate)
    result = shutil.which("openFPGALoader") or shutil.which("openFPGALoader.exe")
    if not result:
        raise FileNotFoundError("No se encontró openFPGALoader. Selecciónalo desde su instalación oficial.")
    return result


def invoke(args, executable=None, runner=subprocess.run, timeout=30):
    cmd = [find_loader(executable)] + list(args)
    result = runner(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    combined = ((result.stdout or "") + "\n" + (result.stderr or ""))[-30000:]
    if result.returncode:
        raise RuntimeError("openFPGALoader código %d:\n%s" % (result.returncode, combined[-3500:]))
    return combined.strip()


def catalog(executable=None, runner=subprocess.run):
    """Query exact boards/cables/chips from *installed* openFPGALoader version."""
    return {key: invoke([flag], executable, runner=runner, timeout=20)
            for key, flag in (("boards", "--list-boards"),
                              ("cables", "--list-cables"), ("fpga", "--list-fpga"))}


def probe_target(target, via="board", executable=None, runner=subprocess.run):
    """JTAG ID scan: read only, but may briefly occupy the selected JTAG cable."""
    if via not in {"board", "cable"} or not VALID_TARGET.fullmatch(target or ""):
        raise ValueError("Selecciona una placa o cable JTAG de nombre válido")
    return invoke(["--detect", "-b" if via == "board" else "-c", target],
                  executable, runner=runner, timeout=45)


def program_target(target, firmware, via="board", flash=False, executable=None, runner=subprocess.run):
    """Physical write: caller must show an explicit confirmation, including flash risk."""
    if via not in {"board", "cable"} or not VALID_TARGET.fullmatch(target or ""):
        raise ValueError("Placa/programador inválido")
    binary = Path(firmware).expanduser().resolve()
    if not binary.is_file() or binary.suffix.lower() not in VALID_FILENAME:
        raise ValueError("Selecciona un archivo de programación de formato reconocido")
    if not 0 < binary.stat().st_size <= 100 * 1024 * 1024:
        raise ValueError("Archivo de firmware vacío o excesivamente grande")
    args = ["-b" if via == "board" else "-c", target]
    args += ["-f" if flash else "-m", str(binary)]
    return invoke(args, executable, runner=runner, timeout=360)


def examples():
    return FPGA_EXAMPLES
