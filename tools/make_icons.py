"""Regenerate PNG/ICO from the original vector using QtSvg and Pillow."""
import os
import sys
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ui.qt import QtWidgets as W, QtCore as C, QtGui as G, QtSvg
from app.utils.paths import assets_dir


def main():
    from PIL import Image
    app = W.QApplication.instance() or W.QApplication([])
    path = assets_dir()
    renderer = QtSvg.QSvgRenderer(str(path / "phoenix.svg"))
    image = G.QImage(512, 512, G.QImage.Format_ARGB32)
    image.fill(0)
    painter = G.QPainter(image)
    renderer.render(painter)
    painter.end()
    image.save(str(path / "phoenix.png"))
    with Image.open(path / "phoenix.png") as bitmap:
        bitmap.save(path / "PhoenixForge.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])


if __name__ == "__main__":
    main()
