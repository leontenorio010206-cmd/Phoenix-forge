"""PhœnixForge Hardware Studio: nonblocking discovery and explicit flashing tools."""
import subprocess
import shutil
from pathlib import Path
from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt, Signal
from app.ui.common import label, button, card
from app.hardware.discovery import list_usb_devices, added_devices
from app.hardware import arduino
from app.devices.catalog import load_profiles

EXAMPLE = """// Ejemplo para Arduino Uno (LED integrado)
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}
void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
}
"""


class HardwareTask(C.QThread):
    success = Signal(object)
    error = Signal(str)

    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.operation = operation

    def run(self):
        try:
            self.success.emit(self.operation())
        except Exception as error:
            self.error.emit(str(error))


class HardwareStudio(W.QWidget):
    """Use only approved, explicit operations on hardware; never auto-flash on attach."""
    def __init__(self):
        super().__init__()
        self.worker = None
        self.detected = []
        self.seen_once = False
        self.last_sketch_folder = None
        outer = W.QVBoxLayout(self)
        outer.setContentsMargins(20, 15, 20, 14)
        outer.setSpacing(10)
        outer.addWidget(label("Hardware Studio", "Heading"))
        outer.addWidget(label(
            "Detecta conexiones USB y COM. Prepara herramientas oficiales, "
            "programa Arduino y Raspberry Pi Pico; conserva el laboratorio HDL para FPGA.",
            "Muted", True))
        bar = W.QHBoxLayout()
        self.status = label("Sin exploración", "Muted")
        bar.addWidget(self.status, 1)
        self.refresh_button = button("↻ Detectar dispositivos", self.scan, True)
        bar.addWidget(self.refresh_button)
        outer.addLayout(bar)
        splitter = W.QSplitter(Qt.Horizontal)
        left = W.QWidget()
        left_layout = W.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(label("Hardware conectado"))
        self.list = W.QListWidget()
        self.list.currentRowChanged.connect(self.describe_device)
        left_layout.addWidget(self.list, 1)
        self.detail = W.QTextBrowser()
        self.detail.setOpenExternalLinks(True)
        self.detail.setMaximumHeight(135)
        left_layout.addWidget(self.detail)
        splitter.addWidget(left)
        self.tabs = W.QTabWidget()
        splitter.addWidget(self.tabs)
        splitter.setSizes([330, 760])
        outer.addWidget(splitter, 1)

        self._make_arduino()
        self._make_pico()
        self._make_fpga()

        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.document().setMaximumBlockCount(3000)
        self.log.setMaximumHeight(135)
        self.log.setPlaceholderText("Registros de detección, instalación, compilación y programación")
        outer.addWidget(self.log)

        self.timer = C.QTimer(self)
        self.timer.setInterval(8000)
        self.timer.timeout.connect(self.automatic_scan)
        self.timer.start()

    def _make_arduino(self):
        page = W.QWidget()
        layout = W.QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        h = W.QHBoxLayout()
        h.addWidget(label("Arduino CLI · oficial", "Heading"))
        h.addStretch()
        h.addWidget(button("Preparar CLI", self.install_cli))
        h.addWidget(button("Ver placas Arduino", self.list_boards))
        layout.addLayout(h)
        self.arduino_status = label("Arduino CLI: pendiente de detectar", "Muted", True)
        layout.addWidget(self.arduino_status)
        opts = W.QHBoxLayout()
        opts.addWidget(label("Placa / FQBN"))
        self.fqbn = W.QComboBox()
        self.fqbn.setEditable(True)
        self.fqbn.addItems(["arduino:avr:uno", "arduino:avr:nano", "arduino:avr:mega",
                            "arduino:samd:mkrzero", "arduino:mbed_rp2040:pico"])
        self.fqbn.setMinimumWidth(220)
        opts.addWidget(self.fqbn, 2)
        opts.addWidget(label("Puerto"))
        self.port = W.QComboBox()
        self.port.setEditable(True)
        self.port.addItem("Selecciona COM...")
        opts.addWidget(self.port, 1)
        layout.addLayout(opts)
        tools = W.QHBoxLayout()
        self.core = W.QComboBox()
        self.core.addItems(["arduino:avr", "arduino:samd", "arduino:mbed_rp2040"])
        tools.addWidget(self.core, 1)
        tools.addWidget(button("Instalar plataforma", self.install_core))
        self.library = W.QLineEdit()
        self.library.setPlaceholderText("Biblioteca: ArduinoJson, Servo...")
        tools.addWidget(self.library, 2)
        tools.addWidget(button("Instalar biblioteca", self.install_library))
        layout.addLayout(tools)
        layout.addWidget(label("Sketch C++ (.ino), listo para editar, compilar y enviar", "Muted"))
        self.sketch = W.QPlainTextEdit(EXAMPLE)
        if hasattr(self.sketch, "setTabStopDistance"):
            self.sketch.setTabStopDistance(32)
        else:
            self.sketch.setTabStopWidth(32)
        font = G.QFont("Consolas", 10)
        self.sketch.setFont(font)
        layout.addWidget(self.sketch, 1)
        actions = W.QHBoxLayout()
        actions.addWidget(button("Abrir .ino", self.open_ino))
        actions.addWidget(button("Guardar .ino", self.save_ino))
        actions.addStretch()
        actions.addWidget(button("Compilar sketch", self.compile_sketch))
        actions.addWidget(button("⚡ Subir al Arduino", self.upload_sketch, True))
        layout.addLayout(actions)
        layout.addWidget(label("Las bibliotecas/plataformas se descargan solo cuando lo autorizas. "
                               "Una placa desconocida necesita elegir manualmente FQBN y puerto.", "Muted", True))
        self.tabs.addTab(page, "Arduino")

    def _make_pico(self):
        page = W.QWidget()
        layout = W.QVBoxLayout(page)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.addWidget(label("Raspberry Pi Pico · RP2040 / RP2350", "Heading"))
        layout.addWidget(label(
            "Para firmware UF2: conecta la Pico manteniendo BOOTSEL y confirma "
            "que aparezca RPI-RP2. PhœnixForge copia el archivo solo cuando lo autorizas.",
            "Muted", True))
        layout.addWidget(button("Subir firmware .uf2 a Pico (BOOTSEL)", self.flash_uf2, True))
        layout.addSpacing(12)
        layout.addWidget(label("Raspberry Pi 4/5 y otros ordenadores Pi", "Heading"))
        layout.addWidget(label("No se programan como una memoria UF2. "
            "Son ordenadores Linux; el desarrollo Python/C++ es remoto mediante SSH "
            "o por una consola local. La detección USB depende de su modo gadget.", "Muted", True))
        layout.addWidget(button("Abrir documentación oficial Raspberry Pi",
                                lambda: G.QDesktopServices.openUrl(C.QUrl(
                                    "https://www.raspberrypi.com/documentation/"))))
        layout.addStretch()
        self.tabs.addTab(page, "Raspberry Pi")

    def _make_fpga(self):
        page = W.QWidget()
        layout = W.QVBoxLayout(page)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.addWidget(label("FPGA · síntesis, programación y JTAG", "Heading"))
        layout.addWidget(label(
            "Los adaptadores USB/JTAG no garantizan conocer la FPGA conectada. "
            "Selecciona el chip, placa y herramienta exactos antes de programar. "
            "PhœnixForge conserva la simulación RTL para diez perfiles; "
            "en v1.6 no escribe bitstreams arbitrarios por JTAG.", "Muted", True))
        for title, url in [
            ("openFPGALoader · placas compatibles", "https://github.com/trabucayre/openFPGALoader"),
            ("nextpnr · familias soportadas", "https://github.com/YosysHQ/nextpnr"),
            ("Arduino CLI · controladores oficiales", "https://docs.arduino.cc/arduino-cli/installation"),
        ]:
            layout.addWidget(button(title, lambda link=url:
                G.QDesktopServices.openUrl(C.QUrl(link))))
        layout.addStretch()
        self.tabs.addTab(page, "FPGA / Drivers")

    def showEvent(self, event):
        super().showEvent(event)
        self.scan()

    def automatic_scan(self):
        if self.isVisible() and self.worker is None:
            self.scan()

    def _run(self, title, operation, on_success=None):
        if self.worker is not None:
            return False
        self.status.setText(title + "…")
        task = HardwareTask(operation, self)
        self.worker = task
        task.success.connect(lambda result: self._completed(title, result, on_success))
        task.error.connect(self._failed)
        task.finished.connect(lambda: self._cleanup_worker(task))
        task.start()
        return True

    def _completed(self, title, result, callback):
        if callback:
            callback(result)
        else:
            self.log.appendPlainText(title + ": " + str(result)[-4500:])
        self.status.setText(title + " · terminado")

    def _failed(self, reason):
        self.log.appendPlainText("ERROR: " + reason[:1800])
        self.status.setText("Error en operación de hardware")
        W.QMessageBox.warning(self, "Hardware Studio", reason[:1200])

    def _cleanup_worker(self, task):
        if self.worker is task:
            self.worker = None
        task.deleteLater()

    def scan(self):
        self._run("Explorando puertos y USB", list_usb_devices, self._set_devices)

    def _set_devices(self, found):
        newcomers = added_devices(self.detected, found) if self.seen_once else []
        self.seen_once = True
        self.detected = found
        previous = self.list.currentRow()
        self.list.clear()
        for device in found:
            name = device.name + ("  •  " + device.port if device.port else "")
            item = W.QListWidgetItem(name)
            item.setData(Qt.UserRole, device)
            self.list.addItem(item)
        if found:
            self.list.setCurrentRow(max(0, min(previous, len(found)-1)))
        else:
            self.detail.setText("No se detectaron dispositivos USB/COM admitidos por el sistema.")
        ports = [d.port for d in found if d.port.upper().startswith("COM")]
        current = self.port.currentText()
        self.port.clear()
        self.port.addItems(sorted(set(ports)) or ["Selecciona COM..."])
        if current in ports:
            self.port.setCurrentText(current)
        if newcomers:
            self.log.appendPlainText("Conectados: " + ", ".join(d.name for d in newcomers)[:600])
        self.status.setText("%d interfaces detectadas · no se instaló ningún controlador" % len(found))
        self.arduino_status.setText(
            "Arduino CLI encontrado" if arduino.local_cli() else
            "Arduino CLI no instalado. Pulsa Preparar CLI para obtenerlo desde Arduino.")

    def describe_device(self, row):
        if row < 0:
            return
        dev = self.list.item(row).data(Qt.UserRole)
        self.detail.setPlainText(
            "Tipo: " + dev.kind + "\n"
            "Identificación: " + dev.confidence + "\n"
            "ID: " + dev.identity + "\n"
            "Puerto: " + (dev.port or "No identificado") + "\n"
            + dev.note)

    def _confirm(self, title, description):
        return W.QMessageBox.question(
            self, title, description, W.QMessageBox.Yes | W.QMessageBox.No,
            W.QMessageBox.No) == W.QMessageBox.Yes

    def install_cli(self):
        if not self._confirm("Instalar Arduino CLI",
            "Se descargará Arduino CLI 1.5.1 desde el repositorio OFICIAL de Arduino. "
            "Se verificará SHA-256 antes de instalar en los datos de PhœnixForge. "
            "No se instalarán controladores ni se modificarán permisos de administrador. ¿Continuar?"):
            return
        self._run("Instalando Arduino CLI verificado", arduino.install_cli)

    def list_boards(self):
        self._run("Leyendo placas de Arduino CLI", arduino.board_list, self._add_boards)

    def _add_boards(self, result):
        count = 0
        for port in result:
            if not isinstance(port, dict):
                continue
            address = (port.get("port") or {}).get("address", "")
            if address and self.port.findText(address) < 0:
                self.port.addItem(address)
            for board in port.get("matching_boards", []):
                fqbn = board.get("fqbn", "")
                if fqbn and self.fqbn.findText(fqbn) < 0:
                    self.fqbn.addItem(fqbn)
                count += 1
        self.log.appendPlainText("Arduino CLI: %d coincidencias de placa; verifica FQBN antes de subir." % count)

    def install_core(self):
        core = self.core.currentText()
        if self._confirm("Instalar plataforma", "Arduino CLI descargará e instalará la plataforma " + core +
                         " y sus dependencias. ¿Continuar?"):
            self._run("Instalando plataforma", lambda: arduino.core_install(core))

    def install_library(self):
        name = self.library.text().strip()
        if name and self._confirm("Instalar biblioteca", "Instalar la biblioteca «" + name +
                                 "» desde el índice Arduino. Algunas bibliotecas añaden código externo. ¿Continuar?"):
            self._run("Instalando biblioteca", lambda: arduino.library_install(name))

    def open_ino(self):
        path, _ = W.QFileDialog.getOpenFileName(self, "Abrir sketch Arduino",
                                               str(Path.home()), "Arduino sketch (*.ino)")
        if path:
            self.sketch.setPlainText(Path(path).read_text(encoding="utf-8"))

    def save_ino(self):
        path, _ = W.QFileDialog.getSaveFileName(self, "Guardar sketch Arduino",
                                               str(Path.home() / "PhoenixSketch.ino"), "Arduino sketch (*.ino)")
        if path:
            if not path.lower().endswith(".ino"):
                path += ".ino"
            Path(path).write_text(self.sketch.toPlainText(), encoding="utf-8")
            self.log.appendPlainText("Sketch guardado: " + path)

    def compile_sketch(self):
        fqbn = self.fqbn.currentText().strip()
        text = self.sketch.toPlainText()
        def build():
            folder = arduino.prepare_sketch(text)
            result = arduino.compile_sketch(folder, fqbn)
            return folder, result
        self._run("Compilando sketch", build, self._sketch_built)

    def _sketch_built(self, output):
        self.last_sketch_folder = output[0]
        self.log.appendPlainText("Compilación Arduino finalizada:\n" + output[1][-4000:])

    def upload_sketch(self):
        fqbn, port = self.fqbn.currentText().strip(), self.port.currentText().strip()
        if not self._confirm("CARGAR FIRMWARE AL DISPOSITIVO",
            "Vas a sobrescribir el programa de la placa conectada a " + port +
            "\nPerfil: " + fqbn + "\n\nConfirma físicamente que este es tu Arduino. "
            "El puerto y el modelo deben coincidir. ¿Continuar?"):
            return
        text = self.sketch.toPlainText()
        def flash():
            folder = arduino.prepare_sketch(text)
            compiled = arduino.compile_sketch(folder, fqbn)
            uploaded = arduino.upload_sketch(folder, fqbn, port)
            return compiled[-1000:] + "\n" + uploaded[-3000:]
        self._run("Compilando y cargando Arduino", flash)

    def flash_uf2(self):
        volume = next((d.port for d in self.detected if d.kind == "Pico UF2"), None)
        if not volume:
            W.QMessageBox.information(self, "Pico", "Conecta la placa pulsando BOOTSEL hasta ver el volumen RPI-RP2.")
            return
        path, _ = W.QFileDialog.getOpenFileName(self, "Seleccionar firmware de confianza",
                                                str(Path.home()), "Firmware Raspberry Pi Pico (*.uf2)")
        if not path:
            return
        if self._confirm("CARGAR UF2", "Se copiará " + Path(path).name + " a " + volume +
                         ". Comprueba que corresponda a tu placa RP2040/RP2350. ¿Continuar?"):
            self._run("Cargando firmware UF2", lambda: arduino.copy_uf2(path, volume))
