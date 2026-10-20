import argparse
import json
import logging
import faulthandler
import platform
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app import __version__
from app.utils.paths import data_dir


def configure_logging():
    handler = RotatingFileHandler(str(data_dir() / "PhoenixForge.log"), maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler], format="%(asctime)s %(levelname)s %(message)s")


def main(argv=None):
    parser = argparse.ArgumentParser(description="PhœnixForge — Forge Digital Logic")
    parser.add_argument("project", nargs="?", help="Proyecto .pforge que desea abrir")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--doctor", action="store_true", help="Mostrar el entorno sin abrir la interfaz")
    parser.add_argument("--self-test", metavar="OUTPUT", help="Aceptación automatizada de desarrollo, con informes")
    parser.add_argument("--offscreen", action="store_true", help="Backend gráfico de pruebas sin escritorio")
    parser.add_argument("--require-bundled", action="store_true", help="Exigir ejecutable y simulador integrados en la aceptación")
    args = parser.parse_args(argv)
    if args.self_test:
        from app.acceptance import run
        return run(args.self_test, args.offscreen, args.require_bundled)
    if args.doctor:
        from app.simulators.icarus import IcarusEngine
        engine = IcarusEngine()
        print(json.dumps({"version": __version__, "python": sys.version, "platform": platform.platform(),
                          "architecture": platform.architecture()[0], "iverilog": engine.iverilog, "vvp": engine.vvp,
                          "windows_compatibility": "Not verified by this command"}, indent=2))
        return 0
    configure_logging()
    try:
        crash_stream = open(data_dir() / 'PhoenixForge-crash.log', 'a', encoding='utf-8')
        faulthandler.enable(file=crash_stream, all_threads=True)
    except (OSError, RuntimeError):
        logging.exception('No se pudo activar el diagnóstico de fallos nativos')
    try:
        from app.ui.qt import QtWidgets as W, QtCore as C, QtGui as G, exec_app
        from app.ui.main_window import MainWindow
    except ImportError as error:
        print("Falta Qt/PySide. Ejecute install_windows.bat modern (Win10) o legacy (Win7).", file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 2
    from app.utils.paths import assets_dir
    application = W.QApplication([sys.argv[0]])
    application.setApplicationName("PhoenixForge")
    application.setApplicationVersion(__version__)
    application.setOrganizationName("PhoenixForge")
    application.setStyle("Fusion")
    window = MainWindow()
    if args.project:
        try:
            from app.core.project import Project
            window.replace_project(Project.open(args.project), args.project, False)
        except Exception as error:
            W.QMessageBox.warning(window, "No se pudo abrir el proyecto", str(error))
    def exception_hook(kind, error, traceback):
        logging.error("Unhandled UI exception", exc_info=(kind, error, traceback))
        W.QMessageBox.warning(window, "Error recuperable", "La operación no se completó.\n" + str(error))
    sys.excepthook = exception_hook
    window.show()
    return exec_app(application)


if __name__ == "__main__":
    sys.exit(main())
