"""Read-only Windows hardware discovery. Detection is heuristic, never a driver installer."""
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict

VID_PID = re.compile(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", re.I)
SERIAL = re.compile(r"\((COM\d+)\)", re.I)
DEVICES_PS = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$items = @(Get-CimInstance Win32_PnPEntity |
  Where-Object { $_.PNPDeviceID -like 'USB*' -or $_.Name -match '\(COM\d+\)' } |
  Select-Object Name, PNPDeviceID, Status)
$items | ConvertTo-Json -Depth 4 -Compress
"""
VOLUMES_PS = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
@((Get-CimInstance Win32_LogicalDisk -Filter "DriveType=2" |
  Select-Object DeviceID, VolumeName)) | ConvertTo-Json -Depth 4 -Compress
"""


@dataclass(frozen=True)
class HardwareDevice:
    name: str
    kind: str
    identity: str
    port: str = ""
    status: str = ""
    confidence: str = "ambigua"
    note: str = ""

    def to_dict(self):
        return asdict(self)


def classify_usb(name, instance, status=""):
    """A USB-UART bridge alone must never be called a specific Arduino or FPGA."""
    match = VID_PID.search(instance or "")
    vid, pid = (match.group(1).upper(), match.group(2).upper()) if match else ("", "")
    port = SERIAL.search(name or "")
    com = port.group(1).upper() if port else ""
    kind, confidence, note = "USB / serie", "ambigua", "No se puede deducir la placa física solo por su adaptador USB."
    if vid in {"2341", "2A03"}:
        kind, confidence, note = "Arduino", "fabricante USB", "Verifica modelo, puerto y FQBN con Arduino CLI."
    elif vid == "2E8A":
        kind, confidence, note = "Raspberry Pi Pico / RP2040", "fabricante USB", "Confirma la revisión concreta de la placa."
    elif vid == "09FB":
        kind, confidence, note = "Programador FPGA Altera/Intel", "adaptador USB", "El adaptador JTAG no identifica el chip FPGA."
    elif vid in {"0403", "1A86", "10C4"}:
        note = "Adaptador USB-serie: compatible con múltiples Arduino, FPGA y otros dispositivos."
    return HardwareDevice((name or "Dispositivo USB")[:180], kind, (instance or "")[:240],
                          com, status or "", confidence, note)


def _parse_json(stream):
    stream = stream.strip().lstrip("\ufeff")
    if not stream:
        return []
    value = json.loads(stream)
    return value if isinstance(value, list) else [value]


def _ps(command, runner=subprocess.run):
    if sys.platform != "win32":
        return []
    process = runner(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                      "-Command", command],
                     capture_output=True, text=True, timeout=12, check=False)
    if process.returncode:
        raise RuntimeError("Windows no pudo enumerar el hardware: " + process.stderr[:300])
    return _parse_json(process.stdout)


def list_usb_devices(runner=subprocess.run):
    results = []
    for item in _ps(DEVICES_PS, runner):
        if isinstance(item, dict) and item.get("PNPDeviceID"):
            results.append(classify_usb(item.get("Name") or "", item["PNPDeviceID"],
                                        item.get("Status") or ""))
    for item in _ps(VOLUMES_PS, runner):
        if not isinstance(item, dict):
            continue
        volume, mount = str(item.get("VolumeName") or ""), str(item.get("DeviceID") or "")
        if volume.upper() == "RPI-RP2" and re.fullmatch(r"[A-Za-z]:", mount):
            results.append(HardwareDevice("Raspberry Pi Pico (BOOTSEL)", "Pico UF2",
                        "VOLUME:RPI-RP2:" + mount.upper(), mount.upper() + "\\",
                        "OK", "modo de arranque", "Admite copiar un firmware .uf2 con confirmación."))
    # Collapse repeated Windows interfaces with identical IDs only.
    return list({(d.identity, d.port): d for d in results}.values())


def added_devices(previous, current):
    """Pure function; used by the UI to announce connections."""
    old = {(d.identity, d.port) for d in previous}
    return [d for d in current if (d.identity, d.port) not in old]
