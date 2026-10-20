# Windows x64, GUI, single file. Run only through tools/build_windows.py.
from pathlib import Path
root = Path(SPECPATH).resolve().parent
if not (root / 'vendor/icarus/manifest.json').is_file():
    raise RuntimeError('A verified Icarus runtime must be staged before packaging')
datas = [(str(root / p), p) for p in ('app/assets', 'docs', 'examples', 'vendor/icarus',
                                     'vendor/licenses', 'vendor/sources')]
datas += [(str(root / 'app/devices/profiles.json'), 'app/devices')]
datas += [(str(root / p), '.') for p in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'VERSION')]
a = Analysis([str(root / 'tools/launcher.py')], pathex=[str(root)], binaries=[],
             datas=datas, hiddenimports=['importlib.util', 'app.acceptance'],
             hookspath=[str(root / 'build/hooks')], runtime_hooks=[],
             excludes=['PySide2', 'shiboken2'], noarchive=False)
# This application uses raster Widgets and SVG, not WebEngine, PDF or OpenGL.
# Limit auto-collected plugins to the corresponding Qt modules whose source ships.
qt_plugins = {'qwindows.dll', 'qsvgicon.dll', 'qsvg.dll', 'qjpeg.dll', 'qico.dll',
              'qgif.dll', 'qmodernwindowsstyle.dll', 'qwindowsvistastyle.dll'}
a.binaries = [x for x in a.binaries if not (
    ('/plugins/' in x[0].replace('\\', '/').lower() and Path(x[0]).name.lower() not in qt_plugins)
    or Path(x[0]).name.lower() in {'opengl32sw.dll', 'd3dcompiler_47.dll'})]
# Only redistribute Qt modules covered by the locked Qt 6.8.3 source
# archives verified by prepare_qt_sources.py. QtNetwork and QtSvgWidgets
# are genuine runtime dependencies that PyInstaller may collect implicitly.
# Unknown modules (notably QtWebEngine/QtQuick) are still rejected.
qtbase_modules = {
    'qt6core.dll', 'qt6gui.dll', 'qt6widgets.dll', 'qt6network.dll',
    'qt6concurrent.dll', 'qt6opengl.dll', 'qt6openglwidgets.dll',
    'qt6printsupport.dll', 'qt6sql.dll', 'qt6xml.dll',
}
qtsvg_modules = {'qt6svg.dll', 'qt6svgwidgets.dll'}
allowed_qt_modules = qtbase_modules | qtsvg_modules
for name, source, kind in a.binaries:
    base = Path(name).name.lower()
    if base.startswith('qt6') and base.endswith('.dll') and base not in allowed_qt_modules:
        raise RuntimeError('Qt module has no reviewed source in this build: ' + base)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
          name='PhoenixForge_v1.7.0_Portable', debug=False, bootloader_ignore_signals=False,
          strip=False, upx=False, console=False, disable_windowed_traceback=False,
          icon=str(root / 'app/assets/PhoenixForge.ico'),
          version=str(root / 'build/windows_version.txt'),
          uac_admin=False, runtime_tmpdir=None)
