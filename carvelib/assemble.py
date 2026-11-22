"""Turn a YAML recipe into a full-size design SVG.

Coordinates in recipes are INCHES. x runs from the product's left edge; y is measured from the
product's horizontal centreline, positive DOWN. Inside a layout group, coordinates are relative to
that group's origin (see LAYOUTS below).

A recipe has:
  product   what the leather piece is (products.py): belt, strap, card_holder, bifold_wallet, ...
  panels    carving areas: product panels by name, or shapes (rect, circle, oval, strap, inset)
  layout    groups of elements placed by repeat / corners / mirror / radial / single
  extras    one-off elements in product coordinates
Older recipes with `panel:` + `repeat:` (belts) still work.
"""
import itertools
import math
import os
import yaml
from shapely.geometry import Polygon, Point, box
from shapely import affinity
from . import elements  # noqa: F401  (registers elements)
from .element import REGISTRY
from .geometry import Xf, f, path, catmull, BG, HARDWARE, INK, LINE, FINE, MARK
from .connectors import stem_svg, ribbon_svg, connect
from .ground import knife_marks, matte
from .products import make as make_product, ring, inset

PLACE_KEYS = {"element", "at", "size", "rotate", "flip_x", "flip_y", "id", "layer", "every", "offset", "skip_first",
              "in_panel", "panel", "only"}


