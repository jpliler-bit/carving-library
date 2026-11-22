"""The Element format every library motif follows.

An element draws itself in LOCAL coordinates (origin at its natural centre or base, units of
0.01 in), at a given SIZE in inches. It is never scaled after drawing, so line weights, seeder
dots and minimum petal sizes stay carvable. Placement only translates, rotates and mirrors.

Each element declares:
  size_default / size_min / size_max  (inches) - what "size" means is in `size_note`
  layer        default stacking order (low draws first, high sits on top)
  anchors()    named connection points (x, y, out_angle_deg) where stems attach;
               out_angle points AWAY from the element, the way a stem leaves it
  flow()       points the knife-mark ground ripples around: (x, y, weight)
  draw()       SVG markup
"""
REGISTRY = {}


def register(cls):
    REGISTRY[cls.name] = cls()
    return cls


class Element:
    name = "element"
    category = "misc"
    description = ""
    size_note = "overall size"
    size_default = 1.0
    size_min = 0.5
    size_max = 2.0
    layer = 50

    def check_size(self, size):
        if size is None:
            return self.size_default
        if not (self.size_min - 1e-9 <= size <= self.size_max + 1e-9):
            raise ValueError(f"{self.name}: size {size}\" is outside the carvable range "
                             f"{self.size_min}\"-{self.size_max}\" ({self.size_note})")
        return size

    def draw(self, size, **opts):
        raise NotImplementedError

    def anchors(self, size, **opts):
        return {}

    def flow(self, size, **opts):
        return [(0.0, 0.0, 1.0)]

    def extent(self, size, **opts):
        """Approximate (xmin, ymin, xmax, ymax) in local units, for catalogs and layout checks."""
        s = size * 100
        return (-s / 2, -s / 2, s / 2, s / 2)
