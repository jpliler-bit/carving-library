"""Flowers: open peony (3/4 view, cupped), peony bud, sakura, kiku, falling sakura petal."""
import math
import random
from ..element import Element, register
from ..geometry import path, smooth, line_path, dot, f, LINE, FINE, INK, WHITE

# ---------------------------------------------------------------- open peony
BETA = math.radians(47)   # camera elevation for the 3/4 view


def _project(X, Y, Z, s):
    return (X * s, (Y * math.sin(BETA) - Z * math.cos(BETA)) * s), Y * math.cos(BETA) + Z * math.sin(BETA)


def _petal3d(a, r_in, ln, theta, W, notches, cup):
    ca, sa = math.cos(a), math.sin(a)
    tx, ty = -sa, ca

    def P(u, t, dip=0.0):
        w = W * (0.42 + 0.58 * math.sqrt(max(u, 0))) * (1 - 0.06 * u * u)
        rho = r_in + u * ln * math.cos(theta) * (1 - dip)
        z = u * ln * math.sin(theta) * (1 - dip) + cup * (t * t) * w
        return rho * ca + tx * t * w, rho * sa + ty * t * w, z

    pts = [P(i / 7 * 0.92, -1) for i in range(7)]
    m = 8 * (notches + 1)
    for i in range(m + 1):
        t = -1 + 2 * i / m
        u = 0.92 + 0.08 * math.cos(t * math.pi / 2)
        dip = 0.07 * (1 - abs(math.sin(math.pi * (notches + 1) * (t + 1) / 2))) ** 1.6
        pts.append(P(u, t, dip))
    pts += [P(i / 7 * 0.92, 1) for i in range(6, -1, -1)]
    veins = [[P(u, d) for u in (0.22, 0.48, 0.70)] for d in (-0.38, 0.0, 0.38)]
    return pts, veins, P(0.55, 0)


