"""Export a *working Verilog External File* component for hneemann/Digital.

This is not a Java plugin JAR and is not an Autodesk/Tinkercad extension.
Digital's External File component invokes installed Icarus for the HDL model.
"""
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from app.core.hdl import modules, ports, identifier
from app.devices.catalog import load_profiles
from app.utils.paths import safe_relative
from app.exporters.digital_symbol import build_component_svg

MAX_SOURCE_BYTES = 2 * 1024 * 1024


def _embedded_source(project, path, stack=()):
    if path in stack:
        raise ValueError("Include HDL circular: " + " → ".join(stack + (path,)))
    if path not in project.files:
        raise ValueError("Archivo HDL no encontrado: " + path)
    if len(stack) > 12:
        raise ValueError("Demasiados includes anidados")
    text = project.files[path]
    def inline(match):
        include = match.group(1)
        safe_relative(include)
        direct = (PurePosixPath(path).parent / include).as_posix()
        target = direct if direct in project.files else include
        if target not in project.files:
            raise ValueError("Include faltante: " + include)
        return "// Comienzo include: " + target + "\n" + _embedded_source(project, target, stack + (path,)) + "\n"
    return re.sub(r'`include\s+"([^"\r\n]+)"', inline, text)


def digital_component_files(project, top=None):
    """Create one self-contained source file and a machine-readable port manifest."""
    project.validate()
    if project.device not in load_profiles():
        raise ValueError("Perfil FPGA desconocido")
    top = identifier(top or project.simulation.get("top", ""))
    found = [m for m in modules(project.files) if m["name"] == top]
    if len(found) != 1:
        raise ValueError("Seleccione un módulo principal único y existente")
    pinout = ports(project.files[found[0]["file"]], top)
    if any(p["direction"] not in ("input", "output") for p in pinout):
        raise ValueError("Digital: puertos inout requieren una integración posterior")
    if any(p["width"] > 32 for p in pinout):
        raise ValueError("Digital: máximo 32 bits por puerto en este exportador")
    included = []
    for path in sorted(project.files):
        if not path.lower().endswith((".v", ".sv")):
            continue
        # Exclude separate testbenches, not design modules.
        filename = PurePosixPath(path).name.lower()
        if filename.startswith("tb_") or filename.endswith("_tb.v") or filename.endswith("_tb.sv"):
            continue
        included.append("// Origen: " + path + "\n" + _embedded_source(project, path))
    if not included:
        raise ValueError("No se encontraron fuentes HDL para exportación")
    merged = "\n\n".join(included).encode("utf-8")
    if len(merged) > MAX_SOURCE_BYTES:
        raise ValueError("La fuente para Digital supera 2 MiB")
    digest = hashlib.sha256(merged).hexdigest()
    manifest = {
        "format": "PhoenixForge-Digital-HDL-ExternalFile",
        "version": 1, "project_name": project.name, "device_profile": project.device,
        "top": top, "source": "component.v", "sha256": digest,
        "ports": pinout, "engine": "Icarus Verilog",
        "symbol_preview": "symbol.svg", "wiring_preview": "connections.svg",
        "scope": "RTL functional; no chip timing, physical pins, JTAG or bitstream",
    }
    readme = """PhœnixForge — componente HDL para Digital (Helmut Neemann)

Este paquete NO es un JAR ni un plugin de Tinkercad. Digital admite módulos
Verilog mediante el componente External File y un Icarus Verilog instalado.
La lógica que se simula es tu HDL; el perfil FPGA es informativo.

1. Descomprime todos los archivos en una carpeta permanente.
2. Abre Digital (versión compatible con External File).
3. Añade el componente External File al circuito desde la biblioteca de Digital.
4. Selecciona Verilog e indica el archivo component.v de esta carpeta.
5. Elige Icarus Verilog en los ajustes de Digital y pulsa Check / Comprobar
   para identificar las entradas y salidas, revisándolas con ports.json.
6. Conecta interruptores, relojes y LED a los puertos indicados.
7. Ejecuta la simulación de Digital y guarda el circuito .dig JUNTO
   a la carpeta del componente, para no perder la ruta del HDL.

El proyecto debe ser compatible con el lenguaje Verilog aceptado por Digital.
No se incluyen Icarus, Digital ni plugins Java de terceros.
Limitaciones: los includes locales se integran al archivo; los parámetros,
IP de fabricante, modelos analógicos y pines de encapsulado no se emulan.
Para publicar un JAR de Digital se necesita otro adaptador de su API Java.

Archivos visuales adicionales:
- symbol.svg: representación automática del bloque con sus puertos HDL.
- connections.svg: ejemplo visual de interruptores/reloj y salidas LED.
Son diagramas de referencia, NO archivos .dig ni librerías Java.
Digital permite importar SVG como forma personalizada en algunos tipos de
componentes, pero no se instala automáticamente como símbolo del componente
External File. El circuito debe enlazarse a component.v de forma manual.
El gráfico no representa pines físicos de una FPGA.

Digital oficial: https://github.com/hneemann/Digital
Documentación de External File: https://github.com/hneemann/Digital/discussions/798
"""
    return {
        "component.v": merged,
        "ports.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        "LEEME_DIGITAL.txt": readme.encode("utf-8"),
        "symbol.svg": build_component_svg(top, pinout),
        "connections.svg": build_component_svg(top, pinout, connections=True)
    }


def export_digital_component(project, path, top=None, overwrite=False):
    """Write an atomic, verifiable ZIP with no arbitrary source paths."""
    files = digital_component_files(project, top)
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError("Archivo destino existente: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    import os
    import tempfile
    fd, temporary = tempfile.mkstemp(prefix=".pf-digital-", suffix=".zip", dir=str(path.parent))
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for filename, data in files.items():
                archive.writestr(filename, data)
        if not overwrite and path.exists():
            raise FileExistsError(str(path))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path
