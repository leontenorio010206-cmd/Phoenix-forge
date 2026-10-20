import hashlib
import importlib.util
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from app.plugins.sdk import API_VERSION, Plugin, PluginContext
from app.utils.paths import confined, safe_relative


def fingerprint(directory):
    h = hashlib.sha256()
    for path in sorted(Path(directory).rglob("*")):
        if path.is_symlink():
            raise ValueError("No se permiten enlaces en plugins")
        if path.is_file() and path.suffix in (".py", ".json"):
            if path.stat().st_size > 1024 * 1024:
                raise ValueError("Archivo de plugin demasiado grande")
            h.update(str(path.relative_to(directory)).encode("utf-8"))
            h.update(path.read_bytes())
    return h.hexdigest()


@dataclass
class PluginInfo:
    directory: Path
    manifest: dict
    compatible: bool
    error: str = ""
    digest: str = ""


class PluginManager:
    def __init__(self):
        self.registry, self.loaded, self.errors = {}, {}, []

    def discover(self, directory):
        results, seen = [], set()
        root = Path(directory)
        if not root.exists():
            return results
        for path in sorted(root.glob("*/plugin.json")):
            manifest = {"id": path.parent.name, "name": path.parent.name}
            try:
                if path.is_symlink() or path.parent.is_symlink() or path.stat().st_size > 65536:
                    raise ValueError("Manifiesto inseguro")
                candidate = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(candidate, dict):
                    raise ValueError("El manifiesto debe ser un objeto JSON")
                manifest = candidate
                pid = manifest["id"]
                if not isinstance(pid, str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+", pid):
                    raise ValueError("ID debe ser único y contener un espacio de nombres")
                if pid in seen:
                    raise ValueError("ID de plugin duplicado")
                seen.add(pid)
                if type(manifest.get("api_version")) is not int or manifest.get("api_version") != API_VERSION:
                    raise ValueError("API incompatible; se requiere API 1")
                if not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
                    raise ValueError("Versión semántica inválida")
                entry = manifest["entry_point"]
                safe_relative(entry)
                if not entry.endswith(".py") or not confined(path.parent, entry).is_file():
                    raise ValueError("Punto de entrada inválido")
                results.append(PluginInfo(path.parent, manifest, True, digest=fingerprint(path.parent)))
            except Exception as error:
                if not isinstance(manifest.get("id"), str):
                    manifest = dict(manifest, id=path.parent.name)
                results.append(PluginInfo(path.parent, manifest, False, str(error)))
        # Both colliding IDs must be disabled, including the first one.
        counts = {}
        for info in results:
            pid = info.manifest.get("id")
            counts[pid] = counts.get(pid, 0) + 1
        for info in results:
            if counts[info.manifest.get("id")] > 1:
                info.compatible, info.error = False, "ID de plugin duplicado"
        return results

    def load(self, info, trusted=False):
        if not trusted:
            raise PermissionError("Un plugin es código de terceros con los permisos de la aplicación")
        if not info.compatible or fingerprint(info.directory) != info.digest:
            raise ValueError("Plugin incompatible o modificado; vuelva a descubrirlo")
        pid = info.manifest["id"]
        if pid in self.loaded:
            raise ValueError("Plugin ya cargado")
        module_name = "phoenixforge_plugin_" + hashlib.sha256(pid.encode()).hexdigest()[:16]
        instance = None
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(confined(info.directory, info.manifest["entry_point"])))
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            instance = module.create_plugin()
            if not isinstance(instance, Plugin):
                raise TypeError("create_plugin debe devolver Plugin")
            instance.activate(PluginContext(pid, self.registry))
            self.loaded[pid] = (instance, module_name)
        except Exception as error:
            self._remove_contributions(pid)
            sys.modules.pop(module_name, None)
            if instance is not None:
                try:
                    instance.deactivate()
                except Exception:
                    logging.exception("Rollback de plugin")
            self.errors.append(str(error))
            logging.exception("Error cargando plugin %s", pid)
            raise

    def _remove_contributions(self, pid):
        for key in list(self.registry):
            if key[1].startswith(pid + ":"):
                del self.registry[key]

    def unload(self, pid):
        instance, name = self.loaded.pop(pid)
        try:
            instance.deactivate()
        except Exception as error:
            self.errors.append(str(error))
            logging.exception("Error descargando plugin")
            raise
        finally:
            self._remove_contributions(pid)
            sys.modules.pop(name, None)

