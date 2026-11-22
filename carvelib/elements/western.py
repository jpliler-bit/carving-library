"""Western / Sheridan-style motifs: Sheridan rose, Sheridan leaf, rose bud."""
import math
from ..element import Element, register
from ..geometry import path, smooth, line_path, dot, f, catmull, LINE, FINE, INK, WHITE


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
