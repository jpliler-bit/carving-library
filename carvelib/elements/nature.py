"""More Japanese motifs: momiji (maple leaf), ginkgo leaf, tombo (dragonfly), lotus, bamboo, wave crest."""
import math
from ..element import Element, register
from ..geometry import path, smooth, line_path, f, catmull, band, tapered, spiral, LINE, FINE, WHITE


def _poly(pts, fill=WHITE, sw=LINE):
    return path("M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z", fill=fill, sw=sw)


def _polar(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


@register
class Momiji(Element):
    name = "momiji"
    category = "leaves"
    description = ("Japanese maple leaf (momiji): seven pointed, finely toothed lobes radiating from a short stem, "
                   "with a vein to each tip. Leaf centre at the origin, stem pointing down (+y).")
    size_note = "leaf width"
    size_default, size_min, size_max = 0.85, 0.50, 1.60
    layer = 40
    LOBES = [(-198, 0.44), (-162, 0.72), (-126, 0.92), (-90, 1.00), (-54, 0.92), (-18, 0.72), (18, 0.44)]

    def _R(self, size):
        return size * 100 / 1.55

    def draw(self, size, **_):
        R = self._R(size)
        rv = 0.30 * R
        lob = self.LOBES
        valleys = [(lob[0][0] - 30, 0.16 * R)]
        for (a1, _), (a2, _) in zip(lob, lob[1:]):
            valleys.append(((a1 + a2) / 2, rv))
        valleys.append((lob[-1][0] + 30, 0.16 * R))
        pts = [_polar(0.10 * R, 90)]
        for k, (a, L) in enumerate(lob):
            (aL, rL), (aR, rR) = valleys[k], valleys[k + 1]
            tip = L * R
            n = 10
            for i in range(n):                       # left valley -> tip
                t = i / n
                r = rL + (tip - rL) * t
                if 0.35 < t < 0.95 and i % 2:
                    r *= 1.045
                pts.append(_polar(r, a + (aL - a) * (1 - t) ** 0.55))
            pts.append(_polar(tip, a))
            for i in range(n - 1, -1, -1):           # tip -> right valley
                t = i / n
                r = rR + (tip - rR) * t
                if 0.35 < t < 0.95 and i % 2:
                    r *= 1.045
                pts.append(_polar(r, a + (aR - a) * (1 - t) ** 0.55))
        stem = catmull([(0, 0), (0.02 * R, 0.35 * R), (0.09 * R, 0.72 * R)], 6)
        o = [path(smooth(tapered(stem, 0.07 * R, 0.05 * R)[::2])), _poly(pts)]
        for a, L in lob:
            tx, ty = _polar(0.84 * L * R, a)
            mx, my = _polar(0.45 * L * R, a + 3)
            o.append(line_path([(0, 0.03 * R), (mx, my), (tx, ty)]))
        return "\n".join(o)

    def anchors(self, size, **_):
        R = self._R(size)
        return {"base": (0.09 * R, 0.72 * R, 90)}

    def flow(self, size, **_):
        return [(0, -0.3 * self._R(size), 0.8)]

    def extent(self, size, **_):
        R = self._R(size)
        return (-0.75 * R, -1.05 * R, 0.75 * R, 0.78 * R)


@register
class Ginkgo(Element):
    name = "ginkgo"
    category = "leaves"
    description = ("Ginkgo leaf: a fan with a wavy outer edge split by a central notch, fine radiating veins and a "
                   "short stem. Fan base at the origin, opening upward (-y), stem pointing down.")
    size_note = "leaf width"
    size_default, size_min, size_max = 0.75, 0.40, 1.40
    layer = 40

    def _R(self, size):
        return size * 100 / 1.73

    def draw(self, size, **_):
        R = self._R(size)
        pts = []
        for t in (0.10, 0.35, 0.58):
            pts.append(_polar(t * R, -150 + 6 * math.sin(math.pi * t)))
        for i in range(61):
            th = -150 + 120 * i / 60
            d = abs(th + 90) / 60
            r = R * (1 + 0.025 * math.sin(math.radians(th) * 14))
            if d < 0.09:
                r *= 1 - 0.24 * (1 - d / 0.09)
            r *= 1 - 0.30 * max(0, (d - 0.84) / 0.16) ** 2
            pts.append(_polar(r, th))
        for t in (0.58, 0.35, 0.10):
            pts.append(_polar(t * R, -30 - 6 * math.sin(math.pi * t)))
        pts.append((0, 0.02 * R))
        stem = catmull([(0, 0), (0.04 * R, 0.30 * R), (0.12 * R, 0.55 * R)], 6)
        o = [path(smooth(tapered(stem, 0.07 * R, 0.05 * R)[::2])), path(smooth(pts))]
        for th in (-138, -120, -104, -76, -60, -42):
            o.append(line_path([_polar(0.16 * R, th), _polar(0.5 * R, th), _polar(0.84 * R, th)]))
        return "\n".join(o)

    def anchors(self, size, **_):
        R = self._R(size)
        return {"base": (0.12 * R, 0.55 * R, 90)}

    def flow(self, size, **_):
        return [(0, -0.5 * self._R(size), 0.8)]

    def extent(self, size, **_):
        R = self._R(size)
        return (-0.9 * R, -1.05 * R, 0.9 * R, 0.6 * R)


@register
class Tombo(Element):
    name = "tombo"
    category = "creatures"
    description = ("Dragonfly (tombo), seen from above: big eyes, thorax, a long segmented body and four veined wings. "
                   "The 'victory insect' of samurai crests. Thorax at the origin, head toward -y.")
    size_note = "wingspan"
    size_default, size_min, size_max = 1.20, 0.80, 2.40
    layer = 55

    def _wing(self, root, tip, width):
        rx, ry = root
        tx, ty = tip
        L = math.hypot(tx - rx, ty - ry)
        ux, uy = (tx - rx) / L, (ty - ry) / L
        nx, ny = -uy, ux
        loc = [(0, 0), (0.12, -0.55), (0.5, -0.75), (0.85, -0.55), (1.0, 0.0), (0.88, 0.45), (0.5, 0.55), (0.12, 0.40)]
        pts = [(rx + ux * u * L + nx * v * width, ry + uy * u * L + ny * v * width) for u, v in loc]
        vein = [(rx + ux * u * L + nx * -0.1 * width, ry + uy * u * L + ny * -0.1 * width) for u in (0.08, 0.5, 0.9)]
        st = [(rx + ux * 0.86 * L + nx * v * width, ry + uy * 0.86 * L + ny * v * width) for v in (-0.5, -0.1)]
        return path(smooth(pts)) + line_path(vein) + line_path(st)

    def draw(self, size, **_):
        s = size * 100
        o = []
        for sx in (-1, 1):
            o.append(self._wing((sx * 0.03 * s, 0.03 * s), (sx * 0.48 * s, 0.10 * s), 0.10 * s))     # hind wings
            o.append(self._wing((sx * 0.03 * s, -0.03 * s), (sx * 0.50 * s, -0.08 * s), 0.085 * s))  # fore wings
        ab = [(0, 0.05 * s + i * 0.05 * s) for i in range(11)]
        o.append(path(smooth(tapered(ab, 0.05 * s, 0.022 * s)[::1])))
        for i in range(1, 10):
            y = 0.05 * s + i * 0.05 * s
            w = 0.05 * s + (0.022 * s - 0.05 * s) * i / 10
            o.append(line_path([(-w / 2 * 0.8, y), (0, y + 1), (w / 2 * 0.8, y)]))
        o.append(f'<ellipse cx="0" cy="0" rx="{f(0.045*s)}" ry="{f(0.075*s)}" fill="{WHITE}" stroke="#111" stroke-width="{LINE}"/>')
        o.append(f'<ellipse cx="0" cy="{f(-0.09*s)}" rx="{f(0.05*s)}" ry="{f(0.035*s)}" fill="{WHITE}" stroke="#111" stroke-width="{LINE}"/>')
        for sx in (-1, 1):
            o.append(f'<circle cx="{f(sx*0.033*s)}" cy="{f(-0.105*s)}" r="{f(0.03*s)}" fill="{WHITE}" stroke="#111" stroke-width="{LINE}"/>')
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 0.8)]

    def extent(self, size, **_):
        s = size * 100
        return (-0.53 * s, -0.16 * s, 0.53 * s, 0.6 * s)


