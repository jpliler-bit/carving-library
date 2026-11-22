"""Shared geometry and SVG helpers.

Internal unit: 1 unit = 0.01 inch (U = 100 units per inch). Recipes are written in inches.
Screen convention (SVG): x to the right, y DOWN.
"""
import math

U = 100.0            # units per inch
LINE = 1.6           # swivel-knife cut line weight (units)
FINE = 0.9           # decorative cut / modeling line weight
INK = "#111"
WHITE = "#fff"
BG = "#e3ddd3"       # background (ground) tone in line drawings
MARK = "#8a8378"     # knife-mark texture strokes
HARDWARE = "#c0392b" # reference marks that are not traced


def f(v):
    """Compact number formatting for SVG."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


def smooth(pts, close=True):
    """Catmull-Rom spline through points, as an SVG cubic-bezier path string."""
    n = len(pts)
    get = (lambda i: pts[i % n]) if close else (lambda i: pts[max(0, min(n - 1, i))])
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    rng = n if close else n - 1
    for i in range(rng):
        p0, p1, p2, p3 = get(i - 1), get(i), get(i + 1), get(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d + (" Z" if close else "")


def catmull(pts, n=10):
    """Sample a Catmull-Rom spline through pts, n samples per segment."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def hermite(p0, d0, p1, d1, n=24):
    """Cubic Hermite curve from p0 (direction d0) to p1 (direction d1). Directions are unit vectors."""
    ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    k = ln * 0.9
    out = []
    for i in range(n + 1):
        t = i / n
        h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
        out.append((h00 * p0[0] + h10 * k * d0[0] + h01 * p1[0] + h11 * k * d1[0],
                    h00 * p0[1] + h10 * k * d0[1] + h01 * p1[1] + h11 * k * d1[1]))
    return out


def band(center, widths):
    """Outline of a band of varying width around a centerline polyline -> (outline, left, right)."""
    left, right = [], []
    n = len(center)
    for i, (x, y) in enumerate(center):
        a, b = center[max(0, i - 1)], center[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        m = math.hypot(tx, ty) or 1
        nx, ny = -ty / m, tx / m
        w = widths[i] / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1], left, right


def tapered(center, w0, w1, power=0.9):
    n = len(center)
    ws = [w0 + (w1 - w0) * (i / max(n - 1, 1)) ** power for i in range(n)]
    return band(center, ws)[0]


def path(d, fill=WHITE, sw=LINE, extra=""):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{f(sw)}" '
            f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')


def line_path(pts, sw=FINE):
    return path(smooth(pts, close=False), fill="none", sw=sw)


def dot(x, y, r=1.7):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{INK}"/>'


def spiral(x0, y0, heading, turn, r0, turns, shrink=0.72, steps=60):
    """Spiral leaving (x0,y0) along heading (radians), curling to one side (turn=+1 clockwise on screen)."""
    side = heading + turn * math.pi / 2
    ccx, ccy = x0 + r0 * math.cos(side), y0 + r0 * math.sin(side)
    a0 = math.atan2(y0 - ccy, x0 - ccx)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        r = r0 * (1 - shrink * t)
        a = a0 + turn * t * turns * 2 * math.pi
        pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return pts


class Xf:
    """Placement transform: mirror (optional), rotate (degrees), then translate. Matches the SVG transform."""

    def __init__(self, x=0.0, y=0.0, rotate=0.0, flip_x=False, flip_y=False):
        self.x, self.y, self.rot = x, y, rotate
        self.sx = -1 if flip_x else 1
        self.sy = -1 if flip_y else 1

    def point(self, p):
        px, py = p[0] * self.sx, p[1] * self.sy
        a = math.radians(self.rot)
        return (self.x + px * math.cos(a) - py * math.sin(a), self.y + px * math.sin(a) + py * math.cos(a))

    def angle(self, deg):
        """Transform a direction angle (degrees)."""
        dx, dy = math.cos(math.radians(deg)) * self.sx, math.sin(math.radians(deg)) * self.sy
        return math.degrees(math.atan2(dy, dx)) + self.rot

    def svg(self):
        t = f"translate({f(self.x)} {f(self.y)})"
        if self.rot:
            t += f" rotate({f(self.rot)})"
        if self.sx != 1 or self.sy != 1:
            t += f" scale({self.sx} {self.sy})"
        return t
