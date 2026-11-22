"""Fill panels: seigaiha (overlapping wave scales)."""
from ..element import Element, register
from ..geometry import path, f, LINE, FINE, INK, WHITE


@register
class Seigaiha(Element):
    name = "seigaiha"
    category = "fills"
    description = ("Seigaiha wave-scale panel, centred on the origin. Outer arcs are cuts; the inner rings can be "
                   "decorative cuts or a 3D-printed seigaiha stamp struck in rows.")
    size_note = "panel length (height comes from the strap width, option 'height')"
    size_default, size_min, size_max = 1.2, 0.4, 6.0
    layer = 25

    def draw(self, size, height=1.18, scale=0.21, uid="sg", **_):
        w, h, R = size * 100, height * 100, scale * 100
        x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
        out = [f'<clipPath id="{uid}"><rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}"/></clipPath>',
               f'<g clip-path="url(#{uid})">']
        row, y = 0, y0 - R
        while y < y1 + R * 1.2:
            x = x0 - 2 * R + (R if row % 2 else 0)
            while x < x1 + 2 * R:
                for k, rr in enumerate((R, R * 0.68, R * 0.36)):
                    out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr)}" fill="{WHITE}" stroke="{INK}" '
                               f'stroke-width="{FINE if k else LINE}"/>')
                x += 2 * R
            y += R / 2
            row += 1
        out.append("</g>")
        out.append(path(f"M{f(x0)},{f(y0)} L{f(x1)},{f(y0)} L{f(x1)},{f(y1)} L{f(x0)},{f(y1)} Z", fill="none"))
        return "\n".join(out)

    def flow(self, size, **_):
        return []

    def extent(self, size, height=1.18, **_):
        return (-size * 50, -height * 50, size * 50, height * 50)


@register
class Asanoha(Element):
    name = "asanoha"
    category = "fills"
    description = ("Asanoha (hemp-leaf) panel: a triangle lattice with spokes from each triangle's centre, making "
                   "six-pointed stars. Heavy lines are cuts; thin spokes can be cuts or a lined beveller. Centred on the origin.")
    size_note = "panel length (height from the strap width, option 'height')"
    size_default, size_min, size_max = 1.2, 0.4, 6.0
    layer = 25

    def draw(self, size, height=1.18, scale=0.30, uid="as", **_):
        import math as m
        w, h, a = size * 100, height * 100, scale * 100
        x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
        rh = a * m.sqrt(3) / 2
        out = [f'<clipPath id="{uid}"><rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}"/></clipPath>',
               f'<g clip-path="url(#{uid})"><rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}" fill="{WHITE}"/>']
        rows = int(h / rh) + 3
        cols = int(w / a) + 3
        for r in range(-1, rows):
            y = y0 + r * rh
            off = (a / 2) if r % 2 else 0
            for c in range(-1, cols):
                xa = x0 + c * a + off
                for tri in (((xa, y), (xa + a, y), (xa + a / 2, y + rh)), ((xa + a / 2, y + rh), (xa + a * 1.5, y + rh), (xa + a, y))):
                    cx = sum(p[0] for p in tri) / 3
                    cy = sum(p[1] for p in tri) / 3
                    for p in tri:
                        out.append(f'<line x1="{f(cx)}" y1="{f(cy)}" x2="{f(p[0])}" y2="{f(p[1])}" stroke="{INK}" stroke-width="{FINE}"/>')
                    out.append(f'<path d="M{f(tri[0][0])},{f(tri[0][1])} L{f(tri[1][0])},{f(tri[1][1])} L{f(tri[2][0])},{f(tri[2][1])} Z" '
                               f'fill="none" stroke="{INK}" stroke-width="{LINE}" stroke-linejoin="round"/>')
        out.append("</g>")
        out.append(path(f"M{f(x0)},{f(y0)} L{f(x1)},{f(y0)} L{f(x1)},{f(y1)} L{f(x0)},{f(y1)} Z", fill="none"))
        return "\n".join(out)

    def flow(self, size, **_):
        return []

    def extent(self, size, height=1.18, **_):
        return (-size * 50, -height * 50, size * 50, height * 50)


