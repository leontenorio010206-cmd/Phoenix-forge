"""Versioned, checksummed project containers; never extract untrusted ZIP paths."""
import copy
import hashlib
import json
import os
import stat
import tempfile
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app import __version__
from app.utils.paths import safe_relative, confined

SCHEMA_VERSION = 1
MAX_BYTES = 32 * 1024 * 1024
MAX_FILES = 512
MAX_MANIFEST = 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Clave JSON duplicada: " + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)


def migrate_manifest(manifest):
    """v0 developer format -> v1. Never silently load future schemas."""
    manifest = copy.deepcopy(manifest)
    version = manifest.get("schema_version")
    if type(version) is not int or version not in (0, 1):
        raise ValueError("Versión de proyecto no soportada: %r" % version)
    if version == 0:
        manifest["schema_version"] = 1
        manifest.setdefault("export_state", {})
        manifest.setdefault("artifacts", [])
        manifest.setdefault("pins", {})
        manifest.setdefault("metadata", {})["migrated_from"] = 0
    return manifest


@dataclass
class Project:
    name: str = "Nuevo proyecto"
    device: str = "ep2c5t144c8n"
    files: dict = field(default_factory=dict)
    simulation: dict = field(default_factory=lambda: {"top": "", "testbench": "", "timeout": 15})
    pins: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    export_state: dict = field(default_factory=dict)
    artifacts: dict = field(default_factory=dict)
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def validate(self):
        if not isinstance(self.name, str) or not self.name.strip() or len(self.name) > 200:
            raise ValueError("Nombre de proyecto inválido")
        if not isinstance(self.device, str) or not self.device:
            raise ValueError("Perfil de dispositivo inválido")
        uuid.UUID(self.project_id)
        for value in (self.simulation, self.pins, self.metadata, self.export_state):
            if not isinstance(value, dict):
                raise ValueError("El manifiesto contiene un objeto inválido")
        for port, pin in self.pins.items():
            if not isinstance(port, str) or not isinstance(pin, str):
                raise ValueError("Los nombres de puertos y pines deben ser texto")
        if not isinstance(self.files, dict) or not isinstance(self.artifacts, dict):
            raise ValueError("Colección de archivos inválida")
        total = 0
        for group, binary in ((self.files, False), (self.artifacts, True)):
            seen = set()
            for name, data in group.items():
                safe_relative(name)
                if name.casefold() in seen:
                    raise ValueError("Colisión de nombres en Windows")
                seen.add(name.casefold())
                if not isinstance(data, bytes if binary else str):
                    raise ValueError("Tipo de contenido incorrecto")
                total += len(data if binary else data.encode("utf-8"))
            for name in seen:
                parts = name.split("/")
                if any("/".join(parts[:i]) in seen for i in range(1, len(parts))):
                    raise ValueError("Un archivo no puede ser también un directorio")
        if total > MAX_BYTES or len(self.files) + len(self.artifacts) > MAX_FILES:
            raise ValueError("Proyecto demasiado grande (32 MiB / 512 archivos)")
        if len(json.dumps(self.manifest(), ensure_ascii=False).encode("utf-8")) > MAX_MANIFEST:
            raise ValueError("Manifiesto demasiado grande")
        return self

    def manifest(self):
        def entries(group, prefix, binary):
            return [{"path": prefix + name, "sha256": digest(value if binary else value.encode("utf-8"))}
                    for name, value in sorted(group.items())]
        return {"format": "PhoenixForge", "schema_version": SCHEMA_VERSION,
                "app_version": __version__, "project_id": self.project_id, "name": self.name,
                "device": self.device, "simulation": self.simulation, "pins": self.pins,
                "metadata": self.metadata, "export_state": self.export_state,
                "hdl_files": entries(self.files, "src/", False),
                "artifacts": entries(self.artifacts, "results/", True)}

    def save(self, path, overwrite=False):
        self.validate()
        path = Path(path)
        if path.exists() and not overwrite:
            raise FileExistsError("El proyecto ya existe; confirme antes de sobrescribir")
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".pforge-", suffix=".tmp", dir=str(path.parent))
        os.close(fd)
        try:
            with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", json.dumps(self.manifest(), indent=2, ensure_ascii=False))
                for name, data in self.files.items():
                    archive.writestr("src/" + name, data.encode("utf-8"))
                for name, data in self.artifacts.items():
                    archive.writestr("results/" + name, data)
            if overwrite:
                os.replace(temp, str(path))
            else:
                # Exclusive creation even if another process creates the path after our first check.
                # Hard-link publishing is atomic on supported filesystems; fall back to exclusive copy.
                try:
                    os.link(temp, str(path))
                except FileExistsError:
                    raise
                except OSError:
                    import shutil
                    with open(path, "xb") as target, open(temp, "rb") as source:
                        shutil.copyfileobj(source, target)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        return path

    @classmethod
    def open(cls, path):
        try:
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                names = [i.filename for i in infos]
                if len(infos) > MAX_FILES + 1 or len({n.casefold() for n in names}) != len(names):
                    raise ValueError("Archivo duplicado o demasiados archivos")
                if sum(i.file_size for i in infos) > MAX_BYTES + MAX_MANIFEST:
                    raise ValueError("Contenedor demasiado grande")
                for info in infos:
                    safe_relative(info.filename)
                    if stat.S_ISLNK(info.external_attr >> 16) or info.is_dir() or info.flag_bits & 1:
                        raise ValueError("Enlaces, directorios y cifrado no admitidos")
                if archive.getinfo("manifest.json").file_size > MAX_MANIFEST:
                    raise ValueError("Manifiesto demasiado grande")
                m = migrate_manifest(unique_json(archive.read("manifest.json")))
                if m.get("format") != "PhoenixForge":
                    raise ValueError("No es un proyecto PhoenixForge")
                groups, expected = [], {"manifest.json"}
                for field_name, prefix, binary in (("hdl_files", "src/", False), ("artifacts", "results/", True)):
                    group = {}
                    for entry in m[field_name]:
                        name = entry["path"]
                        if not name.startswith(prefix) or name in expected:
                            raise ValueError("Entrada no válida en el manifiesto")
                        rel = name[len(prefix):]
                        safe_relative(rel)
                        expected.add(name)
                        data = archive.read(name)
                        if digest(data) != entry["sha256"]:
                            raise ValueError("Integridad incorrecta: " + name)
                        group[rel] = data if binary else data.decode("utf-8")
                    groups.append(group)
                if set(names) != expected:
                    raise ValueError("Hay archivos no declarados o ausentes")
                return cls(name=m["name"], device=m["device"], files=groups[0], artifacts=groups[1],
                           simulation=m["simulation"], pins=m["pins"], metadata=m["metadata"],
                           export_state=m["export_state"], project_id=m["project_id"]).validate()
        except (zipfile.BadZipFile, KeyError, UnicodeError, TypeError, AttributeError, json.JSONDecodeError) as error:
            raise ValueError("Proyecto inválido: %s" % error) from error

    def import_file(self, path, relative=None, overwrite=False):
        path = Path(path)
        relative = relative or path.name
        safe_relative(relative)
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Archivo demasiado grande")
        if relative.casefold() in {n.casefold() for n in self.files} and not overwrite:
            raise FileExistsError(relative)
        text = path.read_text(encoding="utf-8-sig")
        trial = copy.deepcopy(self)
        trial.files[relative] = text
        trial.validate()
        self.files = trial.files

    def write_sources(self, directory):
        self.validate()
        for name, text in self.files.items():
            target = confined(directory, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

