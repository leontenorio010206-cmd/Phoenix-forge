"""Opt-in real GUI acceptance, also callable inside the frozen executable."""
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path


def run(output, offscreen=False, require_bundled=False):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ['PHOENIXFORGE_DATA'] = str(output / 'user-data')
    if offscreen:
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    from app import __version__
    from app.ui.qt import QtWidgets as W, QtCore as C, QtGui as G, BINDING
    from app.ui.main_window import MainWindow
    from app.core.project import Project
    from app.core.examples import adder_project
    from app.plugins.manager import PluginManager
    from app.devices.catalog import load_profiles
    from app.simulators.icarus import IcarusEngine
    from app.utils.paths import resource_root, assets_dir, data_dir
    app = W.QApplication.instance() or W.QApplication([])
    app.setStyle('Fusion')
    report = dict(version=__version__, platform=platform.platform(), python=platform.python_version(),
                  qt_binding=BINDING, qt_version=C.qVersion(), frozen=bool(getattr(sys,'frozen',False)),
                  qpa=app.platformName(), success=False, checks={}, native_windows=False)
    window = None
    original_question, original_save = W.QMessageBox.question, W.QFileDialog.getSaveFileName
    W.QMessageBox.question = lambda *a, **k: W.QMessageBox.Yes
    project_path = output / 'Acceptance.pforge'
    W.QFileDialog.getSaveFileName = lambda *a, **k: (str(project_path), '')
    timer = C.QTimer(); timer.setInterval(1)
    beats = []
    timer.timeout.connect(lambda: beats.append(1))
    try:
        wine = False
        if sys.platform == 'win32':
            import ctypes
            wine = hasattr(ctypes.WinDLL('ntdll'), 'wine_get_version')
        report['wine'] = wine
        report['native_windows'] = sys.platform == 'win32' and not wine and app.platformName() == 'windows'
        engine = IcarusEngine()
        assert engine.available, 'Icarus unavailable'
        if require_bundled:
            assert getattr(sys,'frozen',False), 'Acceptance requires a frozen executable'
            assert engine.bundle, 'External Icarus cannot satisfy bundled acceptance'
        report['bundled_icarus'] = bool(engine.bundle)
        assert len(load_profiles()) == 10
        assert not G.QIcon(str(assets_dir() / 'phoenix.svg')).isNull()
        assert (resource_root() / 'docs/USER_MANUAL.md').is_file()
        assert (resource_root() / 'examples/semaforo/semaforo.pforge').is_file()
        report['checks']['resources'] = True
        if getattr(sys,'frozen',False):
            assert resource_root() not in data_dir().parents
        window = MainWindow(); window.show(); app.processEvents()
        assert window.isVisible()
        if report['native_windows']:
            import ctypes
            from ctypes import wintypes
            visible = ctypes.windll.user32.IsWindowVisible
            visible.argtypes = [wintypes.HWND]
            visible.restype = wintypes.BOOL
            assert visible(int(window.winId()))
        report['checks']['window_visible'] = True
        window.new_clock()
        editor = window.studio.open_source('traffic_light.v')
        editor.moveCursor(G.QTextCursor.End)
        editor.insertPlainText('\n// acceptance edit\n')
        assert window.dirty and editor.search('acceptance edit')
        editor.undo(); editor.redo()
        assert 'acceptance edit' in window.project.files['traffic_light.v']
        report['checks']['editor'] = True
        window.clock.step(5 * 50000000)
        assert window.clock.model.state == 'VERDE'
        window.clock.reset()
        assert window.clock.model.state == 'ROJO'
        report['checks']['traffic_light'] = True
        timer.start()
        window.studio.run_button.click()
        deadline = time.monotonic() + 60
        while window.worker is not None and time.monotonic() < deadline:
            app.processEvents(); time.sleep(.005)
        timer.stop()
        assert window.worker is None, 'Simulation worker timed out'
        assert window.last_result.success, window.last_result.output
        assert 'PASS: 72' in window.last_result.output
        assert window.studio.wave.canvas.trace.signals
        assert beats, 'GUI heartbeat absent'
        report['heartbeat_events'] = len(beats)
        report['checks']['hdl_and_vcd'] = True
        (output / 'simulation.log').write_text(window.last_result.output, encoding='utf-8')
        assert window.save_project()
        loaded = Project.open(project_path)
        assert loaded.files == window.project.files
        assert any(n.endswith('.vcd') for n in loaded.artifacts)
        report['checks']['project_roundtrip'] = True
        manager = PluginManager()
        infos = manager.discover(resource_root() / 'examples/plugins')
        assert len(infos) == 1 and infos[0].compatible
        manager.load(infos[0], trusted=True)
        assert len(next(iter(manager.registry.values()))(adder_project())) == 2
        manager.unload(infos[0].manifest['id'])
        report['checks']['plugin'] = True
        for index,name in ((0,'welcome'),(1,'studio'),(2,'devices'),(3,'clock'),(4,'plugins')):
            window.navigate(index)
            if index == 1: window.studio.output_tabs.setCurrentWidget(window.studio.wave)
            app.processEvents()
            assert window.grab().save(str(output / (name+'.png')))
        window.dirty=False; window.close(); app.processEvents()
        window = MainWindow()
        window.replace_project(Project.open(project_path),project_path,False)
        window.show(); app.processEvents()
        assert window.isVisible() and window.project.files == loaded.files
        report['checks']['close_and_reopen_window'] = True
        report['success'] = True
    except Exception as error:
        report['error'] = str(error)
        report['traceback'] = traceback.format_exc()
    finally:
        timer.stop()
        if window:
            if window.worker is not None:
                window.cancel_simulation()
                while window.worker is not None:
                    app.processEvents(); time.sleep(.01)
            window.dirty=False; window.close(); app.processEvents()
        W.QMessageBox.question, W.QFileDialog.getSaveFileName = original_question, original_save
        (output / 'acceptance.json').write_text(json.dumps(report,indent=2), encoding='utf-8')
    return 0 if report['success'] else 1
