"""Universal FPGA wizard: read-only discovery and truthful toolchain capability report.

No automatic flash, no fabricated pinout and no vendor binaries downloaded.
"""
from pathlib import Path

from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Signal
from app.ui.common import button, label
from app.hardware import fpga, universal_fpga


class UniversalProbeTask(C.QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, cable, loader=None, parent=None):
        super().__init__(parent)
        self.cable = cable
        self.loader = loader

    def run(self):
        try:
            self.completed.emit(universal_fpga.inspect_cable(self.cable, self.loader))
        except Exception as error:
            self.failed.emit(str(error))


class UniversalPanel(W.QWidget):
    """Universal entry point; compilers remain manufacturer-specific."""
    def __init__(self, device_provider=None, parent=None):
        super().__init__(parent)
        self.device_provider = device_provider or (lambda: None)
        self.worker = None
        self.last_survey = None
        outer = W.QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        scroller = W.QScrollArea()
        scroller.setWidgetResizable(True)
        scroller.setFrameShape(W.QFrame.NoFrame)
        outer.addWidget(scroller)
        content = W.QWidget()
        scroller.setWidget(content)
        layout = W.QVBoxLayout(content)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(9)
        layout.addWidget(label("Asistente FPGA universal (experimental)", "Heading"))
        layout.addWidget(label(
            "Conecta tu FPGA y utiliza el diagnóstico JTAG para averiguar la familia "
            "cuando el chip lo permita. Verilog e Icarus son genéricos; generar "
            "un bitstream depende del fabricante y de la arquitectura.",
            "Muted", True))

        layout.addWidget(label("Paso 1 · Herramientas instaladas", "Heading"))
        self.tools_button = button("Revisar compiladores FPGA (sin conectar placa)",
                                   self.show_capabilities, True)
        layout.addWidget(self.tools_button)
        self.capabilities = W.QPlainTextEdit()
        self.capabilities.setReadOnly(True)
        self.capabilities.setMaximumHeight(195)
        layout.addWidget(self.capabilities)

        layout.addWidget(label("Paso 2 · Leer FPGA conectada (solo JTAG)", "Heading"))
        row = W.QHBoxLayout()
        self.loader = W.QLineEdit()
        self.loader.setReadOnly(True)
        self.loader.setPlaceholderText("openFPGALoader instalado o en PATH")
        self.loader.setText(C.QSettings("PhoenixForge", "FPGAStudio").value(
            "openfpgaloader", "", type=str))
        row.addWidget(self.loader, 1)
        row.addWidget(button("Seleccionar herramienta", self.choose_loader))
        layout.addLayout(row)

        row2 = W.QHBoxLayout()
        self.cable = W.QComboBox()
        self.cable.setEditable(True)
        self.cable.addItems(["", "usb-blaster", "usb-blasterII", "ft2232",
                             "cmsisdap", "dirtyjtag", "jlink"])
        self.cable.setCurrentText("")
        row2.addWidget(self.cable, 1)
        row2.addWidget(button("Sugerir por USB", self.suggest_cable))
        layout.addLayout(row2)
        layout.addWidget(label(
            "El cable USB y el chip FPGA son distintos. La sugerencia de cable "
            "requiere confirmación; nunca identifica pines o tarjeta.",
            "Muted", True))

        self.probe_button = button("Leer chip por JTAG (sin modificar)", self.scan, True)
        layout.addWidget(self.probe_button)
        self.status = W.QPlainTextEdit()
        self.status.setReadOnly(True)
        self.status.setMinimumHeight(145)
        self.status.setPlaceholderText(
            "Aquí aparecerá el resultado real del dispositivo conectado. "
            "No es necesario que conozcas el modelo para probar la lectura JTAG.")
        layout.addWidget(self.status, 1)
        layout.addWidget(label(
            "Paso 3 · Para compilar y ejecutar se requiere un backend compatible, "
            "el código de chip completo, el esquema de la placa y sus pines. "
            "El flujo integrado actual de Cyclone IV está en la pestaña contigua; "
            "otras familias todavía tienen integración física pendiente.",
            "Muted", True))
        layout.addStretch()

    def show_capabilities(self):
        tools = universal_fpga.toolchain_inventory()
        statuses = universal_fpga.capability_inventory(tools)
        lines = [
            "HERRAMIENTAS EN PATH (hallarlas no certifica el hardware):",
            *[("%s: %s" % (key, path or "no encontrada"))
              for key, path in sorted(tools.items())],
            "",
            "FAMILIAS Y ESTADO REAL DE LA INTEGRACIÓN:",
        ]
        for row in statuses:
            state = ("adaptador Cyclone IV implementado"
                     if row["integrated"] else "adaptador físico pendiente")
            tools_message = ("dependencias localizadas" if row["tools_installed"]
                             else "faltan: " + (", ".join(row["missing_tools"]) or
                                                "verifica herramientas del fabricante"))
            lines.append("%s — %s; %s. %s" %
                         (row["name"], state, tools_message, row["note"]))
        lines.append("\nNota: solo Icarus simula Verilog genérico; no fabrica "
                     "bitstreams para todos los chips.")
        self.capabilities.setPlainText("\n".join(lines))

    def choose_loader(self):
        path, _ = W.QFileDialog.getOpenFileName(
            self, "Selecciona openFPGALoader instalado", str(Path.home()),
            "openFPGALoader (openFPGALoader.exe openFPGALoader);;Todos (*)")
        if not path:
            return
        try:
            fpga.find_loader(path)
        except (OSError, ValueError) as exc:
            W.QMessageBox.warning(self, "Herramienta JTAG", str(exc))
            return
        self.loader.setText(path)
        C.QSettings("PhoenixForge", "FPGAStudio").setValue("openfpgaloader", path)

    def suggest_cable(self):
        device = self.device_provider()
        if not device:
            self.status.setPlainText(
                "Primero elige un dispositivo USB en la lista de Hardware "
                "conectado, a la izquierda. No se modificará el hardware.")
            return
        target, message = universal_fpga.suggest_cable_for_usb(
            getattr(device, "identity", ""))
        self.status.setPlainText(message)
        if target:
            self.cable.setCurrentText(target)

    def scan(self):
        if self.worker is not None and self.worker.isRunning():
            return
        cable = self.cable.currentText().strip()
        if not universal_fpga.SAFE_CABLE.fullmatch(cable):
            W.QMessageBox.warning(
                self, "Cable requerido",
                "Selecciona el tipo de cable antes de consultar el JTAG. "
                "No es posible deducirlo de cualquier conector USB.")
            return
        self.probe_button.setEnabled(False)
        self.status.setPlainText("Leyendo JTAG... sin programar ni escribir Flash.")
        self.worker = UniversalProbeTask(cable, self.loader.text().strip() or None, self)
        self.worker.completed.connect(self.scanned)
        self.worker.failed.connect(self.scan_failed)
        self.worker.finished.connect(lambda: self.probe_button.setEnabled(True))
        self.worker.start()

    def scanned(self, survey):
        self.last_survey = survey
        self.status.setPlainText(universal_fpga.describe_survey(survey))

    def scan_failed(self, message):
        self.last_survey = None
        self.status.setPlainText(
            "Error al leer el dispositivo: " + message +
            "\nVerifica drivers, energía, conexión, cable y permisos.")
