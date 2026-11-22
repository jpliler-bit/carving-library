"""Products: the piece of leather a design goes on.

Each product turns a few measurements (inches) into:
  outline   the cut line (shapely polygon, units of 0.01 in)
  stitch    stitch lines (list of point lists), drawn dashed
  folds     fold lines (list of point lists), drawn dash-dot
  marks     hardware references (holes, slots, snaps) as SVG
  panels    named default carving areas (shapely polygons)
Frame: x from the left edge, y from the product's horizontal CENTRELINE, positive down.
Internally y is shifted so the top edge is 0 (the assembler handles that).
"""
import math
from shapely.geometry import Polygon, Point, box, LineString
from shapely import affinity
from .geometry import f, HARDWARE

PRODUCTS = {}


def product(cls):
    PRODUCTS[cls.name] = cls
    return cls


def rounded_box(x0, y0, x1, y1, r):
    if r <= 0:
        return box(x0, y0, x1, y1)
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, resolution=16, join_style=1)


def inset(poly, d, round_corners=12):
    """Shrink a shape by d, keeping its corners rounded (radius ~round_corners units)."""
    g = poly.buffer(-d, resolution=16, join_style=1)
    if g.is_empty:
        return poly
    if round_corners:
        g2 = g.buffer(-round_corners, resolution=16).buffer(round_corners, resolution=16)
        if not g2.is_empty:
            g = g2
    return g


def ring(poly):
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    return list(poly.exterior.coords)


def hole(x, y, r=8):
    return (f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="none" stroke="{HARDWARE}" stroke-width="1.1"/>'
            f'<line x1="{f(x-4)}" y1="{f(y)}" x2="{f(x+4)}" y2="{f(y)}" stroke="{HARDWARE}" stroke-width="0.6"/>'
            f'<line x1="{f(x)}" y1="{f(y-4)}" x2="{f(x)}" y2="{f(y+4)}" stroke="{HARDWARE}" stroke-width="0.6"/>')


def slot(x, y, w, h):
    return (f'<rect x="{f(x - w/2)}" y="{f(y - h/2)}" width="{f(w)}" height="{f(h)}" rx="{f(min(w, h)/2)}" fill="none" '
            f'stroke="{HARDWARE}" stroke-width="1.1" stroke-dasharray="4 3"/>')


class Product:
    name = "product"
    description = ""
    defaults = {}
    strap = False          # strap-like: carving panel usually runs lengthwise (belts, straps, collars)

    def __init__(self, params):
        self.p = {**self.defaults, **params}
        self.W = self.p["length"] * 100 if "length" in self.p else self.p["width"] * 100
        self.H = (self.p["width"] if "length" in self.p else self.p["height"]) * 100
        self.outline = None
        self.stitch, self.folds, self.marks, self.panels = [], [], [], {}
        self.build()

    def build(self):
        raise NotImplementedError


# ------------------------------------------------------------------ straps
@product
class Belt(Product):
    name = "belt"
    description = "Belt strap: buckle end on the left, tip on the right. Panel usually from a `panel:` strap block."
    defaults = {"width": 1.5, "length": 36, "tip": "round"}
    strap = True

    def build(self):
        W, H, p = self.W, self.H, self.p
        tip = p.get("tip", "round")
        if tip == "round":
            self.outline = box(0, 0, W - H / 2, H).union(Point(W - H / 2, H / 2).buffer(H / 2, resolution=32))
        elif tip == "point":
            self.outline = Polygon([(0, 0), (W - H * 0.6, 0), (W, H / 2), (W - H * 0.6, H), (0, H)])
        else:
            self.outline = box(0, 0, W, H)
        if p.get("crease", True):
            # crease runs along both edges and round the tip, but not across the buckle end
            ln = LineString(ring(inset(self.outline, 8))).intersection(box(10, -10, W + 10, H + 10))
            parts = list(ln.geoms) if hasattr(ln, "geoms") else [ln]
            from shapely.ops import linemerge
            merged = linemerge(parts)
            for part in (merged.geoms if hasattr(merged, "geoms") else [merged]):
                self.folds.append(("crease", list(part.coords)))
        cy = H / 2
        if "buckle_slot" in p:
            self.marks.append(slot(p["buckle_slot"] * 100, cy, 24, 56))
        if "keeper" in p:
            x = p["keeper"] * 100
            self.marks.append(f'<line x1="{f(x)}" y1="16" x2="{f(x)}" y2="{f(H-16)}" stroke="{HARDWARE}" stroke-width="1" stroke-dasharray="4 3"/>')
        if "holes" in p:
            h = p["holes"]
            for k in range(h.get("count", 5)):
                self.marks.append(hole((h["first"] + k * h.get("spacing", 1.0)) * 100, cy))


