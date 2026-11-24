"""Figures: koi, crane (tsuru), butterfly (cho), rabbit (usagi), horse head, longhorn skull."""
import math
from shapely.geometry import Point, Polygon, LineString
from shapely import affinity
from shapely.ops import unary_union
from ..element import Element, register
from ..geometry import path, smooth, line_path, dot, f, catmull, band, tapered, LINE, FINE, INK, WHITE, BG


def _poly(pts, fill=WHITE, sw=LINE):
    return path("M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z", fill=fill, sw=sw)


def _shape(geom, fill=WHITE, sw=LINE, step=1):
    if geom.geom_type == "MultiPolygon":
        return "\n".join(_shape(g, fill, sw, step) for g in geom.geoms)
    return _poly(list(geom.exterior.coords)[:-1][::step], fill, sw)


def _ellipse(cx, cy, rx, ry, rot=0):
    e = affinity.scale(Point(0, 0).buffer(1, resolution=32), rx, ry)
    return affinity.translate(affinity.rotate(e, rot, origin=(0, 0)), cx, cy)


def _xf(pts, k, ox=0, oy=0, flip_y=False):
    return [(ox + x * k, oy + (-y if flip_y else y) * k) for x, y in pts]


# ------------------------------------------------------------------ koi
@register
class Koi(Element):
    name = "koi"
    category = "creatures"
    description = ("Koi seen from above, body curving: rounded head with eyes and barbels, pectoral fins, rows of "
                   "scale cuts and a flowing split tail. Body centre at the origin, head toward +x.")
    size_note = "length, head to tail tip"
    size_default, size_min, size_max = 1.70, 1.10, 3.20
    layer = 55

    def draw(self, size, **_):
        L = size * 100 / 1.28
        spine = catmull([(0.52 * L, 0), (0.30 * L, 0.025 * L), (0.05 * L, 0.06 * L), (-0.22 * L, 0.04 * L), (-0.44 * L, -0.03 * L)], 10)
        n = len(spine)

        def hw(t):
            return 0.165 * L * math.sin(math.pi / 2 * min(1, t / 0.24)) ** 0.55 * (1 - 0.78 * max(0, (t - 0.24) / 0.76) ** 1.15) + 0.004 * L

        ws = [2 * hw(i / (n - 1)) for i in range(n)]
        outline, left, right = band(spine, ws)
        P = spine[-1]
        dx, dy = P[0] - spine[-3][0], P[1] - spine[-3][1]
        m = math.hypot(dx, dy)
        dx, dy = dx / m, dy / m
        nx, ny = -dy, dx
        T = lambda u, v: (P[0] + dx * u * L + nx * v * L, P[1] + dy * u * L + ny * v * L)
        tail = [T(0, 0.03), T(0.12, 0.10), T(0.27, 0.19), T(0.36, 0.17), T(0.30, 0.08), T(0.22, 0.0),
                T(0.30, -0.08), T(0.36, -0.17), T(0.27, -0.19), T(0.12, -0.10), T(0, -0.03)]
        o = [path(smooth(tail))]
        for v in (0.13, 0.07, -0.07, -0.13):
            o.append(line_path([T(0.04, v * 0.25), T(0.15, v * 0.8), T(0.28, v * 1.3)]))
        i_f = int(0.26 * (n - 1))
        x0, y0 = spine[i_f]
        tx, ty = spine[i_f + 1][0] - spine[i_f - 1][0], spine[i_f + 1][1] - spine[i_f - 1][1]
        m = math.hypot(tx, ty)
        tx, ty = tx / m, ty / m
        px, py = -ty, tx
        for sd in (-1, 1):
            bx, by = x0 + sd * px * hw(0.26) * 0.8, y0 + sd * py * hw(0.26) * 0.8
            fin = [(bx, by), (bx + tx * 0.04 * L + sd * px * 0.05 * L, by + ty * 0.04 * L + sd * py * 0.05 * L),
                   (bx + tx * 0.14 * L + sd * px * 0.13 * L, by + ty * 0.14 * L + sd * py * 0.13 * L),
                   (bx + tx * 0.16 * L + sd * px * 0.08 * L, by + ty * 0.16 * L + sd * py * 0.08 * L),
                   (bx + tx * 0.10 * L + sd * px * 0.01 * L, by + ty * 0.10 * L + sd * py * 0.01 * L)]
            o.append(path(smooth(fin)))
            o.append(line_path([fin[0], ((fin[1][0] + fin[2][0]) / 2, (fin[1][1] + fin[2][1]) / 2), fin[2]]))
        o.append(path(smooth(outline[::2])))
        body = Polygon(outline).buffer(-3)
        # gill line, eyes, barbels
        ig = int(0.17 * (n - 1))
        gx, gy = spine[ig]
        o.append(line_path([(gx + px * hw(0.17) * 0.85, gy + py * hw(0.17) * 0.85), (gx - tx * 0.02 * L, gy - ty * 0.02 * L),
                            (gx - px * hw(0.17) * 0.85, gy - py * hw(0.17) * 0.85)]))
        ie = int(0.07 * (n - 1))
        ex, ey = spine[ie]
        for sd in (-1, 1):
            o.append(dot(ex + sd * px * hw(0.07) * 0.55, ey + sd * py * hw(0.07) * 0.55, 2.2))
            hx, hy = spine[1]
            o.append(line_path([(hx + sd * px * 0.03 * L, hy + sd * py * 0.03 * L), (hx + tx * 0.05 * L + sd * px * 0.06 * L, hy + ty * 0.05 * L + sd * py * 0.06 * L),
                                (hx + tx * 0.04 * L + sd * px * 0.09 * L, hy + ty * 0.04 * L + sd * py * 0.09 * L)]))
        # scales: rows of small arcs bulging toward the tail
        r = 0.032 * L
        for row, t in enumerate([0.24 + 0.055 * k for k in range(11)]):
            i = int(t * (n - 1))
            if i >= n - 2:
                break
            sx, sy = spine[i]
            ux, uy = spine[i + 1][0] - spine[i - 1][0], spine[i + 1][1] - spine[i - 1][1]
            mm = math.hypot(ux, uy)
            ux, uy = ux / mm, uy / mm
            vx, vy = -uy, ux
            h = hw(t) * 0.82
            k = 0
            off = (row % 2) * r
            for j in range(-6, 7):
                v = j * 2 * r + off
                if abs(v) + r > h:
                    continue
                cx, cy = sx + vx * v, sy + vy * v
                a0 = (cx + vx * r, cy + vy * r)
                a1 = (cx - vx * r, cy - vy * r)
                c = (cx + ux * r * 1.6, cy + uy * r * 1.6)
                if body.contains(Point(c)):
                    o.append(f'<path d="M{f(a0[0])},{f(a0[1])} Q{f(c[0])},{f(c[1])} {f(a1[0])},{f(a1[1])}" fill="none" '
                             f'stroke="{INK}" stroke-width="{FINE}" stroke-linecap="round"/>')
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 1.2)]

    def extent(self, size, **_):
        L = size * 100 / 1.28
        return (-0.84 * L, -0.25 * L, 0.56 * L, 0.25 * L)


