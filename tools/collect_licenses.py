"""Collect installed distribution notices, without guessing their contents."""
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys


def collect(root):
    destination = Path(root) / 'vendor/licenses'
    destination.mkdir(parents=True, exist_ok=True)
    inventory = {}
    for package in ('PySide6', 'PySide6-Essentials', 'PySide6-Addons', 'shiboken6', 'PyInstaller'):
        dist = importlib.metadata.distribution(package)
        copied = []
        for item in dist.files or []:
            # The wheel owns these paths. Keep upstream directories and notices.
            if not any(word in str(item).lower() for word in ('license', 'copying', 'copyright', 'notice', 'metadata')):
                continue
            source = Path(dist.locate_file(item))
            if not source.is_file() or source.suffix in ('.pyc', '.pyd', '.dll', '.exe'):
                continue
            if '..' in Path(str(item)).parts:
                continue
            target = destination / package / str(item)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(target))
            copied.append(target.relative_to(destination).as_posix())
        if not copied:
            raise RuntimeError('No metadata found in installed distribution: ' + package)
        inventory[package] = {'version': dist.version, 'notices': copied}
    python_license = next((Path(sys.base_prefix) / name for name in ('LICENSE.txt', 'LICENSE')
                           if (Path(sys.base_prefix) / name).is_file()), None)
    if not python_license:
        raise FileNotFoundError('Python license missing from build interpreter')
    shutil.copy2(str(python_license), str(destination / 'Python-LICENSE.txt'))
    (destination / 'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    return inventory
