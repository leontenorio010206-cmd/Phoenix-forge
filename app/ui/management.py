import html
import json
from pathlib import Path
from app.ui.qt import QtCore as C, QtWidgets as W, Qt, Signal
from app.ui.common import label, button
from app.devices.catalog import load_profiles
from app.ui.virtual_bench import VirtualFPGABench
from app.plugins.manager import PluginManager
from app.utils.paths import data_dir, bundled_icarus


class DevicePanel(W.QWidget):
    device_selected = Signal(str)
    pins_changed = Signal(dict)
    demo_requested = Signal(str)
    simulate_requested = Signal(str)

    def __init__(self, project_provider, settings_provider):
        super().__init__()
        self.profiles = load_profiles()
        outer = W.QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        self.tabs = W.QTabWidget()
        outer.addWidget(self.tabs)
        catalog = W.QWidget()
        layout = W.QVBoxLayout(catalog)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.addWidget(label("Administrador de FPGA", "Heading"))
        layout.addWidget(label("10 perfiles · la simulación RTL es independiente del dispositivo físico.", "Muted", True))
        split = W.QSplitter(Qt.Horizontal)
        self.list = W.QListWidget()
        for key, profile in self.profiles.items():
            item = W.QListWidgetItem(profile["name"])
            item.setData(Qt.UserRole, key)
            self.list.addItem(item)
        self.details = W.QTextBrowser()
        self.details.setOpenExternalLinks(True)
        self.list.currentRowChanged.connect(self.show_profile)
        split.addWidget(self.list); split.addWidget(self.details)
        split.setSizes([320, 650])
        layout.addWidget(split, 3)
        layout.addWidget(button("Usar perfil seleccionado en el proyecto", self.select, True))
        actions = W.QHBoxLayout()
        actions.addWidget(button("Crear demo RTL para esta FPGA", self.demo))
        actions.addWidget(button("Simular proyecto con este perfil", self.simulate))
        layout.addLayout(actions)
        layout.addWidget(label("Los diez perfiles usan simulación funcional RTL con Icarus. "
                               "Esto no emula el silicio ni verifica tiempos, recursos o programación física.", "Muted", True))
        layout.addWidget(label("Asignaciones de pines · metadatos del proyecto; sin validación eléctrica", "Muted"))
        self.pins = W.QTableWidget(0, 2)
        self.pins.setHorizontalHeaderLabels(["Puerto HDL", "Pin físico (texto)"])
        self.pins.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pins, 1)
        row = W.QHBoxLayout()
        row.addWidget(button("+ Asignación", lambda: self.pins.insertRow(self.pins.rowCount())))
        row.addWidget(button("Eliminar fila", self.remove_pin))
        row.addWidget(button("Aplicar pines", self.apply_pins))
        layout.addLayout(row)
        self.list.setCurrentRow(0)
        self.bench = VirtualFPGABench(project_provider, settings_provider)
        self.tabs.addTab(catalog, "Catálogo FPGA")
        self.tabs.addTab(self.bench, "FPGA virtual · E/S")

    def show_profile(self, index):
        item = self.list.item(index)
        if not item:
            return
        p = self.profiles[item.data(Qt.UserRole)]
        text = "<h2>%s</h2><p>%s · %s</p>" % (html.escape(p["name"]), html.escape(p["manufacturer"]), "Perfil general de familia" if p["scope"] == "family" else "Dispositivo identificado")
        text += "<p style='color:#8ec7ee'>● Perfil informativo</p><p style='color:#7ce0b3'>● Simulación lógica RTL compatible</p>"
        text += "<p style='color:#8091a8'>○ Síntesis sin verificar<br>○ Programación física sin verificar</p>"
        for heading, field in (("Recursos documentados", "resources"), ("Restricciones", "restrictions")):
            text += "<h3>%s</h3><ul>%s</ul>" % (heading, "".join("<li>%s</li>" % html.escape(s) for s in p[field]))
        text += "<p>" + html.escape(p["simulation_scope"]) + "</p><h3>Fuentes</h3>"
        for source in p["sources"]:
            text += '<p><a style="color:#efb367" href="%s">%s</a></p>' % (html.escape(source, quote=True), html.escape(source))
        self.details.setHtml(text)

    def select(self):
        if self.list.currentItem():
            self.device_selected.emit(self.list.currentItem().data(Qt.UserRole))

    def demo(self):
        if self.list.currentItem():
            self.demo_requested.emit(self.list.currentItem().data(Qt.UserRole))

    def simulate(self):
        if self.list.currentItem():
            self.simulate_requested.emit(self.list.currentItem().data(Qt.UserRole))

    def bind(self, project):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == project.device:
                self.list.setCurrentRow(i)
        self.bench.bind_project(project)
        self.pins.setRowCount(len(project.pins))
        for row, (name, pin) in enumerate(project.pins.items()):
            self.pins.setItem(row, 0, W.QTableWidgetItem(name))
            self.pins.setItem(row, 1, W.QTableWidgetItem(pin))

    def remove_pin(self):
        if self.pins.currentRow() >= 0:
            self.pins.removeRow(self.pins.currentRow())

    def apply_pins(self):
        values = {}
        for row in range(self.pins.rowCount()):
            items = [self.pins.item(row, c) for c in (0, 1)]
            if not all(items) or not all(item.text().strip() for item in items):
                W.QMessageBox.warning(self, "Pines", "Complete ambas columnas o elimine la fila vacía.")
                return
            name, pin = [item.text().strip() for item in items]
            if name in values:
                W.QMessageBox.warning(self, "Pines", "Puerto duplicado: " + name)
                return
            values[name] = pin
        self.pins_changed.emit(values)


