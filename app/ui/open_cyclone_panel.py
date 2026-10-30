"""Cyclone IV free synthesis + explicitly gated external-RBF SRAM deployment."""
import copy
from pathlib import Path
import uuid

from app.integrations import open_cyclone, cyclone_deploy
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


class DeploymentTask(C.QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, folder, cable, part, parent=None):
        super().__init__(parent)
        self.folder, self.cable, self.part = folder, cable, part

    def run(self):
        try:
            self.completed.emit(cyclone_deploy.deploy_sram(
                self.folder, self.cable, self.part,
                confirmed_board=True, confirmed_external_bitstream=True,
                confirmed_sram_only=True))
        except Exception as exc:
            self.failed.emit(str(exc))


class OpenCyclonePanel(W.QWidget):
    def __init__(self, project_provider=None, parent=None):
        super().__init__(parent)
        self.project_provider = project_provider or (lambda: None)
        self.worker = None
        self.deploy_worker = None
        self.last_project_id = None
        self.staged_folder = None

        outer = W.QVBoxLayout(self)
        scroll = W.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(W.QFrame.NoFrame)
        outer.addWidget(scroll)
        content = W.QWidget()
        scroll.setWidget(content)
        layout = W.QVBoxLayout(content)
        layout.addWidget(label("Cyclone IV · síntesis libre y programación SRAM", "Heading"))
        layout.addWidget(label(
            "Paso 1: Yosys compila lógica Verilog a JSON/BLIF SIN Quartus. "
            "No crea .sof/.rbf físico de Cyclone IV.", "Muted", True))
        form = W.QFormLayout()
        self.part = W.QLineEdit()
        self.part.setPlaceholderText("Chip exacto, ej. EP4CE6F17C8")
        self.top = W.QLineEdit()
        self.top.setPlaceholderText("Módulo superior Verilog")
        self.yosys = W.QLineEdit()
        self.yosys.setReadOnly(True)
        self.yosys.setPlaceholderText("OSS CAD Suite privada / Yosys seleccionado")
        form.addRow("Marcado del chip", self.part)
        form.addRow("Top", self.top)
        form.addRow("Compilador", self.yosys)
        layout.addLayout(form)
        layout.addWidget(button("Elegir Yosys", self.choose))
        layout.addWidget(button("Detectar herramientas Yosys instaladas", self.detect_yosys))
        self.start_button = button("Sintetizar con Yosys (sin Quartus)", self.start, True)
        layout.addWidget(self.start_button)

        layout.addWidget(label("Paso 2 · Importar bitstream RBF externo", "Heading"))
        layout.addWidget(label(
            "El RBF debe proceder de un compilador compatible con el modelo "
            "y la placa exactos. PhoenixForge NO valida la configuración interna "
            "ni convierte netlists JSON en RBF.", "Muted", True))
        self.board = W.QLineEdit()
        self.board.setPlaceholderText("Nombre y revisión de placa, según su documentación")
        layout.addWidget(self.board)
        self.rbf_path = W.QLineEdit()
        self.rbf_path.setReadOnly(True)
        self.rbf_path.setPlaceholderText("Selecciona un .rbf generado externamente")
        layout.addWidget(self.rbf_path)
        layout.addWidget(button("Elegir RBF", self.choose_rbf))
        self.pins_ok = W.QCheckBox(
            "Comparé los pines del proyecto con el esquema de MI placa")
        self.voltage_ok = W.QCheckBox(
            "Verifiqué encapsulado, alimentación y estándares de E/S")
        layout.addWidget(self.pins_ok)
        layout.addWidget(self.voltage_ok)
        layout.addWidget(button("Preparar paquete RBF con SHA-256", self.stage))
        layout.addWidget(button("Abrir paquete preparado anteriormente", self.open_staged))

        layout.addWidget(label("Paso 3 · Cargar por JTAG a SRAM temporal", "Heading"))
        self.cable = W.QComboBox()
        self.cable.setEditable(True)
        self.cable.addItems(["", "usb-blaster", "usb-blasterII", "ft2232"])
        layout.addWidget(self.cable)
        self.board_ok = W.QCheckBox(
            "Comprobé físicamente modelo, marcado y revisión de esta FPGA")
        self.external_ok = W.QCheckBox(
            "Acepto que el bitstream externo no está certificado por PhoenixForge")
        self.sram_ok = W.QCheckBox(
            "Autorizo únicamente SRAM (temporal), nunca Flash")
        for control in (self.board_ok, self.external_ok, self.sram_ok):
            layout.addWidget(control)
        self.deploy_button = button("⚡ Verificar JTAG y cargar RBF en SRAM", self.deploy, True)
        self.deploy_button.setEnabled(False)
        layout.addWidget(self.deploy_button)

        self.status = W.QPlainTextEdit()
        self.status.setReadOnly(True)
        self.status.setMinimumHeight(150)
        layout.addWidget(self.status, 1)

    def showEvent(self, event):
        self.sync_project()
        super().showEvent(event)

    def sync_project(self):
        project = self.project_provider()
        if project and project.project_id != self.last_project_id:
            self.last_project_id = project.project_id
            self.top.setText(project.simulation.get("top", ""))
            self.staged_folder = None
            self.deploy_button.setEnabled(False)
            for item in (self.pins_ok, self.voltage_ok,
                         self.board_ok, self.external_ok, self.sram_ok):
                item.setChecked(False)

    def detect_yosys(self):
        try:
            tool = open_cyclone.find_yosys()
        except (OSError, ValueError) as exc:
            self.yosys.clear()
            self.status.setPlainText(
                "Yosys no encontrado. Instala el componente OSS CAD Suite "
                "desde el Setup de PhoenixForge y vuelve a comprobar.\n" + str(exc))
            return
        self.yosys.setText(tool)
        self.status.setPlainText("Yosys encontrado: " + tool +
                                 "\nLa compilación física Cyclone IV sigue pendiente.")

    def clear_deploy_authorization(self):
        for control in (self.board_ok, self.external_ok, self.sram_ok):
            control.setChecked(False)

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
        self.sync_project()
        project = self.project_provider()
        if not project:
            W.QMessageBox.warning(self, "Síntesis", "Abre un proyecto .pforge.")
            return
        if self.worker and self.worker.isRunning():
            return
        self.start_button.setEnabled(False)
        self.status.setPlainText("Ejecutando síntesis RTL con Yosys...")
        self.worker = SynthesisTask(
            project, self.top.text().strip(), self.part.text().strip(),
            self.yosys.text().strip() or None, self)
        self.worker.completed.connect(self.completed)
        self.worker.failed.connect(self.failed)
        self.worker.finished.connect(lambda: self.start_button.setEnabled(True))
        self.worker.start()

    def completed(self, report):
        self.status.setPlainText(
            "Síntesis RTL terminada. Netlist JSON: " + report["netlist"] +
            "\nBLIF: " + report["blif"] +
            "\nNO es un bitstream cargable en Cyclone IV.\n" + report["log_tail"][-2500:])

    def failed(self, error):
        self.status.setPlainText("Error en síntesis: " + error)

    def choose_rbf(self):
        path, _ = W.QFileDialog.getOpenFileName(
            self, "Bitstream externo para Cyclone IV", str(Path.home()),
            "Bitstream RBF (*.rbf)")
        if path:
            self.rbf_path.setText(path)
            self.staged_folder = None
            self.deploy_button.setEnabled(False)
            self.pins_ok.setChecked(False)
            self.voltage_ok.setChecked(False)
            self.clear_deploy_authorization()

    def stage(self):
        self.sync_project()
        project = self.project_provider()
        if not project:
            self.status.setPlainText("Abre un proyecto con asignaciones físicas de pines.")
            return
        try:
            home = data_dir() / "fpga-deploy"
            home.mkdir(parents=True, exist_ok=True)
            root = home / uuid.uuid4().hex
            result = cyclone_deploy.stage_external_rbf(
                project, self.rbf_path.text(), root,
                self.part.text().strip(), self.board.text().strip(),
                pins_confirmed=self.pins_ok.isChecked(),
                voltage_confirmed=self.voltage_ok.isChecked())
        except (OSError, ValueError, RuntimeError) as exc:
            self.status.setPlainText("Paquete NO preparado: " + str(exc))
            return
        self.staged_folder = result["folder"]
        self.clear_deploy_authorization()
        self.deploy_button.setEnabled(True)
        self.status.setPlainText(
            "Bitstream EXTERNO importado sin certificar.\n"
            "Paquete: " + result["folder"] +
            "\nSHA256: " + result["rbf_sha256"] +
            "\nAntes de cargar, verifica exactamente la placa y el esquema.")

    def open_staged(self):
        root = W.QFileDialog.getExistingDirectory(
            self, "Seleccionar paquete RBF de PhoenixForge", str(data_dir()))
        if not root:
            return
        try:
            record, binary = cyclone_deploy.inspect_staged(root)
            current = self.project_provider()
            if current is not None and current.project_id != record.get("project_id"):
                raise ValueError("El paquete pertenece a otro proyecto; abre el proyecto correcto.")
        except (OSError, ValueError, KeyError) as exc:
            self.status.setPlainText("Paquete inválido: " + str(exc))
            self.deploy_button.setEnabled(False)
            return
        self.staged_folder = root
        self.clear_deploy_authorization()
        self.part.setText(record["part"])
        self.board.setText(record["board"])
        self.deploy_button.setEnabled(True)
        self.status.setPlainText(
            "Paquete externo cargado: " + str(binary) +
            "\nSHA256: " + record["rbf_sha256"] +
            "\nNo se ha verificado el chip físico ni la procedencia.")

    def deploy(self):
        if self.deploy_worker and self.deploy_worker.isRunning():
            return
        if not self.staged_folder:
            self.status.setPlainText("Prepara o abre primero un paquete RBF válido.")
            return
        try:
            record, binary = cyclone_deploy.inspect_staged(self.staged_folder)
            if (record["part"] != self.part.text().strip().upper() or
                    record["board"] != self.board.text().strip()):
                raise ValueError("El chip o la placa cambiaron desde la preparación.")
            if not (self.board_ok.isChecked() and self.external_ok.isChecked()
                    and self.sram_ok.isChecked()):
                raise PermissionError("Marca las tres confirmaciones de programación.")
            cable = self.cable.currentText().strip()
            if not cable:
                raise ValueError("Selecciona un cable JTAG.")
        except (OSError, ValueError, PermissionError) as exc:
            self.status.setPlainText("Carga bloqueada: " + str(exc))
            return
        message = (
            "Se leerá JTAG y después se intentará cargar a SRAM (no Flash).\n\n"
            "Placa: " + record["board"] + "\nChip declarado: " +
            record["part"] + "\nCable: " + cable + "\nSHA256:\n" +
            record["rbf_sha256"] + "\n\n"
            "El RBF es EXTERNO y NO se puede verificar su pinout a partir del "
            "archivo. La detección JTAG tampoco distingue siempre el encapsulado. "
            "¿Confirmas que todo coincide con la placa física?")
        if W.QMessageBox.question(
                self, "Autorizar escritura SRAM Cyclone IV", message,
                W.QMessageBox.Yes | W.QMessageBox.No,
                W.QMessageBox.No) != W.QMessageBox.Yes:
            return
        self.deploy_button.setEnabled(False)
        self.clear_deploy_authorization()
        self.status.setPlainText("Volviendo a leer JTAG antes de cargar SRAM...")
        self.deploy_worker = DeploymentTask(
            self.staged_folder, cable, record["part"], self)
        self.deploy_worker.completed.connect(self.deployed)
        self.deploy_worker.failed.connect(self.deploy_failed)
        self.deploy_worker.finished.connect(lambda: self.deploy_button.setEnabled(True))
        self.deploy_worker.start()

    def deployed(self, result):
        self.status.setPlainText(
            "Comando de SRAM completado (sin Flash).\n"
            "Chip declarado: " + result["part"] +
            "\nIDCODE: " + result["jtag_idcode"] +
            "\nEl comportamiento físico del diseño NO está certificado.\n" +
            result["programmer_output"])

    def deploy_failed(self, message):
        self.status.setPlainText("Carga BLOQUEADA o fallida: " + message)
