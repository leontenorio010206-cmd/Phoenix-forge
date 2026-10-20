"""Bounded digital VCD reader and small internal-lab trace writer."""
import re
from dataclasses import dataclass, field


@dataclass
class Signal:
    name: str
    code: str
    width: int
    events: list = field(default_factory=list)


@dataclass
class Trace:
    signals: list
    timescale: str = "1ns"
    end: int = 0


def parse_vcd(data, max_events=200000, max_signals=256):
    if len(data) > 24 * 1024 * 1024:
        raise ValueError("VCD demasiado grande para el visor integrado")
    if isinstance(data, bytes):
        data = data.decode("ascii", errors="replace")
    marker = re.search(r"\$enddefinitions\s+\$end", data)
    if not marker:
        raise ValueError("VCD sin cabecera válida")
    header, body = data[:marker.end()], data[marker.end():]
    scale = re.search(r"\$timescale\s+(.+?)\s*\$end", header, re.S)
    trace = Trace([], "".join(scale[1].split()) if scale else "1ns")
    scopes, by_code = [], {}
    for directive in re.findall(r"\$(?:scope|upscope|var)\s+.*?\$end", header, re.S):
        parts = directive.split()
        if parts[0] == "$scope":
            scopes.append(parts[2])
        elif parts[0] == "$upscope":
            if scopes:
                scopes.pop()
        else:
            width, code, name = int(parts[2]), parts[3], parts[4]
            if not 1 <= width <= 4096 or len(trace.signals) >= max_signals:
                raise ValueError("El visor admite hasta 256 señales de 4096 bits")
            signal = Signal(".".join(scopes + [name]), code, width)
            trace.signals.append(signal)
            by_code.setdefault(code, []).append(signal)
    time, count = 0, 0
    token_pattern = r"#[0-9]+|[bB][01xXzZ]+\s+\S+|[01xXzZ][^\s]+|\$[^\s]+"
    for token in re.findall(token_pattern, body):
        if token.startswith("#"):
            following = int(token[1:])
            if following < time:
                raise ValueError("Tiempo VCD no monotónico")
            time = following
            trace.end = max(trace.end, time)
            continue
        if token[0] in "bB":
            value, code = token[1:].split()
        elif token[0] in "01xXzZ":
            value, code = token[0], token[1:]
        else:
            continue
        for signal in by_code.get(code, []):
            signal.events.append((time, value.lower()))
            count += 1
            if count > max_events:
                raise ValueError("El visor admite hasta 200000 cambios; use GTKWave")
    return trace


def digital_vcd(names, samples, timescale="1ns"):
    if len(names) > 90:
        raise ValueError("Demasiadas señales")
    codes = {name: chr(33 + i) for i, name in enumerate(names)}
    lines = ["$version PhoenixForge internal educational engine $end", "$timescale %s $end" % timescale,
             "$scope module laboratory $end"]
    lines.extend("$var wire 1 %s %s $end" % (codes[name], name) for name in names)
    lines += ["$upscope $end", "$enddefinitions $end"]
    for time, values in samples:
        lines.append("#%d" % time)
        lines.extend("%d%s" % (int(values[name]), codes[name]) for name in names)
    return ("\n".join(lines) + "\n").encode("ascii")