@register
class PeonyOpen(Element):
    name = "peony_open"
    category = "flowers"
    description = ("Open peony (botan) seen from slightly above: ruffled outer petals, a cupped centre with "
                   "seeded stamens, two large front petals rolling forward. Kamakura-bori focal flower.")
    size_note = "overall width"
    size_default, size_min, size_max = 1.30, 1.00, 2.20
    layer = 60
    RINGS = [  # n, r_in, len, theta_deg, half-width, notches, cup, rotation
        (7, 0.16, 0.90, 10, 0.56, 2, 0.08, 90 + 25.7),
        (6, 0.10, 0.66, 40, 0.46, 2, 0.14, 90),
        (5, 0.05, 0.42, 62, 0.36, 1, 0.16, 90 + 36),
    ]

    def _s(self, size):
        return size * 100 / 2.2

    def draw(self, size, seed=11, **_):
        s = self._s(size)
        rnd = random.Random(seed)
        items = []
        for ri, (n, r_in, ln, th, W, notch, cup, rot) in enumerate(self.RINGS):
            for k in range(n):
                a = math.radians(rot + k * 360 / n + rnd.uniform(-6, 6))
                theta = math.radians(th + rnd.uniform(-4, 4))
                if ri == 0 and math.sin(a) > 0.3:
                    theta = math.radians(th) - 0.10   # front outer petals droop toward the viewer
                pts3, veins3, c3 = _petal3d(a, r_in, ln * rnd.uniform(0.95, 1.05), theta, W, notch, cup)
                pts = [_project(*p, s)[0] for p in pts3]
                vs = [[_project(*p, s)[0] for p in v] for v in veins3]
                vs = vs if ri == 0 else vs[1:2] if ri == 1 else []
                items.append((_project(*c3, s)[1], pts, vs))
        items.sort(key=lambda it: it[0])
        o = []
        for _, pts, vs in items:
            o.append(path(smooth(pts)))
            o += [line_path(v) for v in vs]
        (x, y), _ = _project(0, 0, 0.20, s)
        o.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(0.19*s)}" ry="{f(0.125*s)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        for ring, (rx, ry, n) in enumerate([(0, 0, 1), (0.075, 0.05, 6), (0.145, 0.09, 11)]):
            for i in range(n):
                t = i * 2 * math.pi / n + ring * 0.3
                o.append(dot(x + rx * s * math.cos(t), y + ry * s * math.sin(t), 1.6))
        return "\n".join(o)

    def anchors(self, size, **_):
        s = self._s(size)
        return {"left": (-0.95 * s, 0.07 * s, 180), "right": (0.95 * s, 0.07 * s, 0),
                "bottom": (0, 0.70 * s, 90)}

    def flow(self, size, **_):
        return [(0, 0, 1.6)]

    def extent(self, size, **_):
        s = self._s(size)
        return (-1.12 * s, -0.92 * s, 1.12 * s, 0.82 * s)


# ---------------------------------------------------------------- peony bud
@register
class PeonyBud(Element):
    name = "peony_bud"
    category = "flowers"
    description = "Closed peony bud wrapped by two sepals, with a petal fold line. Base points left (-x); attach a stalk to 'base'."
    size_note = "bud length"
    size_default, size_min, size_max = 0.27, 0.20, 0.50
    layer = 20

    def draw(self, size, **_):
        r = size * 100 / 2.1
        P = lambda u, v: (u * r, v * r)
        o = [path(smooth([P(-0.95, 0), P(-0.7, -0.75), P(0.05, -1.0), P(0.75, -0.6), P(1.05, 0.05), P(0.7, 0.72),
                          P(0.0, 1.0), P(-0.72, 0.72)])),
             line_path([P(-0.3, -0.55), P(0.35, -0.15), P(0.95, 0.02)])]
        for side in (-1, 1):
            o.append(path(smooth([P(-1.05, 0), P(-0.75, side * 0.55), P(-0.2, side * 1.05), P(0.25, side * 0.98),
                                  P(-0.15, side * 0.62), P(-0.6, side * 0.2)])))
        return "\n".join(o)

    def anchors(self, size, **_):
        r = size * 100 / 2.1
        return {"base": (-1.05 * r, 0, 180), "tip": (1.05 * r, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 0.4)]

    def extent(self, size, **_):
        r = size * 100 / 2.1
        return (-1.1 * r, -1.1 * r, 1.1 * r, 1.1 * r)


# ---------------------------------------------------------------- sakura
@register
class Sakura(Element):
    name = "sakura"
    category = "flowers"
    description = "Cherry blossom, front view: five notched petals, petal veins, ten stamens with seeded tips."
    size_note = "flower diameter"
    size_default, size_min, size_max = 0.94, 0.45, 1.30
    layer = 60

    def draw(self, size, rotate_petals=-90, **_):
        R = size * 100 / 2
        o = []
        for k in range(5):
            a = math.radians(rotate_petals + k * 72)
            ca, sa = math.cos(a), math.sin(a)
            local = [(0.12, 0), (0.30, -0.30), (0.62, -0.50), (0.90, -0.42), (1.00, -0.16), (0.86, 0),
                     (1.00, 0.16), (0.90, 0.42), (0.62, 0.50), (0.30, 0.30)]
            o.append(path(smooth([(R * (u * ca - v * sa), R * (u * sa + v * ca)) for u, v in local])))
            o.append(line_path([(R * u * ca, R * u * sa) for u in (0.34, 0.52, 0.68)]))
        o.append(path(smooth([(0.2 * R * math.cos(t), 0.2 * R * math.sin(t)) for t in [i * math.pi / 6 for i in range(12)]])))
        for k in range(10):
            a = math.radians(rotate_petals + 18 + k * 36)
            r1, r2 = 0.2 * R, (0.40 if k % 2 else 0.34) * R
            o.append(f'<line x1="{f(r1*math.cos(a))}" y1="{f(r1*math.sin(a))}" x2="{f(r2*math.cos(a))}" y2="{f(r2*math.sin(a))}" '
                     f'stroke="{INK}" stroke-width="{FINE}" stroke-linecap="round"/>')
            o.append(dot(r2 * math.cos(a), r2 * math.sin(a), 1.9))
        return "\n".join(o)

    def anchors(self, size, **_):
        R = size * 100 / 2
        return {"left": (-0.8 * R, 0, 180), "right": (0.8 * R, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 1.2)]


# ---------------------------------------------------------------- kiku
@register
class Kiku(Element):
    name = "kiku"
    category = "flowers"
    description = "Chrysanthemum, front view: three layered rings of spatulate petals and a seeded centre."
    size_note = "flower diameter"
    size_default, size_min, size_max = 0.92, 0.60, 1.30
    layer = 60

    def draw(self, size, petals=16, spin=0, **_):
        R = size * 100 / 2
        o = []
        for layer, (rr, off, wd) in enumerate([(1.0, 0, 0.17), (0.74, 0.5, 0.19), (0.48, 0.25, 0.22)]):
            for k in range(petals):
                a = math.radians(spin + (k + off) * 360 / petals)
                ca, sa = math.cos(a), math.sin(a)
                local = [(0.10, -wd * 0.35), (0.55 * rr, -wd * 0.8), (0.88 * rr, -wd), (rr, -wd * 0.45), (rr * 1.01, 0),
                         (rr, wd * 0.45), (0.88 * rr, wd), (0.55 * rr, wd * 0.8), (0.10, wd * 0.35)]
                o.append(path(smooth([(R * (u * ca - v * sa), R * (u * sa + v * ca)) for u, v in local]),
                              sw=LINE if layer == 0 else LINE * 0.9))
        o.append(f'<circle cx="0" cy="0" r="{f(0.16*R)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        for i in range(7):
            a = i * 2 * math.pi / 7
            r = 0.08 * R if i else 0
            o.append(dot(r * math.cos(a), r * math.sin(a), 1.6))
        return "\n".join(o)

    def anchors(self, size, **_):
        R = size * 100 / 2
        return {"left": (-0.85 * R, 0, 180), "right": (0.85 * R, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 1.2)]


# ---------------------------------------------------------------- falling petal
@register
class SakuraPetal(Element):
    name = "sakura_petal"
    category = "flowers"
    description = "A single falling cherry petal with a notched tip and a vein. Small filler for open pockets."
    size_note = "petal length"
    size_default, size_min, size_max = 0.20, 0.14, 0.35
    layer = 45

    def draw(self, size, **_):
        R = size * 100
        local = [(-0.5, 0), (-0.2, -0.42), (0.25, -0.48), (0.5, -0.18), (0.36, 0), (0.5, 0.18), (0.25, 0.48), (-0.2, 0.42)]
        return path(smooth([(R * u, R * v) for u, v in local])) + line_path([(R * u, 0) for u in (-0.32, -0.05, 0.18)])

    def flow(self, size, **_):
        return []
