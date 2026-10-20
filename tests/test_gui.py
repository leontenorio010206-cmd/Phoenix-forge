import time
from pathlib import Path
import pytest
from app.core.project import Project
from app.simulators.icarus import IcarusEngine


def wait_for_worker(app, window, deadline_seconds=25):
    deadline = time.monotonic() + deadline_seconds
    while window.worker is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)
    assert window.worker is None, 'Simulation thread did not finish'


@pytest.mark.gui
def test_editor_labs_and_project_actions(qt_app, tmp_path, monkeypatch):
    from app.ui.qt import QtWidgets as W, QtGui as G
    from app.ui.main_window import MainWindow
    messages = []
    monkeypatch.setattr(W.QMessageBox, 'warning', lambda *a, **k: messages.append(a[2]))
    window = MainWindow()
    window.show(); qt_app.processEvents()
    window.resize(1000, 680); window.navigate(3); qt_app.processEvents()
    window.new_adder()
    editor = window.studio.open_source('full_adder.v')
    original = editor.toPlainText()
    editor.moveCursor(G.QTextCursor.End)
    editor.insertPlainText('\n// Test edit')
    assert window.dirty and 'Test edit' in window.project.files['full_adder.v']
    assert editor.search('assign')
    editor.undo(); assert editor.toPlainText() == original
    editor.redo(); assert 'Test edit' in editor.toPlainText()
    assert window.navigation.item(3).text() == 'Proyectos de muestra'
    assert window.examples is not None
    path = tmp_path / 'from_gui.pforge'
    monkeypatch.setattr(W.QFileDialog, 'getSaveFileName', lambda *a, **k: (str(path), ''))
    assert window.save_project()
    assert not window.dirty
    assert Project.open(path).files['full_adder.v'] == editor.toPlainText()
    incoming = tmp_path / 'full_adder.v'
    incoming.write_text('module replacement; endmodule', encoding='utf-8')
    before = window.project.files['full_adder.v']
    monkeypatch.setattr(W.QFileDialog, 'getOpenFileNames', lambda *a, **k: ([str(incoming)], ''))
    monkeypatch.setattr(W.QMessageBox, 'question', lambda *a, **k: W.QMessageBox.No)
    window.import_sources()
    assert window.project.files['full_adder.v'] == before
    window.close()
    assert not messages


@pytest.mark.gui
@pytest.mark.hdl
def test_real_end_to_end_gui_flow(qt_app, tmp_path, monkeypatch):
    if not IcarusEngine().available:
        pytest.skip('Icarus unavailable for real GUI integration')
    from app.ui.qt import QtWidgets as W, QtCore as C
    from app.ui.main_window import MainWindow
    warnings = []
    monkeypatch.setattr(W.QMessageBox, 'question', lambda *a, **k: W.QMessageBox.Yes)
    monkeypatch.setattr(W.QMessageBox, 'warning', lambda *a, **k: warnings.append(a[2]))
    window = MainWindow()
    window.show(); qt_app.processEvents()
    window.new_adder()
    assert window.dirty
    heartbeat = []
    timer = C.QTimer(); timer.setInterval(1); timer.timeout.connect(lambda: heartbeat.append(1)); timer.start()
    # Same button the user presses. Dialog responses are automated; engine is real.
    window.studio.run_button.click()
    wait_for_worker(qt_app, window)
    timer.stop()
    assert heartbeat, 'GUI event loop did not remain responsive'
    assert window.last_result.success
    assert 'PASS: 8' in window.studio.console.toPlainText()
    assert window.studio.wave.canvas.trace.signals
    path = tmp_path / 'integral.pforge'
    monkeypatch.setattr(W.QFileDialog, 'getSaveFileName', lambda *a, **k: (str(path), ''))
    assert window.save_project()
    loaded = Project.open(path)
    assert any(n.endswith('.vcd') for n in loaded.artifacts)
    assert not warnings
    window.close()


@pytest.mark.gui
@pytest.mark.hdl
def test_gui_failure_is_not_success(qt_app, tmp_path, monkeypatch):
    if not IcarusEngine().available:
        pytest.skip('Icarus unavailable')
    from app.ui.qt import QtWidgets as W
    from app.ui.main_window import MainWindow
    monkeypatch.setattr(W.QMessageBox, 'question', lambda *a, **k: W.QMessageBox.Yes)
    window = MainWindow()
    window.project.files['full_adder.v'] = 'module full_adder BROKEN; endmodule'
    window.run_simulation()
    wait_for_worker(qt_app, window)
    assert not window.last_result.success
    assert window.studio.errors.rowCount() > 0
    assert 'Compilación fallida' in window.studio.console.toPlainText()
    window.dirty = False
    window.close()