@product
class Strap(Product):
    name = "strap"
    description = ("Generic strap: guitar strap, dog collar, watch band, bag strap. Ends: square, round or point. "
                   "Optional holes: {first, count, spacing} and rivets: [x, ...].")
    defaults = {"width": 2.5, "length": 40, "ends": "round"}
    strap = True

    def build(self):
        W, H, p = self.W, self.H, self.p
        e = p.get("ends", "round")
        if e == "round":
            self.outline = rounded_box(0, 0, W, H, H / 2 - 0.01)
        elif e == "point":
            k = H * 0.55
            self.outline = Polygon([(k, 0), (W - k, 0), (W, H / 2), (W - k, H), (k, H), (0, H / 2)])
        else:
            self.outline = rounded_box(0, 0, W, H, 6)
        self.folds.append(("crease", ring(inset(self.outline, 8))))
        if "holes" in p:
            h = p["holes"]
            for k in range(h.get("count", 5)):
                self.marks.append(hole((h["first"] + k * h.get("spacing", 1.0)) * 100, H / 2))
        for x in p.get("rivets", []):
            self.marks.append(hole(x * 100, H / 2, 6))
        m = p.get("margin", 0.16) * 100
        self.panels["main"] = rounded_box(H * 0.6, m, W - H * 0.6, H - m, 10)


@product
class Blank(Product):
    name = "blank"
    description = "Plain rectangle of leather, e.g. a test strip. width = short side, length = long side."
    defaults = {"width": 1.5, "length": 5.2, "crease": False}
    strap = True

    def build(self):
        self.outline = box(0, 0, self.W, self.H)
        if self.p.get("crease"):
            self.folds.append(("crease", ring(inset(self.outline, 8))))
        self.panels["main"] = box(30, 16, self.W - 30, self.H - 16)


# ------------------------------------------------------------------ flat goods
class Flat(Product):
    """Flat goods are given as width (x) x height (y)."""

    def __init__(self, params):
        p = {**self.defaults, **params}
        self.p = p
        self.W, self.H = p.get("width", 0) * 100, p.get("height", 0) * 100
        self.outline = None
        self.stitch, self.folds, self.marks, self.panels = [], [], [], {}
        self.build()

    def stitch_line(self, sides="all", d=None):
        d = (self.p.get("stitch_inset", 0.125) if d is None else d) * 100
        c = ring(inset(self.outline, d))
        if sides == "all":
            self.stitch.append(c)
        else:
            cy_top = d + 1
            self.stitch.append([pt for pt in c if pt[1] > cy_top + 0.5] if sides == "no_top" else c)


@product
class Panel(Flat):
    name = "panel"
    description = "Rectangular flat piece with rounded corners (card-holder front, notebook panel, bag flap...)."
    defaults = {"width": 4.0, "height": 3.0, "corner": 0.20, "stitch": "none", "margin": 0.30}

    def build(self):
        p = self.p
        self.outline = rounded_box(0, 0, self.W, self.H, p["corner"] * 100)
        if p["stitch"] != "none":
            self.stitch_line(p["stitch"])
        self.panels["main"] = inset(self.outline, p["margin"] * 100)


@product
class CardHolder(Flat):
    name = "card_holder"
    description = "Card holder front panel (fits standard cards). Stitched on sides and bottom; carve the main panel."
    defaults = {"width": 4.25, "height": 3.0, "corner": 0.20, "margin": 0.32}

    def build(self):
        p = self.p
        self.outline = rounded_box(0, 0, self.W, self.H, p["corner"] * 100)
        self.stitch_line("no_top")
        self.panels["main"] = inset(self.outline, p["margin"] * 100)


@product
class BifoldWallet(Flat):
    name = "bifold_wallet"
    description = ("Bifold wallet outer shell, laid flat. Fold at the centre; 'back' is the left half, 'front' the "
                   "right half, 'whole' spans both. Stitched all round.")
    defaults = {"width": 8.75, "height": 3.625, "corner": 0.25, "margin": 0.30}

    def build(self):
        p = self.p
        W, H, m = self.W, self.H, p["margin"] * 100
        self.outline = rounded_box(0, 0, W, H, p["corner"] * 100)
        self.stitch_line("all")
        self.folds.append(("fold", [(W / 2, -6), (W / 2, H + 6)]))
        r = 12
        self.panels["back"] = rounded_box(m, m, W / 2 - m * 0.9, H - m, r)
        self.panels["front"] = rounded_box(W / 2 + m * 0.9, m, W - m, H - m, r)
        self.panels["whole"] = inset(self.outline, m)


