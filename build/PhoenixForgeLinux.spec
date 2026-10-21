# PhœnixForge Linux x86_64 alpha preview. Icarus uses the distro package
# rather than bundling Windows binaries or redistributing a GPL runtime.
from pathlib import Path

root = Path(SPECPATH).resolve().parent
datas = [(str(root / p), p) for p in ('app/assets', 'docs', 'examples')]
datas += [(str(root / 'app/devices/profiles.json'), 'app/devices')]
datas += [(str(root / p), '.') for p in (
    'LICENSE', 'THIRD_PARTY_NOTICES.md', 'LEGAL.md', 'CREDITS.md', 'VERSION'
)]
a = Analysis(
    [str(root / 'tools/launcher.py')],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=['app.acceptance', 'importlib.util'],
    hookspath=[str(root / 'build/hooks')],
    excludes=['PySide2', 'shiboken2', 'PyQt5', 'PyQt6'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='PhoenixForge',
    console=False,
    debug=False,
    strip=False,
    upx=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    name='PhoenixForge-Linux',
    strip=False,
    upx=False,
)
