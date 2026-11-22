"""Western / Sheridan-style motifs: Sheridan rose, Sheridan leaf, rose bud."""
import math
from ..element import Element, register
from ..geometry import path, smooth, line_path, dot, f, catmull, tapered, LINE, FINE, INK, WHITE


def _fan_petal(a, r_in, r_out, hw, notch=True, tip_bulge=0.10):
    """Petal in polar form around the origin: narrow base at r_in, flaring to a rounded,
    optionally notched tip at r_out. Returns outline points."""
    pts = [(r_in, -hw * 0.30), (r_in + 0.45 * (r_out - r_in), -hw * 0.95)]
    m = 16
    for i in range(m + 1):
        t = -0.92 + 1.84 * i / m
        rr = r_out * (1 + tip_bulge * (1 - t * t)) - (r_out * 0.06 if notch and i == m // 2 else 0)
        pts.append((rr, t * hw))
    pts += [(r_in + 0.45 * (r_out - r_in), hw * 0.95), (r_in, hw * 0.30)]
    return [(r * math.cos(a + t), r * math.sin(a + t)) for r, t in pts]


def _polar(r, a):
    return r * math.cos(a), r * math.sin(a)


@register
class SheridanRose(Element):
    name = "sheridan_rose"
    category = "western"
    description = ("Sheridan-style wild rose, front view: five broad outer petals with rolled-over edges and "
                   "decorative cuts, five cupped inner petals, and a seeded centre ringed by small centre petals. "
                   "The focal flower of Sheridan floral carving.")
    size_note = "flower diameter"
    size_default, size_min, size_max = 1.20, 0.80, 2.00
    layer = 60

    def draw(self, size, spin=-90, **_):
        R = size * 100 / 2 / 1.08
        o = []
        # outer petals, pinwheel overlap
        for k in range(5):
            a = math.radians(spin + k * 72)
            hw = math.radians(39)
            o.append(path(smooth(_fan_petal(a, 0.28 * R, 0.80 * R, hw, tip_bulge=0.24))))
            # rolled-over edge: a line just inside the tip
            roll = [_polar(0.70 * R * (1 + 0.24 * (1 - t * t)), a + t * hw * 0.92) for t in (-0.62, -0.3, 0, 0.3, 0.62)]
            o.append(line_path(roll))
            for d in (-0.40, 0.40):       # decorative cuts, sweeping toward the rolled edge
                o.append(line_path([_polar(r * R, a + d * hw * (r / 0.75)) for r in (0.60, 0.68, 0.76)]))
        # inner cupped petals
        for k in range(5):
            a = math.radians(spin + 36 + k * 72)
            hw = math.radians(36)
            o.append(path(smooth(_fan_petal(a, 0.18 * R, 0.56 * R, hw, notch=False, tip_bulge=0.14))))
            o.append(line_path([_polar(0.47 * R * (1 + 0.1 * (1 - t * t)), a + t * hw * 0.8) for t in (-0.7, 0, 0.7)]))
        # centre petals (a crown of small scallops) and seeded centre
        crown = []
        for i in range(48):
            t = i / 48 * 2 * math.pi
            r = 0.27 * R * (1 + 0.10 * abs(math.sin(5 * t)))
            crown.append(_polar(r, t + math.radians(spin)))
        o.append(path(smooth(crown)))
        o.append(f'<circle cx="0" cy="0" r="{f(0.18*R)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        for ring, (rr, n) in enumerate([(0, 1), (0.07, 6), (0.135, 12)]):
            for i in range(n):
                t = i * 2 * math.pi / n + ring * 0.25
                o.append(dot(rr * R * math.cos(t), rr * R * math.sin(t), 1.6))
        return "\n".join(o)

    def anchors(self, size, **_):
        R = size * 100 / 2 / 1.08
        return {"left": (-0.85 * R, 0, 180), "right": (0.85 * R, 0, 0), "top": (0, -0.85 * R, -90), "bottom": (0, 0.85 * R, 90)}

    def flow(self, size, **_):
        return [(0, 0, 1.6)]


@register
class SheridanLeaf(Element):
    name = "sheridan_leaf"
    category = "western"
    description = ("Sheridan-style leaf: long and curved, smooth on the outer edge and scalloped into lobes on the "
                   "inner edge, with a curving midrib, side veins to each lobe and a tip that flips up. "
                   "Base at the origin, tip toward +x, curving upward (flip_y to curve down).")
    size_note = "leaf length"
    size_default, size_min, size_max = 0.80, 0.45, 1.40
    layer = 40

    OUTLINE = [(0, 0), (0.14, -0.15), (0.38, -0.25), (0.62, -0.27), (0.82, -0.22), (0.96, -0.15), (1.03, -0.20),
               (1.00, -0.09), (0.92, -0.05), (0.88, 0.02), (0.80, -0.02), (0.72, 0.08), (0.63, 0.03), (0.53, 0.12),
               (0.44, 0.06), (0.33, 0.13), (0.24, 0.08), (0.10, 0.07)]
    RIB = [(0.04, 0.0), (0.30, -0.07), (0.60, -0.12), (0.92, -0.12)]
    LOBE_TIPS = [(0.88, 0.02), (0.72, 0.08), (0.53, 0.12), (0.33, 0.13)]

    def draw(self, size, **_):
        L = size * 100
        P = lambda pts: [(x * L, y * L) for x, y in pts]
        o = [path(smooth(P(self.OUTLINE)))]
        rib = catmull(P(self.RIB), 8)
        o.append(line_path(rib[::3]))
        for tx, ty in self.LOBE_TIPS:          # side vein from the rib out toward each lobe
            # nearest rib point a little toward the base
            bx, by = min(rib, key=lambda p: abs(p[0] - (tx - 0.10) * L))
            o.append(line_path([(bx, by), ((bx + tx * L) / 2 + 0.01 * L, (by + ty * L) / 2), (bx * 0.25 + tx * L * 0.75, by * 0.25 + ty * L * 0.75)]))
        return "\n".join(o)

    def anchors(self, size, **_):
        L = size * 100
        return {"base": (0, 0, 180), "tip": (1.03 * L, -0.20 * L, -40)}

    def flow(self, size, **_):
        return []

    def extent(self, size, **_):
        L = size * 100
        return (-2, -0.30 * L, L * 1.05, 0.16 * L)


@register
class RoseBud(Element):
    name = "rose_bud"
    category = "western"
    description = ("Closed rose bud: pointed bud with a spiral wrap of petals and two sepals hugging the base. "
                   "Base points left (-x); attach a stalk to 'base'.")
    size_note = "bud length"
    size_default, size_min, size_max = 0.40, 0.25, 0.70
    layer = 20

    def draw(self, size, **_):
        r = size * 100 / 2.2
        P = lambda u, v: (u * r, v * r)
        body = [P(-0.55, 0), P(-0.30, -0.56), P(0.25, -0.70), P(0.82, -0.40), P(1.30, 0.0), P(0.82, 0.40), P(0.25, 0.70),
                P(-0.30, 0.56)]
        calyx = [P(-1.0, 0), P(-0.74, -0.30), P(-0.34, -0.44), P(0.30, -0.40), P(-0.10, -0.20), P(0.02, 0.0),
                 P(-0.10, 0.20), P(0.30, 0.40), P(-0.34, 0.44), P(-0.74, 0.30)]
        o = [path(smooth(body)),
             line_path([P(0.42, -0.58), P(0.62, -0.18), P(1.05, 0.08)]),
             path(smooth(calyx)),
             line_path([P(-0.78, 0), P(-0.35, 0), P(-0.10, 0)])]
        return "\n".join(o)

    def anchors(self, size, **_):
        r = size * 100 / 2.2
        return {"base": (-1.0 * r, 0, 180), "tip": (1.15 * r, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 0.4)]

    def extent(self, size, **_):
        r = size * 100 / 2.2
        return (-1.05 * r, -1.0 * r, 1.2 * r, 1.0 * r)


@register
class OakLeaf(Element):
    name = "oak_leaf"
    category = "western"
    description = ("Oak leaf: long, with rounded lobes and pointed sinuses alternating along each side, a midrib and "
                   "a vein to each lobe. Pairs with the acorn. Stem at the origin, tip toward +x.")
    size_note = "leaf length (stem to tip)"
    size_default, size_min, size_max = 1.00, 0.55, 1.80
    layer = 40

    def _edge(self, L, side, n=4, phase=0.0):
        pts = []
        for i in range(61):
            t = i / 60
            env = math.sin(math.pi * t ** 0.8) ** 0.9
            lobe = 0.42 + 0.58 * abs(math.sin(math.pi * n * t + phase)) ** 0.6
            hw = 0.24 * L * env * lobe
            x = 0.10 * L + t * 0.90 * L
            y = -0.03 * L * math.sin(math.pi * t) + side * hw
            pts.append((x, y))
        return pts

    def draw(self, size, **_):
        L = size * 100
        up = self._edge(L, -1, phase=0.0)
        lo = self._edge(L, +1, phase=0.7)
        stem = [(0, 0), (0.06 * L, -0.005 * L), (0.13 * L, 0)]
        o = [path(smooth(tapered(stem, 0.045 * L, 0.035 * L))), path(smooth((up + lo[::-1])[::2]))]
        rib = [(0.10 * L + t * 0.86 * L, -0.03 * L * math.sin(math.pi * t)) for t in (0.02, 0.35, 0.7, 0.96)]
        o.append(line_path(rib))
        n = 4
        for side, phase, edge in ((-1, 0.0, up), (1, 0.7, lo)):
            for k in range(n):
                t = (k + 0.5 - phase / math.pi) / n
                if not 0.12 < t < 0.9:
                    continue
                ex, ey = edge[int(t * 60)]
                rx, ry = 0.10 * L + (t - 0.07) * 0.90 * L, -0.03 * L * math.sin(math.pi * (t - 0.07))
                o.append(line_path([(rx, ry), (rx * 0.45 + ex * 0.55 + 0.01 * L, ry * 0.45 + ey * 0.55), (rx * 0.18 + ex * 0.82, ry * 0.18 + ey * 0.82)]))
        return "\n".join(o)

    def anchors(self, size, **_):
        return {"base": (0, 0, 180), "tip": (size * 100, 0, 0)}

    def flow(self, size, **_):
        return []

    def extent(self, size, **_):
        L = size * 100
        return (-2, -0.30 * L, L * 1.01, 0.26 * L)


@register
class Acorn(Element):
    name = "acorn"
    category = "western"
    description = ("Acorn: an oval nut with a small point, under a scaly cap (crosshatched) with a short stem. "
                   "Nut centre at the origin, cap and stem toward -y.")
    size_note = "length including stem"
    size_default, size_min, size_max = 0.50, 0.30, 0.90
    layer = 45

    def draw(self, size, **_):
        from shapely.geometry import Polygon, LineString
        s = size * 100 / 1.0
        nut = []
        for i in range(48):
            th = 2 * math.pi * i / 48
            x, y = 0.27 * s * math.cos(th), 0.30 * s * math.sin(th)
            if y > 0:
                y *= 1 + 0.18 * math.sin(th) ** 6
            nut.append((x, y + 0.10 * s))
        o = [path(smooth(nut)),
             f'<circle cx="0" cy="{f(0.43*s)}" r="{f(0.03*s)}" fill="{WHITE}" stroke="{INK}" stroke-width="{FINE}"/>']
        stem = [(0, -0.26 * s), (0.02 * s, -0.36 * s), (0.06 * s, -0.44 * s)]
        cap_top = [(0.33 * s * math.cos(t), 0.0 * s - 0.27 * s * math.sin(t) ** 0.8) for t in [math.pi * i / 16 for i in range(1, 16)]]
        cap_bot = []
        for i in range(17):
            u = -1 + 2 * i / 16
            cap_bot.append((0.33 * s * u, 0.03 * s + 0.035 * s * abs(math.sin(4.5 * math.pi * (u + 1) / 2))))
        cap = cap_top + cap_bot
        o.insert(0, path(smooth(tapered(stem, 0.05 * s, 0.035 * s))))
        o.append(path(smooth(cap)))
        cp = Polygon(cap).buffer(-4).intersection(Polygon(cap_top + [(0.33 * s, -0.01 * s), (-0.33 * s, -0.01 * s)][::-1]).buffer(0))
        for k in range(-5, 6):
            for sgn in (1, -1):
                ln = LineString([(-0.5 * s + k * 0.12 * s, 0.10 * s), (0.5 * s + k * 0.12 * s, -0.40 * s)] if sgn > 0 else
                                [(0.5 * s + k * 0.12 * s, 0.10 * s), (-0.5 * s + k * 0.12 * s, -0.40 * s)])
                seg = cp.intersection(ln)
                for g in (getattr(seg, "geoms", None) or [seg]):
                    if not g.is_empty and g.length > 2:
                        (x1, y1), (x2, y2) = list(g.coords)[0], list(g.coords)[-1]
                        o.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{INK}" stroke-width="{FINE}"/>')
        return "\n".join(o)

    def anchors(self, size, **_):
        s = size * 100
        return {"stem": (0.06 * s, -0.44 * s, -70)}

    def flow(self, size, **_):
        return [(0, 0, 0.4)]

    def extent(self, size, **_):
        s = size * 100
        return (-0.35 * s, -0.47 * s, 0.35 * s, 0.47 * s)


@register
class Daisy(Element):
    name = "daisy"
    category = "western"
    description = ("Daisy: two rings of long, narrow, round-tipped petals, each with a centre cut, around a large "
                   "seeded centre. A lighter Western alternative to the rose.")
    size_note = "flower diameter"
    size_default, size_min, size_max = 1.00, 0.60, 1.80
    layer = 60

    @staticmethod
    def _petal(a, R, L=1.0):
        loc = [(0.28, -0.05), (0.55, -0.10), (0.85 * L, -0.09), (0.97 * L, -0.045), (1.0 * L, 0), (0.97 * L, 0.045),
               (0.85 * L, 0.09), (0.55, 0.10), (0.28, 0.05)]
        ca, sa = math.cos(a), math.sin(a)
        pts = [(R * (u * ca - v * sa), R * (u * sa + v * ca)) for u, v in loc]
        return path(smooth(pts)) + line_path([(R * u * ca, R * u * sa) for u in (0.42, 0.62, 0.86 * L)])

    def draw(self, size, **_):
        R = size * 100 / 2
        o = []
        for k in range(16):
            o.append(self._petal(math.radians(k * 22.5 + 11.25), R, 0.90))
        for k in range(16):
            o.append(self._petal(math.radians(k * 22.5), R))
        o.append(f'<circle cx="0" cy="0" r="{f(0.30*R)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        ga = math.pi * (3 - math.sqrt(5))
        for i in range(1, 46):
            r = 0.255 * R * math.sqrt(i / 45)
            o.append(dot(r * math.cos(i * ga), r * math.sin(i * ga), 1.35))
        return "\n".join(o)

    def anchors(self, size, **_):
        R = size * 100 / 2
        return {"left": (-0.9 * R, 0, 180), "right": (0.9 * R, 0, 0)}

    def flow(self, size, **_):
        return [(0, 0, 1.3)]


@register
class Feather(Element):
    name = "feather"
    category = "western"
    description = ("Feather: a gently curved quill with a vane on both sides, two splits in the vane and fine barb "
                   "cuts angled toward the tip. Quill end at the origin, tip toward +x.")
    size_note = "feather length"
    size_default, size_min, size_max = 1.60, 0.80, 3.00
    layer = 40

    @staticmethod
    def _shaft(L, t):
        return (t * L, -0.06 * L * math.sin(math.pi * t * 0.9))

    def _width(self, t, side):
        if t < 0.18:
            return 0.0
        u = (t - 0.18) / 0.82
        w = (0.13 if side < 0 else 0.11) * math.sin(math.pi * min(u, 1)) ** 0.55 * (1 - 0.25 * t)
        t0 = 0.55 if side < 0 else 0.70
        return w * (1 - 0.55 * max(0, 1 - abs(t - t0) / 0.03))

    def draw(self, size, **_):
        L = size * 100
        up, lo = [], []
        for i in range(81):
            t = 0.18 + 0.82 * i / 80
            x, y = self._shaft(L, t)
            up.append((x, y - self._width(t, -1) * L))
            lo.append((x, y + self._width(t, 1) * L))
        o = [path(smooth((up + lo[::-1])[::2]))]
        shaft = [self._shaft(L, t) for t in [i / 30 * 0.98 for i in range(31)]]
        o.append(path(smooth(tapered(shaft, 0.024 * L, 0.006 * L)[::2])))
        t = 0.24
        while t < 0.93:
            for side in (-1, 1):
                t2 = min(t + 0.07, 0.99)
                t0 = 0.55 if side < 0 else 0.70
                if abs(t2 - t0) < 0.035:
                    continue
                x1, y1 = self._shaft(L, t)
                x2, y2 = self._shaft(L, t2)
                w = self._width(t2, side) * L * 0.88
                o.append(f'<line x1="{f(x1)}" y1="{f(y1 + side * 0.012 * L)}" x2="{f(x2)}" y2="{f(y2 + side * w)}" '
                         f'stroke="{INK}" stroke-width="{FINE}" stroke-linecap="round"/>')
            t += 0.045
        return "\n".join(o)

    def anchors(self, size, **_):
        return {"base": (0, 0, 180)}

    def flow(self, size, **_):
        return []

    def extent(self, size, **_):
        L = size * 100
        return (-2, -0.20 * L, L * 1.01, 0.12 * L)
