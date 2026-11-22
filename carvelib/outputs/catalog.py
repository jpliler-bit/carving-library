"""Element catalog: one actual-size SVG per element, plus a printable catalog PDF showing each
element at its default size with its anchors, size range and notes."""
import math
import os
import textwrap
from ..element import REGISTRY
from ..geometry import f, HARDWARE
from .common import to_pdf, uniquify

PW, PH = 1100, 850
F = 'font-family="Helvetica, Arial, sans-serif"'
CELL_W, CELL_H = 500, 215


def _opts(el):
    return {"uid": f"sg_{el.name}"} if el.name == "seigaiha" else {}


def element_svg(el, size=None, anchors=True):
    size = el.size_default if size is None else size
    x0, y0, x1, y1 = el.extent(size, **_opts(el))
    pad = 20
    w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    body = el.draw(size, **_opts(el))
    marks = _anchor_marks(el, size) if anchors else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(w/100)}in" height="{f(h/100)}in" '
            f'viewBox="{f(x0-pad)} {f(y0-pad)} {f(w)} {f(h)}"><rect x="{f(x0-pad)}" y="{f(y0-pad)}" width="{f(w)}" '
            f'height="{f(h)}" fill="#fff"/>{body}{marks}</svg>')


def _anchor_marks(el, size):
    o = []
    for name, (x, y, ang) in el.anchors(size, **_opts(el)).items():
        a = math.radians(ang)
        x2, y2 = x + 16 * math.cos(a), y + 16 * math.sin(a)
        o.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="2.6" fill="{HARDWARE}"/>'
                 f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{HARDWARE}" stroke-width="1.2"/>'
                 f'<text x="{f(x2 + 3*math.cos(a))}" y="{f(y2 + 3*math.sin(a) + 3)}" font-size="7" fill="{HARDWARE}" '
                 f'text-anchor="{"end" if math.cos(a) < -0.3 else "start"}" {F}>{name}</text>')
    return "".join(o)


def _cell(el, cx, cy, k):
    size = el.size_default
    x0, y0, x1, y1 = el.extent(size, **_opts(el))
    # drawing area: left 300 units of the cell, element at ACTUAL size (shrunk only if it can't fit)
    s = min(1.0, 270 / (x1 - x0), 150 / (y1 - y0))
    ox = cx + 150 - (x0 + x1) / 2 * s
    oy = cy + 105 - (y0 + y1) / 2 * s
    art = uniquify(el.draw(size, **_opts(el)) + _anchor_marks(el, size), f"_c{k}")
    o = [f'<rect x="{cx}" y="{cy}" width="{CELL_W - 20}" height="{CELL_H - 15}" fill="none" stroke="#ccc" stroke-width="1"/>',
         f'<g transform="translate({f(ox)} {f(oy)}) scale({f(s)})">{art}</g>']
    tx, ty = cx + 305, cy + 24
    note = "actual size" if s == 1 else f"shown at {s:.0%}"
    o.append(f'<text x="{tx}" y="{ty}" font-size="14" font-weight="bold" fill="#222" {F}>{el.name}</text>')
    o.append(f'<text x="{tx}" y="{ty+17}" font-size="10" fill="#666" {F}>{el.category} · {note}</text>')
    o.append(f'<text x="{tx}" y="{ty+36}" font-size="10.5" fill="#222" {F}>size {el.size_default}" '
             f'(range {el.size_min}–{el.size_max}")</text>')
    notes = textwrap.wrap(el.size_note, 40)[:2]
    for i, ln in enumerate(notes):
        o.append(f'<text x="{tx}" y="{ty+50+i*12}" font-size="9.5" fill="#666" {F}>{ln}</text>')
    y2 = ty + 56 + 12 * len(notes)
    for i, ln in enumerate(textwrap.wrap(el.description, 36)[:9]):
        o.append(f'<text x="{tx}" y="{y2+10+i*13}" font-size="9.5" fill="#333" {F}>{ln}</text>')
    return "".join(o)


def build(out_dir):
    os.makedirs(os.path.join(out_dir, "svg"), exist_ok=True)
    els = sorted(REGISTRY.values(), key=lambda e: (e.category, e.name))
    for el in els:
        with open(os.path.join(out_dir, "svg", f"{el.name}.svg"), "w") as fh:
            fh.write(element_svg(el))
    per_page = 6
    pages = []
    for p in range(0, len(els), per_page):
        o = [f'<text x="50" y="55" font-size="22" font-weight="bold" fill="#222" {F}>Carving element library</text>',
             f'<text x="50" y="78" font-size="12" fill="#555" {F}>Each element at its default size (print at 100%). '
             f'Red dots = anchors where stems attach; the tick shows the direction a stem leaves.</text>']
        for i, el in enumerate(els[p:p + per_page]):
            cx = 50 + (i % 2) * CELL_W
            cy = 105 + (i // 2) * CELL_H
            o.append(_cell(el, cx, cy, p + i))
        pages.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="11in" height="8.5in" viewBox="0 0 {PW} {PH}">'
                     f'<rect width="{PW}" height="{PH}" fill="#fff"/>{"".join(o)}</svg>')
    to_pdf(pages, os.path.join(out_dir, "catalog.pdf"))
    print(f"catalog: {len(els)} elements -> {out_dir}/catalog.pdf and {out_dir}/svg/")