@product
class NotebookCover(Flat):
    name = "notebook_cover"
    description = ("Notebook cover laid flat (default fits a 3.5 x 5.5 pocket notebook). Spine fold lines at the centre; "
                   "'front' is the right half, 'back' the left.")
    defaults = {"width": 8.0, "height": 5.75, "corner": 0.25, "margin": 0.35, "spine": 0.375}

    def build(self):
        p = self.p
        W, H, m, s = self.W, self.H, p["margin"] * 100, p["spine"] * 100
        self.outline = rounded_box(0, 0, W, H, p["corner"] * 100)
        self.stitch_line("all")
        for x in (W / 2 - s / 2, W / 2 + s / 2):
            self.folds.append(("fold", [(x, -6), (x, H + 6)]))
        self.panels["back"] = rounded_box(m, m, W / 2 - s / 2 - m * 0.6, H - m, 14)
        self.panels["front"] = rounded_box(W / 2 + s / 2 + m * 0.6, m, W - m, H - m, 14)


@product
class Coaster(Flat):
    name = "coaster"
    description = "Round coaster (diameter = width). Carving panel is a circle inset by `margin`."
    defaults = {"width": 4.0, "height": 4.0, "margin": 0.25, "stitch": False}

    def build(self):
        p = self.p
        r = self.W / 2
        self.H = self.W
        self.outline = Point(r, r).buffer(r, resolution=64)
        if p.get("stitch"):
            self.stitch_line("all")
        self.panels["main"] = Point(r, r).buffer(r - p["margin"] * 100, resolution=64)


@product
class KeyFob(Flat):
    name = "key_fob"
    description = ("Loop key fob laid flat: a strap with round ends, folded at the centre around a ring, riveted near "
                   "both ends. Carve 'face' (the half that shows), or 'both'.")
    defaults = {"width": 5.0, "height": 1.0, "margin": 0.10}

    def build(self):
        W, H, m = self.W, self.H, self.p["margin"] * 100
        self.outline = rounded_box(0, 0, W, H, H / 2 - 0.01)
        self.folds.append(("crease", ring(inset(self.outline, 7))))
        self.folds.append(("fold", [(W / 2, -6), (W / 2, H + 6)]))
        for x in (H * 0.55, W - H * 0.55):
            self.marks.append(hole(x, H / 2, 6))
        r = (H - 2 * m) / 2 - 1
        self.panels["face"] = rounded_box(H * 0.82, m, W / 2 - 16, H - m, r)
        self.panels["back"] = rounded_box(W / 2 + 16, m, W - H * 0.82, H - m, r)


@product
class PancakeSheath(Flat):
    name = "pancake_sheath"
    description = ("Pancake knife sheath front, upright: straight top, sides sweeping to a rounded point. Two belt "
                   "slots near the top; stitch line follows the welt. Size it to the blade (width x height).")
    defaults = {"width": 3.6, "height": 8.0, "margin": 0.45, "slots": True}

    def build(self):
        W, H = self.W, self.H
        pts = [(0, 0), (W, 0), (W, H * 0.55), (W * 0.92, H * 0.78), (W * 0.70, H * 0.94), (W * 0.48, H),
               (W * 0.26, H * 0.95), (W * 0.06, H * 0.80), (0, H * 0.58)]
        from .geometry import catmull
        smooth_pts = catmull(pts[1:] + [pts[0]], 8)
        self.outline = Polygon([pts[0]] + smooth_pts).buffer(0).buffer(-4, join_style=1).buffer(4, join_style=1)
        self.stitch_line("no_top", 0.25)
        if self.p.get("slots", True):
            for x in (W * 0.28, W * 0.72):
                self.marks.append(slot(x, H * 0.10, 18, 70))
        main = inset(self.outline, self.p["margin"] * 100).intersection(box(0, H * 0.20, W, H))
        self.panels["main"] = main


@product
class Custom(Flat):
    name = "custom"
    description = "Any outline: `points: [[x, y], ...]` in inches from the top-left corner (smoothed unless smooth: false)."
    defaults = {"margin": 0.30, "smooth": True,
                "points": [[0.1, 0.1], [2.9, 0.1], [2.9, 1.9], [1.5, 2.6], [0.1, 1.9]]}

    def build(self):
        pts = [(x * 100, y * 100) for x, y in self.p["points"]]
        if self.p.get("smooth", True):
            pts = closed_spline(pts, 10)
        self.outline = Polygon(pts).buffer(0)
        x0, y0, x1, y1 = self.outline.bounds
        self.W, self.H = x1, y1
        if self.p.get("stitch"):
            self.stitch_line("all")
        self.panels["main"] = inset(self.outline, self.p["margin"] * 100)


def closed_spline(pts, n=10):
    """Closed Catmull-Rom curve through every point (wraps around, no corner at the start)."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out


def make(spec):
    t = spec.get("type", "blank")
    if t not in PRODUCTS:
        raise KeyError(f"unknown product '{t}'. Products: {', '.join(sorted(PRODUCTS))}")
    return PRODUCTS[t]({k: v for k, v in spec.items() if k != "type"})
