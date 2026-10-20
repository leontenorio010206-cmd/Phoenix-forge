import copy
import json
import logging
import subprocess
import threading
from pathlib import Path

from app import __version__
from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt, Signal, QAction, BINDING
from app.ui.common import button, card, label
from app.ui.theme import STYLE
from app.ui.studio import Studio
from app.ui.examples_panel import ExamplesPanel
from app.ui.digital_export_panel import DigitalExportPanel
from app.ui.hardware_studio import HardwareStudio
from app.devices.simulation import device_demo_project, rtl_readiness
from app.ui.management import DevicePanel, PluginPanel, SettingsPanel
from app.ui.project_actions import ProjectActions, guarded
from app.core.project import Project
from app.core.examples import clock_project, internal_clock_result
from app.simulators.icarus import IcarusEngine, SimulationResult, find_executable
from app.utils.paths import assets_dir, data_dir, resource_root
from app.utils.platform import process_options


class SimulationThread(C.QThread):
    result_ready = Signal(object)

    def __init__(self, engine, project, parent=None):
        super().__init__(parent)
        self.engine, self.project = engine, copy.deepcopy(project)
        self.cancel = threading.Event()

    def run(self):
        try:
            result = self.engine.run(self.project, cancel=self.cancel)
        except Exception as error:
            logging.exception("Worker de simulación")
            result = SimulationResult(False, "", reason=str(error), output=str(error))
        self.result_ready.emit(result)


