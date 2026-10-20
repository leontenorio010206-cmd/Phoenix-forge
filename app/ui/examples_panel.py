"""Sample projects live outside the primary navigation tools."""
from app.ui.qt import QtWidgets as W, Signal
from app.ui.common import button, card, label


class ExamplesPanel(W.QWidget):
    example_requested = Signal(str)

    def __init__(self):
        super().__init__()
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(16)
        layout.addWidget(label("Proyectos de muestra", "Heading"))
        layout.addWidget(label("Abre un proyecto Verilog de ejemplo, edítalo y pulsa F5 para simular con Icarus.\n"
                               "Los ejemplos no sustituyen la selección ni la validación de un FPGA real.", "Muted", True))
        for key, title, description in (
            ("clock", "Semáforo, relojes y divisores", "Práctica 6 · 50 MHz de referencia · contador, pulso, onda cuadrada y testbench."),
            ("adder", "Sumador de 1 bit", "Lógica combinacional · ocho vectores verificados por testbench."),
            ("device", "Contador RTL en cualquiera de las 10 FPGA", "Ejercicio de 4 bits · doce vectores · usa el perfil FPGA elegido."),
        ):
            frame, content = card()
            content.addWidget(label(title, "Heading"))
            content.addWidget(label(description, "Muted", True))
            content.addWidget(button("Abrir proyecto de ejemplo →", lambda checked=False, k=key: self.example_requested.emit(k), True))
            layout.addWidget(frame)
        layout.addStretch(1)