# ------------------------------------------------------------------ crane
@register
class Tsuru(Element):
    name = "tsuru"
    category = "creatures"
    description = ("Crane (tsuru) in flight, the Japanese symbol of long life: wings raised in a V with fingered "
                   "primary feathers, long neck and beak forward, crown spot, legs trailing. Body at the origin, "
                   "flying toward +x.")
    size_note = "length, beak to feet"
    size_default, size_min, size_max = 2.00, 1.40, 4.00
    layer = 55

    WING = [(0.06, -0.03), (0.10, -0.18), (0.06, -0.34), (-0.02, -0.48), (-0.08, -0.56), (-0.12, -0.50),
            (-0.15, -0.52), (-0.19, -0.44), (-0.22, -0.45), (-0.25, -0.36), (-0.28, -0.36), (-0.29, -0.27),
            (-0.32, -0.25), (-0.30, -0.16), (-0.12, -0.03)]

    def _wing(self, L, k, flip, rot, ox=0, oy=0):
        pts = _xf(self.WING, L * k, ox, oy, flip)
        g = affinity.rotate(Polygon(pts), rot, origin=(ox, oy))
        out = [path(smooth(list(g.exterior.coords)[:-1]))]
        for (sx_, sy_), (nx_, ny_) in zip([(0.03, -0.15), (-0.02, -0.18), (-0.08, -0.19), (-0.14, -0.18), (-0.19, -0.15)],
                                          [(-0.06, -0.47), (-0.12, -0.46), (-0.18, -0.40), (-0.24, -0.33), (-0.28, -0.23)]):
            a = _xf([(sx_, sy_), ((sx_ + nx_) / 2 + 0.01, (sy_ + ny_) / 2), (nx_, ny_)], L * k, ox, oy, flip)
            ln = affinity.rotate(LineString(a), rot, origin=(ox, oy))
            out.append(line_path(list(ln.coords)))
        cov = _xf([(0.08, -0.06), (0.02, -0.16), (-0.10, -0.20), (-0.22, -0.15), (-0.20, -0.06)], L * k, ox, oy, flip)
        out.append(line_path(list(affinity.rotate(LineString(cov), rot, origin=(ox, oy)).coords)))
        return "\n".join(out)

    def draw(self, size, **_):
        L = size * 100 / 1.10
        o = [self._wing(L, 1.0, False, -8)]
        for dy in (0.0, 0.035):        # legs trailing
            leg = [(-0.12 * L, 0.03 * L + dy * L * 0.3), (-0.30 * L, 0.05 * L + dy * L), (-0.48 * L, 0.06 * L + dy * L)]
            o.append(path(smooth(tapered(leg, 0.022 * L, 0.014 * L)[::1])))
        o.append(path(smooth([(-0.17 * L, 0.0), (-0.26 * L, -0.03 * L), (-0.30 * L, 0.01 * L), (-0.26 * L, 0.03 * L), (-0.30 * L, 0.06 * L), (-0.18 * L, 0.05 * L)])))
        body = _ellipse(0, 0.01 * L, 0.17 * L, 0.065 * L, -6)
        neck = Polygon(tapered(catmull([(0.12 * L, -0.01 * L), (0.26 * L, -0.07 * L), (0.38 * L, -0.06 * L), (0.47 * L, -0.10 * L)], 6), 0.06 * L, 0.03 * L))
        head = Point(0.48 * L, -0.105 * L).buffer(0.032 * L, resolution=16)
        o.append(_shape(unary_union([body, neck.buffer(0), head]).simplify(0.3)))
        o.append(_poly([(0.505 * L, -0.12 * L), (0.62 * L, -0.085 * L), (0.505 * L, -0.09 * L)]))
        o.append(f'<circle cx="{f(0.475*L)}" cy="{f(-0.128*L)}" r="{f(0.012*L)}" fill="{WHITE}" stroke="{INK}" stroke-width="{FINE}"/>')
        o.append(dot(0.488 * L, -0.105 * L, 1.8))
        o.append(self._wing(L, 0.92, True, 18, 0.02 * L, 0.02 * L))
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, -0.15 * size * 100 / 1.1, 1.2)]

    def extent(self, size, **_):
        L = size * 100 / 1.10
        return (-0.50 * L, -0.60 * L, 0.63 * L, 0.55 * L)