class MainWindow(W.QMainWindow, ProjectActions):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(G.QIcon(str(assets_dir() / "phoenix.svg")))
        self.resize(1380, 900)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(STYLE)
        self.project = Project()
        self.project_path = None
        self.dirty, self.worker, self.close_after_run = False, None, False
        self.external_viewers = []
        container = W.QWidget()
        shell = W.QHBoxLayout(container)
        shell.setContentsMargins(0, 0, 0, 0); shell.setSpacing(0)
        sidebar = W.QWidget()
        sidebar.setFixedWidth(192)
        side = W.QVBoxLayout(sidebar)
        side.setContentsMargins(0, 18, 0, 12)
        mark = label("")
        mark.setPixmap(G.QIcon(str(assets_dir() / "phoenix.svg")).pixmap(58, 58))
        mark.setAlignment(Qt.AlignCenter)
        side.addWidget(mark)
        brand = label("PhœnixForge")
        brand.setStyleSheet("font-size: 19px; font-weight: 700;")
        brand.setAlignment(Qt.AlignCenter)
        side.addWidget(brand)
        version = label("Forge Digital Logic", "Muted")
        version.setAlignment(Qt.AlignCenter)
        side.addWidget(version)
        self.navigation = W.QListWidget()
        self.navigation.setObjectName("Navigation")
        self.navigation.addItems(["Inicio", "Estudio HDL", "Dispositivos FPGA", "Proyectos de muestra", "Exportar a Digital", "Hardware Studio", "Plugins", "Configuración"])
        side.addWidget(self.navigation, 1)
        build = label("   v%s  /  %s\n   RTL · Sin programación física" % (__version__, BINDING), "Muted")
        build.setStyleSheet("font-size: 10px; color: #7f94ad;")
        side.addWidget(build)
        shell.addWidget(sidebar)
        self.stack = W.QStackedWidget()
        self.home = self.make_home()
        self.studio = Studio()
        self.examples = ExamplesPanel()
        self.clock = self.examples.clock  # Interactive sample, no longer a top-level page.
        self.devices = DevicePanel(lambda: self.project, lambda: self.settings.values)
        self.digital_export = DigitalExportPanel()
        self.hardware = HardwareStudio()
        self.plugins = PluginPanel(lambda: copy.deepcopy(self.project))
        self.settings = SettingsPanel()
        for widget in (self.home, self.studio, self.devices, self.examples, self.digital_export, self.hardware, self.plugins, self.settings):
            self.stack.addWidget(widget)
        self.navigation.currentRowChanged.connect(self.stack.setCurrentIndex)
        shell.addWidget(self.stack, 1)
        self.setCentralWidget(container)
        self.connect_actions()
        self.make_menus()
        self.replace_project(Project(name="Proyecto nuevo", files={"main.v": "module main(input a, output y);\n  assign y = a;\nendmodule\n"}, simulation={"top": "main", "testbench": "", "timeout": 15}), dirty=False)
        self.navigate(0)
        self.update_tool_status()

    def make_home(self):
        widget = W.QWidget()
        layout = W.QVBoxLayout(widget)
        layout.setContentsMargins(46, 42, 46, 34)
        layout.setSpacing(18)
        layout.addWidget(label("EL TALLER DE TU PRÓXIMA IDEA", "Eyebrow"))
        layout.addWidget(label("De una ecuación\na lógica que puedes ver.", "Title"))
        layout.addWidget(label("Escribe Verilog, comprueba tus circuitos y observa cada señal.\nUn entorno de escritorio para aprender, experimentar y construir.", "Muted", True))
        actions = W.QHBoxLayout()
        actions.addWidget(button("Crear proyecto", self.new_project, True))
        actions.addWidget(button("Abrir .pforge", self.open_project))
        actions.addStretch()
        layout.addLayout(actions)
        layout.addSpacing(14)
        cards = W.QHBoxLayout()
        for number, title, text, action in (
                ("01 / DISPOSITIVOS", "Elige tu FPGA", "Diez perfiles documentados.\nSelecciona tu dispositivo y organiza las asignaciones de pines.", lambda: self.navigate(2)),
                ("02 / EJEMPLOS", "Aprende con proyectos", "Semáforo y divisores, sumador, y contador RTL.\nAbre, modifica y simula sin perder los ejemplos.", lambda: self.navigate(3)),
                ("03 / HARDWARE", "Conecta y programa", "Arduino, Raspberry Pi Pico y detección USB/JTAG.\nLas cargas físicas siempre requieren confirmación.", lambda: self.navigate(5))):
            frame, inner = card()
            inner.addWidget(label(number, "Eyebrow"))
            inner.addWidget(label(title, "Heading"))
            inner.addWidget(label(text, "Muted", True))
            inner.addStretch()
            inner.addWidget(button("Abrir →", action))
            cards.addWidget(frame)
        layout.addLayout(cards, 1)
        note, nl = card()
        nl.addWidget(label("Un proyecto que conserva tu trabajo", "Heading"))
        nl.addWidget(label("El formato .pforge reúne fuentes, perfil FPGA, configuración y resultados VCD. Puedes exportarlo y continuar desarrollándolo sin depender de esta interfaz.", "Muted", True))
        layout.addWidget(note)
        self.engine_status = label("", "Muted", True)
        layout.addWidget(self.engine_status)
        return widget

    def connect_actions(self):
        self.studio.source_changed.connect(self.source_changed)
        self.studio.simulation_changed.connect(self.simulation_changed)
        self.studio.run_requested.connect(self.run_simulation)
        self.studio.cancel_requested.connect(self.cancel_simulation)
        self.studio.import_requested.connect(self.import_sources)
        self.studio.new_source_requested.connect(self.new_source)
        self.examples.example_requested.connect(self.open_example)
        self.clock.create_requested.connect(self.new_clock)
        self.clock.trace_requested.connect(self.clock_trace)
        self.devices.demo_requested.connect(self.open_device_demo)
        self.devices.simulate_requested.connect(self.simulate_selected_device)
        self.devices.device_selected.connect(self.choose_device)
        self.devices.pins_changed.connect(self.change_pins)
        self.devices.bench.trace_ready.connect(self.virtual_trace)
        self.digital_export.export_requested.connect(self.export_digital)
        self.digital_export.bridge_requested.connect(self.prepare_and_open_digital)
        self.digital_export.copy_settings_requested.connect(self.copy_digital_settings)
        self.digital_export.virtual_requested.connect(self.open_virtual_from_export)
        self.settings.saved.connect(lambda _: self.update_tool_status())

    def make_menus(self):
        def action(menu, title, callback, shortcut=None):
            a = QAction(title, self)
            if shortcut:
                a.setShortcut(shortcut)
            a.triggered.connect(lambda checked=False: callback())
            menu.addAction(a)
        file = self.menuBar().addMenu("Archivo")
        for title, fn, key in (("Nuevo proyecto…", self.new_project, "Ctrl+N"), ("Abrir proyecto…", self.open_project, "Ctrl+O"),
                               ("Guardar proyecto", self.save_project, "Ctrl+S"), ("Guardar proyecto como…", lambda: self.save_project(True), "Ctrl+Shift+S"),
                               ("Importar archivos…", self.import_sources, "Ctrl+I"), ("Guardar archivo fuente como…", self.export_active_source, "Ctrl+Alt+S"),
                               ("Exportar paquete completo…", self.export_project, None), ("Exportar componente para Digital…", self.export_digital, None), ("Exportar VCD…", self.export_vcd, None),
                               ("Verificar integridad", self.verify_project, None), ("Salir", self.close, "Alt+F4")):
            action(file, title, fn, key)
        edit = self.menuBar().addMenu("Editar")
        action(edit, "Deshacer", lambda: self.editor_command("undo"), "Ctrl+Z")
        action(edit, "Rehacer", lambda: self.editor_command("redo"), "Ctrl+Y")
        action(edit, "Buscar", lambda: self.studio.search_field.setFocus(), "Ctrl+F")
        simulation = self.menuBar().addMenu("Simulación")
        action(simulation, "Ejemplo: semáforo y divisores", self.new_clock)
        action(simulation, "Ejemplo: sumador de 1 bit", self.new_adder)
        action(simulation, "Compilar y simular", self.run_simulation, "F5")
        action(simulation, "Detener", self.cancel_simulation, "Shift+F5")
        action(simulation, "Abrir Hardware Studio", lambda: self.navigate(5))
        action(simulation, "Abrir VCD…", self.open_vcd)
        action(simulation, "Abrir último VCD en GTKWave", self.external_wave)
        help_menu = self.menuBar().addMenu("Ayuda")
        action(help_menu, "Manual de usuario", self.show_manual)
        action(help_menu, "Exportar licencias y fuentes de componentes…", self.export_component_sources)
        action(help_menu, "Acerca de PhœnixForge", self.about)

    def navigate(self, index):
        self.navigation.setCurrentRow(index)
        if index == 4:
            self.digital_export.bind_project(self.project, keep_top=True)

    def editor_command(self, name):
        editor = self.studio.tabs.currentWidget()
        if editor:
            getattr(editor, name)()

    def mark_dirty(self):
        self.dirty = True
        self.update_title()

    def update_title(self):
        self.setWindowTitle("%s%s — PhœnixForge %s" % (self.project.name, " *" if self.dirty else "", __version__))

    def source_changed(self, name, text):
        self.project.files[name] = text
        self.mark_dirty()
        if self.stack.currentWidget() is self.digital_export:
            self.digital_export.bind_project(self.project, keep_top=True)

    def simulation_changed(self, field, name):
        self.project.simulation[field] = name
        self.mark_dirty()
        if self.stack.currentWidget() is self.digital_export:
            self.digital_export.bind_project(self.project, keep_top=True)

    def open_example(self, key):
        if key == "clock":
            self.new_clock()
        elif key == "adder":
            self.new_adder()
        elif key == "device":
            self.open_device_demo(self.project.device)

    @guarded
    def open_device_demo(self, device):
        if self.can_replace():
            self.replace_project(device_demo_project(device))
            self.statusBar().showMessage("Demo RTL preparada para el perfil elegido. Pulse F5 para simular.", 10000)

    @guarded
    def simulate_selected_device(self, device):
        # Preserve the current sources while switching the selected RTL profile.
        self.choose_device(device)
        self.navigate(1)
        self.run_simulation()

    def choose_device(self, device):
        self.project.device = device
        self.mark_dirty()
        self.digital_export.bind_project(self.project, keep_top=True)
        self.statusBar().showMessage("Perfil seleccionado: " + self.devices.profiles[device]["name"], 6000)

    def open_virtual_from_export(self):
        self.navigate(2)
        self.devices.tabs.setCurrentIndex(1)
        self.devices.bench.bind_project(self.project)

    def virtual_trace(self, data):
        self.project.artifacts["virtual/latest/virtual_fpga.vcd"] = data
        self.mark_dirty()
        self.studio.refresh_tree()
        self.studio.wave.load(data, "FPGA virtual")
        self.statusBar().showMessage("Simulación FPGA virtual: VCD disponible en Estudio HDL", 9000)

    def change_pins(self, pins):
        self.project.pins = pins
        self.mark_dirty()
        self.statusBar().showMessage("Asignaciones aplicadas al proyecto; guárdelo para conservarlas.", 7000)

    def update_tool_status(self):
        values = self.settings.values
        engine = IcarusEngine(values.get("iverilog", ""), values.get("vvp", ""))
        text = ("Icarus integrado · simulación RTL y FPGA virtual listas" if engine.bundle else "Icarus detectado · listo para compilar HDL") if engine.available else "Motor HDL no disponible · revisa Configuración. Los modelos internos permanecen disponibles."
        self.engine_status.setText(text)
        self.statusBar().showMessage(text)

    @guarded
    def run_simulation(self):
        if self.worker is not None:
            return
        errors, warnings = rtl_readiness(self.project)
        if errors:
            W.QMessageBox.warning(self, "Simulación FPGA", "\n".join(errors))
            return
        values = self.settings.values
        engine = IcarusEngine(values.get("iverilog", ""), values.get("vvp", ""))
        if not engine.available:
            W.QMessageBox.warning(self, "Motor HDL no disponible", "No se encontraron los componentes de Icarus.\nEn el portable, usa las rutas vacías para seleccionar el motor integrado. Si falta, vuelve a obtener el paquete completo.\nLa ejecución desde fuentes admite una instalación externa.\nLos modelos internos siguen disponibles.")
            return
        answer = W.QMessageBox.question(self, "Ejecutar simulación HDL",
            "Perfil: " + self.devices.profiles[self.project.device]["name"] + "\n" + "\n".join(warnings) +
            "\n\nIcarus ejecutará el testbench en una carpeta separada. HDL puede operar con archivos; no es una sandbox.\n\n¿Confía en estas fuentes y desea simularlas?",
            W.QMessageBox.Yes | W.QMessageBox.No, W.QMessageBox.Yes)
        if answer != W.QMessageBox.Yes:
            return
        self.project.simulation["timeout"] = int(values.get("timeout", 15))
        self.mark_dirty()
        self.studio.refresh_modules()
        self.navigate(1)
        self.studio.output_tabs.setCurrentWidget(self.studio.console)
        self.studio.console.setPlainText("Compilando con Icarus…\n")
        self.studio.errors.setRowCount(0)
        self.studio.set_busy(True)
        self.worker = SimulationThread(engine, self.project, self)
        self.worker.result_ready.connect(self.simulation_finished)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def cancel_simulation(self):
        if self.worker is not None:
            self.worker.cancel.set()
            self.statusBar().showMessage("Cancelando proceso…")

    def worker_finished(self):
        thread = self.worker
        self.worker = None
        if thread:
            thread.deleteLater()
        self.studio.set_busy(False)
        if self.close_after_run:
            self.close_after_run = False
            self.close()

    def simulation_finished(self, result):
        self.last_result = result
        self.studio.console.setPlainText(result.output)
        if self.worker is not None and self.worker.project.files != self.project.files:
            self.studio.console.appendPlainText("AVISO: las fuentes cambiaron durante la ejecución; este resultado corresponde a la copia previa conservada por sus hashes en run.json.")
        self.studio.show_diagnostics(result.diagnostics, None if result.success else result.reason)
        # Failed runs retain the last successful VCD, explicitly separated from latest logs.
        self.project.artifacts = {k: v for k, v in self.project.artifacts.items() if not k.startswith("icarus/latest/")}
        self.project.artifacts.update({"icarus/latest/" + name: data for name, data in result.artifacts.items() if not name.endswith(".vcd")})
        if result.success:
            self.project.artifacts = {k: v for k, v in self.project.artifacts.items() if not k.startswith("icarus/last_success/")}
            self.project.artifacts.update({"icarus/last_success/" + name: data for name, data in result.artifacts.items() if name.endswith(".vcd") or name == "run.json"})
        self.mark_dirty()
        self.studio.refresh_tree()
        self.statusBar().showMessage(result.reason, 15000)
        vcds = [(name, data) for name, data in result.artifacts.items() if name.endswith(".vcd")]
        if result.success and vcds:
            try:
                self.studio.wave.load(vcds[0][1], vcds[0][0])
            except ValueError as error:
                self.studio.console.appendPlainText("Visor: " + str(error))
        if not result.success:
            self.studio.output_tabs.setCurrentWidget(self.studio.console)

    def attach_internal(self, artifacts, prefix):
        self.project.artifacts.update({prefix + "/" + k: v for k, v in artifacts.items()})
        self.mark_dirty()
        self.studio.refresh_tree()
        name = next(k for k in artifacts if k.endswith(".vcd"))
        self.studio.wave.load(artifacts[name], name)
        self.studio.console.appendPlainText("Traza del modelo interno del laboratorio; no ejecuta ni valida el HDL editado.")
        self.navigate(1)
        self.studio.output_tabs.setCurrentWidget(self.studio.wave)

    @guarded
    def clock_trace(self, red, green, yellow):
        self.attach_internal(internal_clock_result(red, green, yellow), "internal_clock")

    @guarded
    def external_wave(self):
        tool = find_executable(self.settings.values.get("gtkwave", ""), "gtkwave")
        if not tool:
            raise ValueError("GTKWave no instalado; use el visor integrado o configure su ruta")
        names = [n for n in self.project.artifacts if n.endswith(".vcd")]
        if not names:
            raise ValueError("El proyecto no tiene un VCD")
        path = data_dir() / (self.project.project_id + "-view.vcd")
        path.write_bytes(self.project.artifacts[names[-1]])
        self.external_viewers = [p for p in self.external_viewers if p.poll() is None]
        self.external_viewers.append(subprocess.Popen([tool, str(path)], shell=False, **process_options()))

    def show_manual(self):
        path = resource_root() / "docs" / "USER_MANUAL.md"
        if path.exists():
            dialog = W.QMessageBox(self)
            dialog.setWindowTitle("Manual de usuario")
            dialog.setText("Guarde un proyecto, edite sus módulos y pulse F5 para compilar.\nLos proyectos de muestra se abren desde la barra lateral.\nManual completo: " + str(path))
            dialog.setDetailedText(path.read_text(encoding="utf-8"))
            from app.ui.qt import exec_dialog
            exec_dialog(dialog)
        else:
            W.QMessageBox.information(self, "Manual", "Consulte docs/USER_MANUAL.md en la distribución fuente.")

    def about(self):
        W.QMessageBox.about(self, "Acerca de PhœnixForge", "<h2>PhœnixForge " + __version__ + "</h2><p>Forge Digital Logic</p><p>Proyecto de Leonardo Antonio Hernández Tenorio.</p><p>Verilog, simulación y FPGA.<br>Identidad SVG original. Código fuente modificable.</p><p>" + BINDING + " · Síntesis y programación física no implementadas.<br>Consulta el informe de distribución para las plataformas verificadas.</p>")

    @guarded
    def export_component_sources(self):
        from app.exporters.components import export_components
        parent = W.QFileDialog.getExistingDirectory(self, "Guardar componentes en una carpeta nueva")
        if parent:
            target = export_components(Path(parent) / "PhoenixForge_components")
            W.QMessageBox.information(self, "Componentes", "Fuentes y avisos disponibles copiados a:\n" + str(target))

    def closeEvent(self, event):
        if self.hardware.worker is not None:
            W.QMessageBox.information(self, "Hardware Studio", "Espere a que termine la operación de hardware antes de cerrar.")
            event.ignore()
            return
        if self.devices.bench.worker is not None:
            W.QMessageBox.information(self, "FPGA virtual", "Espere a que termine el banco de pruebas virtual antes de cerrar.")
            event.ignore()
            return
        if self.worker is not None:
            if W.QMessageBox.question(self, "Simulación activa", "¿Detener la simulación y cerrar?", W.QMessageBox.Yes | W.QMessageBox.No) == W.QMessageBox.Yes:
                self.close_after_run = True
                self.cancel_simulation()
            event.ignore()
            return
        if not self.confirm_discard():
            event.ignore()
            return
        self.clock.stop()
        for pid in list(self.plugins.manager.loaded):
            try:
                self.plugins.manager.unload(pid)
            except Exception:
                logging.exception("Cierre de plugin")
        event.accept()

