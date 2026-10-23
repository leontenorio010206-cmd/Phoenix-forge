"""Cyclone IV to Quartus: explicit export, optional external compile, no flashing."""
from pathlib import Path

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


class QuartusPanel(W.QWidget):
    """Use the current unsaved in-memory PhoenixForge project as the export source."""
    def __init__(self, project_provider=None, parent=None):
        super().__init__(parent)
        self.project_provider = project_provider or (lambda: None)
        self.last_project_id = None
        self.output = None
        self.worker = None
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
        actions = W.QHBoxLayout()
        actions.addWidget(button("Generar proyecto Quartus", self.export, True))
        self.compile_button = button("Compilar con Quartus", self.compile)
        self.compile_button.setEnabled(False)
        actions.addWidget(self.compile_button)
        layout.addLayout(actions)
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
                project, parent, self.part.text(), self.top.text().strip() or None)
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
