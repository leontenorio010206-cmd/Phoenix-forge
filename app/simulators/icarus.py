"""Real Icarus integration with cancellation, timeout and bounded logs."""
import json
import logging
import os
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from app.core.contracts import Simulator
from app.core.hdl import identifier, modules, diagnostics
from app.utils.paths import data_dir, safe_relative, bundled_icarus
from app.utils.platform import process_options, stop_process

LOG_LIMIT = 2 * 1024 * 1024
ARTIFACT_LIMIT = 24 * 1024 * 1024


@dataclass
class SimulationResult:
    success: bool
    directory: str
    output: str = ""
    diagnostics: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)
    commands: list = field(default_factory=list)
    reason: str = ""


def find_executable(configured, default):
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        return shutil.which(configured)
    return shutil.which(default)


class IcarusEngine(Simulator):
    def __init__(self, iverilog="", vvp=""):
        self.bundle = bundled_icarus() if not iverilog and not vvp else None
        if self.bundle:
            iverilog, vvp = str(self.bundle / "bin/iverilog.exe"), str(self.bundle / "bin/vvp.exe")
        self.iverilog = find_executable(iverilog, "iverilog")
        self.vvp = find_executable(vvp, "vvp")

    @property
    def available(self):
        return bool(self.iverilog and self.vvp)

    def _execute(self, command, cwd, log, timeout, cancel):
        with open(log, "wb") as stream:
            environment = os.environ.copy()
            if self.bundle:
                environment["PATH"] = str(self.bundle / "bin") + os.pathsep + environment.get("PATH", "")
            process = subprocess.Popen(command, cwd=str(cwd), stdout=stream, stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL, shell=False, env=environment, **process_options())
            deadline = time.monotonic() + timeout
            next_disk_check = 0.0
            try:
                while process.poll() is None:
                    reason = ""
                    now = time.monotonic()
                    if cancel.is_set():
                        reason = "Simulación cancelada"
                    elif now > deadline:
                        reason = "Tiempo máximo de ejecución agotado"
                    elif now >= next_disk_check:
                        # Avoid walking VCD trees 40 times/s on laptops with HDDs.
                        next_disk_check = now + 0.25
                        if Path(log).stat().st_size > LOG_LIMIT:
                            reason = "La salida excedió el límite de 2 MiB"
                        elif sum(p.stat().st_size for p in Path(cwd).rglob("*.vcd") if p.is_file()) > ARTIFACT_LIMIT:
                            reason = "El VCD excedió el límite de 24 MiB"
                    if reason:
                        stop_process(process)
                        raise RuntimeError(reason)
                    time.sleep(0.05)
                return process.returncode
            finally:
                if process.poll() is None:
                    stop_process(process)

    def run(self, project, root=None, cancel=None):
        cancel = cancel or threading.Event()
        project.validate()
        directory = Path(root or data_dir() / "runs").resolve() / project.project_id / uuid.uuid4().hex
        directory.mkdir(parents=True, exist_ok=False)
        result = SimulationResult(False, str(directory))
        logs = []
        try:
            if not self.available:
                raise RuntimeError("No se encontraron iverilog y vvp. En la distribución autónoma, deje las rutas vacías para usar el motor incluido. Desde fuentes, consulte docs/DEVELOPER_MANUAL.md.")
            top = project.simulation.get("testbench") or project.simulation.get("top")
            identifier(top)
            if top not in {m["name"] for m in modules(project.files)}:
                raise ValueError("El módulo raíz o testbench no existe en el proyecto")
            timeout = int(project.simulation.get("timeout", 15))
            if not 1 <= timeout <= 120:
                raise ValueError("El límite debe estar entre 1 y 120 segundos")
            # Includes must remain in the staged project; no absolute include paths.
            import re
            for name, source in project.files.items():
                if not name.lower().endswith((".v", ".sv", ".vh", ".svh")):
                    continue
                for include in re.findall(r'`include\s+"([^"]+)"', source):
                    safe_relative(include)
                    relative = str(PurePosixPath(name).parent / include)
                    if include not in project.files and relative not in project.files:
                        raise ValueError("Include ausente: " + include)
            source_dir = directory / "src"
            source_dir.mkdir()
            project.write_sources(source_dir)
            sources = [str(source_dir / name) for name in project.files if name.lower().endswith((".v", ".sv"))]
            if not sources:
                raise ValueError("No hay archivos Verilog para compilar")
            include_dirs = sorted({str(source_dir)} | {str((source_dir / n).parent) for n in project.files})
            command = [self.iverilog, "-g2012", "-Wall", "-s", top, "-o", str(directory / "simulation.vvp")]
            if self.bundle:
                command.extend(["-B", str(self.bundle / "lib/ivl")])
            for path in include_dirs:
                command.extend(["-I", path])
            command.extend(sources)
            result.commands.append(command)
            log = directory / "compile.log"
            logs.append(log)
            status = self._execute(command, directory, log, timeout, cancel)
            if status:
                raise RuntimeError("Compilación fallida (código %d)" % status)
            command = [self.vvp, "-N"]
            if self.bundle:
                command.extend(["-M", str(self.bundle / "lib/ivl")])
            command.append(str(directory / "simulation.vvp"))
            result.commands.append(command)
            log = directory / "simulation.log"
            logs.append(log)
            status = self._execute(command, directory, log, timeout, cancel)
            if status:
                raise RuntimeError("Simulación fallida (código %d)" % status)
            total = 0
            for path in sorted(directory.rglob("*.vcd")):
                if path.is_symlink() or not path.is_file():
                    continue
                path.resolve().relative_to(directory.resolve())
                total += path.stat().st_size
                if total > ARTIFACT_LIMIT:
                    raise RuntimeError("Los resultados excedieron 24 MiB")
                result.artifacts[str(path.relative_to(directory)).replace("\\", "/")] = path.read_bytes()
            result.success = True
            result.reason = "Compilación y ejecución terminadas (código 0)"
        except Exception as error:
            result.reason = str(error)
            logging.exception("Icarus: %s", error)
        for log in logs:
            if log.exists():
                with log.open("rb") as stream:
                    data = stream.read(LOG_LIMIT)
                result.artifacts[log.name] = data
                result.output += data.decode("utf-8", errors="replace") + "\n"
        result.output += result.reason
        result.diagnostics = diagnostics(result.output)
        summary = {"engine": "Icarus Verilog", "success": result.success, "reason": result.reason,
                   "commands": result.commands, "project_manifest": project.manifest()}
        data = json.dumps(summary, indent=2, ensure_ascii=False).encode("utf-8")
        result.artifacts["run.json"] = data
        (directory / "run.json").write_bytes(data)
        return result

