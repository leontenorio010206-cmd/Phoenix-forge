"""PhœnixForge Hardware Studio: nonblocking discovery and explicit flashing tools."""
import subprocess
import shutil
from pathlib import Path
from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt, Signal
from app.ui.common import label, button, card
from app.hardware.discovery import list_usb_devices, added_devices
from app.hardware import arduino, fpga
from app.hardware.arduino_catalog import (model_shortcuts, merge_catalog,
    BASIC_PACK, CORE_HEADERS, EXAMPLES, DEFAULT_CORES)
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
        self.model_catalog = model_shortcuts()
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
        self._make_arduino_catalog()

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
        self.fqbn.addItems([fqbn for name, fqbn, core in model_shortcuts()])
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
        self.core.addItems(list(DEFAULT_CORES))
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
        outer = W.QVBoxLayout(page)
        outer.setContentsMargins(4, 4, 4, 4)
        scroll = W.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(W.QFrame.NoFrame)
        outer.addWidget(scroll)
        body = W.QWidget()
        scroll.setWidget(body)
        layout = W.QVBoxLayout(body)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(9)
        layout.addWidget(label("FPGA / JTAG Hardware Studio", "Heading"))
        layout.addWidget(label(
            "Intel/Altera, Xilinx/AMD, Gowin, Lattice, Efinix, Anlogic y más. "
            "También placas económicas o poco conocidas: lo que cuenta es el chip, "
            "cable, driver y herramienta compatibles, no el país de fabricación.",
            "Muted", True))
        layout.addWidget(label(
            "USB identifica principalmente el PROGRAMADOR; --detect puede identificar "
            "un chip accesible por JTAG. Nunca afirma reconocer todas las FPGA.",
            "Muted", True))

        layout.addWidget(label("Diagnóstico de driver de la interfaz USB seleccionada", "Heading"))
        driver_actions = W.QHBoxLayout()
        driver_actions.addWidget(button("Diagnosticar driver Windows", self.fpga_driver_diagnose, True))
        driver_actions.addWidget(button("Abrir guía oficial de drivers",
            lambda: G.QDesktopServices.openUrl(C.QUrl(
                "https://trabucayre.github.io/openFPGALoader/guide/install.html"))))
        layout.addLayout(driver_actions)
        self.fpga_driver_text = W.QPlainTextEdit()
        self.fpga_driver_text.setReadOnly(True)
        self.fpga_driver_text.setMaximumHeight(145)
        self.fpga_driver_text.setPlaceholderText(
            "Selecciona una interfaz USB en Hardware conectado y pulsa Diagnosticar. "
            "No se reemplazarán drivers ni interfaces serie.")
        layout.addWidget(self.fpga_driver_text)

        layout.addWidget(label("openFPGALoader · herramienta externa", "Heading"))
        line = W.QHBoxLayout()
        self.fpga_tool = W.QLineEdit()
        self.fpga_tool.setReadOnly(True)
        self.fpga_tool.setPlaceholderText("openFPGALoader.exe — elegir instalación")
        line.addWidget(self.fpga_tool, 1)
        line.addWidget(button("Seleccionar EXE", self.fpga_choose_tool))
        layout.addLayout(line)
        settings = C.QSettings("PhoenixForge", "FPGAStudio")
        self.fpga_tool.setText(settings.value("openfpgaloader", "", type=str))
        layout.addWidget(button("Consultar todas las placas, cables y FPGA soportados",
                                self.fpga_read_catalog, True))
        self.fpga_catalog_text = W.QPlainTextEdit()
        self.fpga_catalog_text.setReadOnly(True)
        self.fpga_catalog_text.setMaximumHeight(170)
        self.fpga_catalog_text.setPlaceholderText(
            "El catálogo completo se consulta desde tu versión instalada de openFPGALoader.")
        layout.addWidget(self.fpga_catalog_text)

        selector = W.QHBoxLayout()
        self.fpga_via = W.QComboBox()
        self.fpga_via.addItems(["Placa (-b)", "Cable (-c)"])
        self.fpga_via.currentIndexChanged.connect(self.fpga_change_via)
        selector.addWidget(self.fpga_via)
        self.fpga_target = W.QComboBox()
        self.fpga_target.setEditable(True)
        self.fpga_target.setMinimumWidth(180)
        self.fpga_target.addItems([entry[1] for entry in fpga.examples()])
        selector.addWidget(self.fpga_target, 1)
        selector.addWidget(button("Detectar chip por JTAG", self.fpga_probe))
        layout.addLayout(selector)
        layout.addWidget(label(
            "Ejemplos: Sipeed Tang Nano, QMTech Cyclone, iCEBreaker, ULX3S, Arty. "
            "Para otra placa china, rusa o genérica escribe su identificador oficial "
            "tras comprobarlo en --list-boards. Para un cable sin perfil de placa usa -c.",
            "Muted", True))

        layout.addWidget(label("Cargar bitstream (solo si conoces la placa exacta)", "Heading"))
        firmware = W.QHBoxLayout()
        self.fpga_firmware = W.QLineEdit()
        self.fpga_firmware.setReadOnly(True)
        self.fpga_firmware.setPlaceholderText("Selecciona bitstream válido para el FPGA físico")
        firmware.addWidget(self.fpga_firmware, 1)
        firmware.addWidget(button("Elegir bitstream", self.fpga_choose_bitstream))
        layout.addLayout(firmware)
        target_type = W.QHBoxLayout()
        self.fpga_storage = W.QComboBox()
        self.fpga_storage.addItems(["SRAM — temporal", "FLASH — persistente"])
        target_type.addWidget(self.fpga_storage)
        target_type.addWidget(button("Programar FPGA (confirmación obligatoria)",
                                      self.fpga_program, True))
        layout.addLayout(target_type)
        layout.addWidget(label(
            "No sintetiza ni crea bitstreams por sí solo. Necesitas el archivo "
            "generado por un toolchain compatible. La escritura FLASH puede "
            "sobrescribir arranque/configuración y exige doble confirmación.",
            "Muted", True))
        links = W.QHBoxLayout()
        for title, url in [
            ("openFPGALoader", "https://github.com/trabucayre/openFPGALoader"),
            ("nextpnr", "https://github.com/YosysHQ/nextpnr"),
            ("Intel/AMD", "https://trabucayre.github.io/openFPGALoader/compatibility/fpga.html"),
        ]:
            links.addWidget(button(title, lambda link=url:
                G.QDesktopServices.openUrl(C.QUrl(link))))
        layout.addLayout(links)
        layout.addStretch()
        self.tabs.addTab(page, "FPGA / Drivers")

    def fpga_change_via(self, index):
        self.fpga_target.clear()
        if index == 0:
            self.fpga_target.addItems([entry[1] for entry in fpga.examples()])
        else:
            # Popular supported cable types, to be verified with --list-cables.
            self.fpga_target.addItems(["usb-blaster", "ft2232", "cmsisdap"])

    def fpga_choose_tool(self):
        path, _ = W.QFileDialog.getOpenFileName(self, "Seleccionar openFPGALoader",
                str(Path.home()), "Herramienta FPGA (openFPGALoader.exe)")
        if not path:
            return
        try:
            fpga.find_loader(path)
        except (OSError, ValueError) as error:
            W.QMessageBox.warning(self, "Herramienta FPGA", str(error))
            return
        self.fpga_tool.setText(path)
        C.QSettings("PhoenixForge", "FPGAStudio").setValue("openfpgaloader", path)

    def fpga_choose_bitstream(self):
        path, _ = W.QFileDialog.getOpenFileName(self, "Bitstream de tu FPGA",
            str(Path.home()), "Bitstream FPGA (*.bit *.bin *.fs *.svf *.jed *.pof *.rbf *.hex *.mcs)")
        if path:
            self.fpga_firmware.setText(path)

    def fpga_driver_diagnose(self):
        selected = self.list.currentItem()
        if selected is None:
            W.QMessageBox.information(self, "Driver FPGA",
                                      "Selecciona un dispositivo USB de la lista de la izquierda.")
            return
        dev = selected.data(Qt.UserRole)
        hint, note = fpga.cable_hint(dev.name, dev.identity)
        if hint == "No identificado":
            self.fpga_driver_text.setPlainText(
                "No hay coincidencia segura para FPGA. " + note +
                "\nSe puede diagnosticar el driver USB sin instalar nada.")
        self._run("Diagnosticando driver FPGA",
                  lambda: fpga.driver_report(dev.identity), self._fpga_driver_result)

    def _fpga_driver_result(self, data):
        lines = [
            "Adaptador: " + data["probe"],
            "Nombre Windows: " + data["device_name"],
            "Driver / servicio: " + data["service"],
            "Proveedor: " + data["provider"],
            "Versión: " + data["version"],
            "INF: " + data["inf"],
            "Estado: " + data["windows_status"],
            "Código de problema: " + str(data["problem_code"]),
            "Notas: " + data["description"],
            *["AVISO: " + text for text in data["alerts"]],
            data["driver_installation"]
        ]
        self.fpga_driver_text.setPlainText("\n".join(lines))

    def fpga_read_catalog(self):
        path = self.fpga_tool.text().strip() or None
        self._run("Consultando openFPGALoader",
                  lambda: fpga.catalog(path), self._fpga_catalog_result)

    def _fpga_catalog_result(self, catalogs):
        self.fpga_catalog_text.setPlainText("\n\n".join(
            ("=== " + name.upper() + " ===\n" + content)
            for name, content in catalogs.items()))
        self.log.appendPlainText("Catálogo openFPGALoader actualizado desde el ejecutable elegido.")

    def fpga_probe(self):
        target = self.fpga_target.currentText().strip()
        via = "board" if self.fpga_via.currentIndex() == 0 else "cable"
        if not self._confirm("Exploración JTAG FPGA",
            "Se accederá al bus JTAG conectado mediante openFPGALoader.\n"
            "Placa/cable: " + target + "\nNo instalará drivers ni escribirá bitstream."
            "\nComprueba que otros programas no estén usando el cable. ¿Continuar?"):
            return
        self._run("Consultando ID JTAG",
                  lambda: fpga.probe_target(target, via, self.fpga_tool.text().strip() or None),
                  lambda result: self.fpga_catalog_text.setPlainText(
                      "Detección JTAG:\n" + str(result)[-10000:]))

    def fpga_program(self):
        target = self.fpga_target.currentText().strip()
        firmware = self.fpga_firmware.text().strip()
        via = "board" if self.fpga_via.currentIndex() == 0 else "cable"
        flash = self.fpga_storage.currentIndex() == 1
        if not target or not firmware:
            W.QMessageBox.warning(self, "Programar FPGA",
                "Elige primero una placa/cable y un bitstream compatible.")
            return
        warning = ("FLASH PERMANENTE" if flash else "SRAM TEMPORAL")
        detail = ("Dispositivo: " + target + " (" + via + ")\n"
                  "Archivo: " + firmware + "\nDestino: " + warning +
                  "\n\nUna selección equivocada puede inutilizar la configuración "
                  "de la FPGA. Debes verificar chip, voltajes, cable y bitstream.")
        if not self._confirm("GRABAR HARDWARE FPGA", detail + "\n\n¿Continuar?"):
            return
        if flash and not self._confirm("CONFIRMAR FLASH PERMANENTE",
            "La memoria no volátil puede sobrescribirse. ¿Confirmas la escritura FLASH?"):
            return
        self._run("Programando FPGA " + warning, lambda:
            fpga.program_target(target, firmware, via, flash,
                               self.fpga_tool.text().strip() or None),
            lambda result: self.fpga_catalog_text.setPlainText(
                "Resultado de programación:\n" + str(result)[-10000:]))

    def _make_arduino_catalog(self):
        page = W.QWidget()
        outer = W.QVBoxLayout(page)
        outer.setContentsMargins(10, 10, 10, 10)
        scroller = W.QScrollArea()
        scroller.setWidgetResizable(True)
        outer.addWidget(scroller)
        surface = W.QWidget()
        scroller.setWidget(surface)
        layout = W.QVBoxLayout(surface)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(label("Modelos y bibliotecas Arduino", "Heading"))
        layout.addWidget(label(
            "Perfiles iniciales incluidos; los modelos adicionales los proporciona Arduino CLI "
            "según las plataformas instaladas. Un adaptador USB no certifica la autenticidad.",
            "Muted", True))
        line = W.QHBoxLayout()
        self.model_filter = W.QLineEdit()
        self.model_filter.setPlaceholderText("Buscar Uno, Nano, Mega, Portenta, MKR, FQBN...")
        self.model_filter.textChanged.connect(self.filter_models)
        line.addWidget(self.model_filter, 1)
        line.addWidget(button("Leer catálogo Arduino CLI", self.read_model_catalog, True))
        layout.addLayout(line)
        self.models = W.QTreeWidget()
        self.models.setHeaderLabels(["Modelo", "FQBN", "Plataforma"])
        self.models.setMinimumHeight(170)
        self.models.itemDoubleClicked.connect(self.choose_model)
        layout.addWidget(self.models)
        layout.addWidget(label("Doble clic en el modelo para seleccionar FQBN y plataforma.", "Muted"))
        layout.addSpacing(9)
        layout.addWidget(label("Bibliotecas básicas", "Heading"))
        layout.addWidget(label(
            "Arduino.h y estas cabeceras, cuando las soporte tu placa, se proporcionan "
            "al instalar su plataforma: " + ", ".join(CORE_HEADERS) + ".",
            "Muted", True))
        layout.addWidget(label(
            "Paquete adicional recomendado (instalación opcional): " + ", ".join(BASIC_PACK),
            "Muted", True))
        buttons = W.QHBoxLayout()
        buttons.addWidget(button("Instalar paquete básico", self.install_basics, True))
        buttons.addWidget(button("Actualizar bibliotecas", self.upgrade_libraries))
        buttons.addWidget(button("Ver instaladas", self.list_libraries))
        layout.addLayout(buttons)
        libtools = W.QHBoxLayout()
        self.catalog_search = W.QLineEdit()
        self.catalog_search.setPlaceholderText("Buscar biblioteca actual en Arduino Library Manager")
        self.catalog_search.returnPressed.connect(self.search_library)
        libtools.addWidget(self.catalog_search, 1)
        libtools.addWidget(button("Buscar en línea", self.search_library))
        libtools.addWidget(button("Instalar nombre exacto", self.install_catalog_library))
        layout.addLayout(libtools)
        self.library_results = W.QPlainTextEdit()
        self.library_results.setReadOnly(True)
        self.library_results.setMaximumHeight(140)
        layout.addWidget(self.library_results)
        layout.addSpacing(8)
        layout.addWidget(label("Ejemplos básicos integrados", "Heading"))
        demos = W.QHBoxLayout()
        self.example = W.QComboBox()
        self.example.addItems(list(EXAMPLES))
        demos.addWidget(self.example, 1)
        demos.addWidget(button("Enviar al editor .ino", self.apply_example))
        layout.addLayout(demos)
        layout.addWidget(label(
            "El paquete inicial instala bibliotecas a través de Arduino CLI con tu permiso. "
            "No se distribuye una copia universal de código de terceros ni se cambian "
            "controladores USB automáticamente.", "Muted", True))
        layout.addStretch()
        self.tabs.addTab(page, "Modelos y librerías")
        self.filter_models("")

    def filter_models(self, term):
        query = term.strip().casefold()
        self.models.clear()
        count = 0
        for name, fqbn, core in self.model_catalog:
            if not query or query in name.casefold() or query in fqbn.casefold():
                row = W.QTreeWidgetItem(self.models, [name, fqbn, core])
                row.setData(0, Qt.UserRole, fqbn)
                count += 1
        if count:
            self.models.setCurrentItem(self.models.topLevelItem(0))

    def choose_model(self, item, column=0):
        fqbn, core = item.text(1), item.text(2)
        self.fqbn.setCurrentText(fqbn)
        if self.core.findText(core) < 0:
            self.core.addItem(core)
        self.core.setCurrentText(core)
        self.tabs.setCurrentIndex(0)
        self.log.appendPlainText("Placa seleccionada: " + item.text(0) + " / " + fqbn +
                                 " (revisa el hardware físico antes de subir).")

    def read_model_catalog(self):
        self._run("Leyendo modelos de plataformas instaladas", arduino.board_listall,
                  self._got_model_catalog)

    def _got_model_catalog(self, models):
        self.model_catalog = models
        self.filter_models(self.model_filter.text())
        for name, fqbn, core in models:
            if self.fqbn.findText(fqbn) < 0:
                self.fqbn.addItem(fqbn)
            if self.core.findText(core) < 0:
                self.core.addItem(core)
        self.log.appendPlainText("%d modelos disponibles (atajos + plataformas instaladas)." % len(models))

    def install_basics(self):
        description = (
            "Se consultará el índice de Arduino Library Manager y se intentarán instalar "
            "las bibliotecas recomendadas:\n\n" + ", ".join(BASIC_PACK) +
            "\n\nLas dependencias se instalan según el gestor. Puede usar Internet "
            "y ejecutar herramientas externas. ¿Autorizar instalación?")
        if self._confirm("Instalar bibliotecas básicas", description):
            self._run("Instalando paquete básico", arduino.install_starter_pack,
                      self._basics_installed)

    def _basics_installed(self, result):
        names = result.get("installed_or_present", [])
        failed = result.get("failed", [])
        self.library_results.setPlainText(
            "Instaladas o presentes:\n" + "\n".join(names) +
            "\n\nNo instaladas:\n" +
            ("\n".join(name + ": " + error for name, error in failed) if failed else "Ninguna"))
        self.log.appendPlainText("Paquete básico: %d listas, %d fallidas." %
                                 (len(names), len(failed)))

    def upgrade_libraries(self):
        if self._confirm("Actualizar bibliotecas",
            "Arduino CLI comprobará versiones actuales en el índice oficial e instalará "
            "las últimas versiones compatibles según el gestor. Algunas actualizaciones "
            "pueden romper proyectos previos. ¿Continuar?"):
            self._run("Actualizando bibliotecas Arduino", arduino.upgrade_libraries,
                      lambda result: self.library_results.setPlainText(str(result)[-9000:]))

    def list_libraries(self):
        self._run("Leyendo bibliotecas instaladas", arduino.library_list,
                  self._show_libraries)

    def _show_libraries(self, items):
        names = []
        for item in items:
            if not isinstance(item, dict):
                continue
            library = item.get("library", item)
            name = library.get("name", "") if isinstance(library, dict) else ""
            version = library.get("version", "") if isinstance(library, dict) else ""
            if name:
                names.append(name + (" " + str(version) if version else ""))
        self.library_results.setPlainText(
            "\n".join(names[:200]) or "No hay bibliotecas listadas. Instala una plataforma primero.")

    def search_library(self):
        name = self.catalog_search.text().strip()
        if name:
            self._run("Buscando bibliotecas", lambda: arduino.library_search(name),
                      lambda response: self.library_results.setPlainText(str(response)[-9000:]))

    def install_catalog_library(self):
        name = self.catalog_search.text().strip()
        if not name:
            return
        if self._confirm("Instalar biblioteca Arduino",
            "Descargar e instalar desde Arduino Library Manager la biblioteca «" + name +
            "» y sus dependencias. Confirma el nombre exacto antes de instalar. ¿Continuar?"):
            self._run("Instalando biblioteca", lambda: arduino.library_install(name),
                      lambda response: self.library_results.setPlainText(str(response)[-9000:]))

    def apply_example(self):
        name = self.example.currentText()
        if name not in EXAMPLES:
            return
        if self.sketch.toPlainText().strip() and not self._confirm(
            "Cambiar sketch", "Se sustituirá el texto del editor por el ejemplo " + name +
            ". Los cambios no guardados se perderán. ¿Continuar?"):
            return
        self.sketch.setPlainText(EXAMPLES[name])
        self.tabs.setCurrentIndex(0)

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
            "Origen Arduino: " + dev.origin + "\n"
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
