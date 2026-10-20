"""Make packaged third-party notices and corresponding source accessible."""
import os
from pathlib import Path
import shutil
import tempfile

from app.utils.paths import resource_root


def export_components(destination):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Seleccione una carpeta nueva para los componentes')
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.pforge-components-', dir=str(destination.parent)))
    try:
        root = resource_root()
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
            shutil.copy2(str(root / name), str(stage / name))
        for source, target in (('vendor/sources','sources'), ('vendor/licenses','licenses'),
                               ('vendor/icarus/licenses','licenses/Icarus-runtime')):
            if (root / source).is_dir():
                shutil.copytree(str(root / source), str(stage / target))
        if destination.exists():
            raise FileExistsError(destination)
        os.rename(str(stage), str(destination))
    finally:
        if stage.exists():
            shutil.rmtree(str(stage))
    return destination
