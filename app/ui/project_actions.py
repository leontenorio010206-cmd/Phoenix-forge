"""Project/file actions kept separate from main-window composition."""
import json
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps

from app.ui.qt import QtWidgets as W
from app.core.project import Project
from app.core.examples import adder_project, clock_project
from app.exporters.bundle import export_bundle
from app.exporters.digital_hdl import export_digital_component
from app.utils.paths import safe_relative, user_projects_dir


def guarded(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as error:
            import logging
            logging.exception("Acción de interfaz fallida")
            W.QMessageBox.warning(self, "PhœnixForge", str(error))
            return False
    return wrapped


class ProjectActions:
    def can_replace(self):
        if self.worker is not None or (hasattr(self, 'devices') and self.devices.bench.worker is not None):
            W.QMessageBox.information(self, "Simulación activa", "Espere a que termine la simulación antes de cambiar de proyecto.")
            return False
        return self.confirm_discard()

    def confirm_discard(self):
        if not self.dirty:
            return True
        answer = W.QMessageBox.question(self, "Cambios sin guardar", "¿Desea guardar los cambios del proyecto?",
                                       W.QMessageBox.Save | W.QMessageBox.Discard | W.QMessageBox.Cancel, W.QMessageBox.Save)
        if answer == W.QMessageBox.Cancel:
            return False
        if answer == W.QMessageBox.Save:
            return bool(self.save_project())
        return True

    def confirm_overwrite(self, path):
        return not Path(path).exists() or W.QMessageBox.question(
            self, "Confirmar sobrescritura", "¿Reemplazar el archivo existente?\n" + str(path),
            W.QMessageBox.Yes | W.QMessageBox.No, W.QMessageBox.No) == W.QMessageBox.Yes

    def replace_project(self, project, path=None, dirty=True):
        project.validate()
        self.project, self.project_path, self.dirty = project, Path(path) if path else None, dirty
        self.studio.bind_project(project)
        self.devices.bind(project)
        self.digital_export.bind_project(project)
        self.update_title()
        self.navigate(1)

    @guarded
    def new_project(self):
        if not self.can_replace():
            return
        name, ok = W.QInputDialog.getText(self, "Nuevo proyecto", "Nombre:", text="Mi proyecto")
        if ok and name.strip():
            self.replace_project(Project(name.strip(), files={"main.v": "module main(input A, output Y);\n  assign Y = A;\nendmodule\n"}, simulation={"top": "main", "testbench": "", "timeout": 15}))

    @guarded
    def new_adder(self):
        if self.can_replace():
            self.replace_project(adder_project())

    @guarded
    def new_clock(self, red=5, green=5, yellow=2):
        if self.can_replace():
            project = clock_project(**red) if isinstance(red, dict) else clock_project(red, green, yellow)
            self.replace_project(project)

    @guarded
    def open_project(self):
        if not self.can_replace():
            return
        path, _ = W.QFileDialog.getOpenFileName(self, "Abrir proyecto", str(user_projects_dir()), "PhoenixForge (*.pforge)")
        if path:
            loaded = Project.open(path)
            if loaded.device not in self.devices.profiles:
                W.QMessageBox.information(self, "Perfil no instalado", "Se conserva el ID de perfil del proyecto, pero no está en el catálogo local.")
            self.replace_project(loaded, path, False)

    @guarded
    def save_project(self, save_as=False):
        path = self.project_path
        if save_as or path is None:
            path, _ = W.QFileDialog.getSaveFileName(self, "Guardar proyecto", str(user_projects_dir() / "Proyecto.pforge"), "PhoenixForge (*.pforge)")
            if not path:
                return False
            if not path.lower().endswith(".pforge"):
                path += ".pforge"
            path = Path(path)
        if not self.confirm_overwrite(path):
            return False
        self.project.save(path, overwrite=True)
        self.project_path, self.dirty = Path(path), False
        self.studio.mark_saved()
        self.update_title()
        self.statusBar().showMessage("Proyecto e integridad guardados: " + Path(path).name, 7000)
        return True

    @guarded
    def new_source(self):
        name, ok = W.QInputDialog.getText(self, "Archivo fuente", "Ruta relativa dentro del proyecto:", text="modulo.v")
        if not ok:
            return
        safe_relative(name)
        if name.casefold() in {p.casefold() for p in self.project.files}:
            raise FileExistsError("Ya existe un archivo con ese nombre")
        self.project.files[name] = ""
        self.mark_dirty()
        self.studio.refresh_tree()
        self.studio.open_source(name)

    @guarded
    def import_sources(self):
        paths, _ = W.QFileDialog.getOpenFileNames(self, "Importar fuentes (no se ejecutan al importar)", "", "Fuentes (*.v *.sv *.vh *.svh *.vhd *.vhdl *.py *.cpp *.c *.h);;Todos (*)")
        for path in paths:
            name = Path(path).name
            if name in self.project.files:
                answer = W.QMessageBox.question(self, "Reemplazar fuente", "¿Reemplazar la fuente del proyecto?\n" + name,
                                               W.QMessageBox.Yes | W.QMessageBox.No, W.QMessageBox.No)
                if answer != W.QMessageBox.Yes:
                    continue
            self.project.import_file(path, overwrite=name in self.project.files)
            if name in self.studio.editors:
                self.studio.editors[name].setPlainText(self.project.files[name])
            self.studio.open_source(name)
            self.mark_dirty()
        self.studio.refresh_tree()
        self.studio.refresh_modules()

    @guarded
    def export_active_source(self):
        editor = self.studio.tabs.currentWidget()
        if not editor:
            return
        path, _ = W.QFileDialog.getSaveFileName(self, "Guardar archivo fuente", Path(editor.name).name, "Todos (*)")
        if path and self.confirm_overwrite(path):
            Path(path).write_text(editor.toPlainText(), encoding="utf-8")
            self.statusBar().showMessage("Archivo fuente exportado", 5000)

    @guarded
    def export_project(self):
        parent = W.QFileDialog.getExistingDirectory(self, "Seleccione la carpeta que contendrá la exportación")
        if not parent:
            return
        name, ok = W.QInputDialog.getText(self, "Nombre de carpeta nueva", "La carpeta no debe existir:", text="PhoenixForge_export")
        if ok:
            relative = safe_relative(name)
            if len(relative.parts) != 1:
                raise ValueError("Utilice un nombre simple de carpeta")
            export_bundle(self.project, Path(parent) / name)
            self.project.export_state["last_bundle"] = {"name": name, "utc": datetime.now(timezone.utc).isoformat()}
            self.mark_dirty()
            self.statusBar().showMessage("Exportados fuentes, testbench, resultados, manifiesto, puertos y .pforge", 9000)

    @guarded
    def export_digital(self, top=None):
        top = top if isinstance(top, str) and top else self.project.simulation.get("top", "")
        if not top:
            raise ValueError("Seleccione primero el módulo HDL principal en Estudio HDL")
        suggested = "PhoenixForge_" + "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in top) + "_Digital.zip"
        path, _ = W.QFileDialog.getSaveFileName(
            self, "Exportar componente Verilog para Digital", suggested, "Paquete Digital HDL (*.zip)")
        if not path:
            return False
        if not path.lower().endswith(".zip"):
            path += ".zip"
        if not self.confirm_overwrite(path):
            return False
        export_digital_component(self.project, path, top=top, overwrite=True)
        self.digital_export.set_last_export(path)
        self.project.export_state["last_digital"] = {
            "module": top, "filename": Path(path).name,
            "utc": datetime.now(timezone.utc).isoformat(),
            "format": "External File Verilog"
        }
        self.mark_dirty()
        W.QMessageBox.information(self, "Componente para Digital",
            "Paquete exportado:\n" + path +
            "\n\nEn Digital: añade External File → Verilog, selecciona component.v, "
            "configura Icarus y comprueba los puertos. El ZIP incluye "
            "symbol.svg y connections.svg, además de la guía de importación. "
            "Las vistas SVG no son un componente .dig ni un plugin de Tinkercad.")
        return True

    @guarded
    def open_vcd(self):
        path, _ = W.QFileDialog.getOpenFileName(self, "Abrir VCD", "", "VCD (*.vcd)")
        if path:
            if Path(path).stat().st_size > 24 * 1024 * 1024:
                raise ValueError("El visor admite archivos de hasta 24 MiB; use GTKWave")
            self.studio.wave.load(Path(path).read_bytes(), Path(path).name)
            self.navigate(1)
            self.studio.output_tabs.setCurrentWidget(self.studio.wave)

    @guarded
    def export_vcd(self):
        names = [name for name in self.project.artifacts if name.endswith(".vcd")]
        if not names:
            raise ValueError("No hay un VCD conservado en este proyecto")
        name, ok = W.QInputDialog.getItem(self, "Exportar VCD", "Traza:", names, 0, False)
        if ok:
            path, _ = W.QFileDialog.getSaveFileName(self, "Guardar VCD", Path(name).name, "VCD (*.vcd)")
            if path and self.confirm_overwrite(path):
                Path(path).write_bytes(self.project.artifacts[name])

    @guarded
    def verify_project(self):
        self.project.validate()
        if self.project_path:
            Project.open(self.project_path)
        W.QMessageBox.information(self, "Integridad", "Proyecto en memoria válido." + ("\nContenedor guardado y hashes SHA-256 válidos." if self.project_path else "\nTodavía no se ha guardado un contenedor."))

