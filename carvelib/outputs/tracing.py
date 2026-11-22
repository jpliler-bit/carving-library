"""Actual-size tracing PDF on US Letter (landscape). Long designs are split into 10" segments that
overlap by 1/2"; line up the inch numbers on the rulers when tracing."""
from ..assemble import ruler_svg
from ..geometry import BG, MARK, HARDWARE
from .common import uniquify, to_pdf

PW, PH = 1100, 850
F = 'font-family="Helvetica, Arial, sans-serif"'
SEG, OVER = 1000, 50


def _text(x, y, t, size=12, bold=False, color="#222", anchor="start"):
    w = ' font-weight="bold"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}"{w} fill="{color}" text-anchor="{anchor}" {F}>{t}</text>'


def _header(d, page, pages):
    return (_text(50, 58, d.name, 22, True)
            + _text(50, 82, f'{d.r["product"]["width"]}" × {d.r["product"]["length"]}" · page {page} of {pages}', 12.5)
            + _text(50, 102, "PRINT AT 100% / ACTUAL SIZE — check the 1\" square before tracing.", 12.5, True, HARDWARE)
            + f'<rect x="950" y="30" width="100" height="100" fill="none" stroke="#111" stroke-width="1.5"/>'
            + _text(1000, 85, '1" × 1"', 13, anchor="middle"))


def _segment(d, body, x0, x1, px, py, label, k):
    w = x1 - x0
    return (_text(px, py + 14, label, 13, True)
            + f'<svg x="{px}" y="{py + 20}" width="{w}" height="{d.W + 60}" viewBox="{x0} -14 {w} {d.W + 60}" overflow="hidden">'
            + uniquify(body, f"_s{k}") + ruler_svg(d.W + 8, max(0, x0), x1) + "</svg>")


def _key(y):
    rows = [
        (f'<line x1="0" y1="0" x2="40" y2="0" stroke="#111" stroke-width="1.6"/>', "Swivel-knife cut, then bevel away from the motif"),
        (f'<line x1="0" y1="0" x2="40" y2="0" stroke="#111" stroke-width="0.9"/>', "Decorative cut / modeling line"),
        (f'<circle cx="20" cy="0" r="2.5" fill="#111"/>', "Seeder (stamen tips, flower centres)"),
        (f'<rect x="0" y="-8" width="40" height="16" fill="{BG}" stroke="#111" stroke-width="0.8"/>'
         f'<path d="M6,3 Q11,6 16,-2 M22,4 Q27,7 32,-1" stroke="{MARK}" fill="none"/>', "Ground: grey strokes = knife-mark stamp direction (don't trace)"),
        (f'<line x1="0" y1="0" x2="40" y2="0" stroke="{HARDWARE}" stroke-width="1.2" stroke-dasharray="5 4"/>', "Red = reference only (cut lines, buckle slot, keeper, holes)"),
    ]
    o = [_text(50, y, "Key", 14, True)]
    for i, (sym, t) in enumerate(rows):
        yy = y + 22 + i * 19
        o.append(f'<g transform="translate(50,{yy - 4})">{sym}</g>' + _text(105, yy, t, 11.5))
    return "".join(o)


def pdf(d, out_pdf):
    body = d.body()
    L = d.Lp
    segs = []
    x = -10
    while True:
        x1 = min(x + SEG, L + 12)
        segs.append((x, x1))
        if x1 >= L + 12:
            break
        x = x1 - OVER
    seg_h = d.W + 80
    per_page = max(1, int((PH - 150) // seg_h))
    pages_segs = [segs[i:i + per_page] for i in range(0, len(segs), per_page)]
    detail = len(segs) == 1 and L <= 800
    dscale = min(2.0, 1000 / (L + 20))
    key_needs_page = False
    used_last = 160 + len(pages_segs[-1]) * seg_h + (dscale * d.W + 40 if detail else 0)
    if used_last + 135 > PH:
        key_needs_page = True
    total = len(pages_segs) + (1 if key_needs_page else 0)
    pages, k = [], 0
    for pi, group in enumerate(pages_segs):
        o = [_header(d, pi + 1, total)]
        y = 150
        for (a, b) in group:
            lab = f'Actual size · {max(0, a)/100:.1f}"–{min(b, L)/100:.1f}"' if len(segs) > 1 else "Actual size"
            o.append(_segment(d, body, a, b, 50, y, lab, k))
            k += 1
            y += seg_h
        if detail and pi == 0:
            o.append(_text(50, y + 4, f"{dscale:.1f}× detail (reference — don't trace this one)", 13, True))
            o.append(f'<g transform="translate(60,{y + 14}) scale({dscale:.3f})">{uniquify(body, "_d")}</g>')
            y += dscale * d.W + 40
        if pi == len(pages_segs) - 1 and not key_needs_page:
            o.append(_key(max(y + 10, PH - 125)))
        pages.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="11in" height="8.5in" viewBox="0 0 {PW} {PH}">'
                     f'<rect width="{PW}" height="{PH}" fill="#fff"/>{"".join(o)}</svg>')
    if key_needs_page:
        pages.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="11in" height="8.5in" viewBox="0 0 {PW} {PH}">'
                     f'<rect width="{PW}" height="{PH}" fill="#fff"/>{_header(d, total, total)}{_key(170)}</svg>')
    to_pdf(pages, out_pdf)
    return out_pdf