# ------------------------------------------------------------------ butterfly
@register
class Cho(Element):
    name = "cho"
    category = "creatures"
    description = ("Butterfly (cho), from above: rounded forewings and tailed hindwings, each with an inner edge "
                   "line and an eye spot; slim body; curled antennae. Body at the origin, head toward -y.")
    size_note = "wingspan"
    size_default, size_min, size_max = 1.10, 0.60, 2.20
    layer = 55

    FORE = [(0.02, -0.03), (0.10, -0.20), (0.28, -0.33), (0.45, -0.32), (0.49, -0.20), (0.42, -0.06), (0.22, 0.0), (0.04, 0.0)]
    HIND = [(0.03, 0.01), (0.20, 0.03), (0.35, 0.10), (0.36, 0.22), (0.25, 0.29), (0.18, 0.42), (0.13, 0.30), (0.04, 0.17)]

    def draw(self, size, **_):
        s = size * 100
        o = []
        for sd in (-1, 1):
            for pts, spot in ((self.HIND, (0.22, 0.16, 0.035)), (self.FORE, (0.33, -0.20, 0.045))):
                P = [(sd * x * s, y * s) for x, y in pts]
                o.append(path(smooth(P)))
                inner = Polygon(P).buffer(-0.035 * s)
                if not inner.is_empty:
                    o.append(path(smooth(list(inner.exterior.coords)[:-1][::2]), fill="none", sw=FINE))
                o.append(f'<circle cx="{f(sd*spot[0]*s)}" cy="{f(spot[1]*s)}" r="{f(spot[2]*s)}" fill="{WHITE}" stroke="{INK}" stroke-width="{FINE}"/>')
                o.append(dot(sd * spot[0] * s, spot[1] * s, 1.6))
            for a in (-0.15, -0.25):
                o.append(line_path([(sd * 0.04 * s, -0.01 * s), (sd * 0.18 * s, (a + 0.02) * s * 0.7), (sd * 0.30 * s, a * s)]))
        ab = [(0, -0.06 * s), (0, 0.06 * s), (0, 0.18 * s), (0, 0.26 * s)]
        o.append(path(smooth(tapered(catmull(ab, 4), 0.05 * s, 0.018 * s))))
        o.append(f'<circle cx="0" cy="{f(-0.10*s)}" r="{f(0.03*s)}" fill="{WHITE}" stroke="{INK}" stroke-width="{LINE}"/>')
        for sd in (-1, 1):
            o.append(line_path([(sd * 0.01 * s, -0.12 * s), (sd * 0.06 * s, -0.24 * s), (sd * 0.13 * s, -0.33 * s)], sw=LINE * 0.8))
            o.append(f'<circle cx="{f(sd*0.14*s)}" cy="{f(-0.34*s)}" r="{f(0.018*s)}" fill="{WHITE}" stroke="{INK}" stroke-width="{FINE}"/>')
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 0.8)]

    def extent(self, size, **_):
        s = size * 100
        return (-0.51 * s, -0.37 * s, 0.51 * s, 0.44 * s)


