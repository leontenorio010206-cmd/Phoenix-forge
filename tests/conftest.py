import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def qt_app(tmp_path, monkeypatch):
    monkeypatch.setenv("PHOENIXFORGE_DATA", str(tmp_path / "data"))
    qt = pytest.importorskip("app.ui.qt")
    app = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    app.setStyle("Fusion")
    yield app
    app.processEvents()

