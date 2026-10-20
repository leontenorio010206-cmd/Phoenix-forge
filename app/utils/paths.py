"""Conservative portable paths, including Windows filename rules."""
import os
import re
import sys
from pathlib import Path, PurePosixPath

RESERVED = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} | {"LPT%d" % i for i in range(1, 10)}


def safe_relative(name):
    if not isinstance(name, str) or not name or len(name) > 220:
        raise ValueError("Nombre de archivo vacío o demasiado largo")
    if "\\" in name or any(ord(c) < 32 for c in name) or re.search(r'[:*?"<>|]', name):
        raise ValueError("Ruta no portátil: %r" % name)
    path = PurePosixPath(name)
    if path.is_absolute() or str(path) != name or any(p in (".", "..", "") for p in name.split("/")):
        raise ValueError("Ruta insegura: %r" % name)
    for part in path.parts:
        if part.endswith((".", " ")) or part.split(".")[0].upper() in RESERVED:
            raise ValueError("Nombre reservado en Windows: %r" % name)
    return path


def confined(root, name):
    path = Path(root).resolve().joinpath(*safe_relative(name).parts)
    try:
        path.resolve().relative_to(Path(root).resolve())
    except ValueError:
        raise ValueError("La ruta sale del directorio de destino")
    return path


def data_dir():
    override = os.environ.get("PHOENIXFORGE_DATA")
    if override:
        root = Path(override)
    elif sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "PhoenixForge"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "PhoenixForge"
    root.mkdir(parents=True, exist_ok=True)
    return root


def assets_dir():
    return resource_root() / "app" / "assets"


def resource_root():
    """Read-only resources; frozen extraction must not hold persistent data."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


def bundled_icarus():
    root = resource_root() / "vendor" / "icarus"
    return root if sys.platform == "win32" and (root / "bin/iverilog.exe").is_file() else None


def user_projects_dir():
    root = data_dir() / "projects"
    root.mkdir(parents=True, exist_ok=True)
    return root

