from app.ui.qt import QtCore as C, QtGui as G, QtWidgets as W, Qt
from app.simulators.vcd import parse_vcd
from app.ui.common import button, label


class WaveCanvas(W.QWidget):
    def __init__(self):
        super().__init__()
        self.trace = None
        self.zoom = 1.0
        self.cursor_x = None
        self.setMouseTracking(True)
        self.setMinimumSize(750, 170)

    def set_trace(self, trace):
        self.trace = trace
        self.cursor_x = None
        self.setMinimumSize(int(900 * self.zoom), max(170, 48 + len(trace.signals) * 38))
        self.update()

    def mouseMoveEvent(self, event):
        self.cursor_x = event.pos().x()
        self.update()

    def paintEvent(self, event):
        p = G.QPainter(self)
        p.fillRect(self.rect(), G.QColor("#0c1421"))
        if self.trace is None:
            p.setPen(G.QColor("#8498af"))
            p.drawText(24, 50, "Simula un testbench con $dumpfile / $dumpvars o abre un archivo VCD.")
            return
        left, right = 240, self.width() - 24
        span = max(1, self.trace.end)
        scale = (right - left) / span
        p.setFont(G.QFont("Consolas", 10))
        for tick in range(9):
            x = left + tick * (right - left) / 8
            p.setPen(G.QColor("#223348"))
            p.drawLine(int(x), 30, int(x), self.height())
            p.setPen(G.QColor("#8094a9"))
            p.drawText(int(x) - 12, 20, str(round(tick * span / 8)))
        for index, signal in enumerate(self.trace.signals):
            y = 52 + index * 38
            p.setPen(G.QColor("#b7c6d9"))
            name = p.fontMetrics().elidedText(signal.name, Qt.ElideLeft, left - 22)
            p.drawText(10, y + 7, name)
            events = signal.events
            if not events:
                continue
            previous_y = None
            for i, (time, value) in enumerate(events):
                end = events[i + 1][0] if i + 1 < len(events) else span
                x1, x2 = left + time * scale, left + end * scale
                unknown = "x" in value or "z" in value
                p.setPen(G.QPen(G.QColor("#e99955" if unknown else "#72d8b0"), 1.5))
                if signal.width == 1:
                    vy = y - 9 if value == "1" else y + 10
                    if previous_y is not None and previous_y != vy:
                        p.drawLine(int(x1), previous_y, int(x1), vy)
                    p.drawLine(int(x1), vy, int(x2), vy)
                    if unknown and x2 - x1 > 12:
                        p.drawText(int(x1) + 3, y, value.upper())
                    previous_y = vy
                else:
                    p.drawLine(int(x1), y - 9, int(x2), y - 9)
                    p.drawLine(int(x1), y + 10, int(x2), y + 10)
                    p.drawLine(int(x1), y - 9, int(x1) + 4, y + 10)
                    text = value if unknown else hex(int(value, 2))
                    if x2 - x1 > p.fontMetrics().horizontalAdvance(text) + 10:
                        p.drawText(int(x1) + 6, y + 4, text)
        if self.cursor_x and self.cursor_x >= left:
            p.setPen(G.QColor("#fabb70"))
            p.drawLine(self.cursor_x, 26, self.cursor_x, self.height())
            self.setToolTip("t = %.2f × %s" % ((self.cursor_x - left) / scale, self.trace.timescale))


class WaveViewer(W.QWidget):
    def __init__(self):
        super().__init__()
        layout = W.QVBoxLayout(self)
        row = W.QHBoxLayout()
        self.info = label("Sin traza cargada", "Muted")
        row.addWidget(self.info, 1)
        row.addWidget(button("−", lambda: self.zoom(0.7)))
        row.addWidget(button("+", lambda: self.zoom(1.4)))
        layout.addLayout(row)
        self.scroll = W.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.canvas = WaveCanvas()
        self.scroll.setWidget(self.canvas)
        layout.addWidget(self.scroll)

    def zoom(self, ratio):
        self.canvas.zoom = min(12, max(0.5, self.canvas.zoom * ratio))
        if self.canvas.trace:
            self.canvas.set_trace(self.canvas.trace)

    def load(self, data, name="VCD"):
        trace = parse_vcd(data)
        self.canvas.set_trace(trace)
        self.info.setText("%s · %d señales · unidad %s" % (name, len(trace.signals), trace.timescale))