class PluginPanel(W.QWidget):
    def __init__(self, project_provider):
        super().__init__()
        self.manager = PluginManager()
        self.project_provider = project_provider
        self.infos = []
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.addWidget(label("Plugins y extensiones", "Heading"))
        layout.addWidget(label("SDK API 1 · descubrir manifiestos no ejecuta código. La carga siempre requiere aceptación.", "Muted", True))
        row = W.QHBoxLayout()
        self.path = W.QLineEdit(str(data_dir() / "plugins"))
        row.addWidget(self.path, 1)
        row.addWidget(button("Carpeta…", self.choose))
        row.addWidget(button("Descubrir", self.discover))
        layout.addLayout(row)
        self.table = W.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID / nombre", "Versión", "Estado", "Detalle"])
        self.table.setSelectionBehavior(W.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(W.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        row2 = W.QHBoxLayout()
        row2.addWidget(button("Cargar seleccionado", self.load_selected, True))
        row2.addWidget(button("Descargar seleccionado", self.unload_selected))
        row2.addWidget(button("Ejecutar herramienta HDL", self.execute_tool))
        layout.addLayout(row2)
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(190)
        layout.addWidget(self.log)
        self.discover()

    def choose(self):
        path = W.QFileDialog.getExistingDirectory(self, "Carpeta que contiene los plugins")
        if path:
            self.path.setText(path)
            self.discover()

    def discover(self):
        self.infos = self.manager.discover(self.path.text())
        self.table.setRowCount(len(self.infos))
        for i, info in enumerate(self.infos):
            m = info.manifest
            status = "Cargado" if m.get("id") in self.manager.loaded else "Compatible · sin cargar" if info.compatible else "Incompatible"
            for j, text in enumerate((m.get("id", "?"), m.get("version", "?"), status, info.error or m.get("description", ""))):
                self.table.setItem(i, j, W.QTableWidgetItem(str(text)))
        self.table.resizeColumnsToContents()

    def selected(self):
        row = self.table.currentRow()
        return self.infos[row] if 0 <= row < len(self.infos) else None

    def load_selected(self):
        info = self.selected()
        if not info:
            return
        if not info.compatible:
            W.QMessageBox.warning(self, "Plugin incompatible", info.error)
            return
        message = "Este plugin ejecutará código Python con sus permisos y podrá acceder a archivos.\n\n%s\n%s\n\n¿Confía en el código de esta carpeta?" % (info.manifest["id"], info.directory)
        if W.QMessageBox.question(self, "Código de terceros", message, W.QMessageBox.Yes | W.QMessageBox.No, W.QMessageBox.No) != W.QMessageBox.Yes:
            return
        try:
            self.manager.load(info, trusted=True)
            self.log.appendPlainText("Cargado: " + info.manifest["id"])
        except Exception as error:
            self.log.appendPlainText("ERROR: " + str(error))
        self.discover()

    def unload_selected(self):
        info = self.selected()
        if info and info.manifest.get("id") in self.manager.loaded:
            try:
                self.manager.unload(info.manifest["id"])
                self.log.appendPlainText("Descargado: " + info.manifest["id"])
            except Exception as error:
                self.log.appendPlainText("ERROR: " + str(error))
            self.discover()

    def execute_tool(self):
        items = [(key, value) for key, value in self.manager.registry.items() if key[0] == "hdl_tool"]
        if not items:
            W.QMessageBox.information(self, "Herramientas", "Cargue un plugin con una contribución hdl_tool; hay un ejemplo en examples/plugins.")
            return
        name, ok = W.QInputDialog.getItem(self, "Herramienta HDL", "Seleccione una herramienta:", [k[1] for k, v in items], 0, False)
        if ok:
            try:
                result = dict((k[1], v) for k, v in items)[name](self.project_provider())
                self.log.appendPlainText(json.dumps(result, indent=2, ensure_ascii=False))
            except Exception as error:
                self.log.appendPlainText("ERROR: " + str(error))


class SettingsPanel(W.QWidget):
    saved = Signal(dict)

    def __init__(self):
        super().__init__()
        self.file = data_dir() / "settings.json"
        self.values = {"iverilog": "", "vvp": "", "gtkwave": "", "timeout": 15}
        try:
            saved = json.loads(self.file.read_text(encoding="utf-8"))
            self.values.update({k: v for k, v in saved.items() if k in self.values})
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.addWidget(label("Configuración", "Heading"))
        hint = ("Motor Icarus incluido: deja ambas rutas vacías para usarlo." if bundled_icarus()
                else "Esta ejecución no contiene Icarus Windows integrado; las rutas vacías buscan una instalación externa.")
        layout.addWidget(label(hint + " Las rutas personalizadas son opcionales. Los ajustes se conservan en tu perfil de usuario.", "Muted", True))
        form = W.QFormLayout()
        self.fields = {}
        for key, title in (("iverilog", "Icarus / iverilog.exe"), ("vvp", "Runtime / vvp.exe"), ("gtkwave", "GTKWave (opcional)")):
            edit = W.QLineEdit(str(self.values.get(key, "")))
            self.fields[key] = edit
            line = W.QHBoxLayout()
            line.addWidget(edit)
            line.addWidget(button("…", lambda checked=False, field=edit: self.browse(field)))
            form.addRow(title, line)
        self.timeout = W.QSpinBox()
        self.timeout.setRange(1, 120)
        try:
            self.timeout.setValue(int(self.values["timeout"]))
        except (ValueError, TypeError):
            self.timeout.setValue(15)
        form.addRow("Tiempo máximo por proceso / s", self.timeout)
        layout.addLayout(form)
        layout.addWidget(button("Guardar configuración", self.save, True))
        layout.addWidget(label("El visor VCD está integrado. GTKWave es opcional. Consulta el informe de distribución para conocer el estado verificado de cada plataforma.", "Muted", True))
        layout.addStretch()

    def browse(self, field):
        path, _ = W.QFileDialog.getOpenFileName(self, "Seleccione el ejecutable")
        if path:
            field.setText(path)

    def save(self):
        self.values = {key: field.text().strip() for key, field in self.fields.items()}
        self.values["timeout"] = self.timeout.value()
        try:
            temporary = self.file.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.values, indent=2), encoding="utf-8")
            temporary.replace(self.file)
            self.saved.emit(self.values)
            W.QMessageBox.information(self, "Configuración", "Ajustes guardados.")
        except OSError as error:
            W.QMessageBox.warning(self, "Configuración", str(error))

