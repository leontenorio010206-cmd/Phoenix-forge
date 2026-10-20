"""Deterministic, escaped SVG previews for Digital External File components.

SVG files are *visual references*, not an automatically installed .dig symbol.
Port coordinates and labels come from the Verilog parser, never guessed pins.
"""
from html import escape


def _txt(value):
    return escape(str(value), quote=True)


def _rect(x, y, w, h, fill, stroke, radius=9, stroke_width=2):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" '
            'fill="%s" stroke="%s" stroke-width="%s"/>' %
            (x, y, w, h, radius, fill, stroke, stroke_width))


def _text(x, y, content, size=17, color="#E6F1FF", anchor="start", weight=400):
    return ('<text x="%s" y="%s" text-anchor="%s" font-family="DejaVu Sans,Segoe UI,sans-serif" '
            'font-size="%s" font-weight="%s" fill="%s">%s</text>' %
            (x, y, anchor, size, weight, color, _txt(content)))


def build_component_svg(top, pinout, connections=False):
    """Generate an SVG with the actual HDL input/output ports and bus widths."""
    left = [p for p in pinout if p["direction"] == "input"]
    right = [p for p in pinout if p["direction"] == "output"]
    if len(left) + len(right) > 80:
        raise ValueError("Demasiados puertos para la vista previa SVG")
    count = max(1, len(left), len(right))
    spacing = 38
    h = max(330, 160 + (count - 1) * spacing)
    w = 1130 if connections else 850
    chip_x, chip_w = (430, 285) if connections else (285, 280)
    chip_y, chip_h = 92, max(156, 70 + count * spacing)
    input_x = chip_x - 68
    output_x = chip_x + chip_w + 68
    y0 = chip_y + 64
    title = _txt(top)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (w,h,w,h),
           '<defs><linearGradient id="chip" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0%" stop-color="#162E49"/><stop offset="100%" stop-color="#152135"/>'
           '</linearGradient><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
           '<path d="M24 0H0V24" fill="none" stroke="#29415A" stroke-width=".55"/></pattern></defs>',
           _rect(1, 1, w-2, h-2, "#081321", "#253D56", 13),
           '<rect x="2" y="2" width="%d" height="%d" fill="url(#grid)" opacity=".8"/>' % (w-4,h-4),
           _text(26, 35, "PHŒNIXFORGE / " + ("ESQUEMA ILUSTRATIVO" if connections else "SÍMBOLO HDL"), 14, "#78AEDD", weight=700)]
    out.append(_rect(chip_x, chip_y, chip_w, chip_h, "url(#chip)", "#FFAB67", 15, 2.5))
    out.append(_text(chip_x+chip_w/2, chip_y+chip_h/2, top, 21 if len(top)<25 else 15, "#FFFFFF", "middle", 700))
    out.append(_text(chip_x+chip_w/2, chip_y+chip_h/2+25, "RTL / Verilog", 13, "#96BDDA", "middle"))
    for side, group in (("input", left), ("output", right)):
        for i, pin in enumerate(group):
            yy = y0 + i*spacing
            color = "#59B9FF" if side=="input" else "#FFB172"
            bus = (" [%d]" % pin["width"]) if pin["width"] > 1 else ""
            name = pin["name"] + bus
            if side == "input":
                out += ['<path d="M%d %dH%d" stroke="%s" stroke-width="3"/>' % (input_x,yy,chip_x,color),
                        '<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (input_x, yy, color),
                        _text(input_x-12,yy+5,name,15,"#C2DAEB","end",600)]
            else:
                out += ['<path d="M%d %dH%d" stroke="%s" stroke-width="3"/>' % (chip_x+chip_w,yy,output_x,color),
                        '<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (output_x,yy,color),
                        _text(output_x+12,yy+5,name,15,"#F7D9C1","start",600)]
            if connections:
                if side == "input":
                    terminal_x = 45
                    out += [_rect(terminal_x, yy-15, 118, 30, "#102A42", "#3776B5", 6, 1),
                            _text(terminal_x+59, yy+5, "CLOCK" if pin["name"].lower() in ("clk","clock") else "SWITCH / BUS", 11, "#AEDDFF","middle"),
                            '<path d="M163 %dH%d" stroke="#3EA7EF" stroke-width="2"/>' % (yy, input_x)]
                else:
                    terminal_x = w-154
                    out += ['<path d="M%d %dH%d" stroke="#E8A66C" stroke-width="2"/>' % (output_x,yy,terminal_x),
                            _rect(terminal_x, yy-15, 115, 30, "#26202C", "#B86E50", 6, 1),
                            '<circle cx="%d" cy="%d" r="8" fill="#FCAD67"/>' % (terminal_x+17, yy),
                            _text(terminal_x+69,yy+5,"LED / BUS",11,"#F9D6BE","middle")]
    out += [_text(26,h-20,"Conexiones de referencia, sin simulación de señales ni asignación física de pines.",12,"#819BB4"),
            '</svg>']
    return ("\n".join(out)+"\n").encode("utf-8")
