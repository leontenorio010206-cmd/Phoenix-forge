"""Cyclone IV to Quartus: explicit export, optional external compile, no flashing."""
from pathlib import Path
import copy
import tempfile

from app.utils.paths import data_dir
from app.integrations import cyclone_runner

from app.ui.qt import QtCore as C, QtWidgets as W, Signal
from app.ui.common import label, button
from app.integrations import quartus_bridge


class CompileTask(C.QThread):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, folder, executable, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.executable = executable

    def run(self):
        try:
            self.completed.emit(quartus_bridge.compile_project(self.folder, self.executable))
        except Exception as exc:
            self.failed.emit(str(exc))


class ScanTask(C.QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, executable=None, parent=None):
        super().__init__(parent)
        self.executable = executable

    def run(self):
        try:
            tools = cyclone_runner.discover_tools(self.executable)
            self.completed.emit(cyclone_runner.scan_hardware(tools))
        except Exception as exc:
            self.failed.emit(str(exc))


class OneClickTask(C.QThread):
    progress = Signal(str)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, project, folder, part, top, cable, executable, parent=None):
        super().__init__(parent)
        self.project = copy.deepcopy(project)
        self.folder = folder
        self.part = part
        self.top = top
        self.cable = cable
        self.executable = executable

    def run(self):
        try:
            result = cyclone_runner.compile_and_run(
                self.project, self.folder, self.part, self.top,
                cable_number=self.cable, executable=self.executable,
                on_stage=self.progress.emit)
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class QuartusPanel(W.QWidget):
    """Use the current unsaved in-memory PhoenixForge project as the export source."""
    def __init__(self, project_provider=None, parent=None):
        super().__init__(parent)
        self.project_provider = project_provider or (lambda: None)
        self.last_project_id = None
        self.output = None
        self.worker = None
        self.scan_worker = None
        layout = W.QVBoxLayout(self)
        layout.addWidget(label("Cyclone IV · Quartus Prime Lite", "Heading"))
        layout.addWidget(label(
            "Exporta Verilog a .qpf/.qsf y compila con Quartus externo. "
            "Necesitas confirmar el código exacto del chip (no solo 'Cyclone IV'). "
            "NUNCA se programará la FPGA automáticamente.", "Muted", True))
        form = W.QFormLayout()
        self.part = W.QLineEdit()
        self.part.setPlaceholderText("Ejemplo: EP4CE6E22C8N (NO se selecciona por defecto)")
        form.addRow("Marcado exacto del chip", self.part)
        self.top = W.QLineEdit()
        self.top.setPlaceholderText("Módulo principal de tu proyecto")
        form.addRow("Módulo top", self.top)
        self.quartus_exe = W.QLineEdit()
        self.quartus_exe.setPlaceholderText("quartus_sh en PATH, o seleccionar el EXE oficial")
        self.quartus_exe.setReadOnly(True)
        exe_row = W.QHBoxLayout()
        exe_row.addWidget(self.quartus_exe, 1)
        exe_row.addWidget(button("Seleccionar quartus_sh", self.choose_exe))
        form.addRow("Compilador Quartus", exe_row)
        layout.addLayout(form)
        layout.addWidget(label(
            "Las asignaciones de pines guardadas en el proyecto solo se exportan "
            "si tienen formato PIN_XX. Sin un pinout validado la salida es "
            "únicamente para revisión y NO está lista para cargar en la placa.",
            "Muted", True))
        self.include_pins = W.QCheckBox("Incluir pines solo si comprobé TODOS en el esquema físico")
        self.include_pins.setChecked(False)
        layout.addWidget(self.include_pins)
        actions = W.QHBoxLayout()
        actions.addWidget(button("Generar proyecto Quartus", self.export, True))
        self.compile_button = button("Compilar con Quartus", self.compile)
        self.compile_button.setEnabled(False)
        actions.addWidget(self.compile_button)
        layout.addLayout(actions)
        layout.addWidget(label(
            "Flujo integrado: instalas Quartus con Cyclone IV una sola vez. "
            "Después PhœnixForge compila y carga el .sof sin abrir Quartus. "
            "No se escribe Flash; el circuito se pierde al cortar alimentación.",
            "Muted", True))
        self.scan_button = button("Detectar FPGA conectada por JTAG", self.scan)
        layout.addWidget(self.scan_button)
        self.jtag_results = W.QPlainTextEdit()
        self.jtag_results.setReadOnly(True)
        self.jtag_results.setMaximumHeight(100)
        layout.addWidget(self.jtag_results)
        self.cable = W.QComboBox()
        self.cable.addItem("Detectar cable automáticamente", None)
        layout.addWidget(self.cable)
        self.run_button = button("⚡ Compilar y ejecutar en Cyclone IV (SRAM)",
                                 self.run_on_fpga, True)
        layout.addWidget(self.run_button)
        self.status = W.QPlainTextEdit()
        self.status.setReadOnly(True)
        self.status.setPlaceholderText("Se mostrarán la carpeta generada y los resultados de Quartus.")
        layout.addWidget(self.status, 1)

    def showEvent(self, event):
        self.sync_project()
        super().showEvent(event)

    def sync_project(self):
        project = self.project_provider()
        if project is not None and project.project_id != self.last_project_id:
            self.last_project_id = project.project_id
            self.top.setText(project.simulation.get("top", ""))
            self.output = None
            self.compile_button.setEnabled(False)

    def choose_exe(self):
        path, _ = W.QFileDialog.getOpenFileName(
            self, "Selecciona quartus_sh", str(Path.home()),
            "Quartus shell (quartus_sh.exe quartus_sh);;Todos (*)")
        if path:
            try:
                quartus_bridge.find_quartus(path)
            except (ValueError, OSError) as exc:
                W.QMessageBox.warning(self, "Quartus", str(exc))
            else:
                self.quartus_exe.setText(path)

    def export(self):
        self.sync_project()
        project = self.project_provider()
        if project is None:
            W.QMessageBox.warning(self, "Quartus", "No hay proyecto abierto.")
            return
        parent = W.QFileDialog.getExistingDirectory(self, "Destino para proyecto Quartus",
                                                    str(Path.home()))
        if not parent:
            return
        try:
            self.output = quartus_bridge.export_project(
                project, parent, self.part.text(), self.top.text().strip() or None,
                pins=project.pins if self.include_pins.isChecked() else {})
        except (ValueError, OSError) as exc:
            W.QMessageBox.warning(self, "Exportación Quartus", str(exc))
            return
        self.status.setPlainText(
            "Proyecto exportado: " + str(self.output) +
            "\nAbre el .qpf en Quartus para revisar chip, reloj, pinout y voltajes. "
            "NO está habilitada la programación automática.")
        self.compile_button.setEnabled(True)

    def compile(self):
        if self.worker is not None and self.worker.isRunning():
            return
        if self.output is None:
            W.QMessageBox.warning(self, "Quartus", "Exporta primero un proyecto.")
            return
        self.compile_button.setEnabled(False)
        self.status.appendPlainText("\nCompilando en Quartus (sin programar la placa)...")
        self.worker = CompileTask(self.output, self.quartus_exe.text().strip() or None, self)
        self.worker.completed.connect(self.compiled)
        self.worker.failed.connect(self.failed)
        self.worker.finished.connect(lambda: self.compile_button.setEnabled(True))
        self.worker.start()

    def compiled(self, output):
        self.status.appendPlainText("\nCompilación completada:\n" + output[-8000:])
        self.status.appendPlainText("\nADVERTENCIA: revisa restricciones antes de programar.")

    def failed(self, error):
        self.status.appendPlainText("\nError de Quartus: " + error)

    def scan(self):
        if self.scan_worker is not None and self.scan_worker.isRunning():
            return
        self.scan_button.setEnabled(False)
        self.jtag_results.setPlainText("Explorando JTAG sin modificar la FPGA...")
        self.scan_worker = ScanTask(self.quartus_exe.text().strip() or None, self)
        self.scan_worker.completed.connect(self.scanned)
        self.scan_worker.failed.connect(self.scan_failed)
        self.scan_worker.finished.connect(lambda: self.scan_button.setEnabled(True))
        self.scan_worker.start()

    def scanned(self, result):
        self.jtag_results.setPlainText(result["raw"][:4000])
        self.cable.clear()
        self.cable.addItem("Detectar cable automáticamente", None)
        for cable in result["cables"]:
            self.cable.addItem("%s) %s" % (cable["number"], cable["name"]),
                               cable["number"])

    def scan_failed(self, error):
        self.jtag_results.setPlainText("No fue posible detectar JTAG: " + error)

    def run_on_fpga(self):
        """One-click local flow only after all physical preconditions are accepted."""
        self.sync_project()
        project = self.project_provider()
        if project is None:
            W.QMessageBox.warning(self, "FPGA", "Primero abre un proyecto .pforge.")
            return
        if self.worker is not None and self.worker.isRunning():
            return
        if not self.include_pins.isChecked():
            W.QMessageBox.warning(
                self, "Pines sin verificar",
                "Marca la casilla de pines SOLO después de comprobarlos con "
                "el esquema exacto de tu placa. No cargaremos un diseño con "
                "conexiones desconocidas.")
            return
        part = self.part.text().strip()
        top = self.top.text().strip()
        try:
            cyclone_runner.quartus_bridge.validate_part(part)
            cyclone_runner.verify_pin_coverage(project, top)
        except (ValueError, KeyError) as error:
            W.QMessageBox.warning(self, "Configuración incompleta", str(error))
            return
        choice = W.QMessageBox.question(
            self, "Confirmar programación temporal JTAG",
            "Se compilará el proyecto %s para %s y se configurará la FPGA "
            "conectada por JTAG.\n\nLa programación será SOLO SRAM, no Flash. "
            "Los pines, niveles de voltaje, reloj y esquema de la placa "
            "deben estar revisados; JTAG no confirma encapsulado ni pinout.\n\n"
            "¿Autorizas cargar este diseño a la placa?" % (project.name, part),
            W.QMessageBox.Yes | W.QMessageBox.No, W.QMessageBox.No)
        if choice != W.QMessageBox.Yes:
            return
        parent = data_dir() / "quartus-builds"
        parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="compile-", dir=str(parent)))
        cable = self.cable.currentData()
        self.run_button.setEnabled(False)
        self.status.appendPlainText("\nIniciando flujo integrado Cyclone IV...")
        self.worker = OneClickTask(project, work, part, top, cable,
                                   self.quartus_exe.text().strip() or None, self)
        self.worker.progress.connect(self.status.appendPlainText)
        self.worker.completed.connect(self.run_completed)
        self.worker.failed.connect(self.run_failed)
        self.worker.finished.connect(lambda: self.run_button.setEnabled(True))
        self.worker.start()

    def run_completed(self, result):
        self.status.appendPlainText(
            "\nFPGA configurada en SRAM. Archivo: " + result["bitstream"] +
            "\n" + result["programmer"])
        W.QMessageBox.information(
            self, "FPGA configurada",
            "Se cargó la configuración en SRAM. El hardware opera mientras "
            "esté alimentado; PhoenixForge no ejecuta Verilog como un programa de PC.")

    def run_failed(self, error):
        self.status.appendPlainText("\nError de compilación/programación: " + error)
