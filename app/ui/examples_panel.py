"""Sample HDL projects and the preserved interactive clock/semaphore lab."""
from app.ui.qt import QtWidgets as W, Signal
from app.ui.common import button, card, label
from app.ui.labs import ClockLab


class ExamplesPanel(W.QWidget):
    example_requested = Signal(str)

    def __init__(self):
        super().__init__()
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)
        layout.addWidget(label("Proyectos de muestra", "Heading"))
        layout.addWidget(label("Ejemplos Verilog con testbench y laboratorio visual. "
                               "Puedes modificarlos, guardar el proyecto y ver señales VCD.", "Muted", True))
        self.tabs = W.QTabWidget()
        gallery = W.QWidget()
        inner = W.QVBoxLayout(gallery)
        inner.setContentsMargins(10, 12, 10, 12)
        for key, title, description in (
            ("clock", "Semáforo, relojes y divisores", "Práctica 6 · contador, pulso, onda cuadrada y testbench."),
            ("adder", "Sumador de 1 bit", "Combinacional · ocho vectores verificados por testbench."),
            ("device", "Contador RTL para 10 FPGA", "Ejercicio de 4 bits · doce vectores · perfil seleccionado."),
        ):
            frame, content = card()
            content.addWidget(label(title, "Heading"))
            content.addWidget(label(description, "Muted", True))
            content.addWidget(button("Abrir proyecto HDL →", lambda checked=False, k=key: self.example_requested.emit(k), True))
            inner.addWidget(frame)
        inner.addWidget(button("Abrir semáforo animado y sus controles →",
                               lambda: self.tabs.setCurrentIndex(1)))
        inner.addStretch(1)
        self.clock = ClockLab()
        self.tabs.addTab(gallery, "Ejemplos Verilog")
        self.tabs.addTab(self.clock, "Semáforo interactivo")
        layout.addWidget(self.tabs, 1)
