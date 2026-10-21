"""Opt-in real GUI acceptance, also callable inside the frozen executable."""
import json
import os
import platform
import sys
import time
import traceback
import faulthandler
from pathlib import Path


def run(output, offscreen=False, require_bundled=False):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Persist progress before risky Qt work so a timed-out frozen build has a
    # precise last stage even when a modal dialog or native thread blocks.
    trace_path = output / "stage-events.log"
    def trace(stage):
        with trace_path.open("a", encoding="utf-8") as stream:
            stream.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), stage))
            stream.flush()
    trace("acceptance_process_started")
    error_stream = (output / "frozen-python-stacks.log").open("a", encoding="utf-8")
    faulthandler.dump_traceback_later(80, repeat=True, file=error_stream)
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
                  qpa=app.platformName(), success=False, checks={}, native_windows=False,
                  stage='initialization', stages_completed=[])
    window = None
    original_question, original_save = W.QMessageBox.question, W.QFileDialog.getSaveFileName
    original_modal = {name: getattr(W.QMessageBox, name) for name in ("warning", "critical", "information")}
    def unexpected_modal(*args, **kwargs):
        title = str(args[1]) if len(args) > 1 else "Sin título"
        message = str(args[2]) if len(args) > 2 else ""
        trace("UNEXPECTED_MODAL " + title + ": " + message[:240])
        raise RuntimeError("Unexpected modal during frozen acceptance: " + title + ": " + message[:240])
    W.QMessageBox.question = lambda *a, **k: W.QMessageBox.Yes
    for name in original_modal:
        setattr(W.QMessageBox, name, unexpected_modal)
    project_path = output / 'Acceptance.pforge'
    W.QFileDialog.getSaveFileName = lambda *a, **k: (str(project_path), '')
    timer = C.QTimer(); timer.setInterval(1)
    beats = []
    timer.timeout.connect(lambda: beats.append(1))
    def checkpoint(name):
        report['checks'][name] = True
        report['stages_completed'].append(name)
        report['stage'] = name
        trace("CHECKPOINT " + name)

    try:
        wine = False
        if sys.platform == 'win32':
            import ctypes
            wine = hasattr(ctypes.WinDLL('ntdll'), 'wine_get_version')
        report['wine'] = wine
        report['native_windows'] = sys.platform == 'win32' and not wine and app.platformName() == 'windows'
        trace('initializing_bundled_icarus')
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
        checkpoint('resources')
        if getattr(sys,'frozen',False):
            assert resource_root() not in data_dir().parents
        trace('constructing_main_window')
        window = MainWindow(); window.show(); app.processEvents()
        assert window.isVisible()
        if report['native_windows']:
            import ctypes
            from ctypes import wintypes
            visible = ctypes.windll.user32.IsWindowVisible
            visible.argtypes = [wintypes.HWND]
            visible.restype = wintypes.BOOL
            assert visible(int(window.winId()))
        checkpoint('window_visible')
        trace('generating_clock_project')
        window.new_clock()
        editor = window.studio.open_source('traffic_light.v')
        editor.moveCursor(G.QTextCursor.End)
        editor.insertPlainText('\n// acceptance edit\n')
        assert window.dirty and editor.search('acceptance edit')
        editor.undo(); editor.redo()
        assert 'acceptance edit' in window.project.files['traffic_light.v']
        checkpoint('editor')
        window.clock.step(5 * 50000000)
        assert window.clock.model.state == 'VERDE'
        window.clock.reset()
        assert window.clock.model.state == 'ROJO'
        checkpoint('traffic_light')
        trace('starting_real_hdl_simulation')
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
        checkpoint('hdl_and_vcd')
        (output / 'simulation.log').write_text(window.last_result.output, encoding='utf-8')
        trace('saving_project')
        assert window.save_project()
        loaded = Project.open(project_path)
        assert loaded.files == window.project.files
        assert any(n.endswith('.vcd') for n in loaded.artifacts)
        checkpoint('project_roundtrip')
        trace('loading_plugin')
        manager = PluginManager()
        infos = manager.discover(resource_root() / 'examples/plugins')
        assert len(infos) == 1 and infos[0].compatible
        manager.load(infos[0], trusted=True)
        assert len(next(iter(manager.registry.values()))(adder_project())) == 2
        manager.unload(infos[0].manifest['id'])
        checkpoint('plugin')
        # These indices reflect the CURRENT sidebar. Avoid screenshotting obsolete pages.
        trace('navigating_all_pages')
        for index,name in ((0,'welcome'),(1,'studio'),(2,'devices'),(3,'examples'),
                           (4,'digital'),(5,'hardware'),(6,'plugins'),(7,'settings')):
            window.navigate(index)
            if index == 1: window.studio.output_tabs.setCurrentWidget(window.studio.wave)
            app.processEvents()
            assert window.grab().save(str(output / (name+'.png'))), name
        checkpoint('all_navigation')
        # Navigating Hardware Studio launches a PnP scan on a worker thread.
        # Never close or destroy QThread while it is still running.
        trace('waiting_for_hardware_scan')
        window.hardware.timer.stop()
        deadline = time.monotonic() + 20
        while window.hardware.worker is not None and time.monotonic() < deadline:
            app.processEvents(); time.sleep(.01)
        assert window.hardware.worker is None, 'Hardware enumeration worker hung'
        checkpoint('hardware_worker_completed')
        assert window.hardware.tabs.count() >= 4, 'Hardware Studio missing Arduino/Pico/FPGA tabs'
        assert window.digital_export is not None
        checkpoint('hardware_and_digital_ui')
        trace('closing_first_window')
        window.dirty=False; window.close(); app.processEvents()
        window = MainWindow()
        window.replace_project(Project.open(project_path),project_path,False)
        window.show(); app.processEvents()
        assert window.isVisible() and window.project.files == loaded.files
        checkpoint('close_and_reopen_window')
        checkpoint('reopened_window')
        report['success'] = True
        trace('acceptance_success')
    except Exception as error:
        trace('acceptance_failed %s %s' % (type(error).__name__, str(error)[:240]))
        report['error'] = str(error)
        report['failed_stage'] = report['stage']
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
        for name, original in original_modal.items():
            setattr(W.QMessageBox, name, original)
        (output / 'acceptance.json').write_text(json.dumps(report,indent=2), encoding='utf-8')
        trace('acceptance_report_saved')
        faulthandler.cancel_dump_traceback_later()
        error_stream.close()
    return 0 if report['success'] else 1
