"""Visual Digital export studio: live symbols from actual HDL ports.

The SVGs preview connections; Digital's External File integration still
requires selecting the Verilog source in Digital itself.
"""
from pathlib import Path

from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt, Signal, QtSvg
from app.ui.common import label, button
from app.core.hdl import modules, ports
from app.devices.catalog import load_profiles
from app.exporters.digital_symbol import build_component_svg


class SvgPreview(W.QWidget):
    """Resolution-independent symbol preview, rendered from the exact export SVG."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = QtSvg.QSvgRenderer(self)
        self.setMinimumHeight(220)

    def set_svg(self, svg):
        self.renderer.load(C.QByteArray(svg))
        self.update()

    def paintEvent(self, event):
        painter = G.QPainter(self)
        painter.setRenderHint(G.QPainter.Antialiasing)
        painter.fillRect(self.rect(), G.QColor("#0C1624"))
        if self.renderer.isValid():
            native = self.renderer.viewBoxF()
            if native.width() and native.height():
                ratio = min((self.width()-12)/native.width(), (self.height()-12)/native.height())
                target_w, target_h = native.width()*ratio, native.height()*ratio
                target = C.QRectF((self.width()-target_w)/2, (self.height()-target_h)/2,
                                  target_w, target_h)
                self.renderer.render(painter, target)
        painter.end()


class DigitalExportPanel(W.QWidget):
    export_requested = Signal(str)
    virtual_requested = Signal()

    def __init__(self):
        super().__init__()
        self.project = None
        self.pinout = []
        self.last_path = None
        container = W.QVBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)
        scroller = W.QScrollArea()
        scroller.setWidgetResizable(True)
        scroller.setFrameShape(W.QFrame.NoFrame)
        container.addWidget(scroller)
        body = W.QWidget()
        scroller.setWidget(body)
        root = W.QVBoxLayout(body)
        root.setContentsMargins(24, 20, 24, 18)
        root.setSpacing(12)

        eyebrow = label("PHŒNIXFORGE  /  EXPORTACIÓN HDL", "Eyebrow")
        root.addWidget(eyebrow)
        root.addWidget(label("Componente para simulador", "Heading"))
        root.addWidget(label("Visualiza tus pines HDL, prepara un componente externo de Verilog "
                             "y llévalo al simulador Digital.", "Muted", True))

        select = W.QHBoxLayout()
        select.addWidget(label("Módulo principal"))
        self.top = W.QComboBox()
        self.top.setMinimumWidth(190)
        self.top.currentTextChanged.connect(self.refresh)
        select.addWidget(self.top, 1)
        self.profile = label("FPGA", "Muted")
        select.addWidget(self.profile)
        root.addLayout(select)

        upper = W.QHBoxLayout()
        upper.setSpacing(12)
        previews = W.QVBoxLayout()
        previews.setSpacing(10)
        box1 = self.panel("Vista del componente")
        self.symbol = SvgPreview()
        box1.layout().addWidget(self.symbol)
        previews.addWidget(box1)
        box2 = self.panel("Vista previa de conexiones · esquema ilustrativo")
        self.wiring = SvgPreview()
        box2.layout().addWidget(self.wiring)
        previews.addWidget(box2)
        upper.addLayout(previews, 4)

        right = self.panel("Exportación")
        right.setMinimumWidth(245)
        side = right.layout()
        self.info = label("Cargando proyecto…", "Muted", True)
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        side.addWidget(self.info)
        side.addSpacing(5)
        self.export_button = button("⬇  Exportar componente ZIP", self.request_export, True)
        side.addWidget(self.export_button)
        side.addWidget(button("▶  Probar entradas y salidas", self.virtual_requested.emit))
        self.folder_button = button("▣  Abrir carpeta exportada", self.open_folder)
        self.folder_button.setEnabled(False)
        side.addWidget(self.folder_button)
        side.addStretch()
        side.addWidget(label("El SVG es una vista del diseño. Digital utiliza component.v mediante "
                             "External File; el símbolo no se instala automáticamente.", "Muted", True))
        upper.addWidget(right, 2)
        root.addLayout(upper)

        self.tabs = W.QTabWidget()
        self.pin_table = W.QTableWidget(0, 4)
        self.pin_table.setHorizontalHeaderLabels(["Señal", "Dirección", "Bits", "Pin físico"])
        self.pin_table.horizontalHeader().setStretchLastSection(True)
        self.pin_table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.pin_table.setSelectionBehavior(W.QAbstractItemView.SelectRows)
        self.pin_table.setAlternatingRowColors(True)
        self.tabs.addTab(self.pin_table, "Puertos")
        docs = W.QTextBrowser()
        docs.setOpenExternalLinks(True)
        docs.setHtml(
            "<h3>Importación en Digital</h3>"
            "<p>1. Exporta y descomprime el ZIP. 2. En Digital, añade <b>External File</b> "
            "y selecciona <b>component.v</b> como Verilog. 3. Configura Icarus, comprueba "
            "los puertos y conecta los pines del circuito.</p>"
            "<p><b>symbol.svg</b> es la ilustración del símbolo, y <b>connections.svg</b> "
            "un diagrama de referencia con terminales de entrada y salida. "
            "No es un archivo .dig ni un plugin de Tinkercad.</p>"
            "<p>Los diez perfiles comparten simulación lógica RTL: no hay emulación "
            "de pines eléctricos, retardos ni bitstream físico.</p>")
        self.tabs.addTab(docs, "Documentación")
        self.status = label("Selecciona un proyecto Verilog.", "Muted", True)
        status_page = W.QWidget()
        status_box = W.QVBoxLayout(status_page)
        status_box.addWidget(self.status)
        status_box.addStretch(1)
        self.tabs.addTab(status_page, "Compatibilidad")
        self.tabs.setMinimumHeight(180)
        root.addWidget(self.tabs)

    @staticmethod
    def panel(title):
        frame = W.QFrame()
        frame.setObjectName("Card")
        layout = W.QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(9)
        heading = label(title)
        heading.setStyleSheet("font-weight: 700; color: #cce6ff;")
        layout.addWidget(heading)
        return frame

    def bind_project(self, project, keep_top=False):
        self.project = project
        selected = self.top.currentText() if keep_top else project.simulation.get("top", "")
        choices = [m["name"] for m in modules(project.files) if not m["testbench_hint"]]
        self.top.blockSignals(True)
        self.top.clear()
        self.top.addItems(choices)
        if selected in choices:
            self.top.setCurrentText(selected)
        self.top.blockSignals(False)
        profile = load_profiles().get(project.device, {})
        self.profile.setText(profile.get("name", project.device))
        self.refresh()

    def refresh(self, unused=None):
        if self.project is None:
            return
        name = self.top.currentText()
        try:
            found = [m for m in modules(self.project.files) if m["name"] == name]
            if len(found) != 1:
                raise ValueError("Selecciona un módulo Verilog principal único.")
            pinout = ports(self.project.files[found[0]["file"]], name)
            if any(p["direction"] not in ("input", "output") for p in pinout):
                raise ValueError("Los puertos bidireccionales inout aún no son exportables.")
            if any(p["width"] > 32 for p in pinout):
                raise ValueError("Bus HDL demasiado ancho: límite actual de 32 bits.")
            self.pinout = pinout
            self.symbol.set_svg(build_component_svg(name, pinout))
            self.wiring.set_svg(build_component_svg(name, pinout, connections=True))
            self.info.setText(
                "Formato: Digital External File\n\n"
                "Motor: Icarus Verilog\n\n"
                "Módulo: " + name + "\n\n"
                "Puertos: " + str(len(pinout)) + "\n\n"
                "Compatibilidad: RTL funcional")
            self.status.setText("Vista generada desde los puertos HDL de " + name +
                                ". Revisa que el módulo y las fuentes sean compatibles con Digital.")
            self.export_button.setEnabled(True)
            self.populate_pins()
        except (ValueError, KeyError) as error:
            self.pinout = []
            self.symbol.set_svg(b"")
            self.wiring.set_svg(b"")
            self.pin_table.setRowCount(0)
            self.info.setText("Exportación no disponible:\n" + str(error))
            self.status.setText(str(error))
            self.export_button.setEnabled(False)

    def populate_pins(self):
        self.pin_table.setRowCount(len(self.pinout))
        for row, pin in enumerate(self.pinout):
            physical = self.project.pins.get(pin["name"], "Sin asignar")
            values = (pin["name"], "Entrada" if pin["direction"] == "input" else "Salida",
                      str(pin["width"]), physical)
            for col, value in enumerate(values):
                item = W.QTableWidgetItem(value)
                if col == 1:
                    item.setForeground(G.QColor("#65C1FF" if pin["direction"] == "input" else "#FFC18A"))
                self.pin_table.setItem(row, col, item)

    def request_export(self):
        if self.pinout and self.top.currentText():
            self.export_requested.emit(self.top.currentText())

    def set_last_export(self, path):
        self.last_path = Path(path)
        self.folder_button.setEnabled(True)

    def open_folder(self):
        if self.last_path and self.last_path.parent.is_dir():
            G.QDesktopServices.openUrl(C.QUrl.fromLocalFile(str(self.last_path.parent)))