# ------------------------------------------------------------------ rabbit
@register
class Usagi(Element):
    name = "usagi"
    category = "creatures"
    description = ("Rabbit (usagi) sitting, side view, as in the Japanese moon-rabbit motif: round body and haunch, "
                   "head with long ears laid back, puff tail, front paw. Body at the origin, facing +x.")
    size_note = "length, tail to nose"
    size_default, size_min, size_max = 1.10, 0.70, 2.20
    layer = 55

    def draw(self, size, **_):
        s = size * 100 / 0.92
        o = []
        far_ear = _ellipse(0.11 * s, -0.46 * s, 0.20 * s, 0.055 * s, 38)
        o.append(_shape(far_ear))
        o.append(_shape(Point(-0.38 * s, -0.02 * s).buffer(0.08 * s, resolution=16)))
        body = unary_union([_ellipse(0, 0, 0.32 * s, 0.25 * s), Point(-0.12 * s, 0.05 * s).buffer(0.22 * s, resolution=32),
                            _ellipse(0.27 * s, -0.22 * s, 0.16 * s, 0.12 * s, 15), _ellipse(0.20 * s, -0.10 * s, 0.12 * s, 0.13 * s)])
        o.append(_shape(body.simplify(0.3)))
        o.append(_shape(_ellipse(0.27 * s, 0.21 * s, 0.10 * s, 0.045 * s)))
        o.append(line_path([(-0.30 * s, 0.10 * s), (-0.20 * s, -0.12 * s), (0.02 * s, -0.12 * s), (0.08 * s, 0.10 * s)]))
        near_ear = _ellipse(0.03 * s, -0.43 * s, 0.22 * s, 0.065 * s, 30)
        o.append(_shape(near_ear))
        o.append(line_path(list(affinity.rotate(LineString([(-0.13 * s, -0.43 * s), (0.03 * s, -0.43 * s), (0.15 * s, -0.43 * s)]), 30, origin=(0.03 * s, -0.43 * s)).coords)))
        o.append(f'<circle cx="{f(0.33*s)}" cy="{f(-0.25*s)}" r="{f(0.022*s)}" fill="{WHITE}" stroke="{INK}" stroke-width="{FINE}"/>')
        o.append(dot(0.335 * s, -0.25 * s, 1.8))
        o.append(dot(0.425 * s, -0.20 * s, 1.6))
        o.append(line_path([(0.40 * s, -0.16 * s), (0.36 * s, -0.13 * s), (0.31 * s, -0.14 * s)]))
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 1.1)]

    def extent(self, size, **_):
        s = size * 100 / 0.92
        return (-0.47 * s, -0.60 * s, 0.45 * s, 0.30 * s)


