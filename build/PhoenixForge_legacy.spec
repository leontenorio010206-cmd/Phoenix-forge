# Experimental onedir candidate for PyInstaller 4.10 and PySide2.
import os
from pathlib import Path
root = Path(SPECPATH).resolve().parent
binding = os.environ.get('PHOENIXFORGE_QT', 'pyside2')
excluded = ['PySide6', 'shiboken6'] if binding == 'pyside2' else ['PySide2', 'shiboken2']
a = Analysis([str(root / 'tools' / 'launcher.py')], pathex=[str(root)],
    binaries=[], datas=[(str(root / 'app' / 'assets'), 'app/assets'),
    (str(root / 'app' / 'devices' / 'profiles.json'), 'app/devices'),
    (str(root / 'docs'), 'docs'), (str(root / 'examples'), 'examples'),
    (str(root / 'LICENSE'), '.'), (str(root / 'THIRD_PARTY_NOTICES.md'), '.')],
    hiddenimports=['importlib.util'], hookspath=[], runtime_hooks=[], excludes=excluded, noarchive=False)
pyz = PYZ(a.pure, getattr(a, 'zipped_data', []))
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PhoenixForge',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'app' / 'assets' / 'PhoenixForge.ico'))
coll = COLLECT(exe, a.binaries, getattr(a, 'zipfiles', []), a.datas, strip=False, upx=False, name='PhoenixForge')
