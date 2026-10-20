"""Collect raster/SVG plugins before dependency scanning pulls in unused modules."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
allowed = {'qwindows.dll', 'qsvgicon.dll', 'qsvg.dll', 'qjpeg.dll', 'qico.dll', 'qgif.dll'}
binaries = [(source, target) for source, target in binaries
            if Path(source).name.lower() in allowed]
