"""Stems and ribbons: the lines that tie elements together.

A stem either runs through a list of points (Catmull-Rom spline) or connects two ends, where each
end is a point or an element anchor ('bud1.base'). Anchor ends use the anchor's direction so the
stem flows into the element instead of meeting it at an angle.
"""
import math
from .geometry import path, smooth, line_path, catmull, hermite, band, tapered, spiral


def stem_svg(center, width, end_width=None, line=True):
    end_width = width if end_width is None else end_width
    o = [path(smooth(tapered(center, width, end_width)[::2]))]
    if line and len(center) > 8:
        o.append(line_path(center[::6]))
    return "\n".join(o)


def ribbon_svg(center, width, spiral_start=False, spiral_end=False, r0=24, turns=1.3):
    """Flowing-water ribbon (ryusui): a band with two inner flow lines; optional spiral ends."""
    pts = list(center)
    n_lt = n_rt = 0
    if spiral_start:
        a = math.atan2(pts[0][1] - pts[1][1], pts[0][0] - pts[1][0])
        turn = 1 if math.sin(a) <= 0 and math.cos(a) < 0 else -1
        lt = spiral(pts[0][0], pts[0][1], a, -turn, r0, turns)
        pts = lt[::-1] + pts[1:]
        n_lt = len(lt)
    if spiral_end:
        a = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
        rt = spiral(pts[-1][0], pts[-1][1], a, +1 if math.cos(a) >= 0 else -1, r0, turns)
        pts = pts[:-1] + rt
        n_rt = len(rt)
    ws = []
    n = len(pts)
    for i in range(n):
        t = 0.0
        if i < n_lt:
            t = 1 - i / n_lt
        elif i >= n - n_rt and n_rt:
            t = (i - (n - n_rt)) / n_rt
        ws.append(width + (3 - width) * t ** 0.8)
    o = [path(smooth(band(pts, ws)[0][::2]))]
    for k in (0.44, -0.44):
        _, l2, r2 = band(pts, [w * abs(k) for w in ws])
        side = l2 if k > 0 else r2
        a, b = int(n_lt * 0.35), len(side) - int(n_rt * 0.35)
        o.append(line_path(side[a:b][::3]))
    return "\n".join(o)


def resolve_end(spec, anchors, default_toward=None):
    """Return (point, direction-unit-vector-out-of-that-end) for a connector end."""
    if isinstance(spec, str):
        if spec not in anchors:
            raise KeyError(f"unknown anchor '{spec}'. Known: {', '.join(sorted(anchors))}")
        x, y, ang = anchors[spec]
        return (x, y), (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    if isinstance(spec, dict):          # already converted to global units by the assembler
        return tuple(spec["pt"]), None
    raise TypeError(f"connector end must be an anchor name or a point, got {spec!r}")


def connect(frm, to, anchors, start_dir=None, end_dir=None, via=None):
    p0, d0 = resolve_end(frm, anchors)
    p1, d1o = resolve_end(to, anchors)
    if start_dir is not None:
        d0 = (math.cos(math.radians(start_dir)), math.sin(math.radians(start_dir)))
    if d0 is None:
        m = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1
        d0 = ((p1[0] - p0[0]) / m, (p1[1] - p0[1]) / m)
    if end_dir is not None:
        d1 = (math.cos(math.radians(end_dir)), math.sin(math.radians(end_dir)))
    elif d1o is not None:
        d1 = (-d1o[0], -d1o[1])        # arrive travelling INTO the anchor
    else:
        d1 = d0
    if via:
        pts = [p0] + [tuple(v) for v in via] + [p1]
        return catmull(pts, 10)
    return hermite(p0, d0, p1, d1)