def _bezier(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def poly_d(poly):
    pts = ring(poly)
    return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z"


class Frame:
    """A chain of placement transforms applied innermost-first: local -> ... -> product."""

    def __init__(self, *xfs):
        self.xfs = [x for x in xfs if x is not None]

    def then(self, xf):
        return Frame(xf, *self.xfs)        # xf is applied before the existing ones

    def point(self, p):
        for xf in self.xfs:
            p = xf.point(p)
        return p

    def angle(self, a):
        for xf in self.xfs:
            a = xf.angle(a)
        return a

    def wrap(self, svg):
        for xf in self.xfs:
            svg = f'<g transform="{xf.svg()}">{svg}</g>'
        return svg


class Design:
    def __init__(self, recipe):
        self.r = recipe
        self.name = recipe.get("name", "design")
        self.prod = make_product(recipe["product"])
        self.Lp, self.W = self.prod.W, self.prod.H     # x extent, y extent (units)
        self.cy = self.W / 2
        self.items = []          # (layer, seq, svg, panel-name or None)
        self.anchors = {}
        self.flows = []
        self.seq = itertools.count()
        self.uid = itertools.count()
        self.panels = {}         # name -> dict(poly, ground, border, seed)

    # -------------------------------------------------------------- coordinates
    def P(self, xy):
        """Recipe point (inches, y from centreline) -> internal units."""
        return (xy[0] * 100, self.cy + xy[1] * 100)

    # -------------------------------------------------------------- panels
    def _strap_panel(self, pn):
        b = pn.get("border", 0.16) * 100
        x0 = pn["start"] * 100
        rep = self.r.get("repeat", {})
        x1 = x0 + pn.get("length", rep.get("length", 0) * rep.get("count", 1)) * 100
        t, btm, cy = b, self.W - b, self.cy
        ends = pn.get("ends", "square")
        if ends == "round":
            rr = (btm - t) / 2
            return box(x0, t, x1, btm).union(Point(x0, cy).buffer(rr, resolution=24)).union(Point(x1, cy).buffer(rr, resolution=24))
        if ends in ("pointed", "ogee"):
            if ends == "pointed":
                right = (_bezier((x1, t), (x1 + 22, t), (x1 + 30, cy - 28), (x1 + 36, cy))
                         + _bezier((x1 + 36, cy), (x1 + 30, cy + 28), (x1 + 22, btm), (x1, btm))[1:])
            else:
                e = 52
                right = (_bezier((x1, t), (x1 + e * 0.55, t), (x1 + e * 0.2, cy - 10), (x1 + e, cy))
                         + _bezier((x1 + e, cy), (x1 + e * 0.2, cy + 10), (x1 + e * 0.55, btm), (x1, btm))[1:])
            left = [(2 * x0 - (x - x1 + x0) - 0, y) for x, y in right]   # mirror of the right end about the panel's left edge
            left = [(x0 - (x - x1), y) for x, y in right][::-1]
            return Polygon(right + left).buffer(0)
        return box(x0, t, x1, btm)

    def _panel_shape(self, spec):
        shape = spec.get("shape")
        if "use" in spec:
            if spec["use"] not in self.prod.panels:
                raise KeyError(f"product '{self.prod.name}' has no panel '{spec['use']}'. It has: "
                               f"{', '.join(self.prod.panels) or 'none'}")
            return self.prod.panels[spec["use"]]
        if shape == "strap" or "start" in spec:
            return self._strap_panel(spec)
        if shape == "rect":
            (x0, x1), (y0, y1) = spec["x"], spec["y"]
            r = spec.get("radius", 0) * 100
            g = box(x0 * 100, self.cy + y0 * 100, x1 * 100, self.cy + y1 * 100)
            return g.buffer(-r).buffer(r, resolution=16) if r else g
        if shape in ("circle", "oval"):
            cx, cy = self.P(spec["center"])
            rx = spec.get("rx", spec.get("r")) * 100
            ry = spec.get("ry", spec.get("r")) * 100
            return affinity.scale(Point(cx, cy).buffer(1, resolution=64), rx, ry, origin=(cx, cy))
        if shape == "inset":
            return inset(self.prod.outline, spec.get("margin", 0.3) * 100)
        raise ValueError(f"panel needs `use:` or a shape (rect, circle, oval, strap, inset): {spec}")

    def _setup_panels(self):
        r = self.r
        specs = {}
        if "panel" in r:                      # legacy single strap panel
            specs["main"] = {"shape": "strap", **r["panel"]}
        pn = r.get("panels")
        if isinstance(pn, list):
            for name in pn:
                specs[name] = {"use": name}
        elif isinstance(pn, dict):
            for name, s in pn.items():
                s = s or {}
                specs[name] = s if ("shape" in s or "use" in s or "start" in s) else {"use": name, **s}
        for name, s in specs.items():
            self.panels[name] = {"poly": self._panel_shape(s), "ground": s.get("ground", "knife_marks"),
                                 "border": s.get("border_style", "line"), "seed": s.get("seed", 5)}

    def default_panel(self):
        return next(iter(self.panels), None)

    # -------------------------------------------------------------- placement
    def place(self, spec, frame, panel, suffix=""):
        el = REGISTRY.get(spec["element"])
        if el is None:
            raise KeyError(f"unknown element '{spec['element']}'. Library has: {', '.join(sorted(REGISTRY))}")
        size = el.check_size(spec.get("size"))
        opts = {k: v for k, v in spec.items() if k not in PLACE_KEYS}
        if el.category == "fills":
            opts.setdefault("uid", f"fill{next(self.uid)}")
            if panel in self.panels:
                x0, y0, x1, y1 = self.panels[panel]["poly"].bounds
                opts.setdefault("height", (y1 - y0) / 100)
            else:
                opts.setdefault("height", (self.W - 32) / 100)
        x, y = spec.get("at", [0, 0])
        el_xf = Xf(x * 100, y * 100, spec.get("rotate", 0), spec.get("flip_x", False), spec.get("flip_y", False))
        fr = frame.then(el_xf)
        self.items.append((spec.get("layer", el.layer), next(self.seq), fr.wrap(el.draw(size, **opts)), panel))
        if "id" in spec:
            for name, (ax, ay, ang) in el.anchors(size, **opts).items():
                gx, gy = fr.point((ax, ay))
                self.anchors[f"{spec['id']}{suffix}.{name}"] = (gx, gy, fr.angle(ang))
        for fx, fy, w in el.flow(size, **opts):
            gx, gy = fr.point((fx, fy))
            self.flows.append((gx, gy, w))

    def _line(self, s, pts, panel):
        style = s.get("style", "stem")
        w = s.get("width", 0.125) * 100
        if style == "ribbon":
            svg = ribbon_svg(pts, w, s.get("spiral_start", False), s.get("spiral_end", False))
        else:
            ew = s.get("end_width")
            svg = stem_svg(pts, w, None if ew is None else ew * 100, s.get("line", True))
        self.items.append((s.get("layer", 30), next(self.seq), svg, panel if s.get("in_panel", True) else None))

    def _connector(self, c, frame, anchors, panel):
        loc = lambda p: {"pt": frame.point((p[0] * 100, p[1] * 100))}
        frm = loc(c["from"]) if isinstance(c["from"], list) else c["from"]
        to = loc(c["to"]) if isinstance(c["to"], list) else c["to"]
        via = [loc(v)["pt"] for v in c["via"]] if "via" in c else None
        sd = frame.angle(c["start_dir"]) if "start_dir" in c else None
        ed = frame.angle(c["end_dir"]) if "end_dir" in c else None
        pts = connect(frm, to, anchors, sd, ed, via)
        self._line({"layer": 19, **c}, pts, panel)

    # -------------------------------------------------------------- layouts
    def _frames(self, g, panel):
        """Origins for each copy of a layout group, as Frames mapping group-local units -> product units."""
        t = g.get("type", "single")
        if panel in self.panels:
            bx0, by0, bx1, by1 = self.panels[panel]["poly"].bounds
        else:
            bx0, by0, bx1, by1 = 0, 0, self.Lp, self.W
        pc = ((bx0 + bx1) / 2, (by0 + by1) / 2)
        center = self.P(g["center"]) if "center" in g else pc
        if t == "single":
            o = self.P(g["origin"]) if "origin" in g else (0, self.cy)
            return [Frame(Xf(*o))]
        if t == "repeat":
            start = g.get("start", bx0 / 100) * 100
            L = g["length"] * 100
            return [Frame(Xf(start + i * L, self.cy + g.get("y", 0) * 100)) for i in range(g.get("count", 1))]
        if t == "corners":
            dx, dy = (v * 100 for v in g.get("offset", [0, 0]))
            table = {"tl": Xf(bx0 + dx, by0 + dy), "tr": Xf(bx1 - dx, by0 + dy, flip_x=True),
                     "bl": Xf(bx0 + dx, by1 - dy, flip_y=True), "br": Xf(bx1 - dx, by1 - dy, flip_x=True, flip_y=True)}
            return [Frame(table[c]) for c in g.get("corners", ["tl", "tr", "bl", "br"])]
        if t == "mirror":
            ax = g.get("axis", "x")
            fr = [Frame(Xf(*center))]
            if "x" in ax:
                fr.append(Frame(Xf(*center, flip_x=True)))
            if "y" in ax:
                fr.append(Frame(Xf(*center, flip_y=True)))
            if ax == "xy":
                fr.append(Frame(Xf(*center, flip_x=True, flip_y=True)))
            return fr
        if t == "radial":
            n = g.get("count", 6)
            fr = [Frame(Xf(*center, rotate=g.get("start_angle", 0) + 360 * k / n)) for k in range(n)]
            if g.get("mirror"):
                fr += [Frame(Xf(*center, rotate=g.get("start_angle", 0) + 360 * k / n, flip_y=True)) for k in range(n)]
            return fr
        raise ValueError(f"unknown layout type '{t}' (repeat, corners, mirror, radial, single)")

    def _group(self, g):
        panel = g.get("panel", self.default_panel())
        frames = self._frames(g, panel)
        n = len(frames)
        for i, fr in enumerate(frames):
            for spec in g.get("place", []):
                if (i - spec.get("offset", 0)) % spec.get("every", 1) or (spec.get("skip_first") and i == 0):
                    continue
                if "only" in spec and i not in spec["only"]:
                    continue
                pn = None if spec.get("in_panel") is False else spec.get("panel", panel)
                self.place(spec, fr, pn, suffix=f"@{i}" if n > 1 else "")
        for i, fr in enumerate(frames):
            local = {k: v for k, v in self.anchors.items() if "@" not in k}
            for k, v in self.anchors.items():
                if f"@{i}." in k:
                    local[k.replace(f"@{i}", "")] = v
            for c in g.get("connect", []):
                self._connector(c, fr, local, panel)
        for s in g.get("stems", []):
            pts = [(x * 100, y * 100) for x, y in s["points"]]
            if g.get("type") == "repeat" and s.get("continuous", True):
                allp = []
                for i, fr in enumerate(frames):
                    seg = [fr.point(p) for p in pts]
                    allp += seg if i == 0 else seg[1:]
                ext = s.get("extend", 0.12) * 100
                allp = [(allp[0][0] - ext, allp[0][1])] + allp + [(allp[-1][0] + ext, allp[-1][1])]
                self._line(s, catmull(allp, 14), panel)
            else:
                for fr in frames:
                    self._line(s, [fr.point(p) for p in catmull(pts, 14)], panel)

    def build(self):
        r = self.r
        self._setup_panels()
        groups = list(r.get("layout", []))
        if "repeat" in r:                         # legacy belt repeat
            pn = self.default_panel()
            start = r.get("panel", {}).get("start")
            groups.insert(0, {"type": "repeat", **({"start": start} if start is not None else {}), **r["repeat"],
                              "panel": pn})
        for g in groups:
            self._group(g)
        for spec in r.get("extras", []):
            pn = spec.get("panel") if spec.get("in_panel", "panel" in spec) else None
            self.place(spec, Frame(Xf(0, self.cy)), pn)
        for c in r.get("connect", []):
            self._connector(c, Frame(Xf(0, self.cy)), self.anchors, self.default_panel())
        return self

    # -------------------------------------------------------------- drawing
    def _border(self, poly, style):
        if style == "none":
            return ""
        o = [path(poly_d(poly), fill="none", sw=LINE)]
        if style == "double":
            o.append(path(poly_d(inset(poly, 7)), fill="none", sw=FINE))
        elif style == "beaded":
            # a raised strip just inside the edge carries the beads; its inner edge is a cut line
            o.append(f'<path d="{poly_d(inset(poly, 6, 0))}" fill="none" stroke="#fff" stroke-width="12"/>')
            o.append(path(poly_d(poly), fill="none", sw=LINE))
            o.append(path(poly_d(inset(poly, 12, 0)), fill="none", sw=LINE))
            ln = LineString_ring(inset(poly, 6, 0))
            n = max(8, int(ln.length / 8.5))
            for k in range(n):
                p = ln.interpolate(k / n, normalized=True)
                o.append(f'<circle cx="{f(p.x)}" cy="{f(p.y)}" r="2.6" fill="#fff" stroke="{INK}" stroke-width="{FINE}"/>')
        elif style == "rope":
            o.append(f'<path d="{poly_d(inset(poly, 6.5, 0))}" fill="none" stroke="#fff" stroke-width="13"/>')
            o.append(path(poly_d(poly), fill="none", sw=LINE))
            o.append(path(poly_d(inset(poly, 13, 0)), fill="none", sw=LINE))
            ln = LineString_ring(inset(poly, 6.5, 0))
            n = max(10, int(ln.length / 7))
            for k in range(n):
                p = ln.interpolate(k / n, normalized=True)
                q = ln.interpolate((k + 0.3) / n, normalized=True)
                tx, ty = q.x - p.x, q.y - p.y
                m = math.hypot(tx, ty) or 1
                tx, ty = tx / m, ty / m
                nx, ny = -ty, tx
                a0 = (p.x - nx * 5.5 - tx * 3.5, p.y - ny * 5.5 - ty * 3.5)
                a1 = (p.x + nx * 5.5 + tx * 3.5, p.y + ny * 5.5 + ty * 3.5)
                c = (p.x + tx * 2.2, p.y + ty * 2.2)
                o.append(f'<path d="M{f(a0[0])},{f(a0[1])} Q{f(c[0])},{f(c[1])} {f(a1[0])},{f(a1[1])}" fill="none" '
                         f'stroke="{INK}" stroke-width="{FINE}" stroke-linecap="round"/>')
        return "\n".join(o)

    def body(self):
        pr = self.prod
        o = [path(poly_d(pr.outline), fill="#fff", sw=2.2)]
        for kind, pts in pr.folds:
            dash = "6 5" if kind == "crease" else "12 4 2 4"
            col = "#777" if kind == "crease" else "#555"
            o.append(f'<path d="M' + " L".join(f"{f(x)},{f(y)}" for x, y in pts) +
                     f'" fill="none" stroke="{col}" stroke-width="0.9" stroke-dasharray="{dash}"/>')
        for pts in pr.stitch:
            o.append(f'<path d="M' + " L".join(f"{f(x)},{f(y)}" for x, y in pts) +
                     f'" fill="none" stroke="#555" stroke-width="1" stroke-dasharray="3 3"/>')
        items = sorted(self.items)
        for name, pn in self.panels.items():
            poly = pn["poly"]
            d = poly_d(poly)
            cid = f"panel{next(self.uid)}"
            x0, y0, x1, y1 = poly.bounds
            o.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
            o.append(path(d, fill=BG if pn["ground"] != "none" else "#fff", sw=0 if pn["border"] == "none" else LINE))
            o.append(f'<g clip-path="url(#{cid})">')
            if pn["ground"] == "knife_marks":
                o.append(knife_marks(x0, x1, y0, y1, self.flows, seed=pn["seed"]))
            elif pn["ground"] == "matte":
                o.append(matte(x0, x1, y0, y1))
            o += [svg for _, _, svg, p in items if p == name]
            o.append("</g>")
            o.append(self._border(poly, pn["border"]))
        o += [svg for _, _, svg, p in items if p not in self.panels]
        o += pr.marks
        for c in self.r.get("cuts", []):
            x = c * 100
            o.append(f'<line x1="{f(x)}" y1="-14" x2="{f(x)}" y2="{f(self.W+14)}" stroke="{HARDWARE}" stroke-width="1.2" stroke-dasharray="5 4"/>')
        return "\n".join(o)

    def svg(self, margin=0.3, ruler=True):
        m = margin * 100
        top, bot = 30, (60 if ruler else 30)
        vb = f"{f(-m)} {-top} {f(self.Lp + 2*m)} {f(self.W + top + bot)}"
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{f((self.Lp+2*m)/100)}in" height="{f((self.W+top+bot)/100)}in" viewBox="{vb}">',
             f'<rect x="{f(-m)}" y="{-top}" width="{f(self.Lp+2*m)}" height="{f(self.W+top+bot)}" fill="#fff"/>',
             self.body()]
        if ruler:
            o.append(ruler_svg(self.W + 8, 0, self.Lp))
        o.append("</svg>")
        return "\n".join(o)


