"""Interactive virtual FPGA pin bench, using Icarus and generated testbenches."""
import copy
import threading
from app.ui.qt import QtCore as C, QtWidgets as W, Signal
from app.ui.common import label, button
from app.core.hdl import modules
from app.devices.catalog import load_profiles
from app.simulators.icarus import IcarusEngine
from app.simulators.virtual_fpga import select_ports, make_probe_project, outputs_from_result


class BenchThread(C.QThread):
    finished_result = Signal(object)
    def __init__(self, engine, project, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.project = project
        self.cancel = threading.Event()

    def run(self):
        try:
            result = self.engine.run(self.project, cancel=self.cancel)
        except Exception as error:
            from app.simulators.icarus import SimulationResult
            result = SimulationResult(False, "", reason=str(error), output=str(error))
        self.finished_result.emit(result)


class VirtualFPGABench(W.QWidget):
    trace_ready = Signal(bytes)

    def __init__(self, project_provider, settings_provider):
        super().__init__()
        self.project_provider = project_provider
        self.settings_provider = settings_provider
        self.inputs = {}
        self.outputs = {}
        self.ports = []
        self.worker = None
        outer = W.QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.addWidget(label("FPGA virtual · banco de señales", "Heading"))
        outer.addWidget(label("Conecta entradas HDL, genera flancos de reloj y observa las salidas reales del Verilog. "
                              "Motor Icarus para los 10 perfiles; NO representa pines físicos, voltajes ni tiempos del chip.",
                              "Muted", True))
        topbar = W.QHBoxLayout()
        self.device_label = label("", "Muted")
        topbar.addWidget(self.device_label, 1)
        self.module = W.QComboBox()
        self.module.currentTextChanged.connect(self.select_module)
        topbar.addWidget(self.module)
        topbar.addWidget(button("Actualizar puertos", self.refresh))
        outer.addLayout(topbar)
        self.scroll = W.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.pad = W.QWidget()
        self.padlayout = W.QVBoxLayout(self.pad)
        self.padlayout.setContentsMargins(8, 8, 8, 8)
        self.scroll.setWidget(self.pad)
        outer.addWidget(self.scroll, 1)
        controls = W.QHBoxLayout()
        self.clock = W.QComboBox()
        self.clock.addItem("Sin reloj", "")
        controls.addWidget(label("Reloj:"))
        controls.addWidget(self.clock)
        self.cycles = W.QSpinBox()
        self.cycles.setRange(0, 100)
        self.cycles.setValue(1)
        controls.addWidget(label("Pulsos:"))
        controls.addWidget(self.cycles)
        self.run_button = button("Ejecutar FPGA virtual", self.run, True)
        controls.addWidget(self.run_button)
        outer.addLayout(controls)
        self.status = label("Elija un módulo Verilog en el proyecto.", "Muted", True)
        outer.addWidget(self.status)

    def bind_project(self, project=None):
        project = project or self.project_provider()
        self.device_label.setText(load_profiles().get(project.device, {}).get("name", project.device))
        current = project.simulation.get("top", "")
        self.module.blockSignals(True)
        self.module.clear()
        self.module.addItems([m["name"] for m in modules(project.files)
                              if not m["testbench_hint"]])
        index = self.module.findText(current)
        if index >= 0:
            self.module.setCurrentIndex(index)
        self.module.blockSignals(False)
        self.refresh()

    def select_module(self, unused=None):
        self.refresh()

    def refresh(self):
        if self.worker is not None:
            return
        while self.padlayout.count():
            child = self.padlayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.inputs, self.outputs = {}, {}
        self.clock.clear()
        self.clock.addItem("Sin reloj", "")
        project = self.project_provider()
        try:
            top, self.ports = select_ports(project, self.module.currentText())
        except (ValueError, KeyError) as error:
            self.ports = []
            self.status.setText("No se pueden mostrar los puertos: " + str(error))
            return
        for p in self.ports:
            name, width = p["name"], p["width"]
            line = W.QHBoxLayout()
            line.addWidget(label(name + (" [%d bits]" % width if width > 1 else "")))
            if p["direction"] == "input":
                if width == 1:
                    w = W.QCheckBox("1 / HIGH")
                else:
                    w = W.QSpinBox()
                    w.setRange(0, (1 << width) - 1)
                self.inputs[name] = w
                line.addWidget(w)
                if width == 1:
                    self.clock.addItem(name, name)
            else:
                w = label("X · sin simular")
                w.setStyleSheet("color:#9fb2c7; font-weight:700;")
                self.outputs[name] = w
                line.addWidget(w)
            line.addStretch(1)
            row = W.QWidget()
            row.setLayout(line)
            self.padlayout.addWidget(row)
        self.padlayout.addStretch()
        self.status.setText("%d puertos HDL preparados; seleccione entradas y ejecute Icarus." % len(self.ports))

    def run(self):
        if self.worker is not None:
            return
        project = copy.deepcopy(self.project_provider())
        settings = self.settings_provider()
        try:
            top = self.module.currentText()
            signals = {name: int(w.isChecked()) if isinstance(w, W.QCheckBox) else w.value()
                       for name, w in self.inputs.items()}
            clock = self.clock.currentData() or None
            simulated = make_probe_project(project, signals, clock=clock, cycles=self.cycles.value(), top=top)
            engine = IcarusEngine(settings.get("iverilog", ""), settings.get("vvp", ""))
            if not engine.available:
                raise RuntimeError("Icarus no disponible. Vacíe las rutas manuales para usar el motor integrado.")
        except (ValueError, RuntimeError, KeyError) as error:
            W.QMessageBox.warning(self, "FPGA virtual", str(error))
            return
        consent = W.QMessageBox.question(self, "Simular HDL",
            "El código Verilog y las directivas de prueba se ejecutan con Icarus. "
            "La compilación ocurre en una carpeta temporal, pero NO es una sandbox de seguridad. "
            "Ejecute únicamente proyectos de confianza. ¿Continuar?",
            W.QMessageBox.Yes | W.QMessageBox.No, W.QMessageBox.No)
        if consent != W.QMessageBox.Yes:
            return
        self.run_button.setEnabled(False)
        self.status.setText("Compilando y simulando RTL…")
        self.worker = BenchThread(engine, simulated, self)
        self.worker.finished_result.connect(self.show_result)
        self.worker.finished.connect(self.cleanup)
        self.worker.start()

    def show_result(self, result):
        try:
            if not result.success:
                raise RuntimeError(result.reason + "\n" + result.output[-800:])
            values = outputs_from_result(result, self.ports)
            for name, bits in values.items():
                state = "UNKNOWN" if "x" in bits or "z" in bits else ("1 · HIGH" if int(bits, 2) else "0 · LOW")
                if len(bits) > 1:
                    state = bits + (" (0x%x)" % int(bits, 2) if "x" not in bits and "z" not in bits else "")
                self.outputs[name].setText(state)
                color = "#73e4b6" if "x" not in bits and "z" not in bits and int(bits, 2) else "#f0a46f" if "x" in bits or "z" in bits else "#9fb2c7"
                self.outputs[name].setStyleSheet("font-weight:700;color:%s;" % color)
            self.status.setText("Simulación terminada; salidas y VCD generados por Icarus.")
            for filename, data in result.artifacts.items():
                if filename.endswith(".vcd"):
                    self.trace_ready.emit(data)
                    break
        except (ValueError, RuntimeError) as error:
            self.status.setText("Fallo HDL: " + str(error)[:300])
        self.run_button.setEnabled(True)

    def cleanup(self):
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        self.run_button.setEnabled(True)
