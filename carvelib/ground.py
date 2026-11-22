"""Background (ground) treatments."""
import math
import random
from .geometry import f, MARK


def knife_marks(x0, x1, y0, y1, centers, seed=5):
    """Kamakura-bori style gouge marks. Strokes ripple around the flow centres (x, y, weight) of the
    placed elements instead of running in uniform rows. Shown in grey: stamp them, don't trace them."""
    rnd = random.Random(seed)
    out = []
    y = y0 + 3
    row = 0
    while y < y1 + 2:
        x = x0 - 8 + (row % 2) * 8
        while x < x1 + 8:
            vx, vy = 0.35, 0.0
            for cx, cy, wt in centers:
                dx, dy = x - cx, y - cy
                d2 = dx * dx + dy * dy + 60
                w = wt * 900 / d2
                m = math.sqrt(d2)
                tx, ty = -dy / m, dx / m
                if tx < 0:
                    tx, ty = -tx, -ty
                vx += tx * w
                vy += ty * w
            a = math.atan2(vy, vx) + rnd.uniform(-0.12, 0.12)
            ln = 10 + rnd.random() * 3.5
            x2, y2 = x + ln * math.cos(a), y + ln * math.sin(a)
            mx, my = (x + x2) / 2 - 2.2 * math.sin(a), (y + y2) / 2 + 2.2 * math.cos(a)
            out.append(f'<path d="M{f(x)},{f(y)} Q{f(mx)},{f(my)} {f(x2)},{f(y2)}" fill="none" stroke="{MARK}" '
                       f'stroke-width="0.9" stroke-linecap="round"/>')
            x += 14 + rnd.random() * 3
        y += 8
        row += 1
    return "\n".join(out)
