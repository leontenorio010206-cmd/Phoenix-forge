"""Opt-in Digital integration: persistent Icarus, unpacked HDL and launcher.

No downloads, Digital configuration edits, administrator rights or PATH
changes are performed. A Digital External File must still be placed in Digital.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.core.hdl import identifier
from app.exporters.digital_hdl import digital_component_files
from app.utils.paths import bundled_icarus, data_dir

MAX_BUNDLED_FILES = 400
MAX_BUNDLED_BYTES = 180 * 1024 * 1024
ALLOWED_FILENAMES = {
    "component.v", "ports.json", "LEEME_DIGITAL.txt", "symbol.svg", "connections.svg"
}


def digital_root():
    return data_dir() / "digital"


def _safe_inventory_path(base, rel):
    """Manifest paths can only refer to regular files inside their root."""
    if not isinstance(rel, str) or not rel or len(rel) > 240:
        raise ValueError("Archivo incorrecto en manifiesto Icarus")
    if "\\" in rel or rel.startswith("/") or ":" in rel or any(p in ("", ".", "..") for p in rel.split("/")):
        raise ValueError("Ruta Icarus no portátil: " + repr(rel))
    full = base.joinpath(*rel.split("/"))
    if full.is_symlink() or not full.is_file():
        raise ValueError("Archivo Icarus faltante o enlace no admitido: " + rel)
    if not full.resolve().is_relative_to(base.resolve()):
        raise ValueError("Ruta Icarus fuera de su directorio")
    return full


def verify_icarus_bundle(bundle):
    """Read and verify the exact source manifest created by our build pipeline."""
    bundle = Path(bundle)
    manifest = bundle / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise FileNotFoundError("No se encontró el inventario firmado por la compilación de Icarus")
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    files = doc.get("files")
    if doc.get("architecture") != "AMD64" or not isinstance(files, dict):
        raise ValueError("Inventario Icarus no reconocido (requiere AMD64)")
    if not 4 <= len(files) <= MAX_BUNDLED_FILES:
        raise ValueError("Número de archivos Icarus fuera de límite")
    total = 0
    for rel, digest in files.items():
        file = _safe_inventory_path(bundle, rel)
        total += file.stat().st_size
        if total > MAX_BUNDLED_BYTES:
            raise ValueError("Icarus excede el tamaño esperado")
        if not isinstance(digest, str) or len(digest) != 64 or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise ValueError("Icarus dañado o modificado: " + rel)
    if not {"bin/iverilog.exe", "bin/vvp.exe", "lib/ivl/ivl.exe", "lib/ivl/ivlpp.exe"}.issubset(files):
        raise ValueError("La distribución Icarus está incompleta")
    return doc


def prepare_icarus_for_digital(bundle=None, destination=None):
    """Copy the bundled, integrity-checked runtime to a stable user-writable path.

    Does not touch Digital configuration or the user's global PATH.
    """
    if sys.platform != "win32":
        raise OSError("La preparación de Icarus para Digital requiere Windows")
    bundle = Path(bundle) if bundle is not None else bundled_icarus()
    if not bundle:
        raise FileNotFoundError("Esta versión no incluye Icarus. Use el EXE de Windows completo.")
    doc = verify_icarus_bundle(bundle)
    destination = Path(destination) if destination is not None else digital_root() / "icarus"
    if destination.exists():
        verify_icarus_bundle(destination)
        if (destination / "manifest.json").read_bytes() == (bundle / "manifest.json").read_bytes():
            return destination
        raise FileExistsError("Hay otra versión de Icarus en la carpeta de destino; no se sobrescribirá.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".pf-icarus-", dir=str(destination.parent)))
    try:
        for rel in doc["files"]:
            origin = _safe_inventory_path(bundle, rel)
            target = temp.joinpath(*rel.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, target)
        shutil.copy2(bundle / "manifest.json", temp / "manifest.json")
        verify_icarus_bundle(temp)
        temp.rename(destination)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return destination


def export_unpacked_component(project, top=None, root=None):
    """Create a stable Digital External File directory, not a ZIP to accidentally select.

    Replace only folders previously created by us; preserve unknown files.
    """
    top = identifier(top or project.simulation.get("top", ""))
    name = "PF_" + top
    files = digital_component_files(project, top=top)
    if set(files) != ALLOWED_FILENAMES:
        raise ValueError("Archivos Digital inesperados")
    base = Path(root) if root is not None else digital_root() / "components"
    base.mkdir(parents=True, exist_ok=True)
    destination = base / name
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            raise ValueError("El destino existe, pero no es una carpeta segura")
        if not (destination / ".phoenixforge-export.json").is_file():
            raise FileExistsError("La carpeta existente no pertenece a PhœnixForge")
        other = set(p.name for p in destination.iterdir())
        if other != ALLOWED_FILENAMES | {".phoenixforge-export.json"}:
            raise FileExistsError("Hay archivos adicionales en la carpeta: no se sobrescribirá")
    temp = Path(tempfile.mkdtemp(prefix=".pf-component-", dir=str(base)))
    try:
        for filename, data in files.items():
            (temp / filename).write_bytes(data)
        marker = {
            "format": "PhoenixForge-Digital-Prepared", "top": top,
            "hashes": {n: hashlib.sha256(v).hexdigest() for n, v in files.items()}
        }
        (temp / ".phoenixforge-export.json").write_text(
            json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")
        if destination.exists():
            # Files are replaced individually; keep the marker for power loss recovery.
            for filename, data in files.items():
                os.replace(str(temp / filename), str(destination / filename))
            os.replace(str(temp / ".phoenixforge-export.json"),
                       str(destination / ".phoenixforge-export.json"))
        else:
            temp.rename(destination)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return destination / "component.v"


def port_config(project, top=None):
    """Return the exact Digital fields read from HDL port declarations."""
    import json
    package = digital_component_files(project, top)
    doc = json.loads(package["ports.json"].decode("utf-8"))
    fields = {}
    for direction, key in (("input", "entradas"), ("output", "salidas")):
        fields[key] = ",".join(p["name"] + (":" + str(p["width"]) if p["width"] != 1 else "")
                              for p in doc["ports"] if p["direction"] == direction)
    return {"etiqueta": doc["top"], **fields, "aplicacion": "IVerilog"}


def locate_java():
    return shutil.which("javaw") or shutil.which("java")


def launch_digital(digital_jar, icarus_dir, java=None, popen=subprocess.Popen):
    """Start a user-selected Digital.jar, with Icarus visible to that child only."""
    jar = Path(digital_jar).expanduser().resolve()
    if jar.name.lower() != "digital.jar" or not jar.is_file():
        raise FileNotFoundError("Seleccione el archivo Digital.jar oficial ya descomprimido")
    icarus_dir = Path(icarus_dir).resolve()
    if not (icarus_dir / "bin/iverilog.exe").is_file():
        raise FileNotFoundError("Primero prepare Icarus para Digital")
    java = java or locate_java()
    if not java:
        raise FileNotFoundError("Java no está instalado; Digital necesita Java para abrirse")
    env = os.environ.copy()
    env["PATH"] = str(icarus_dir / "bin") + os.pathsep + env.get("PATH", "")
    return popen([java, "-jar", str(jar)], cwd=str(jar.parent), env=env,
                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL)
