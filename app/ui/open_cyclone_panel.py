"""Cyclone IV open logic synthesis; never creates physical bitstreams."""
import copy
from pathlib import Path
from app.integrations import open_cyclone
from app.ui.qt import QtCore as C, QtWidgets as W, Signal
from app.ui.common import label, button
from app.utils.paths import data_dir


class SynthesisTask(C.QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, project, top, part, executable, parent=None):
        super().__init__(parent)
        self.project = copy.deepcopy(project)
        self.top, self.part, self.executable = top, part, executable

    def run(self):
        try:
            self.completed.emit(open_cyclone.synthesize(
                self.project, data_dir() / "yosys-builds",
                self.top, self.part, executable=self.executable))
        except Exception as exc:
            self.failed.emit(str(exc))


class OpenCyclonePanel(W.QWidget):
    def __init__(self, project_provider=None, parent=None):
        super().__init__(parent)
        self.project_provider = project_provider or (lambda: None)
        self.worker = None
        self.last_project_id = None
        layout = W.QVBoxLayout(self)
        layout.addWidget(label("Cyclone IV · Síntesis libre", "Heading"))
        layout.addWidget(label(
            "Yosys crea netlists sin Quartus. Aún NO genera archivos .rbf/.sof: "
            "falta la cadena de mapeo físico, ruteo y bitgen.", "Muted", True))
        form = W.QFormLayout()
        self.part = W.QLineEdit()
        self.part.setPlaceholderText("EP4CE6F17C8 u otro chip completo")
        self.top = W.QLineEdit()
        self.yosys = W.QLineEdit()
        self.yosys.setReadOnly(True)
        self.yosys.setPlaceholderText("Yosys empaquetado o PATH")
        form.addRow("Chip previsto", self.part)
        form.addRow("Módulo top", self.top)
        form.addRow("Yosys", self.yosys)
        layout.addLayout(form)
        layout.addWidget(button("Elegir Yosys", self.choose))
        self.start_button = button("Sintetizar con Yosys (sin Quartus)", self.start, True)
        layout.addWidget(self.start_button)
        self.status = W.QPlainTextEdit()
        self.status.setReadOnly(True)
        layout.addWidget(self.status, 1)

    def showEvent(self, event):
        project = self.project_provider()
        if project and project.project_id != self.last_project_id:
            self.last_project_id = project.project_id
            self.top.setText(project.simulation.get("top", ""))
        super().showEvent(event)

    def choose(self):
        path, _ = W.QFileDialog.getOpenFileName(
            self, "Seleccionar Yosys", str(Path.home()),
            "Yosys (yosys.exe yosys);;Todos (*)")
        if path:
            try:
                self.yosys.setText(open_cyclone.find_yosys(path))
            except (ValueError, OSError) as exc:
                W.QMessageBox.warning(self, "Yosys", str(exc))

    def start(self):
        project = self.project_provider()
        if not project:
            W.QMessageBox.warning(self, "Síntesis", "Abre un proyecto .pforge.")
            return
        if self.worker and self.worker.isRunning():
            return
        self.start_button.setEnabled(False)
        self.status.setPlainText("Ejecutando Yosys sin Quartus...")
        self.worker = SynthesisTask(
            project, self.top.text().strip(), self.part.text().strip(),
            self.yosys.text().strip() or None, self)
        self.worker.completed.connect(self.completed)
        self.worker.failed.connect(self.failed)
        self.worker.finished.connect(lambda: self.start_button.setEnabled(True))
        self.worker.start()

    def completed(self, result):
        self.status.setPlainText(
            "Netlist JSON: " + result["netlist"] + "\nBLIF: " + result["blif"]
            + "\nNO hay bitstream, no se puede programar.\n" + result["log_tail"][-2500:])

    def failed(self, message):
        self.status.setPlainText("Síntesis fallida: " + message)
