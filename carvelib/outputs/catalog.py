"""Element catalog: one actual-size SVG per element, plus a printable catalog PDF showing each
element at its default size with its anchors, size range and notes."""
import math
import os
import textwrap
from ..element import REGISTRY
from ..geometry import f, HARDWARE, BG as BG_
from .common import to_pdf, uniquify

PW, PH = 1100, 850
F = 'font-family="Helvetica, Arial, sans-serif"'
CELL_W, CELL_H = 500, 215


def _opts(el):
    if el.category == "fills":
        return {"uid": f"fill_{el.name}"}
    if el.name == "mokko_cartouche":
        return {"text": "JPL"}
    return {}


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
        o = [f'<text x="50" y="55" font-size="22" font-weight="bold" fill="#222" {F}>Carving elements</text>',
             f'<text x="50" y="78" font-size="12" fill="#555" {F}>Each element at its default size (print at 100%). '
             f'Red dots = anchors where stems attach; the tick shows the direction a stem leaves.</text>']
        for i, el in enumerate(els[p:p + per_page]):
            cx = 50 + (i % 2) * CELL_W
            cy = 105 + (i // 2) * CELL_H
            o.append(_cell(el, cx, cy, p + i))
        pages.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="11in" height="8.5in" viewBox="0 0 {PW} {PH}">'
                     f'<rect width="{PW}" height="{PH}" fill="#fff"/>{"".join(o)}</svg>')
    pages.append(products_page())
    to_pdf(pages, os.path.join(out_dir, "catalog.pdf"))
    print(f"catalog: {len(els)} elements -> {out_dir}/catalog.pdf and {out_dir}/svg/")


def products_page():
    """One page showing every product shape with its default panels, folds, stitching and marks."""
    from ..products import PRODUCTS
    from ..assemble import poly_d
    o = [f'<text x="50" y="55" font-size="22" font-weight="bold" fill="#222" {F}>Products</text>',
         f'<text x="50" y="78" font-size="12" fill="#555" {F}>Product shapes at reduced size. Grey = default carving panels '
         f'(use them by name under panels:). Dashed = stitching, dash-dot = folds, red = hardware.</text>']
    names = [n for n in PRODUCTS if n != "custom"]
    cols, cw, ch = 4, 250, 232
    for i, n in enumerate(names):
        pr = PRODUCTS[n]({})
        cx, cy = 50 + (i % cols) * cw, 100 + (i // cols) * ch
        x0, y0, x1, y1 = pr.outline.bounds
        s = min((cw - 30) / (x1 - x0 + 20), (ch - 75) / (y1 - y0 + 20))
        g = [f'<path d="{poly_d(pr.outline)}" fill="#fff" stroke="#111" stroke-width="{2/s:.2f}"/>']
        shown = {k: v for k, v in pr.panels.items() if k != "whole"} or pr.panels
        for name, poly in shown.items():
            g.append(f'<path d="{poly_d(poly)}" fill="{BG_}" stroke="#111" stroke-width="{1/s:.2f}"/>')
            c = poly.representative_point()
            g.append(f'<text x="{c.x:.1f}" y="{c.y:.1f}" font-size="{11/s:.1f}" text-anchor="middle" fill="#555" {F}>{name}</text>')
        for kind, pts in pr.folds:
            g.append('<path d="M' + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) +
                     f'" fill="none" stroke="#666" stroke-width="{0.8/s:.2f}" stroke-dasharray="{(6 if kind == "crease" else 10)/s:.1f} {4/s:.1f}"/>')
        for pts in pr.stitch:
            g.append('<path d="M' + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) +
                     f'" fill="none" stroke="#555" stroke-width="{0.8/s:.2f}" stroke-dasharray="{3/s:.1f} {3/s:.1f}"/>')
        g += pr.marks
        o.append(f'<rect x="{cx}" y="{cy}" width="{cw - 15}" height="{ch - 12}" fill="none" stroke="#ccc"/>')
        o.append(f'<text x="{cx + 10}" y="{cy + 20}" font-size="13" font-weight="bold" fill="#222" {F}>{n}</text>')
        w_in, h_in = (x1 - x0) / 100, (y1 - y0) / 100
        o.append(f'<text x="{cx + 10}" y="{cy + 35}" font-size="9.5" fill="#666" {F}>default {w_in:.4g}" × {h_in:.4g}"'
                 f'{" · also: whole" if "whole" in pr.panels else ""}</text>')
        o.append(f'<g transform="translate({cx + (cw - 15 - (x1 - x0) * s) / 2 - x0 * s:.1f} {cy + 45 - y0 * s:.1f}) scale({s:.4f})">{"".join(g)}</g>')
    o.append(f'<text x="50" y="{100 + ((len(names) - 1) // cols + 1) * ch + 10}" font-size="11" fill="#555" {F}>'
             f'Also: custom (any outline from points). Every product takes its own measurements — see README.</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="11in" height="8.5in" viewBox="0 0 {PW} {PH}">'
            f'<rect width="{PW}" height="{PH}" fill="#fff"/>{"".join(o)}</svg>')
