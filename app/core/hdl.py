"""Lightweight HDL indexing, not a compiler. Icarus owns syntax validation."""
import re
from dataclasses import dataclass

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def identifier(name):
    if not isinstance(name, str) or not IDENTIFIER.fullmatch(name):
        raise ValueError("Identificador HDL no válido: %r" % name)
    return name


def strip_comments(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', lambda m: "\n" * m.group().count("\n"), text, flags=re.S)


def modules(files):
    result = []
    for path, text in files.items():
        if path.lower().endswith((".v", ".sv")):
            for match in re.finditer(r"\bmodule\s+([A-Za-z_][\w$]*)", strip_comments(text)):
                name = match.group(1)
                result.append({"name": name, "file": path, "testbench_hint": name.lower().startswith("tb_") or name.lower().endswith("_tb")})
    return result


def ports(text, module_name):
    """Literal-width ANSI / non-ANSI declarations. Refuse ambiguous widths.

    No parameter elaboration, interfaces, structs, macros or escaped names.
    A real elaborator can implement LanguageAdapter later.
    """
    identifier(module_name)
    clean = strip_comments(text)
    match = re.search(r"\bmodule\s+" + re.escape(module_name) + r"\b(.*?)\bendmodule\b", clean, re.S)
    if not match:
        raise ValueError("Módulo no encontrado")
    body = match.group(1)
    found = []
    # End each declaration at another direction, semicolon or closing header.
    pattern = r"\b(input|output|inout)\s+(.+?)(?=\b(?:input|output|inout)\b|;|\)\s*;)"
    for direction, declaration in re.findall(pattern, body, re.S):
        declaration = re.sub(r"\b(wire|reg|logic|signed|unsigned)\b", "", declaration).strip().rstrip(",")
        width, msb, lsb = 1, None, None
        bus = re.match(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*", declaration)
        if bus:
            msb, lsb = int(bus[1]), int(bus[2])
            width = abs(msb - lsb) + 1
            declaration = declaration[bus.end():]
        elif "[" in declaration:
            raise ValueError("Ancho parametrizado o arreglo: requiere elaboración externa")
        for name in declaration.split(","):
            name = name.strip()
            identifier(name)
            found.append({"name": name, "direction": direction, "width": width, "msb": msb, "lsb": lsb})
    if not found or len({p["name"] for p in found}) != len(found):
        raise ValueError("Puertos no reconocidos o duplicados; solo declaraciones Verilog simples")
    return found


@dataclass
class Diagnostic:
    file: str
    line: int
    severity: str
    message: str


def diagnostics(output):
    result = []
    for line in output.splitlines():
        match = re.match(r"^(.*?):(\d+):\s*(.*)$", line)
        if match:
            message = match[3]
            if "$finish called" in message:
                continue
            result.append(Diagnostic(match[1], int(match[2]), "warning" if "warning" in message.lower() else "error", message))
        elif line.lower().startswith("warning:"):
            result.append(Diagnostic("", 0, "warning", line))
    return result

