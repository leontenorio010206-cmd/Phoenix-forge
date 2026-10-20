"""Opt-in Arduino CLI provisioning and board/library tools.

Pinned official Arduino CLI Windows x64 archive + audited checksum; no
execution of arbitrary USB-suggested drivers or untrusted installers.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from app.utils.paths import data_dir

CLI_VERSION = "1.5.1"
CLI_URL = ("https://github.com/arduino/arduino-cli/releases/download/v1.5.1/"
           "arduino-cli_1.5.1_Windows_64bit.zip")
CLI_SHA256 = "fabe42e0eb04d00e776a66178299ff95a46c623dbc260f997e58fd514853dd40"
FQBN_RE = re.compile(r"^[A-Za-z0-9_]+:[A-Za-z0-9_]+:[A-Za-z0-9_.-]+(?::[A-Za-z0-9_]+=[A-Za-z0-9_.-]+(?:,[A-Za-z0-9_]+=[A-Za-z0-9_.-]+)*)?$")
CORE_RE = re.compile(r"^arduino:[A-Za-z0-9_-]+$")
LIB_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_. \-]{0,99}$")
PORT_RE = re.compile(r"^(COM[1-9][0-9]{0,2}|/dev/tty(?:ACM|USB)[0-9]+)$", re.I)


def local_cli():
    root = data_dir() / "tools" / "arduino-cli" / CLI_VERSION
    executable = root / ("arduino-cli.exe" if sys.platform == "win32" else "arduino-cli")
    return str(executable) if executable.is_file() else (shutil.which("arduino-cli") or "")


def install_cli(download=None, target=None):
    """Download a pinned official ZIP into a private user directory after UI consent."""
    if sys.platform != "win32":
        raise OSError("Instalación automática Arduino CLI 1.5.1: Windows 64 bits")
    root = Path(target) if target else data_dir() / "tools" / "arduino-cli" / CLI_VERSION
    exe = root / "arduino-cli.exe"
    if exe.is_file():
        return exe
    root.parent.mkdir(parents=True, exist_ok=True)
    get = download or urllib.request.urlopen
    payload = get(CLI_URL, timeout=40)
    with payload:
        content = payload.read(32 * 1024 * 1024 + 1)
    if len(content) > 32 * 1024 * 1024 or hashlib.sha256(content).hexdigest() != CLI_SHA256:
        raise ValueError("No coincide la firma SHA256 publicada por Arduino: descarga rechazada")
    import io
    with zipfile.ZipFile(io.BytesIO(content)) as bundle:
        members = [i for i in bundle.infolist() if not i.is_dir()]
        candidates = [i for i in members if i.filename == "arduino-cli.exe"]
        if len(candidates) != 1 or candidates[0].file_size > 50 * 1024 * 1024:
            raise ValueError("No se encontró arduino-cli.exe válido en el ZIP")
        binary = bundle.read(candidates[0])
    stage = Path(tempfile.mkdtemp(prefix=".arduino-cli-", dir=str(root.parent)))
    try:
        (stage / "arduino-cli.exe").write_bytes(binary)
        (stage / "SOURCE.txt").write_text("Arduino CLI " + CLI_VERSION + "\n" + CLI_URL +
             "\nSHA256: " + CLI_SHA256 + "\n", encoding="utf-8")
        stage.rename(root)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return exe


def call_cli(args, cli=None, timeout=90, runner=subprocess.run):
    path = cli or local_cli()
    if not path:
        raise FileNotFoundError("Arduino CLI no está instalado. Pulsa Preparar Arduino CLI.")
    if any(not isinstance(s, str) or not s or s.startswith("--config-file=") for s in args):
        raise ValueError("Argumentos Arduino CLI inválidos")
    result = runner([path] + list(args), capture_output=True, text=True,
                    timeout=timeout, check=False)
    log = (result.stdout or "") + "\n" + (result.stderr or "")
    if len(log) > 200000:
        log = log[:200000] + "\n[registro truncado]"
    if result.returncode:
        raise RuntimeError("Arduino CLI (" + str(result.returncode) + "):\n" + log[-1800:])
    return log.strip()


def board_list(cli=None, runner=subprocess.run):
    text = call_cli(["board", "list", "--format", "json"], cli=cli, runner=runner)
    data = json.loads(text)
    return data.get("detected_ports", []) if isinstance(data, dict) else []


def core_install(core, cli=None, runner=subprocess.run):
    if not CORE_RE.fullmatch(core):
        raise ValueError("Solo se instalan plataformas oficiales arduino:* en v1.6")
    call_cli(["core", "update-index"], cli=cli, timeout=300, runner=runner)
    return call_cli(["core", "install", core], cli=cli, timeout=900, runner=runner)


def library_install(name, cli=None, runner=subprocess.run):
    if not LIB_RE.fullmatch(name):
        raise ValueError("Nombre de biblioteca Arduino inválido")
    call_cli(["lib", "update-index"], cli=cli, timeout=300, runner=runner)
    return call_cli(["lib", "install", name], cli=cli, timeout=900, runner=runner)


def prepare_sketch(text, basename="PhoenixBlink", root=None):
    """Write a user-authored sketch into a controlled unique directory."""
    if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 1024 * 1024:
        raise ValueError("Sketch vacío o demasiado grande")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,60}", basename):
        raise ValueError("Nombre de sketch inválido")
    root = Path(root) if root else data_dir() / "sketches"
    root.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=basename + "_", dir=str(root)))
    # Arduino requires sketch file to have the same name as the directory.
    (folder / (folder.name + ".ino")).write_text(text, encoding="utf-8")
    return folder


def compile_sketch(folder, fqbn, cli=None, runner=subprocess.run):
    if not FQBN_RE.fullmatch(fqbn):
        raise ValueError("FQBN de placa Arduino inválido")
    build = Path(folder).resolve().parent / (Path(folder).name + "-build")
    return call_cli(["compile", "--fqbn", fqbn, "--output-dir", str(build),
                     str(Path(folder).resolve())],
                    cli=cli, timeout=600, runner=runner)


def upload_sketch(folder, fqbn, port, cli=None, runner=subprocess.run):
    if not FQBN_RE.fullmatch(fqbn) or not PORT_RE.fullmatch(port):
        raise ValueError("Selecciona un puerto y un FQBN Arduino válidos")
    build = Path(folder).resolve().parent / (Path(folder).name + "-build")
    if not build.is_dir():
        raise FileNotFoundError("Primero compila el sketch y conserva su carpeta de salida")
    return call_cli(["upload", "-p", port, "--fqbn", fqbn, "--input-dir", str(build),
                     str(Path(folder).resolve())],
                    cli=cli, timeout=600, runner=runner)


def copy_uf2(firmware, mount):
    """User-confirmed Raspberry Pi Pico BOOTSEL transfer, no drive formatting."""
    image = Path(firmware)
    destination = Path(mount)
    if image.suffix.lower() != ".uf2" or not image.is_file() or image.stat().st_size > 32*1024*1024:
        raise ValueError("Seleccione un firmware .uf2 válido de máximo 32 MiB")
    # UF2 blocks must have the standard magic values at header and footer.
    if image.stat().st_size < 512 or image.stat().st_size % 512:
        raise ValueError("El UF2 debe contener bloques completos de 512 bytes")
    import struct
    with image.open("rb") as stream:
        block = stream.read(512)
    if (struct.unpack_from("<II", block) != (0x0A324655, 0x9E5D5157)
            or struct.unpack_from("<I", block, 508)[0] != 0x0AB16F30):
        raise ValueError("El archivo no tiene la cabecera UF2 válida")
    if not destination.is_dir() or not (destination / "INFO_UF2.TXT").is_file():
        raise ValueError("No se detectó un volumen BOOTSEL compatible con Pico")
    target = destination / image.name
    if target.exists():
        raise FileExistsError("Ya existe ese firmware en el destino")
    with image.open("rb") as src, target.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    return str(target)


# Arduino CLI is the authoritative source for available board FQBNs and library
# versions. The short offline list is just for convenient first use.
def board_listall(cli=None, runner=subprocess.run):
    """All boards from INSTALLED platforms (not every board ever manufactured)."""
    from app.hardware.arduino_catalog import merge_catalog, model_shortcuts
    raw = call_cli(["board", "listall", "--json"], cli=cli, runner=runner)
    data = json.loads(raw)
    items = data.get("boards", []) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("Inventario de placas de Arduino CLI no reconocido")
    return merge_catalog(model_shortcuts(), items)


def library_list(cli=None, runner=subprocess.run):
    """Inventory installed libraries, including those shipped by the board core."""
    raw = call_cli(["lib", "list", "--all", "--json"], cli=cli, runner=runner)
    data = json.loads(raw)
    if isinstance(data, dict):
        items = data.get("installed_libraries", data.get("libraries", []))
    else:
        items = data
    if not isinstance(items, list):
        raise ValueError("Inventario de bibliotecas no reconocido")
    return items


def library_search(query, cli=None, runner=subprocess.run):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 80:
        raise ValueError("Escribe una búsqueda de biblioteca (1–80 caracteres)")
    if any(ord(c) < 32 for c in query):
        raise ValueError("Consulta inválida")
    return call_cli(["lib", "search", "--names", query.strip()],
                    cli=cli, timeout=90, runner=runner)


def install_starter_pack(cli=None, runner=subprocess.run):
    """One-click transaction requested by the user. No hidden background installs.

    Arduino platform includes Wire/SPI/etc. Download optional library manager
    dependencies only; report all partial failures instead of hiding them.
    """
    from app.hardware.arduino_catalog import BASIC_PACK
    call_cli(["lib", "update-index"], cli=cli, timeout=300, runner=runner)
    successes, failures = [], []
    for name in BASIC_PACK:
        try:
            call_cli(["lib", "install", name], cli=cli, timeout=900, runner=runner)
            successes.append(name)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            failures.append((name, str(error)[:240]))
    return {"installed_or_present": successes, "failed": failures}


def upgrade_libraries(cli=None, runner=subprocess.run):
    """Update installed libraries after confirmation, not on USB attachment."""
    call_cli(["lib", "update-index"], cli=cli, timeout=300, runner=runner)
    return call_cli(["lib", "upgrade"], cli=cli, timeout=900, runner=runner)
