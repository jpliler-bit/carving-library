"""Actual-size tracing PDF on US Letter (landscape).

Narrow pieces (6" tall or less: belts, straps, wallets, card holders) are cut into 10"-wide strips
that overlap by 1/2", stacked on the page. Taller pieces (sheaths, notebook covers) are tiled in both
directions, one tile per page, with rulers on two edges; line up the ruler numbers when tracing."""
from ..assemble import ruler_svg, vruler_svg
from ..geometry import BG, MARK, HARDWARE
from .common import uniquify, to_pdf

PW, PH = 1100, 850
F = 'font-family="Helvetica, Arial, sans-serif"'
SEG, OVER = 1000, 50
TILE_W, TILE_H = 960, 600


def _text(x, y, t, size=12, bold=False, color="#222", anchor="start"):
    w = ' font-weight="bold"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}"{w} fill="{color}" text-anchor="{anchor}" {F}>{t}</text>'


def _header(d, page, pages):
    return (_text(50, 58, d.name, 22, True)
            + _text(50, 82, f'{d.prod.name.replace("_", " ")} · {d.Lp/100:g}" × {d.W/100:g}" · page {page} of {pages}', 12.5)
            + _text(50, 102, "PRINT AT 100% / ACTUAL SIZE — check the 1\" square before tracing.", 12.5, True, HARDWARE)
            + '<rect x="950" y="30" width="100" height="100" fill="none" stroke="#111" stroke-width="1.5"/>'
            + _text(1000, 85, '1" × 1"', 13, anchor="middle"))


def _key(y):
    rows = [
        ('<line x1="0" y1="0" x2="40" y2="0" stroke="#111" stroke-width="1.6"/>', "Swivel-knife cut, then bevel away from the motif"),
        ('<line x1="0" y1="0" x2="40" y2="0" stroke="#111" stroke-width="0.9"/>', "Decorative cut / modeling line"),
        ('<circle cx="20" cy="0" r="2.5" fill="#111"/>', "Seeder (stamen tips, flower centres)"),
        (f'<rect x="0" y="-8" width="40" height="16" fill="{BG}" stroke="#111" stroke-width="0.8"/>'
         f'<path d="M6,3 Q11,6 16,-2 M22,4 Q27,7 32,-1" stroke="{MARK}" fill="none"/>', "Ground: grey texture shows the backgrounder/stamp (don't trace)"),
        ('<line x1="0" y1="0" x2="40" y2="0" stroke="#555" stroke-width="1" stroke-dasharray="3 3"/>', "Stitch line · dash-dot = fold · grey dashes = edge crease"),
        (f'<line x1="0" y1="0" x2="40" y2="0" stroke="{HARDWARE}" stroke-width="1.2" stroke-dasharray="5 4"/>', "Red = reference only (holes, slots, cut lines)"),
    ]
    o = [_text(50, y, "Key", 14, True)]
    for i, (sym, t) in enumerate(rows):
        yy = y + 22 + i * 19
        o.append(f'<g transform="translate(50,{yy - 4})">{sym}</g>' + _text(105, yy, t, 11.5))
    return "".join(o)


def _page(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="11in" height="8.5in" viewBox="0 0 {PW} {PH}">'
            f'<rect width="{PW}" height="{PH}" fill="#fff"/>{body}</svg>')


def _window(d, body, x0, y0, w, h, px, py, k, rulers="bottom"):
    """Draw the region (x0, y0, w, h) of the design at actual size with its top-left at page (px, py)."""
    o = [f'<svg x="{px}" y="{py}" width="{w}" height="{h}" viewBox="{x0} {y0} {w} {h}" overflow="hidden">'
         + uniquify(body, f"_w{k}") + "</svg>"]
    o.append(f'<g transform="translate({px - x0} {py - y0})">' + ruler_svg(y0 + h + 6, max(0, x0), min(x0 + w, d.Lp)) + "</g>")
    if rulers == "both":
        o.append(f'<g transform="translate({px - x0} {py - y0})">' + vruler_svg(x0 - 6, max(0, y0), min(y0 + h, d.W), d.cy) + "</g>")
    return "".join(o)