@register
class Lotus(Element):
    name = "lotus"
    category = "flowers"
    description = ("Lotus (renge), side view as in Buddhist carving: a fan of pointed petals rising from a crescent "
                   "receptacle, centre petal in front. A classic Kamakura-bori motif. Base at the origin, petals up.")
    size_note = "overall width"
    size_default, size_min, size_max = 1.20, 0.80, 2.20
    layer = 60

    @staticmethod
    def _petal(bx, by, ang, L, W, veins=1):
        loc = [(-0.10, 0), (-0.42, -0.25), (-0.46, -0.55), (-0.30, -0.82), (-0.10, -0.96), (0, -1.0),
               (0.10, -0.96), (0.30, -0.82), (0.46, -0.55), (0.42, -0.25), (0.10, 0)]
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        P = lambda u, v: (bx + (u * W) * ca - (v * L) * sa, by + (u * W) * sa + (v * L) * ca)
        o = [path(smooth([P(u, v) for u, v in loc]))]
        o.append(line_path([P(0, -0.15), P(0, -0.5), P(0, -0.82)]))
        if veins > 1:
            for sd in (-1, 1):
                o.append(line_path([P(sd * 0.16, -0.18), P(sd * 0.24, -0.5), P(sd * 0.12, -0.78)]))
        return "\n".join(o)

    def draw(self, size, **_):
        s = size * 100 / 1.1
        o = []
        for sd in (-1, 1):
            o.append(self._petal(sd * 0.08 * s, -0.02 * s, sd * 16, 0.50 * s, 0.20 * s))
        for sd in (-1, 1):
            o.append(self._petal(sd * 0.20 * s, 0.0, sd * 60, 0.42 * s, 0.24 * s))
        for sd in (-1, 1):
            o.append(self._petal(sd * 0.11 * s, 0.01 * s, sd * 33, 0.52 * s, 0.27 * s, veins=3))
        o.append(self._petal(0, 0.02 * s, 0, 0.58 * s, 0.31 * s, veins=3))
        rec = [(-0.36 * s, -0.01 * s), (-0.18 * s, 0.03 * s), (0, 0.04 * s), (0.18 * s, 0.03 * s), (0.36 * s, -0.01 * s),
               (0.26 * s, 0.09 * s), (0, 0.15 * s), (-0.26 * s, 0.09 * s)]
        o.append(path(smooth(rec)))
        o.append(line_path([(-0.2 * s, 0.08 * s), (0, 0.105 * s), (0.2 * s, 0.08 * s)]))
        return "\n".join(o)

    def anchors(self, size, **_):
        s = size * 100 / 1.1
        return {"base": (0, 0.15 * s, 90), "left": (-0.5 * s, -0.2 * s, 180), "right": (0.5 * s, -0.2 * s, 0)}

    def flow(self, size, **_):
        return [(0, -0.25 * size * 100 / 1.1, 1.3)]

    def extent(self, size, **_):
        s = size * 100 / 1.1
        return (-0.6 * s, -0.62 * s, 0.6 * s, 0.17 * s)


