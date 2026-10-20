"""Small compatibility boundary for the modern and legacy dependency sets."""
import os
import sys

binding = os.environ.get("PHOENIXFORGE_QT", "pyside2" if sys.version_info < (3, 9) else "pyside6")
if binding == "pyside2":
    from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
    from PySide2.QtCore import Signal, Slot, Qt
    from PySide2.QtWidgets import QAction
    BINDING = "PySide2"
else:
    from PySide6 import QtCore, QtGui, QtWidgets, QtSvg
    from PySide6.QtCore import Signal, Slot, Qt
    from PySide6.QtGui import QAction
    BINDING = "PySide6"


def exec_app(app):
    return app.exec_() if BINDING == "PySide2" else app.exec()


def exec_dialog(dialog):
    return dialog.exec_() if BINDING == "PySide2" else dialog.exec()