def pdf(d, out_pdf):
    body = d.body()
    L, Hh = d.Lp, d.W
    pages = []
    if Hh <= 600:                                       # strips
        segs, x = [], -12
        while True:
            x1 = min(x + SEG, L + 12)
            segs.append((x, x1))
            if x1 >= L + 12:
                break
            x = x1 - OVER
        seg_h = Hh + 90
        per_page = max(1, int((PH - 150) // seg_h))
        groups = [segs[i:i + per_page] for i in range(0, len(segs), per_page)]
        detail = len(segs) == 1 and L <= 800
        dscale = min(2.0, 1000 / (L + 30), (PH - 150 - seg_h - 175) / (Hh + 30)) if detail else 0
        detail = detail and dscale >= 1.2
        used_last = 150 + len(groups[-1]) * seg_h + (dscale * Hh + 45 if detail else 0)
        key_page = used_last + 140 > PH
        total = len(groups) + (1 if key_page else 0)
        k = 0
        for pi, grp in enumerate(groups):
            o = [_header(d, pi + 1, total)]
            y = 150
            for a, b in grp:
                lab = f'Actual size · {max(0, a)/100:.1f}"–{min(b, L)/100:.1f}"' if len(segs) > 1 else "Actual size"
                o.append(_text(50, y + 2, lab, 13, True))
                o.append(_window(d, body, a, -14, b - a, Hh + 28, 50, y + 10, k))
                k += 1
                y += seg_h
            if detail and pi == 0:
                o.append(_text(50, y + 4, f"{dscale:.1f}× detail (reference — don't trace this one)", 13, True))
                o.append(f'<g transform="translate(60,{y + 16}) scale({dscale:.3f})">{uniquify(body, "_d")}</g>')
                y += dscale * Hh + 45
            if pi == len(groups) - 1 and not key_page:
                o.append(_key(max(y + 10, PH - 135)))
            pages.append(_page("".join(o)))
        if key_page:
            pages.append(_page(_header(d, total, total) + _key(170)))
    else:                                               # 2-D tiles
        tw = min(TILE_W, L + 24)
        xs, x = [], -12
        while True:
            xs.append(x)
            if x + tw >= L + 12:
                break
            x += tw - OVER
        th = min(TILE_H, Hh + 24)
        ys, y = [], -12
        while True:
            ys.append(y)
            if y + th >= Hh + 12:
                break
            y += th - OVER
        tiles = [(tx, ty) for ty in ys for tx in xs]
        per = max(1, int((TILE_W + 60) // (tw + 70)))       # narrow pieces: tiles side by side
        pages_t = [tiles[i:i + per] for i in range(0, len(tiles), per)]
        total = len(pages_t) + 1
        for pi, grp in enumerate(pages_t):
            o = [_header(d, pi + 1, total),
                 _text(110, 140, f'Tiles overlap ½" with their neighbours; match the ruler numbers', 12, True)]
            for j, (tx, ty) in enumerate(grp):
                n = tiles.index((tx, ty)) + 1
                px = 110 + j * (tw + 70)
                o.append(_text(px, 158, f"Tile {n} of {len(tiles)}", 12, True, HARDWARE))
                o.append(_window(d, body, tx, ty, tw, th, px, 170, n, rulers="both"))
            pages.append(_page("".join(o)))
        s = min(900 / (L + 40), 420 / (Hh + 40))
        o = [_header(d, total, total), _text(50, 150, "Overview (reduced — tiles outlined in red)", 13, True),
             f'<g transform="translate(70,{175}) scale({s:.4f})">{uniquify(body, "_ov")}']
        for i, (tx, ty) in enumerate(tiles):
            w = min(tw, L + 12 - tx)
            h = min(th, Hh + 12 - ty)
            o.append(f'<rect x="{tx}" y="{ty}" width="{w}" height="{h}" fill="none" stroke="{HARDWARE}" stroke-width="{2/s:.2f}" stroke-dasharray="{8/s:.1f} {6/s:.1f}"/>'
                     f'<text x="{tx + 14/s:.1f}" y="{ty + 30/s:.1f}" font-size="{22/s:.1f}" fill="{HARDWARE}" {F}>{i + 1}</text>')
        o.append("</g>")
        o.append(_key(PH - 135))
        pages.append(_page("".join(o)))
    to_pdf(pages, out_pdf)
    return out_pdf
