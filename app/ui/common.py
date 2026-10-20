from app.ui.qt import QtWidgets as W


def label(text, kind=None, wrap=False):
    widget = W.QLabel(text)
    if kind:
        widget.setObjectName(kind)
    widget.setWordWrap(wrap)
    return widget


def button(text, callback=None, primary=False):
    widget = W.QPushButton(text)
    if primary:
        widget.setObjectName("Primary")
    if callback:
        widget.clicked.connect(lambda checked=False: callback())
    return widget


def card():
    frame = W.QFrame()
    frame.setObjectName("Card")
    layout = W.QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    return frame, layout


def page(title, subtitle):
    widget = W.QWidget()
    layout = W.QVBoxLayout(widget)
    layout.setContentsMargins(26, 22, 26, 22)
    layout.setSpacing(14)
    layout.addWidget(label(title, "Heading"))
    layout.addWidget(label(subtitle, "Muted", True))
    return widget, layout