# ------------------------------------------------------------------ horse head
@register
class HorseHead(Element):
    name = "horse_head"
    category = "creatures"
    description = ("Horse head and neck, side view, facing right: pricked ears, eye, flared nostril, jaw and cheek "
                   "lines, and a flowing mane of separate locks. Western figure carving. Centre of the head near the "
                   "origin.")
    size_note = "width, mane to muzzle"
    size_default, size_min, size_max = 1.80, 1.20, 3.50
    layer = 55

    OUT = [(0.18, -0.62), (0.27, -0.42), (0.40, -0.36), (0.62, -0.24), (0.82, -0.10), (0.94, 0.01), (0.98, 0.10),
           (0.95, 0.19), (0.87, 0.22), (0.81, 0.28), (0.67, 0.25), (0.52, 0.31), (0.37, 0.31), (0.28, 0.37),
           (0.22, 0.60), (0.22, 0.80), (-0.16, 0.80), (-0.15, 0.50), (-0.08, 0.16), (0.02, -0.16), (0.08, -0.36), (0.10, -0.50)]

    def draw(self, size, **_):
        k = size * 100 / 1.25
        P = lambda pts: [((x - 0.44) * k, (y - 0.05) * k) for x, y in pts]
        o = []
        locks = [(0.07, -0.34, 0.0), (0.02, -0.17, 0.10), (-0.04, 0.0, 0.05), (-0.09, 0.17, 0.16), (-0.13, 0.34, 0.08),
                 (-0.15, 0.52, 0.18), (-0.16, 0.68, 0.10)]
        for x, y, lean in locks:
            c = P([(x + 0.02, y), (x - 0.09, y + 0.03 + lean * 0.2), (x - 0.17, y + 0.13 + lean * 0.4), (x - 0.15 + lean * 0.3, y + 0.25 + lean * 0.5)])
            o.append(path(smooth(tapered(catmull(c, 5), 0.10 * k, 0.012 * k)[::2])))
            o.append(line_path(catmull(c, 5)[2:-3][::2]))
        o.append(path(smooth(P(self.OUT))))
        o.append(path(smooth(P([(0.30, -0.42), (0.37, -0.26), (0.47, -0.30), (0.36, -0.36)]))))   # forelock
        o.append(line_path(P([(0.20, -0.55), (0.22, -0.46), (0.25, -0.41)])))                       # inner ear
        o.append(path(smooth(P([(0.33, -0.14), (0.38, -0.18), (0.45, -0.15), (0.38, -0.11)]))))     # eye
        o.append(dot(*P([(0.385, -0.145)])[0], 2.2))
        o.append(line_path(P([(0.85, 0.06), (0.90, 0.02), (0.93, 0.07), (0.89, 0.10)])))            # nostril
        o.append(line_path(P([(0.84, 0.20), (0.92, 0.17)])))                                        # mouth
        o.append(line_path(P([(0.30, -0.02), (0.36, 0.14), (0.48, 0.24), (0.62, 0.22)])))           # cheek
        o.append(line_path(P([(0.48, -0.04), (0.62, 0.02), (0.76, 0.06)])))                         # face
        o.append(line_path(P([(0.20, 0.42), (0.06, 0.60), (-0.02, 0.78)])))                          # neck
        return "\n".join(o)

    def flow(self, size, **_):
        return [(0, 0, 1.4)]

    def extent(self, size, **_):
        k = size * 100 / 1.25
        return (-0.70 * k, -0.68 * k, 0.56 * k, 0.76 * k)