@register
class Bamboo(Element):
    name = "bamboo"
    category = "leaves"
    description = ("Bamboo (take): a jointed stalk with node rings and two sprays of narrow pointed leaves. "
                   "Base at the origin, stalk rising toward -y; rotate to lean it.")
    size_note = "stalk length"
    size_default, size_min, size_max = 1.40, 0.80, 3.00
    layer = 35

    @staticmethod
    def _leaf(x, y, ang, L):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        loc = [(0, 0), (0.25, -0.11), (0.6, -0.10), (1.0, 0.0), (0.6, 0.08), (0.25, 0.09)]
        pts = [(x + ux * u * L + nx * v * L, y + uy * u * L + ny * v * L) for u, v in loc]
        return path(smooth(pts)) + line_path([(x + ux * u * L, y + uy * u * L) for u in (0.08, 0.5, 0.88)])

    def draw(self, size, **_):
        L = size * 100
        w = 0.085 * L
        nodes = [0.30, 0.60, 0.88]
        o = []
        ys = [-L * i / 40 for i in range(41)]
        ws = []
        for y in ys:
            t = -y / L
            bump = max([max(0, 1 - abs(t - n) / 0.025) for n in nodes] + [0])
            ws.append(w * (1 + 0.14 * bump))
        o.append(path(smooth(band([(0, y) for y in ys], ws)[0][::2])))
        for n in nodes:
            y = -n * L
            o.append(line_path([(-w * 0.55, y - 1.5), (0, y - 3), (w * 0.55, y - 1.5)]))
            o.append(line_path([(-w * 0.55, y + 1.5), (0, y), (w * 0.55, y + 1.5)]))
        tw = catmull([(w * 0.45, -0.60 * L), (0.18 * L, -0.70 * L), (0.32 * L, -0.76 * L)], 6)
        o.append(path(smooth(tapered(tw, 0.028 * L, 0.018 * L)[::2])))
        tw2 = catmull([(-w * 0.45, -0.30 * L), (-0.14 * L, -0.38 * L), (-0.24 * L, -0.42 * L)], 6)
        o.append(path(smooth(tapered(tw2, 0.026 * L, 0.016 * L)[::2])))
        for ang, ln in ((-28, 0.42), (8, 0.38), (42, 0.30)):
            o.append(self._leaf(0.32 * L, -0.76 * L, ang, ln * L))
        for ang, ln in ((205, 0.32), (165, 0.28)):
            o.append(self._leaf(-0.24 * L, -0.42 * L, ang, ln * L))
        return "\n".join(o)

    def anchors(self, size, **_):
        return {"base": (0, 0, 90), "top": (0, -size * 100, -90)}

    def flow(self, size, **_):
        L = size * 100
        return [(0.4 * L, -0.75 * L, 0.5)]

    def extent(self, size, **_):
        L = size * 100
        return (-0.55 * L, -1.02 * L, 0.75 * L, 0.03 * L)


