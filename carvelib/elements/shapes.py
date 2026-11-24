"""Shapes: lone star, horseshoe, mitsudomoe, folding fan (sensu), diamond frame (hishi)."""
import math
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
from ..element import Element, register
from ..geometry import path, smooth, line_path, dot, f, catmull, band, tapered, LINE, FINE, INK, WHITE


def _poly(pts, fill=WHITE, sw=LINE, close=True):
    return path("M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + (" Z" if close else ""), fill=fill if close else "none", sw=sw)


def _shape(geom, fill=WHITE, sw=LINE):
    if geom.geom_type == "MultiPolygon":
        return "\n".join(_shape(g, fill, sw) for g in geom.geoms)
    return _poly(list(geom.exterior.coords)[:-1], fill, sw)


@register
class LoneStar(Element):
    name = "lone_star"
    category = "shapes"
    description = ("Five-point Texas star, beveled: lines from the centre to every point and notch split each arm "
                   "into a light and a dark facet. Option ring: true circles it, as on a Texas star concho.")
    size_note = "diameter, point to point"
    size_default, size_min, size_max = 0.80, 0.35, 3.00
    layer = 60

    def draw(self, size, ring=False, inner=0.40, **_):
        R = size * 50
        if ring:
            R *= 0.80
        pts = []
        for k in range(10):
            a = math.radians(-90 + 36 * k)
            r = R if k % 2 == 0 else R * inner
            pts.append((r * math.cos(a), r * math.sin(a)))
        o = []
        if ring:
            Rr = size * 50
            o.append(path(f"M{f(Rr)},0 A{f(Rr)},{f(Rr)} 0 1 0 {f(-Rr)},0 A{f(Rr)},{f(Rr)} 0 1 0 {f(Rr)},0 Z "
                          f"M{f(Rr*0.88)},0 A{f(Rr*0.88)},{f(Rr*0.88)} 0 1 1 {f(-Rr*0.88)},0 A{f(Rr*0.88)},{f(Rr*0.88)} 0 1 1 {f(Rr*0.88)},0 Z",
                          extra='fill-rule="evenodd"'))
        o.append(_poly(pts))
        for x, y in pts:
            o.append(f'<line x1="0" y1="0" x2="{f(x)}" y2="{f(y)}" stroke="{INK}" stroke-width="{FINE}"/>')
        # shade one facet of each arm (the side away from the light) as a guide for the bevel
        for k in range(0, 10, 2):
            tri = [(0, 0), pts[k], pts[(k + 1) % 10]]
            o.append(_poly(tri, fill="#d6d1c9", sw=0))
            o.append(f'<line x1="0" y1="0" x2="{f(pts[k][0])}" y2="{f(pts[k][1])}" stroke="{INK}" stroke-width="{FINE}"/>')
        o.append(_poly(pts, fill="none"))
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 0.8)]


@register
class Horseshoe(Element):
    name = "horseshoe"
    category = "shapes"
    description = ("Horseshoe, opening up (to hold the luck): a creased groove along the shoe with nail holes, and "
                   "heel calks. Centre of the curve at the origin.")
    size_note = "width"
    size_default, size_min, size_max = 0.80, 0.45, 2.00
    layer = 55

    def draw(self, size, **_):
        s = size * 100
        R = 0.38 * s
        c = []
        for i in range(41):
            th = math.radians(200 - 220 * i / 40)
            r = R * (1 + 0.06 * math.sin(math.radians(200 - 220 * i / 40)))
            c.append((r * math.cos(th), r * math.sin(th) * 1.08))
        c = [(c[0][0], c[0][1] - 0.10 * s)] + c + [(c[-1][0], c[-1][1] - 0.10 * s)]
        w = 0.20 * s
        shoe = LineString(c).buffer(w / 2, cap_style=2, join_style=1, resolution=16)
        o = [_shape(shoe)]
        groove = [(x * 1.0, y * 1.0) for x, y in band(c, [w * 0.40] * len(c))[1]]
        o.append(line_path(groove[2:-2][::2]))
        for i in list(range(6, 20, 4)) + list(range(23, 38, 4)):
            x, y = groove[i]
            o.append(f'<rect x="{f(x - 0.018*s)}" y="{f(y - 0.012*s)}" width="{f(0.036*s)}" height="{f(0.024*s)}" '
                     f'fill="#d6d1c9" stroke="{INK}" stroke-width="{FINE}" '
                     f'transform="rotate({f(math.degrees(math.atan2(groove[i+1][1]-groove[i-1][1], groove[i+1][0]-groove[i-1][0])))} {f(x)} {f(y)})"/>')
        for end, nxt in ((c[0], c[2]), (c[-1], c[-3])):
            o.append(line_path([(end[0] - w * 0.45, end[1] + 0.03 * s), (end[0] + w * 0.45, end[1] + 0.03 * s)]))
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 0.6)]

    def extent(self, size, **_):
        s = size * 100
        return (-0.52 * s, -0.42 * s, 0.52 * s, 0.56 * s)


