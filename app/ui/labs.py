"""Interactive academic laboratories; all calculations use tested core models."""
from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt, Signal
from app.ui.common import label, button, card
from app.simulators.clock import Counter, PulseDivider, SquareDivider, TrafficLight, bits_for_cycles


class TrafficDisplay(W.QWidget):
    def __init__(self):
        super().__init__()
        self.state = "ROJO"
        self.setMinimumSize(170, 230)

    def paintEvent(self, event):
        p = G.QPainter(self)
        p.setRenderHint(G.QPainter.Antialiasing)
        cx = self.width() / 2
        p.setBrush(G.QColor("#0a1220"))
        p.setPen(G.QPen(G.QColor("#2d4059"), 2))
        p.drawRoundedRect(C.QRectF(cx - 48, 8, 96, 212), 28, 28)
        for name, y, color in (("ROJO", 48, "#ff635e"), ("AMARILLO", 115, "#ffd365"), ("VERDE", 181, "#66dba2")):
            active = name == self.state
            p.setPen(G.QPen(G.QColor(color if active else "#253349"), 3))
            p.setBrush(G.QColor(color if active else "#172435"))
            p.drawEllipse(C.QPointF(cx, y), 25, 25)


class ClockLab(W.QWidget):
    create_requested = Signal(object)
    trace_requested = Signal(int, int, int)

    def __init__(self):
        super().__init__()
        outer = W.QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.addWidget(label("Reloj, contadores y semáforo", "Heading"))
        outer.addWidget(label("PRÁCTICA 06   /   REFERENCIA 50 MHz", "Eyebrow"))
        content = W.QWidget()
        layout = W.QVBoxLayout(content)
        scroll = W.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        row = W.QHBoxLayout()
        controls, cl = card()
        form = W.QFormLayout()
        self.red = self.spin(5, 3600); self.green = self.spin(5, 3600); self.yellow = self.spin(2, 3600)
        self.hz = self.spin(50000000, 1000000000)
        self.period = self.spin(50000000, 1000000000)
        self.half = self.spin(25000000, 1000000000)
        self.modulus = self.spin(5208, 1000000000)
        for title, field in (("Rojo / segundos", self.red), ("Verde / segundos", self.green), ("Amarillo / segundos", self.yellow),
                             ("Reloj de entrada / Hz", self.hz), ("Pulso cada N ciclos", self.period),
                             ("Semiperiodo cuadrada / ciclos", self.half), ("Módulo del contador", self.modulus)):
            form.addRow(title, field)
            field.valueChanged.connect(self.reset)
        cl.addLayout(form)
        cl.addWidget(label("Cambiar un parámetro detiene y reinicia el modelo.", "Muted", True))
        row.addWidget(controls, 3)
        monitor, ml = card()
        self.display = TrafficDisplay()
        ml.addWidget(self.display)
        self.state_label = label("ROJO", "Heading")
        self.state_label.setAlignment(Qt.AlignCenter)
        ml.addWidget(self.state_label)
        self.readout = label("", "Muted", True)
        ml.addWidget(self.readout)
        row.addWidget(monitor, 2)
        layout.addLayout(row)
        self.math = label("", "Muted", True)
        layout.addWidget(self.math)
        layout.addWidget(label("5,208 ciclos → 13 bits · 50,000,000 ciclos → 26 bits · 50 MHz → 20 ns", "Eyebrow", True))
        layout.addWidget(label("Diseño añadido: rojo → verde → amarillo, reset síncrono y LED activos en 1. Los indicadores se muestrean; el reloj de 50 MHz se inspecciona mediante una traza reducida.", "Muted", True))
        actions = W.QHBoxLayout()
        actions.addWidget(button("Iniciar", self.start, True))
        actions.addWidget(button("Detener", self.stop))
        actions.addWidget(button("Reiniciar", self.reset))
        actions.addWidget(button("+1 ciclo", lambda: self.step(1)))
        actions.addWidget(button("+1 segundo", lambda: self.step(self.hz.value())))
        self.speed = W.QComboBox()
        for speed in (1, 10, 100, 1000):
            self.speed.addItem("%d×" % speed, speed)
        actions.addWidget(self.speed)
        layout.addLayout(actions)
        actions2 = W.QHBoxLayout()
        actions2.addWidget(button("Crear proyecto HDL", lambda: self.create_requested.emit(self.configuration()), True))
        actions2.addWidget(button("Traza de prueba reducida", lambda: self.trace_requested.emit(self.red.value(), self.green.value(), self.yellow.value())))
        layout.addLayout(actions2)
        layout.addStretch()
        self.timer = C.QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self.elapsed = C.QElapsedTimer()
        self.remainder = 0.0
        self.reset()

    def configuration(self):
        return {"red": self.red.value(), "green": self.green.value(), "yellow": self.yellow.value(),
                "clock_hz": self.hz.value(), "period": self.period.value(), "half_period": self.half.value(),
                "modulus": self.modulus.value()}

    def spin(self, value, maximum):
        result = W.QSpinBox()
        result.setRange(1, maximum)
        result.setValue(value)
        return result

    def reset(self, *_):
        if not hasattr(self, "timer"):
            return
        self.timer.stop()
        self.model = TrafficLight(self.red.value(), self.green.value(), self.yellow.value(), self.hz.value())
        self.pulse = PulseDivider(self.period.value())
        self.square = SquareDivider(self.half.value())
        self.counter = Counter(self.modulus.value())
        self.remainder = 0.0
        self.refresh()

    def start(self):
        self.elapsed.start()
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def step(self, cycles):
        self.stop()
        self.advance(cycles)

    def tick(self):
        milliseconds = self.elapsed.restart()
        cycles = milliseconds / 1000.0 * self.hz.value() * self.speed.currentData() + self.remainder
        whole = int(cycles)
        self.remainder = cycles - whole
        self.advance(whole)

    def advance(self, cycles):
        self.model.advance(cycles)
        self.pulse.advance(cycles)
        self.square.advance(cycles)
        self.counter.advance(cycles)
        self.refresh()

    def refresh(self):
        self.display.state = self.model.state
        self.display.update()
        self.state_label.setText(self.model.state)
        self.readout.setText("Tiempo virtual: %.3f s\nCiclos: %d\nContador: %d / %d\nPulso: %d   ·   Cuadrada: %d" %
                             (self.model.cycles / self.hz.value(), self.model.cycles, self.counter.value, self.modulus.value() - 1, self.pulse.pulse, self.square.output))
        self.math.setText("Pulso: %.6g Hz, ancho de 1 ciclo; %d bits.   Cuadrada: %.6g Hz (50%%).\nContador: %d bits para 0…%d. Un pulso por segundo NO es una onda cuadrada de 1 Hz." %
                          (self.hz.value() / self.period.value(), bits_for_cycles(self.period.value()), self.hz.value() / (2 * self.half.value()), bits_for_cycles(self.modulus.value()), self.modulus.value() - 1))

