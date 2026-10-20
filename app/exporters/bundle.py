import json
import os
import shutil
import tempfile
from pathlib import Path

from app.core.hdl import modules, ports
from app.utils.paths import confined


def port_metadata(project):
    result = {"format": "PhoenixForge ports", "schema_version": 1, "device": project.device,
              "scope": "Logical ports only; pin assignments are user metadata, not electrically validated",
              "modules": []}
    for module in modules(project.files):
        record = dict(module)
        try:
            record["ports"] = ports(project.files[module["file"]], module["name"])
            record["status"] = "parsed_literal_declarations"
            for port in record["ports"]:
                port["physical_pin"] = project.pins.get(port["name"])
        except ValueError as error:
            record["ports"] = []
            record["status"] = "requires_elaboration"
            record["reason"] = str(error)
        result["modules"].append(record)
    return result


def export_bundle(project, destination):
    """Create an entirely new folder atomically; never merge into existing files."""
    project.validate()
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("Seleccione un nombre de carpeta nuevo")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".pforge-export-", dir=str(destination.parent)))
    try:
        project.write_sources(staging / "src")
        for name, data in project.artifacts.items():
            path = confined(staging / "results", name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (staging / "manifest.json").write_text(json.dumps(project.manifest(), indent=2, ensure_ascii=False), encoding="utf-8")
        (staging / "ports.json").write_text(json.dumps(port_metadata(project), indent=2, ensure_ascii=False), encoding="utf-8")
        project.save(staging / "project.pforge")
        (staging / "README.txt").write_text(
            "PhoenixForge export\nSources, testbenches and results are separate.\n"
            "ports.json only parses literal Verilog port declarations; unresolved modules are marked.\n"
            "Python/C++ files are inert source attachments, not converted hardware.\n"
            "No FPGA bitstream or programming support is included.\n", encoding="utf-8")
        if destination.exists():
            raise FileExistsError(destination)
        os.rename(str(staging), str(destination))
    finally:
        if staging.exists():
            shutil.rmtree(str(staging))
    return destination

