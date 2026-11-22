"""Turn a YAML recipe into a full-size design SVG.

Coordinates in recipes are INCHES. x runs from the left end of the product (buckle end of a belt);
y is measured from the strap's centreline, positive DOWN. Inside `repeat`, x is measured from the
start of each repeat (the panel start for the first one).
"""
import itertools
import math
import yaml
from . import elements  # noqa: F401  (registers elements)
from .element import REGISTRY
from .geometry import Xf, f, path, catmull, BG, HARDWARE, INK, LINE
from .connectors import stem_svg, ribbon_svg, connect
from .ground import knife_marks, matte

PLACE_KEYS = {"element", "at", "size", "rotate", "flip_x", "flip_y", "id", "layer", "every", "offset", "skip_first", "in_panel"}


class Design:
    def __init__(self, recipe):
        self.r = recipe
        self.name = recipe.get("name", "design")
        p = recipe["product"]
        self.W = p["width"] * 100
        self.Lp = p["length"] * 100
        self.cy = self.W / 2
        self.items = []          # (layer, seq, svg, in_panel)
        self.anchors = {}        # "id.anchor" -> (x, y, angle) global
        self.flows = []
        self.seq = itertools.count()
        self.uid = itertools.count()
        self.warnings = []

    # -------------------------------------------------------------- placement
    def place(self, spec, dx=0.0, in_panel=True, suffix=""):
        el = REGISTRY.get(spec["element"])
        if el is None:
            raise KeyError(f"unknown element '{spec['element']}'. Library has: {', '.join(sorted(REGISTRY))}")
        size = el.check_size(spec.get("size"))
        opts = {k: v for k, v in spec.items() if k not in PLACE_KEYS}
        if el.category == "fills":
            opts.setdefault("uid", f"fill{next(self.uid)}")
            opts.setdefault("height", (self.W - 2 * self.r.get("panel", {}).get("border", 0.16) * 100) / 100)
        x, y = spec["at"]
        xf = Xf(dx + x * 100, self.cy + y * 100, spec.get("rotate", 0), spec.get("flip_x", False), spec.get("flip_y", False))
        svg = f'<g transform="{xf.svg()}">{el.draw(size, **opts)}</g>'
        self.items.append((spec.get("layer", el.layer), next(self.seq), svg, in_panel))
        if "id" in spec:
            for name, (ax, ay, ang) in el.anchors(size, **opts).items():
                gx, gy = xf.point((ax, ay))
                self.anchors[f"{spec['id']}{suffix}.{name}"] = (gx, gy, xf.angle(ang))
        for fx, fy, w in el.flow(size, **opts):
            gx, gy = xf.point((fx, fy))
            self.flows.append((gx, gy, w))

    # -------------------------------------------------------------- build
    def build(self):
        r = self.r
        panel = r.get("panel")
        rep = r.get("repeat")
        if panel and rep:
            start = panel["start"] * 100
            n, L = rep.get("count", 1), rep["length"] * 100
            # elements first (so connectors can use their anchors)
            for i in range(n):
                for spec in rep.get("place", []):
                    # every: N / offset: k -> only in repeats k, k+N, ...; skip_first -> not in repeat 0
                    if (i - spec.get("offset", 0)) % spec.get("every", 1) or (spec.get("skip_first") and i == 0):
                        continue
                    self.place(spec, dx=start + i * L, suffix=f"@{i}" if n > 1 else "")
            # connectors inside a repeat: 'bud1.base' means bud1 in the SAME repeat
            for i in range(n):
                dx = start + i * L
                local = {k: v for k, v in self.anchors.items() if "@" not in k}
                for k, v in self.anchors.items():
                    if f"@{i}." in k:
                        local[k.replace(f"@{i}", "")] = v
                for c in rep.get("connect", []):
                    self._connector(c, local, dx)
            # stems that run through the repeat
            for s in rep.get("stems", []):
                pts_tile = [(x * 100, y * 100) for x, y in s["points"]]
                if s.get("continuous", True):
                    allp = []
                    for i in range(n):
                        seg = [(start + i * L + x, y) for x, y in pts_tile]
                        allp += seg if i == 0 else seg[1:]
                    ext = s.get("extend", 0.12) * 100
                    allp = [(allp[0][0] - ext, allp[0][1])] + allp + [(allp[-1][0] + ext, allp[-1][1])]
                    self._add_line(s, catmull(allp, 14))
                else:
                    for i in range(n):
                        self._add_line(s, catmull([(start + i * L + x, y) for x, y in pts_tile], 14))
        for spec in r.get("extras", []):
            self.place(spec, dx=0, in_panel=spec.get("in_panel", False))
        for c in r.get("connect", []):
            self._connector(c, self.anchors, 0.0)
        return self

    def _connector(self, c, anchors, dx):
        g = lambda p: {"pt": (dx + p[0] * 100, self.cy + p[1] * 100)}
        frm = g(c["from"]) if isinstance(c["from"], list) else c["from"]
        to = g(c["to"]) if isinstance(c["to"], list) else c["to"]
        via = [g(v)["pt"] for v in c["via"]] if "via" in c else None
        pts = connect(frm, to, anchors, c.get("start_dir"), c.get("end_dir"), via)
        c = {"layer": 19, **c}
        self._add_line(c, pts, global_y=True)

    def _add_line(self, s, pts, global_y=False):
        if not global_y:
            pts = [(x, y + self.cy) for x, y in pts]
        style = s.get("style", "stem")
        w = s.get("width", 0.125) * 100
        if style == "ribbon":
            svg = ribbon_svg(pts, w, s.get("spiral_start", False), s.get("spiral_end", False))
        else:
            ew = s.get("end_width")
            svg = stem_svg(pts, w, None if ew is None else ew * 100, s.get("line", True))
        self.items.append((s.get("layer", 30), next(self.seq), svg, s.get("in_panel", True)))

    # -------------------------------------------------------------- product, panel, ground
    def _product_outline(self):
        p = self.r["product"]
        W, L = self.W, self.Lp
        if p.get("type") == "belt" and p.get("tip", "round") == "round":
            rr = W / 2
            return f"M0,0 L{f(L - rr)},0 A{f(rr)},{f(rr)} 0 0 1 {f(L - rr)},{f(W)} L0,{f(W)} Z"
        return f"M0,0 L{f(L)},0 L{f(L)},{f(W)} L0,{f(W)} Z"

    def _panel_path(self):
        pn = self.r["panel"]
        b = pn.get("border", 0.16) * 100
        x0 = pn["start"] * 100
        x1 = x0 + pn.get("length", self.r["repeat"]["length"] * self.r["repeat"].get("count", 1)) * 100
        t, btm, cy = b, self.W - b, self.cy
        ends = pn.get("ends", "square")
        if ends == "round":
            rr = (btm - t) / 2
            return (f"M{f(x0)},{f(t)} L{f(x1)},{f(t)} A{f(rr)},{f(rr)} 0 0 1 {f(x1)},{f(btm)} L{f(x0)},{f(btm)} "
                    f"A{f(rr)},{f(rr)} 0 0 1 {f(x0)},{f(t)} Z"), (x0 - rr, x1 + rr, t, btm)
        if ends == "ogee":
            e = 52
            return (f"M{f(x0)},{f(t)} L{f(x1)},{f(t)} C{f(x1+e*0.55)},{f(t)} {f(x1+e*0.2)},{f(cy-10)} {f(x1+e)},{f(cy)} "
                    f"C{f(x1+e*0.2)},{f(cy+10)} {f(x1+e*0.55)},{f(btm)} {f(x1)},{f(btm)} L{f(x0)},{f(btm)} "
                    f"C{f(x0-e*0.55)},{f(btm)} {f(x0-e*0.2)},{f(cy+10)} {f(x0-e)},{f(cy)} "
                    f"C{f(x0-e*0.2)},{f(cy-10)} {f(x0-e*0.55)},{f(t)} {f(x0)},{f(t)} Z"), (x0 - e, x1 + e, t, btm)
        if ends == "pointed":
            return (f"M{f(x0)},{f(t)} L{f(x1)},{f(t)} C{f(x1+22)},{f(t)} {f(x1+30)},{f(cy-28)} {f(x1+36)},{f(cy)} "
                    f"C{f(x1+30)},{f(cy+28)} {f(x1+22)},{f(btm)} {f(x1)},{f(btm)} L{f(x0)},{f(btm)} "
                    f"C{f(x0-22)},{f(btm)} {f(x0-30)},{f(cy+28)} {f(x0-36)},{f(cy)} "
                    f"C{f(x0-30)},{f(cy-28)} {f(x0-22)},{f(t)} {f(x0)},{f(t)} Z"), (x0 - 36, x1 + 36, t, btm)
        return f"M{f(x0)},{f(t)} L{f(x1)},{f(t)} L{f(x1)},{f(btm)} L{f(x0)},{f(btm)} Z", (x0, x1, t, btm)

    def _hardware(self):
        p = self.r["product"]
        o = []
        cy = self.cy
        if "buckle_slot" in p:
            x = p["buckle_slot"] * 100
            o.append(f'<rect x="{f(x-12)}" y="{f(cy-28)}" width="24" height="56" rx="12" fill="none" stroke="{HARDWARE}" stroke-width="1.1" stroke-dasharray="4 3"/>')
        if "keeper" in p:
            x = p["keeper"] * 100
            o.append(f'<line x1="{f(x)}" y1="16" x2="{f(x)}" y2="{f(self.W-16)}" stroke="{HARDWARE}" stroke-width="1" stroke-dasharray="4 3"/>')
        if "holes" in p:
            h = p["holes"]
            for k in range(h.get("count", 5)):
                x = (h["first"] + k * h.get("spacing", 1.0)) * 100
                o.append(f'<circle cx="{f(x)}" cy="{f(cy)}" r="8" fill="none" stroke="{HARDWARE}" stroke-width="1.1"/>')
                o.append(f'<line x1="{f(x-4)}" y1="{f(cy)}" x2="{f(x+4)}" y2="{f(cy)}" stroke="{HARDWARE}" stroke-width="0.6"/>')
                o.append(f'<line x1="{f(x)}" y1="{f(cy-4)}" x2="{f(x)}" y2="{f(cy+4)}" stroke="{HARDWARE}" stroke-width="0.6"/>')
        for c in self.r.get("cuts", []):
            x = c * 100
            o.append(f'<line x1="{f(x)}" y1="-14" x2="{f(x)}" y2="{f(self.W+14)}" stroke="{HARDWARE}" stroke-width="1.2" stroke-dasharray="5 4"/>')
        return "\n".join(o)

    def body(self):
        """The design as SVG markup in units (no outer <svg>)."""
        o = [f'<path d="{self._product_outline()}" fill="#fff" stroke="{INK}" stroke-width="2.2"/>']
        if self.r["product"].get("crease", True):
            c = 8
            W, L = self.W, self.Lp
            if self.r["product"].get("type") == "belt":
                rr = W / 2 - c
                o.append(f'<path d="M{c},{c} L{f(L-W/2)},{c} A{f(rr)},{f(rr)} 0 0 1 {f(L-W/2)},{f(W-c)} L{c},{f(W-c)}" fill="none" stroke="#777" stroke-width="0.9" stroke-dasharray="6 5"/>')
        if "panel" in self.r:
            pd, (x0, x1, t, b) = self._panel_path()
            cid = f"panel{next(self.uid)}"
            o.append(f'<clipPath id="{cid}"><path d="{pd}"/></clipPath>')
            o.append(path(pd, fill=BG, sw=LINE))
            o.append(f'<g clip-path="url(#{cid})">')
            ground = self.r["panel"].get("ground", "knife_marks")
            if ground == "knife_marks":
                o.append(knife_marks(x0, x1, t, b, self.flows, seed=self.r["panel"].get("seed", 5)))
            elif ground == "matte":
                o.append(matte(x0, x1, t, b))
            o += [svg for _, _, svg, inp in sorted(self.items) if inp]
            o.append("</g>")
            o.append(path(pd, fill="none", sw=LINE))
        o += [svg for _, _, svg, inp in sorted(self.items) if not inp]
        o.append(self._hardware())
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


def ruler_svg(y, x0, x1):
    o = []
    for i in range(int(x0 // 100), int(x1 // 100) + 1):
        x = i * 100
        o.append(f'<line x1="{x}" y1="{f(y)}" x2="{x}" y2="{f(y+14)}" stroke="#555" stroke-width="1"/>')
        o.append(f'<text x="{x}" y="{f(y+28)}" font-family="Helvetica, Arial" font-size="11" text-anchor="middle" fill="#555">{i}"</text>')
        if x + 50 <= x1:
            o.append(f'<line x1="{x+50}" y1="{f(y)}" x2="{x+50}" y2="{f(y+8)}" stroke="#555" stroke-width="0.8"/>')
    return "\n".join(o)


def load(path_):
    """Load a recipe. `repeat_from: other.yaml` borrows that recipe's repeat; keys under this
    recipe's own `repeat:` (count, length, extra place/connect entries) override or extend it."""
    import os
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
