"""Fill panels: seigaiha (overlapping wave scales)."""
from ..element import Element, register
from ..geometry import path, f, LINE, FINE, INK, WHITE


@register
class Seigaiha(Element):
    name = "seigaiha"
    category = "fills"
    description = ("Seigaiha wave-scale panel, centred on the origin. Outer arcs are cuts; the inner rings can be "
                   "decorative cuts or a 3D-printed seigaiha stamp struck in rows.")
    size_note = "panel length (height comes from the strap width, option 'height')"
    size_default, size_min, size_max = 1.2, 0.4, 6.0
    layer = 25

    def draw(self, size, height=1.18, scale=0.21, uid="sg", **_):
        w, h, R = size * 100, height * 100, scale * 100
        x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
        out = [f'<clipPath id="{uid}"><rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}"/></clipPath>',
               f'<g clip-path="url(#{uid})">']
        row, y = 0, y0 - R
        while y < y1 + R * 1.2:
            x = x0 - 2 * R + (R if row % 2 else 0)
            while x < x1 + 2 * R:
                for k, rr in enumerate((R, R * 0.68, R * 0.36)):
                    out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr)}" fill="{WHITE}" stroke="{INK}" '
                               f'stroke-width="{FINE if k else LINE}"/>')
                x += 2 * R
            y += R / 2
            row += 1
        out.append("</g>")
        out.append(path(f"M{f(x0)},{f(y0)} L{f(x1)},{f(y0)} L{f(x1)},{f(y1)} L{f(x0)},{f(y1)} Z", fill="none"))
        return "\n".join(out)

    def flow(self, size, **_):
        return []

    def extent(self, size, height=1.18, **_):
        return (-size * 50, -height * 50, size * 50, height * 50)