@register
class NamiCrest(Element):
    name = "nami_crest"
    category = "scrolls"
    description = ("Wave crest (nami): a swelling band of water that rises and curls over, with foam 'claws' "
                   "along its crest and flow lines inside. Base at the origin, travelling toward +x.")
    size_note = "wave length"
    size_default, size_min, size_max = 1.20, 0.80, 2.50
    layer = 15

    def _center(self, L):
        lead = catmull([(0, 0), (0.25 * L, -0.04 * L), (0.48 * L, -0.16 * L), (0.64 * L, -0.34 * L)], 8)
        a = math.atan2(lead[-1][1] - lead[-2][1], lead[-1][0] - lead[-2][0])
        sp = spiral(lead[-1][0], lead[-1][1], a, +1, 0.13 * L, 1.15, shrink=0.78, steps=40)
        side = a + math.pi / 2
        cc = (lead[-1][0] + 0.13 * L * math.cos(side), lead[-1][1] + 0.13 * L * math.sin(side))
        return lead[:-1] + sp, cc

    def draw(self, size, **_):
        L = size * 100
        c, cc = self._center(L)
        n = len(c)
        ws = [0.012 * L + 0.20 * L * math.sin(math.pi * (i / (n - 1)) ** 0.62) ** 1.1 for i in range(n)]
        outline, left, right = band(c, ws)
        o = []
        # foam claws on the outer edge of the crest (the side away from the curl centre)
        for frac in (0.40, 0.50, 0.58):
            i = int(frac * n)
            p_l, p_r = left[i], right[i]
            dl = math.hypot(p_l[0] - cc[0], p_l[1] - cc[1])
            dr = math.hypot(p_r[0] - cc[0], p_r[1] - cc[1])
            p = p_l if dl > dr else p_r
            ox, oy = p[0] - c[i][0], p[1] - c[i][1]
            m = math.hypot(ox, oy) or 1
            tx, ty = c[i + 1][0] - c[i - 1][0], c[i + 1][1] - c[i - 1][1]
            heading = math.atan2(oy / m - 0.6 * ty / (math.hypot(tx, ty) or 1), ox / m - 0.6 * tx / (math.hypot(tx, ty) or 1))
            sp = spiral(p[0] - ox / m * 2, p[1] - oy / m * 2, heading, -1, 0.045 * L, 0.95, shrink=0.7, steps=24)
            o.append(path(smooth(tapered(sp, 0.035 * L, 0.006 * L)[::2])))
        o.insert(0, path(smooth(outline[::2])))
        for k in (0.35, -0.2):
            _, l2, r2 = band(c, [w * abs(k) * 2 for w in ws])
            side = l2 if k > 0 else r2
            o.append(line_path(side[int(n * 0.12):int(n * 0.72)][::3]))
        return "\n".join(o)

    def anchors(self, size, **_):
        return {"base": (0, 0, 180)}

    def flow(self, size, **_):
        L = size * 100
        return [(0.7 * L, -0.25 * L, 0.7)]

    def extent(self, size, **_):
        L = size * 100
        return (-0.05 * L, -0.65 * L, 1.0 * L, 0.15 * L)