@register
class Mitsudomoe(Element):
    name = "mitsudomoe"
    category = "shapes"
    description = ("Mitsudomoe: three comma shapes (tomoe) swirling round a centre, one of the most common "
                   "Japanese crests. Option ring: true adds a maru ring. Option turn: -1 swirls the other way.")
    size_note = "diameter"
    size_default, size_min, size_max = 0.90, 0.45, 3.00
    layer = 60

    def draw(self, size, ring=False, turn=1, **_):
        R = size * 50 * (0.82 if ring else 1.0)
        o = []
        if ring:
            Rr = size * 50
            o.append(path(f"M{f(Rr)},0 A{f(Rr)},{f(Rr)} 0 1 0 {f(-Rr)},0 A{f(Rr)},{f(Rr)} 0 1 0 {f(Rr)},0 Z "
                          f"M{f(Rr*0.89)},0 A{f(Rr*0.89)},{f(Rr*0.89)} 0 1 1 {f(-Rr*0.89)},0 A{f(Rr*0.89)},{f(Rr*0.89)} 0 1 1 {f(Rr*0.89)},0 Z",
                          extra='fill-rule="evenodd"'))
        for k in range(3):
            a0 = math.radians(-90 + 120 * k)
            hc = (0.40 * R * math.cos(a0), 0.40 * R * math.sin(a0))
            hc = (0.42 * R * math.cos(a0), 0.42 * R * math.sin(a0))
            head = Point(hc).buffer(0.30 * R, resolution=32)
            tail = []
            for i in range(31):
                t = i / 30
                a = a0 + turn * math.radians(140 * t)
                r = 0.42 * R + 0.46 * R * t ** 0.6
                tail.append((r * math.cos(a), r * math.sin(a)))
            ws = [2 * 0.30 * R * (1 - i / 30) ** 1.1 + 0.4 for i in range(31)]
            g = unary_union([head, Polygon(band(tail, ws)[0]).buffer(0)]).intersection(Point(0, 0).buffer(R * 0.98, resolution=64))
            o.append(_shape(g.simplify(0.2)))
            o.append(f'<circle cx="{f(hc[0])}" cy="{f(hc[1])}" r="{f(0.12*R)}" fill="none" stroke="{INK}" stroke-width="{FINE}"/>')
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 0.9)]


