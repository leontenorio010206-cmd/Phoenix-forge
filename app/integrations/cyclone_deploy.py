"""Fail-closed Cyclone IV SRAM deployment of an EXTERNAL, user-verified RBF.

This does not synthesize or generate Cyclone IV bitstreams. An RBF is opaque:
no tool can infer its original pinout or part marking from its filename.
Never programs Flash; never writes on USB attach or JTAG scan.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

from app.hardware import fpga
from app.integrations.quartus_bridge import validate_part

SCHEMA = "phoenixforge-cyclone-iv-sram-v1"
MAX_RBF_BYTES = 32 * 1024 * 1024
MIN_RBF_BYTES = 64 * 1024
JTAG_CODE = re.compile(r"\b(?:idcode|id[\s_-]?code)\s*(?:is\s*)?[:=]?\s*(?:0x)?([0-9a-f]{7,8})\b", re.I)
JTAG_UNKNOWN = re.compile(r"\b(?:unknown|unrecognized)\s+(?:jtag\s+)?device\b", re.I)
PART_CANDIDATE = re.compile(r"\bEP4C(?:E|GX)\d+[A-Z0-9]*\b", re.I)
SAFE_BOARD = re.compile(r"^[\w .()-]{3,100}$", re.UNICODE)


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def check_physical_profile(project, chip, board, pins_confirmed, voltage_confirmed):
    project.validate()
    part = validate_part(chip)
    if not SAFE_BOARD.fullmatch(str(board or "").strip()):
        raise ValueError("Escribe nombre y revisión de la placa física, no solo 'Cyclone IV'.")
    if not project.pins or not isinstance(project.pins, dict):
        raise ValueError("Faltan pines físicos; consulta el esquema exacto de la placa.")
    if not pins_confirmed or not voltage_confirmed:
        raise ValueError("Confirma pines, voltajes y encapsulado contra el esquema real.")
    pins = {}
    used = set()
    for port, location in project.pins.items():
        if not isinstance(port, str) or not re.fullmatch(r"[A-Za-z_]\w*(?:\[\d+\])?", port):
            raise ValueError("Puerto HDL inválido: " + str(port))
        if not isinstance(location, str) or not re.fullmatch(r"PIN_[A-Z0-9]{1,8}", location.upper()):
            raise ValueError("Ubicación física inválida: " + str(location))
        if location.upper() in used:
            raise ValueError("Pin físico duplicado: " + location)
        used.add(location.upper())
        pins[port] = location.upper()
    return part, dict(sorted(pins.items()))


def stage_external_rbf(project, firmware, destination, chip, board,
                       pins_confirmed=False, voltage_confirmed=False):
    """Copy external .rbf with a transparent unverified-origin provenance.

    This is an import, NOT a declaration of correct silicon configuration.
    Only the user can inspect external compilation logs and board schematic.
    """
    part, pins = check_physical_profile(
        project, chip, board, pins_confirmed, voltage_confirmed)
    unchecked_source = Path(firmware).expanduser()
    if unchecked_source.is_symlink():
        raise ValueError("No se admiten enlaces simbólicos como bitstreams.")
    source = unchecked_source.resolve()
    if source.suffix.lower() != ".rbf" or not source.is_file():
        raise ValueError("Para el flujo libre Cyclone IV importa un .rbf existente.")
    if not MIN_RBF_BYTES <= source.stat().st_size <= MAX_RBF_BYTES:
        raise ValueError("Tamaño RBF fuera de límites; verifica procedencia y modelo.")
    output = Path(destination).expanduser().resolve()
    if output.exists():
        raise FileExistsError("No se sobrescribe una carpeta de firmware existente.")
    if not output.parent.is_dir():
        raise FileNotFoundError("La carpeta de destino no existe.")
    temp = Path(tempfile.mkdtemp(prefix=".pf-rbf-", dir=str(output.parent)))
    try:
        image = temp / "firmware.rbf"
        shutil.copy2(source, image)
        original = digest(source)
        if digest(image) != original:
            raise RuntimeError("La copia del bitstream no coincide con el original.")
        record = {
            "schema": SCHEMA,
            "source": "EXTERNAL_RBF_UNVERIFIED",
            "warning": ("Este RBF no fue compilado ni validado contra el chip "
                        "por PhoenixForge. No se certifica su pinout ni origen."),
            "part": part, "board": str(board).strip(),
            "project_id": project.project_id,
            "pins": pins,
            "rbf": "firmware.rbf",
            "rbf_bytes": image.stat().st_size,
            "rbf_sha256": original,
            "pins_reviewed_by_user": True,
            "voltages_reviewed_by_user": True,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "programming_automatic": False,
        }
        (temp / "manifest.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.rename(output)
        return {**record, "folder": str(output)}
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def inspect_staged(folder):
    root = Path(folder).expanduser().resolve()
    manifest = root / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise FileNotFoundError("No existe el manifiesto de firmware preparado.")
    if manifest.stat().st_size > 128 * 1024:
        raise ValueError("Manifiesto excesivamente grande.")
    record = json.loads(manifest.read_text(encoding="utf-8"))
    if (record.get("schema") != SCHEMA or
        record.get("source") != "EXTERNAL_RBF_UNVERIFIED" or
        record.get("rbf") != "firmware.rbf" or
        not record.get("pins_reviewed_by_user") or
        not record.get("voltages_reviewed_by_user")):
        raise ValueError("Manifiesto incompleto o de origen no admitido.")
    validate_part(record.get("part"))
    if not isinstance(record.get("pins"), dict) or not record["pins"] or not SAFE_BOARD.fullmatch(str(record.get("board", ""))):
        raise ValueError("Falta confirmación de placa y pines.")
    seen_pins = set()
    for port, location in record["pins"].items():
        if (not isinstance(port, str) or not re.fullmatch(r"[A-Za-z_]\w*(?:\[\d+\])?", port) or
            not isinstance(location, str) or not re.fullmatch(r"PIN_[A-Z0-9]{1,8}", location)):
            raise ValueError("Asignación física del paquete inválida.")
        if location in seen_pins:
            raise ValueError("Hay pines físicos duplicados en el paquete.")
        seen_pins.add(location)
    binary = root / "firmware.rbf"
    if binary.is_symlink() or not binary.is_file() or binary.resolve().parent != root:
        raise ValueError("Firmware ausente o fuera de carpeta.")
    size = binary.stat().st_size
    if size != record.get("rbf_bytes") or not MIN_RBF_BYTES <= size <= MAX_RBF_BYTES:
        raise ValueError("Tamaño del firmware modificado.")
    if digest(binary) != record.get("rbf_sha256"):
        raise ValueError("SHA256 del firmware no coincide; programación bloqueada.")
    return record, binary


def jtag_preflight(output, part):
    """Require one recognized JTAG ID, never infer package or pinout from it."""
    text = str(output or "")
    if JTAG_UNKNOWN.search(text) or "programación bloqueada" in text.lower():
        raise RuntimeError("La lectura JTAG muestra un dispositivo desconocido.")
    if re.search(r"\b(?:no\s+(?:device|cable|fpga)|multiple\s+(?:jtag\s+)?devices|chain\s+length\s*[:=]\s*[2-9])\b", text, re.I):
        raise RuntimeError("No hay una única FPGA/cadena JTAG confirmada.")
    codes = JTAG_CODE.findall(text)
    # Do not deduplicate repeated IDCODEs: two identical chips remain two devices.
    if len(codes) != 1:
        raise RuntimeError("Se requiere exactamente un dispositivo JTAG.")
    candidates = {name.upper() for name in PART_CANDIDATE.findall(text)}
    if len(candidates) > 1:
        raise RuntimeError("El JTAG muestra varios modelos posibles; selección ambigua.")
    if candidates and part not in candidates:
        raise RuntimeError("El chip mostrado por JTAG no coincide con el chip confirmado.")
    # One IDCODE may still correspond to several parts or packages.
    return {"jtag_idcode": codes[0].upper().zfill(8), "part_from_physical_marking": part,
            "jtag_exact_part_verified": False}


def deploy_sram(folder, cable, physical_part, confirmed_board=False,
                confirmed_external_bitstream=False, confirmed_sram_only=False,
                loader=None, runner=subprocess.run):
    """Read JTAG again, then execute -m (volatile SRAM), never -f (Flash).

    The three booleans are set only by an explicit confirmation in the UI.
    """
    record, bitstream = inspect_staged(folder)
    if not (confirmed_board and confirmed_external_bitstream and confirmed_sram_only):
        raise PermissionError("La carga requiere confirmar placa, archivo externo y SRAM.")
    if validate_part(physical_part) != record["part"]:
        raise ValueError("El marcado físico no coincide con el manifiesto.")
    if not fpga.VALID_TARGET.fullmatch(str(cable or "")):
        raise ValueError("Selecciona un cable JTAG concreto.")
    detected = fpga.probe_target(cable, via="cable", executable=loader, runner=runner)
    evidence = jtag_preflight(detected, record["part"])
    # Re-verify after the JTAG scan, then program a private throwaway copy,
    # not the potentially editable source file in the project directory.
    record_again, bitstream = inspect_staged(folder)
    if record_again["rbf_sha256"] != record["rbf_sha256"]:
        raise RuntimeError("El firmware cambió durante la lectura JTAG.")
    with tempfile.TemporaryDirectory(prefix="pf-sram-") as temporary:
        clean_copy = Path(temporary) / "firmware.rbf"
        shutil.copyfile(bitstream, clean_copy)
        if (clean_copy.stat().st_size != record["rbf_bytes"] or
                digest(clean_copy) != record["rbf_sha256"]):
            raise RuntimeError("El firmware cambió antes de programar; operación cancelada.")
        # Never use FLASH (-f) or change global drivers.
        report = fpga.program_target(
            cable, clean_copy, via="cable", flash=False,
            executable=loader, runner=runner)
    return {"status": "sram_configuration_sent",
            "board": record["board"], "part": record["part"],
            "jtag_idcode": evidence["jtag_idcode"],
            "rbf_sha256": record["rbf_sha256"],
            "flash_written": False, "verification_on_silicon": False,
            "programmer_output": report[-5000:]}