# ------------------------------------------------------------------ longhorn skull
@register
class LonghornSkull(Element):
    name = "longhorn_skull"
    category = "western"
    description = ("Texas longhorn skull, front view: long tapering face with eye sockets and nasal openings "
                   "(cut and backgrounded), wide horns sweeping out and up with growth rings at the base. "
                   "Centre of the skull at the origin.")
    size_note = "horn span, tip to tip"
    size_default, size_min, size_max = 2.40, 1.40, 5.00
    layer = 55

    SKULL = [(0, -0.30), (0.10, -0.30), (0.15, -0.26), (0.16, -0.16), (0.17, -0.07), (0.13, 0.02), (0.09, 0.20),
             (0.075, 0.34), (0.05, 0.41), (0, 0.43)]

    def draw(self, size, **_):
        s = size * 100 / 1.92
        o = []
        for sd in (-1, 1):
            hc = catmull([(sd * 0.11 * s, -0.24 * s), (sd * 0.36 * s, -0.27 * s), (sd * 0.62 * s, -0.25 * s),
                          (sd * 0.82 * s, -0.32 * s), (sd * 0.95 * s, -0.47 * s)], 8)
            o.append(path(smooth(tapered(hc, 0.10 * s, 0.012 * s, 0.8)[::2])))
            for i in (3, 6, 9):
                (x0, y0), (x1, y1) = hc[i - 1], hc[i + 1]
                tx, ty = x1 - x0, y1 - y0
                m = math.hypot(tx, ty)
                nx, ny = -ty / m, tx / m
                w = 0.05 * s * (1 - i / len(hc)) ** 0.8
                x, y = hc[i]
                o.append(line_path([(x + nx * w, y + ny * w), (x + tx / m * 2, y + ty / m * 2), (x - nx * w, y - ny * w)]))
            o.append(line_path(hc[14:-6][::4]))
        right = self.SKULL
        pts = [(x * s, y * s) for x, y in right] + [(-x * s, y * s) for x, y in right[::-1][1:-1]]
        o.append(path(smooth(pts)))
        for sd in (-1, 1):
            eye = [(sd * 0.06 * s, -0.12 * s), (sd * 0.11 * s, -0.15 * s), (sd * 0.14 * s, -0.09 * s), (sd * 0.11 * s, -0.04 * s), (sd * 0.07 * s, -0.06 * s)]
            o.append(path(smooth(eye), fill=BG))
            nose = [(sd * 0.012 * s, 0.30 * s), (sd * 0.035 * s, 0.28 * s), (sd * 0.045 * s, 0.35 * s), (sd * 0.02 * s, 0.38 * s)]
            o.append(path(smooth(nose), fill=BG))
            o.append(line_path([(sd * 0.03 * s, -0.27 * s), (sd * 0.05 * s, -0.20 * s), (sd * 0.03 * s, -0.12 * s)]))
            o.append(line_path([(sd * 0.05 * s, 0.02 * s), (sd * 0.045 * s, 0.14 * s), (sd * 0.035 * s, 0.25 * s)]))
        o.append(line_path([(0, -0.29 * s), (0, -0.05 * s), (0, 0.22 * s)]))
        return "\n".join(o)

    def anchors(self, size, **_):
        s = size * 100 / 1.92
        return {"left": (-0.95 * s, -0.47 * s, -110), "right": (0.95 * s, -0.47 * s, -70)}

    def flow(self, size, **_):
        return [(0, 0, 1.2)]

    def extent(self, size, **_):
        s = size * 100 / 1.92
        return (-0.98 * s, -0.52 * s, 0.98 * s, 0.45 * s)