def LineString_ring(poly):
    from shapely.geometry import LineString
    return LineString(ring(poly))


def ruler_svg(y, x0, x1):
    o = []
    for i in range(int(x0 // 100), int(x1 // 100) + 1):
        x = i * 100
        o.append(f'<line x1="{x}" y1="{f(y)}" x2="{x}" y2="{f(y+14)}" stroke="#555" stroke-width="1"/>')
        o.append(f'<text x="{x}" y="{f(y+28)}" font-family="Helvetica, Arial" font-size="11" text-anchor="middle" fill="#555">{i}"</text>')
        if x + 50 <= x1:
            o.append(f'<line x1="{x+50}" y1="{f(y)}" x2="{x+50}" y2="{f(y+8)}" stroke="#555" stroke-width="0.8"/>')
    return "\n".join(o)


def vruler_svg(x, y0, y1, cy):
    """Vertical ruler; labels are inches from the top edge."""
    o = []
    for i in range(int(y0 // 100), int(y1 // 100) + 1):
        y = i * 100
        o.append(f'<line x1="{f(x)}" y1="{y}" x2="{f(x-14)}" y2="{y}" stroke="#555" stroke-width="1"/>')
        o.append(f'<text x="{f(x-18)}" y="{y+4}" font-family="Helvetica, Arial" font-size="11" text-anchor="end" fill="#555">{i}"</text>')
        if y + 50 <= y1:
            o.append(f'<line x1="{f(x)}" y1="{y+50}" x2="{f(x-8)}" y2="{y+50}" stroke="#555" stroke-width="0.8"/>')
    return "\n".join(o)


def load(path_):
    """Load a recipe. `repeat_from: other.yaml` borrows that recipe's repeat; keys under this
    recipe's own `repeat:` (count, length, extra place/connect entries) override or extend it."""
    with open(path_) as fh:
        r = yaml.safe_load(fh)
    if "repeat_from" in r:
        src = os.path.join(os.path.dirname(path_), r["repeat_from"])
        with open(src) as fh:
            base = dict(yaml.safe_load(fh)["repeat"])
        own = r.get("repeat", {}) or {}
        for k, v in own.items():
            base[k] = base.get(k, []) + v if k in ("place", "connect", "stems") else v
        r["repeat"] = base
    return Design(r).build()
