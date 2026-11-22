"""Leaves: botan (peony) leaf."""
from ..element import Element, register
from ..geometry import path, smooth, line_path


@register
class BotanLeaf(Element):
    name = "botan_leaf"
    category = "leaves"
    description = "Peony leaf with three pointed lobes and a midrib. Base at the origin, tip along +x. Tuck the base under a stem or flower."
    size_note = "leaf length (base to tip)"
    size_default, size_min, size_max = 0.66, 0.40, 1.20
    layer = 40

    def draw(self, size, width_ratio=0.41, **_):
        ln = size * 100
        w = ln * width_ratio
        loc = [(0.0, 0.0), (0.12, -0.16), (0.30, -0.44), (0.46, -0.62), (0.50, -0.36), (0.60, -0.40), (0.78, -0.30),
               (1.0, 0.0), (0.78, 0.30), (0.60, 0.40), (0.50, 0.36), (0.46, 0.62), (0.30, 0.44), (0.12, 0.16)]
        o = [path(smooth([(u * ln, v * w) for u, v in loc])),
             line_path([(0.05 * ln, 0), (0.5 * ln, 0), (0.9 * ln, 0)]),
             line_path([(0.32 * ln, 0), (0.44 * ln, -0.36 * w)]),
             line_path([(0.32 * ln, 0), (0.44 * ln, 0.36 * w)])]
        return "\n".join(o)

    def anchors(self, size, **_):
        return {"base": (0, 0, 180), "tip": (size * 100, 0, 0)}

    def flow(self, size, **_):
        return []

    def extent(self, size, width_ratio=0.41, **_):
        ln = size * 100
        return (0, -0.62 * ln * width_ratio, ln, 0.62 * ln * width_ratio)