@register
class Basketweave(Element):
    name = "basketweave"
    category = "fills"
    description = ("Basket weave panel: blocks of three strands alternating across and along, like a woven basket. "
                   "Stamp it with a basket-weave stamp; the drawing is the layout guide. Centred on the origin.")
    size_note = "panel length (height from the strap width, option 'height')"
    size_default, size_min, size_max = 1.2, 0.4, 36.0
    layer = 25

    def draw(self, size, height=1.18, cell=0.295, uid="bw", **_):
        w, h, c = size * 100, height * 100, cell * 100
        x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
        out = [f'<clipPath id="{uid}"><rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}"/></clipPath>',
               f'<g clip-path="url(#{uid})"><rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}" fill="{WHITE}"/>']
        n_r = int(h / c) + 2
        n_c = int(w / c) + 2
        oy = -((n_r - 1) * c) / 2
        ox = -((n_c - 1) * c) / 2
        s = c / 3
        for i in range(n_r):
            for j in range(n_c):
                cx, cy = ox + j * c, oy + i * c
                across = (i + j) % 2 == 0
                for k in range(3):
                    off = -c / 2 + s * k + s / 2
                    if across:
                        x, y, ww, hh = cx - c / 2 + 1.2, cy + off - s / 2 + 1.2, c - 2.4, s - 2.4
                    else:
                        x, y, ww, hh = cx + off - s / 2 + 1.2, cy - c / 2 + 1.2, s - 2.4, c - 2.4
                    out.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(ww)}" height="{f(hh)}" rx="{f(min(ww, hh)/2)}" '
                               f'fill="{WHITE}" stroke="{INK}" stroke-width="{FINE}"/>')
        out.append("</g>")
        out.append(path(f"M{f(x0)},{f(y0)} L{f(x1)},{f(y0)} L{f(x1)},{f(y1)} L{f(x0)},{f(y1)} Z", fill="none"))
        return "\n".join(out)

    def flow(self, size, **_):
        return []

    def extent(self, size, height=1.18, **_):
        return (-size * 50, -height * 50, size * 50, height * 50)


@register
class MokkoCartouche(Element):
    name = "mokko_cartouche"
    category = "frames"
    description = ("Mokko cartouche: the four-lobed Japanese crest frame, stretched to hold a name or initials "
                   "(stamp them with a 3D-printed name stamp). Double outline: cut the outer, decorative-cut the inner. "
                   "Option 'text' shows a grey placement guide.")
    size_note = "frame width"
    size_default, size_min, size_max = 1.60, 0.80, 4.00
    layer = 55

    def _geom(self, size, height):
        from shapely.geometry import Point, box
        from shapely.ops import unary_union
        w, h = size * 100, height * 100
        r_side = h * 0.42
        r_tb = h * 0.30
        parts = [Point(-w / 2 + r_side, 0).buffer(r_side, resolution=32), Point(w / 2 - r_side, 0).buffer(r_side, resolution=32),
                 Point(0, -h / 2 + r_tb).buffer(r_tb, resolution=32), Point(0, h / 2 - r_tb).buffer(r_tb, resolution=32),
                 box(-w / 2 + r_side, -h * 0.30, w / 2 - r_side, h * 0.30)]
        if w > 2.2 * h:
            parts += [Point(sx * (w / 4), sy * (h / 2 - r_tb)).buffer(r_tb, resolution=32) for sx in (-1, 1) for sy in (-1, 1)]
        return unary_union(parts)

    def draw(self, size, height=0.90, text=None, **_):
        g = self._geom(size, height)
        outer = list(g.exterior.coords)[:-1]
        inner = list(g.buffer(-6.5, join_style=1).exterior.coords)[:-1]
        o = [f'<path d="M' + " L".join(f"{f(x)},{f(y)}" for x, y in outer) + f' Z" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}" stroke-linejoin="round"/>',
             f'<path d="M' + " L".join(f"{f(x)},{f(y)}" for x, y in inner) + f' Z" fill="none" stroke="{INK}" stroke-width="{FINE}" stroke-linejoin="round"/>']
        if text:
            o.append(f'<text x="0" y="{f(height*100*0.14)}" font-family="Georgia, serif" font-size="{f(height*100*0.42)}" '
                     f'text-anchor="middle" fill="#9a9a9a">{text}</text>')
        return "\n".join(o)

    def anchors(self, size, height=0.90, **_):
        return {"left": (-size * 50, 0, 180), "right": (size * 50, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 1.0)]

    def extent(self, size, height=0.90, **_):
        return (-size * 50, -height * 50, size * 50, height * 50)