@register
class Sensu(Element):
    name = "sensu"
    category = "shapes"
    description = ("Folding fan (sensu), open: pleated leaf with a scalloped top edge, slats fanning from a riveted "
                   "pivot, heavier guard sticks at both sides. Pivot at the origin, fan opening upward.")
    size_note = "width when open"
    size_default, size_min, size_max = 1.20, 0.70, 3.00
    layer = 55

    def draw(self, size, spread=120, ribs=12, **_):
        R = size * 100 / (2 * math.sin(math.radians(spread / 2)))
        a0, a1 = -90 - spread / 2, -90 + spread / 2
        r0 = 0.42 * R
        angs = [a0 + (a1 - a0) * i / ribs for i in range(ribs + 1)]
        o = []
        inner = [(0.07 * R * math.cos(math.radians(a)), 0.07 * R * math.sin(math.radians(a))) for a in angs]
        inner += [(r0 * math.cos(math.radians(a)), r0 * math.sin(math.radians(a))) for a in angs[::-1]]
        o.append(_poly(inner))                               # slats, carved as one raised fan
        for a in angs[2:-2:2]:
            ar = math.radians(a)
            o.append(f'<line x1="{f(0.16*R*math.cos(ar))}" y1="{f(0.16*R*math.sin(ar))}" x2="{f(r0*math.cos(ar))}" y2="{f(r0*math.sin(ar))}" stroke="{INK}" stroke-width="{FINE}"/>')
        leaf = []
        for i in range(len(angs) - 1):
            for t in (0.0, 0.5):
                a = math.radians(angs[i] + (angs[i + 1] - angs[i]) * t)
                r = R * (1.0 if t == 0 else 1.025)
                leaf.append((r * math.cos(a), r * math.sin(a)))
        leaf.append((R * math.cos(math.radians(a1)), R * math.sin(math.radians(a1))))
        leaf += [(r0 * math.cos(math.radians(a)), r0 * math.sin(math.radians(a))) for a in angs[::-1]]
        o.append(_poly(leaf))
        for a in angs[1:-1]:
            ar = math.radians(a)
            o.append(f'<line x1="{f(r0*math.cos(ar))}" y1="{f(r0*math.sin(ar))}" x2="{f(R*math.cos(ar))}" y2="{f(R*math.sin(ar))}" stroke="{INK}" stroke-width="{FINE}"/>')
        for a in (a0, a1):                                   # guard sticks
            ar = math.radians(a)
            o.append(path(smooth(tapered([(0.05 * R * math.cos(ar), 0.05 * R * math.sin(ar)), (1.02 * R * math.cos(ar), 1.02 * R * math.sin(ar))], 0.055 * R, 0.035 * R))))
        o.append(f'<circle cx="0" cy="0" r="{f(0.06*R)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        o.append(dot(0, 0, 2.0))
        return "\n".join(o)

    def anchors(self, size, spread=120, **_):
        return {"pivot": (0, 0, 90)}

    def flow(self, size, **_):
        return [(0, -size * 30, 0.8)]

    def extent(self, size, spread=120, **_):
        R = size * 100 / (2 * math.sin(math.radians(spread / 2)))
        return (-size * 52, -1.05 * R, size * 52, 0.08 * R)


@register
class HishiFrame(Element):
    name = "hishi_frame"
    category = "frames"
    description = ("Diamond frame (hishi): a raised rhombus border with a double outline, to hold a crest or "
                   "initials. Option height sets the vertical diagonal (default = width).")
    size_note = "width (horizontal diagonal)"
    size_default, size_min, size_max = 1.10, 0.50, 4.00
    layer = 55

    def draw(self, size, height=None, thickness=0.09, **_):
        w = size * 50
        h = (height if height is not None else size) * 50
        outer = Polygon([(0, -h), (w, 0), (0, h), (-w, 0)])
        inner = outer.buffer(-thickness * 100, join_style=2)
        mid = outer.buffer(-thickness * 50, join_style=2)
        ring = outer.difference(inner)
        return (_shape(ring.exterior and Polygon(ring.exterior)) + "\n" +
                _poly(list(inner.exterior.coords)[:-1], fill="none") + "\n" +
                _poly(list(mid.exterior.coords)[:-1], fill="none", sw=FINE))

    def anchors(self, size, height=None, **_):
        w = size * 50
        h = (height if height is not None else size) * 50
        return {"top": (0, -h, -90), "bottom": (0, h, 90), "left": (-w, 0, 180), "right": (w, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 0.6)]

    def extent(self, size, height=None, **_):
        h = (height if height is not None else size) * 50
        return (-size * 50, -h, size * 50, h)
