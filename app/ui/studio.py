from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt, Signal
from app.ui.common import button, label
from app.editors.verilog import CodeEditor
from app.core.hdl import modules
from app.ui.waveform import WaveViewer


class Studio(W.QWidget):
    source_changed = Signal(str, str)
    simulation_changed = Signal(str, str)
    run_requested = Signal()
    cancel_requested = Signal()
    import_requested = Signal()
    new_source_requested = Signal()

    def __init__(self):
        super().__init__()
        self.project = None
        self.editors = {}
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        header = W.QHBoxLayout()
        self.title = label("Sin proyecto", "Heading")
        header.addWidget(self.title, 1)
        header.addWidget(button("+ Archivo", self.new_source_requested.emit))
        header.addWidget(button("Importar", self.import_requested.emit))
        layout.addLayout(header)
        toolbar = W.QHBoxLayout()
        toolbar.addWidget(label("Módulo"))
        self.top = W.QComboBox()
        self.testbench = W.QComboBox()
        toolbar.addWidget(self.top, 1)
        toolbar.addWidget(label("Testbench / raíz"))
        toolbar.addWidget(self.testbench, 1)
        toolbar.addWidget(button("↻ Módulos", self.refresh_modules))
        self.run_button = button("▶ Simular", self.run_requested.emit, True)
        self.cancel_button = button("Detener", self.cancel_requested.emit)
        self.cancel_button.setEnabled(False)
        toolbar.addWidget(self.run_button); toolbar.addWidget(self.cancel_button)
        layout.addLayout(toolbar)
        self.top.currentTextChanged.connect(lambda name: self.simulation_changed.emit("top", name))
        self.testbench.currentTextChanged.connect(lambda name: self.simulation_changed.emit("testbench", name))
        horizontal = W.QSplitter(Qt.Horizontal)
        self.tree = W.QTreeWidget()
        self.tree.setHeaderLabels(["PROYECTO"])
        self.tree.itemDoubleClicked.connect(self.open_item)
        horizontal.addWidget(self.tree)
        vertical = W.QSplitter(Qt.Vertical)
        editor_area = W.QWidget()
        editor_layout = W.QVBoxLayout(editor_area)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        search = W.QHBoxLayout()
        self.search_field = W.QLineEdit()
        self.search_field.setPlaceholderText("Buscar en el archivo activo · Ctrl+F")
        self.search_field.returnPressed.connect(self.find_text)
        search.addWidget(self.search_field, 1)
        search.addWidget(button("Buscar siguiente", self.find_text))
        editor_layout.addLayout(search)
        self.tabs = W.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        editor_layout.addWidget(self.tabs, 1)
        vertical.addWidget(editor_area)
        self.output_tabs = W.QTabWidget()
        self.console = W.QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(G.QFont("Consolas", 10))
        self.console.document().setMaximumBlockCount(10000)
        self.errors = W.QTableWidget(0, 4)
        self.errors.setHorizontalHeaderLabels(["Nivel", "Archivo", "Línea", "Mensaje"])
        self.errors.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.errors.horizontalHeader().setStretchLastSection(True)
        self.errors.cellDoubleClicked.connect(self.go_error)
        self.wave = WaveViewer()
        self.output_tabs.addTab(self.console, "Consola")
        self.output_tabs.addTab(self.errors, "Errores y advertencias")
        self.output_tabs.addTab(self.wave, "Señales VCD")
        vertical.addWidget(self.output_tabs)
        vertical.setSizes([400, 240])
        horizontal.addWidget(vertical)
        horizontal.setSizes([210, 900])
        layout.addWidget(horizontal, 1)

    def bind_project(self, project):
        self.project = project
        self.editors.clear()
        while self.tabs.count():
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            widget.deleteLater()
        self.title.setText(project.name)
        self.console.clear()
        self.errors.setRowCount(0)
        self.wave.canvas.trace = None
        self.wave.canvas.update()
        self.wave.info.setText("Sin traza cargada")
        self.refresh_tree()
        self.refresh_modules()
        for name in list(project.files)[:2]:
            self.open_source(name)

    def refresh_tree(self):
        self.tree.clear()
        if self.project is None:
            return
        sources = W.QTreeWidgetItem(self.tree, ["Archivos fuente"])
        for name in sorted(self.project.files):
            item = W.QTreeWidgetItem(sources, [name])
            item.setData(0, Qt.UserRole, ("source", name))
        results = W.QTreeWidgetItem(self.tree, ["Resultados conservados"])
        for name in sorted(self.project.artifacts):
            item = W.QTreeWidgetItem(results, [name])
            item.setData(0, Qt.UserRole, ("artifact", name))
        self.tree.expandAll()

    def refresh_modules(self):
        if self.project is None:
            return
        names = [m["name"] for m in modules(self.project.files)]
        for field, combo in (("top", self.top), ("testbench", self.testbench)):
            selected = self.project.simulation.get(field, "")
            combo.blockSignals(True)
            combo.clear(); combo.addItem(""); combo.addItems(names)
            combo.setCurrentText(selected if selected in names else "")
            combo.blockSignals(False)

    def open_item(self, item, column=0):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        kind, name = data
        if kind == "source":
            self.open_source(name)
        elif name.lower().endswith(".vcd"):
            try:
                self.wave.load(self.project.artifacts[name], name)
                self.output_tabs.setCurrentWidget(self.wave)
            except ValueError as error:
                W.QMessageBox.warning(self, "VCD", str(error))
        else:
            self.console.setPlainText(self.project.artifacts[name].decode("utf-8", errors="replace"))
            self.output_tabs.setCurrentWidget(self.console)

    def open_source(self, name):
        if name in self.editors:
            self.tabs.setCurrentWidget(self.editors[name])
            return self.editors[name]
        editor = CodeEditor(name, self.project.files[name])
        self.editors[name] = editor
        self.tabs.addTab(editor, name)
        editor.textChanged.connect(lambda: self.changed(editor))
        self.tabs.setCurrentWidget(editor)
        return editor

    def changed(self, editor):
        index = self.tabs.indexOf(editor)
        self.tabs.setTabText(index, editor.name + " *")
        self.source_changed.emit(editor.name, editor.toPlainText())

    def mark_saved(self):
        for name, editor in self.editors.items():
            editor.document().setModified(False)
            self.tabs.setTabText(self.tabs.indexOf(editor), name)

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        # Content is already in the in-memory project; closing a tab never discards it.
        self.editors.pop(editor.name, None)
        self.tabs.removeTab(index)
        editor.deleteLater()

    def find_text(self):
        editor = self.tabs.currentWidget()
        if editor and not editor.search(self.search_field.text()):
            self.search_field.setToolTip("No se encontró el texto")

    def set_busy(self, busy):
        self.run_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)

    def show_diagnostics(self, diagnostics, failure=None):
        rows = [(d.severity, d.file, str(d.line), d.message) for d in diagnostics]
        if failure:
            rows.append(("error", "", "", failure))
        self.errors.setRowCount(len(rows))
        for i, values in enumerate(rows):
            for j, value in enumerate(values):
                self.errors.setItem(i, j, W.QTableWidgetItem(value))
        self.errors.resizeColumnsToContents()

    def go_error(self, row, column=0):
        path = self.errors.item(row, 1).text().replace("\\", "/")
        line = self.errors.item(row, 2).text()
        for name in self.project.files:
            if path == name or path.endswith("/src/" + name):
                self.open_source(name).go_to_line(int(line or 1))
                break

