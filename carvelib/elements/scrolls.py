"""Scrolls: guri pommel (paired spirals), single guri scroll, sheath (bract), wave curl."""
import math
from ..element import Element, register
from ..geometry import path, smooth, line_path, catmull, tapered, band, spiral

# Reference guri arm, drawn with its heart point at the origin, opening toward +x, curling upward.
_ARM_REF = [(0, 0), (10, -13), (25, -29), (45, -42), (66, -48)]
_C = (82, -24)
for _i in range(1, 31):
    _t = _i / 30
    _a = math.radians(-112 + _t * 1.3 * 360)
    _r = 25 * (1 - 0.80 * _t)
    _ARM_REF.append((_C[0] + _r * math.cos(_a), _C[1] + _r * math.sin(_a)))
_REF_LEN = 107.0   # x-extent of the reference pommel (units)


def _arm(scale, mirror):
    pts = catmull(_ARM_REF, 4)
    return [(x * scale, (-y if mirror else y) * scale) for x, y in pts]


def _draw_arm(pts, scale):
    w0 = max(10.0, 13 * scale)
    return path(smooth(tapered(pts, w0, 3.5)[::2])) + line_path(pts[8:int(len(pts) * 0.80)][::3])


@register
class GuriPommel(Element):
    name = "guri_pommel"
    category = "scrolls"
    description = ("Guri 'sword-pommel' heart: two scroll arms leave one point and curl back into spirals, "
                   "one above and one below the stem. Point at the origin, opening toward +x. "
                   "Run a stem straight through it and cap the point with a sheath.")
    size_note = "length from the point to the far side of the spirals"
    size_default, size_min, size_max = 1.07, 0.70, 1.50
    layer = 10

    def draw(self, size, **_):
        k = size * 100 / _REF_LEN
        return _draw_arm(_arm(k, False), k) + "\n" + _draw_arm(_arm(k, True), k)

    def anchors(self, size, **_):
        L = size * 100
        return {"point": (0, 0, 180), "far": (L * 0.98, 0, 0)}

    def flow(self, size, **_):
        k = size * 100 / _REF_LEN
        return [(_C[0] * k, _C[1] * k, 0.8), (_C[0] * k, -_C[1] * k, 0.8)]

    def extent(self, size, **_):
        k = size * 100 / _REF_LEN
        return (0, -50 * k, _REF_LEN * k, 50 * k)


@register
class GuriScroll(Element):
    name = "guri_scroll"
    category = "scrolls"
    description = "One guri arm: sweeps out from its base and curls back into a spiral (curls upward; mirror for downward)."
    size_note = "length from base to far side of the spiral"
    size_default, size_min, size_max = 1.07, 0.60, 1.50
    layer = 10

    def draw(self, size, **_):
        k = size * 100 / _REF_LEN
        return _draw_arm(_arm(k, False), k)

    def anchors(self, size, **_):
        return {"base": (0, 0, 180)}

    def flow(self, size, **_):
        k = size * 100 / _REF_LEN
        return [(_C[0] * k, _C[1] * k, 0.8)]

    def extent(self, size, **_):
        k = size * 100 / _REF_LEN
        return (0, -50 * k, _REF_LEN * k, 3 * k)


@register
class Sheath(Element):
    name = "sheath"
    category = "scrolls"
    description = "Pointed bract that wraps a stem where it branches. Points toward +x."
    size_note = "length"
    size_default, size_min, size_max = 0.28, 0.20, 0.45
    layer = 50

    def draw(self, size, **_):
        k = size * 100 / 28
        pts = [(-12 * k, -8 * k), (4 * k, -9 * k), (16 * k, 0), (4 * k, 9 * k), (-12 * k, 8 * k), (-8 * k, 0)]
        return path(smooth(pts)) + line_path([(-6 * k, 0), (4 * k, 0), (12 * k, 0)])

    def anchors(self, size, **_):
        k = size * 100 / 28
        return {"back": (-12 * k, 0, 180), "tip": (16 * k, 0, 0)}

    def flow(self, size, **_):
        return []


@register
class WaveCurl(Element):
    name = "wave_curl"
    category = "scrolls"
    description = "Free wave swirl (ryusui): a tapering band that spirals inward. Starts at the origin heading +x, curls clockwise."
    size_note = "swirl diameter"
    size_default, size_min, size_max = 0.46, 0.30, 0.80
    layer = 15

    def draw(self, size, **_):
        r0 = size * 100 / 2
        pts = spiral(0, 0, 0, +1, r0, 1.25)
        ws = [11 + (2.5 - 11) * (i / (len(pts) - 1)) ** 0.8 for i in range(len(pts))]
        outline, _, _ = band(pts, ws)
        return path(smooth(outline[::2])) + line_path(pts[8:int(len(pts) * 0.8)][::4])

    def flow(self, size, **_):
        r0 = size * 100 / 2
        return [(0, r0, 0.5)]

    def extent(self, size, **_):
        r0 = size * 100 / 2
        return (-r0, -5, r0, 2 * r0)
