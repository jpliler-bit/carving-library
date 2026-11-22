"""Japanese motifs: camellia (tsubaki), plum blossom (ume), cloud scroll (kumo), karakusa tendril."""
import math
import random
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
from ..element import Element, register
from ..geometry import path, smooth, line_path, dot, f, catmull, band, spiral, LINE, FINE, INK, WHITE
from .flowers import _petal3d, _project


def _ring_coords(geom, step=1):
    """Exterior coordinates of a shapely polygon (largest part if multi)."""
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    return list(geom.exterior.coords)[:-1][::step]


# ---------------------------------------------------------------- camellia
@register
class Camellia(Element):
    name = "camellia"
    category = "flowers"
    description = ("Camellia (tsubaki), seen from slightly above: five broad rounded petals in two rings, cupped, "
                   "around the camellia's tube of stamens. Kamakura's local flower; simpler to carve than the peony.")
    size_note = "overall width"
    size_default, size_min, size_max = 1.10, 0.80, 1.80
    layer = 60
    RINGS = [  # n, r_in, len, theta_deg, half-width, notches, cup, rotation
        (6, 0.18, 0.86, 14, 0.46, 0, 0.08, 90 + 30),
        (5, 0.12, 0.58, 50, 0.50, 0, 0.12, 90 + 36),
    ]

    def _s(self, size):
        return size * 100 / 2.1

    def draw(self, size, seed=3, **_):
        s = self._s(size)
        rnd = random.Random(seed)
        items = []
        for ri, (n, r_in, ln, th, W, notch, cup, rot) in enumerate(self.RINGS):
            for k in range(n):
                a = math.radians(rot + k * 360 / n + rnd.uniform(-5, 5))
                theta = math.radians(th + rnd.uniform(-3, 3))
                if ri == 1 and math.sin(a) > -0.2:
                    continue                      # inner ring: back petals only, framing the stamens
                if ri == 0 and math.sin(a) > 0.3:
                    theta = math.radians(th) - 0.18
                pts3, veins3, c3 = _petal3d(a, r_in, ln * rnd.uniform(0.96, 1.04), theta, W, notch, cup, round_tip=0.30)
                pts = [_project(*p, s)[0] for p in pts3]
                vs = [[_project(*p, s)[0] for p in v] for v in veins3]
                items.append((_project(*c3, s)[1], "p" if ri == 0 else "pi", pts, [] if ri else [vs[0], vs[2]]))
        # stamen tube: a short cylinder, ring of anthers on top
        inner = [d for d, k, _, _ in items if k == "pi"]
        items.append(((max(inner) if inner else 0) + 0.01, "tube", None, None))
        items.sort(key=lambda it: it[0])
        o = []
        for depth, kind, pts, vs in items:
            if kind in ("p", "pi"):
                o.append(path(smooth(pts)))
                o += [line_path(v) for v in vs]
            else:
                o.append(self._tube(s))
        return "\n".join(o)

    def _tube(self, s):
        (bx, by), _ = _project(0, 0, 0.05, s)
        (tx, ty), _ = _project(0, 0, 0.36, s)
        rx = 0.20 * s
        ry_t = 0.20 * s * math.sin(math.radians(47))
        body = [(tx - rx, ty), (bx - rx * 0.85, by), (bx, by + ry_t * 0.8), (bx + rx * 0.85, by), (tx + rx, ty), (tx, ty + ry_t)]
        o = [path(smooth(body))]
        for k in range(-3, 4):            # filaments
            x = k / 3.5
            o.append(line_path([(bx + x * rx * 0.8, by + ry_t * 0.75 * (1 - x * x) ** 0.5), (tx + x * rx * 0.95, ty + ry_t * 0.9 * (1 - x * x) ** 0.5)]))
        o.append(f'<ellipse cx="{f(tx)}" cy="{f(ty)}" rx="{f(rx)}" ry="{f(ry_t)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        for i in range(12):
            t = i * 2 * math.pi / 12
            o.append(dot(tx + 0.72 * rx * math.cos(t), ty + 0.72 * ry_t * math.sin(t), 1.6))
        o.append(dot(tx, ty, 1.6))
        return "\n".join(o)

    def anchors(self, size, **_):
        s = self._s(size)
        return {"left": (-0.92 * s, 0.10 * s, 180), "right": (0.92 * s, 0.10 * s, 0), "bottom": (0, 0.62 * s, 90)}

    def flow(self, size, **_):
        return [(0, 0, 1.4)]

    def extent(self, size, **_):
        s = self._s(size)
        return (-1.05 * s, -0.95 * s, 1.05 * s, 0.85 * s)


# ---------------------------------------------------------------- ume
@register
class Ume(Element):
    name = "ume"
    category = "flowers"
    description = ("Plum blossom (ume), front view: five round, un-notched petals and long radiating stamens. "
                   "Rounder and plainer than sakura; carves well small.")
    size_note = "flower diameter"
    size_default, size_min, size_max = 0.70, 0.35, 1.10
    layer = 60

    def draw(self, size, rotate_petals=-90, **_):
        R = size * 100 / 2
        o = []
        for k in range(5):
            a = math.radians(rotate_petals + k * 72)
            cx, cy = 0.58 * R * math.cos(a), 0.58 * R * math.sin(a)
            r = 0.41 * R
            pts = [(cx + r * math.cos(a + i * 2 * math.pi / 16), cy + r * math.sin(a + i * 2 * math.pi / 16)) for i in range(16)]
            o.append(path(smooth(pts)))
        o.append(f'<circle cx="0" cy="0" r="{f(0.17*R)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        for k in range(15):
            a = math.radians(rotate_petals + 12 + k * 24)
            r2 = (0.62 if k % 2 else 0.50) * R
            o.append(f'<line x1="{f(0.17*R*math.cos(a))}" y1="{f(0.17*R*math.sin(a))}" x2="{f(r2*math.cos(a))}" '
                     f'y2="{f(r2*math.sin(a))}" stroke="{INK}" stroke-width="{FINE}" stroke-linecap="round"/>')
            o.append(dot(r2 * math.cos(a), r2 * math.sin(a), 1.8))
        o.append(dot(0, 0, 2.0))
        return "\n".join(o)

    def anchors(self, size, **_):
        R = size * 100 / 2
        return {"left": (-0.85 * R, 0, 180), "right": (0.85 * R, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 1.0)]


# ---------------------------------------------------------------- cloud scroll
@register
class CloudScroll(Element):
    name = "cloud_scroll"
    category = "scrolls"
    description = ("Kamakura-bori cloud (kumo): a head of three curled lobes, each with a spiral cut, trailing a "
                   "tapering tail. Head at the origin; the tail streams toward -x. A classic Kamakura-bori filler.")
    size_note = "overall length (head + tail)"
    size_default, size_min, size_max = 1.10, 0.70, 2.00
    layer = 15

    def _geom(self, size):
        k = size * 100 / 110
        lobes = [(0, -8, 16), (27, -13, 13), (22, 13, 12), (-16, 11, 11), (40, 2, 9)]
        shapes = [Point(x * k, y * k).buffer(r * k, resolution=24) for x, y, r in lobes]
        shapes.append(Point(14 * k, 1 * k).buffer(17 * k, resolution=24))   # core ties the lobes together
        tail_c = catmull([(-8 * k, 12 * k), (-30 * k, 18 * k), (-55 * k, 10 * k), (-75 * k, 16 * k), (-88 * k, 12 * k)], 8)
        ws = [16 * k * (1 - i / (len(tail_c) - 1)) ** 0.9 + 1.5 for i in range(len(tail_c))]
        tail = Polygon(band(tail_c, ws)[0]).buffer(0)
        return unary_union(shapes + [tail]).simplify(0.2), lobes, tail_c, k

    def draw(self, size, **_):
        g, lobes, tail_c, k = self._geom(size)
        o = [path(smooth(_ring_coords(g, 2)))]
        for x, y, r in lobes:
            sp = spiral((x + r * 0.55) * k, y * k, -math.pi / 2, -1, r * 0.55 * k, 1.1, shrink=0.75, steps=40)
            o.append(line_path(sp[::3]))
        o.append(line_path(tail_c[2:-6][::3]))
        return "\n".join(o)

    def anchors(self, size, **_):
        k = size * 100 / 110
        return {"tail": (-88 * k, 12 * k, 180)}

    def flow(self, size, **_):
        k = size * 100 / 110
        return [(0, 0, 0.9)]

    def extent(self, size, **_):
        k = size * 100 / 110
        return (-92 * k, -27 * k, 52 * k, 28 * k)


# ---------------------------------------------------------------- karakusa tendril
@register
class KarakusaTendril(Element):
    name = "karakusa_tendril"
    category = "scrolls"
    description = ("Karakusa (arabesque) tendril: a thin vine leaving its base, carrying two small pointed leaves, "
                   "ending in a tight curl. Base at the origin heading +x, curls upward (flip_y to curl down).")
    size_note = "length from base to the far side of the curl"
    size_default, size_min, size_max = 0.75, 0.45, 1.30
    layer = 18

    def _center(self, size):
        k = size * 100 / 75
        lead = [(0, 0), (14 * k, -3 * k), (30 * k, -10 * k), (46 * k, -20 * k)]
        sp = spiral(46 * k, -20 * k, math.radians(-40), +1, 16 * k, 1.15, shrink=0.78, steps=40)
        return catmull(lead, 6)[:-1] + sp, k

    def draw(self, size, **_):
        c, k = self._center(size)
        ws = [5.5 * k * (1 - 0.55 * i / (len(c) - 1)) + 1.8 for i in range(len(c))]
        o = [path(smooth(band(c, ws)[0][::2]))]
        for idx, side, ln in ((7, -1, 19), (13, 1, 15)):
            x, y = c[idx]
            a0 = math.atan2(c[idx + 1][1] - c[idx - 1][1], c[idx + 1][0] - c[idx - 1][0]) + side * 0.9
            L = ln * k
            ux, uy = math.cos(a0), math.sin(a0)
            nx, ny = -uy, ux
            loc = [(0, 0), (0.3, -0.22), (0.62, -0.28), (1.0, 0.0), (0.62, 0.22), (0.3, 0.2)]
            o.append(path(smooth([(x + ux * u * L + nx * v * L, y + uy * u * L + ny * v * L) for u, v in loc])))
            o.append(line_path([(x + ux * 0.1 * L, y + uy * 0.1 * L), (x + ux * 0.5 * L, y + uy * 0.5 * L), (x + ux * 0.85 * L, y + uy * 0.85 * L)]))
        return "\n".join(o)

    def anchors(self, size, **_):
        return {"base": (0, 0, 180)}

    def flow(self, size, **_):
        k = size * 100 / 75
        return [(52 * k, -30 * k, 0.5)]

    def extent(self, size, **_):
        k = size * 100 / 75
        return (-3 * k, -48 * k, 72 * k, 14 * k)
