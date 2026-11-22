"""Knife-mark texture stamp (Kamakura-bori 'flowing knife marks') as a binary STL.

Print standing, face UP: PLA, 0.12 mm layers, 4 walls, 40% infill, 5 mm brim.
Units: mm. Run:  python tools/knife_mark_stamp.py  ->  stamps/knife_mark_texture_stamp.stl
"""
import os
OUT = os.path.join(os.path.dirname(__file__), "..", "stamps", "knife_mark_texture_stamp.stl")
import math, struct
import numpy as np

SIDE = 10.0          # shaft cross-section (mm)
LEN = 60.0           # shaft length
BOSS_H = 1.3         # height of the gouge bosses above the face
N = 201              # grid resolution across the face

xs = np.linspace(-SIDE / 2, SIDE / 2, N)
X, Y = np.meshgrid(xs, xs, indexing="xy")


def stroke(cx, cy, length, w0, w1, ang_deg, bend):
    """Height field of one gouge stroke: wide start, tapering tail, rounded profile."""
    a = math.radians(ang_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    dx, dy = X - cx, Y - cy
    u = dx * ux + dy * uy                      # along stroke
    v = dx * nx + dy * ny                      # across stroke
    t = (u + length / 2) / length              # 0..1 along
    v = v - bend * (t - 0.5) ** 2 * 4 + bend   # gentle curve
    w = w0 + (w1 - w0) * np.clip(t, 0, 1)
    inside = (t >= 0) & (t <= 1) & (np.abs(v) < w / 2)
    prof = np.sqrt(np.clip(1 - (2 * v / w) ** 2, 0, 1))
    endfade = np.clip(np.minimum(t / 0.12, (1 - t) / 0.25), 0, 1)
    return np.where(inside, prof * np.sqrt(endfade), 0.0)


h = np.zeros_like(X)
strokes = [(-1.13, -3.6, 6.0, 2.1, 0.6), (-1.31, -0.76, 6.6, 2.2, 0.6), (1.31, 1.4, 6.6, 2.2, 0.6), (1.0, 3.9, 4.6, 1.8, 0.6)]
for cx, cy, l, w0, w1 in strokes:
    h = np.maximum(h, stroke(cx, cy, l, w0, w1, -28, 0.45))
h *= BOSS_H

# chamfer the face edge so only the bosses touch the leather
r = np.maximum(np.abs(X), np.abs(Y))
base = -np.clip((r - 3.8) / 1.2, 0, 1) * 1.0
Z = LEN + base + h

tris = []


def quad(a, b, c, d):
    tris.append((a, b, c))
    tris.append((a, c, d))


P = lambda i, j, z: (xs[j], xs[i], z)
# top surface
for i in range(N - 1):
    for j in range(N - 1):
        quad(P(i, j, Z[i, j]), P(i, j + 1, Z[i, j + 1]), P(i + 1, j + 1, Z[i + 1, j + 1]), P(i + 1, j, Z[i + 1, j]))
# bottom: fan from the centre through every boundary vertex (no T-junctions), facing down
ring = ([(xs[j], xs[0]) for j in range(N)] + [(xs[N-1], xs[i]) for i in range(1, N)]
        + [(xs[j], xs[N-1]) for j in range(N - 2, -1, -1)] + [(xs[0], xs[i]) for i in range(N - 2, 0, -1)])
for k in range(len(ring)):
    a, b = ring[k], ring[(k + 1) % len(ring)]
    tris.append(((0.0, 0.0, 0.0), (b[0], b[1], 0.0), (a[0], a[1], 0.0)))
# side walls: stitch top boundary to bottom edge, one strip per side, fanned to the bottom corners
def wall(edge_pts, b0, b1):
    # edge_pts: top boundary points in order from corner b0 side to b1 side (outward-facing order)
    n = len(edge_pts)
    for k in range(n - 1):
        t0, t1 = edge_pts[k], edge_pts[k + 1]
        bt0 = (t0[0], t0[1], 0.0)
        bt1 = (t1[0], t1[1], 0.0)
        tris.append((bt0, t1, t0))
        tris.append((bt0, bt1, t1))

wall([P(0, j, Z[0, j]) for j in range(N)], None, None)                     # y = -s
wall([P(i, N - 1, Z[i, N - 1]) for i in range(N)], None, None)             # x = +s
wall([P(N - 1, j, Z[N - 1, j]) for j in range(N - 1, -1, -1)], None, None) # y = +s
wall([P(i, 0, Z[i, 0]) for i in range(N - 1, -1, -1)], None, None)         # x = -s


def normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    m = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    return nx / m, ny / m, nz / m


with open(OUT, "wb") as fh:
    fh.write(b"Kamakura-bori knife-mark texture stamp".ljust(80, b" "))
    fh.write(struct.pack("<I", len(tris)))
    for a, b, c in tris:
        fh.write(struct.pack("<12fH", *normal(a, b, c), *a, *b, *c, 0))
print(len(tris), "triangles")

# preview of the face as an impression map (dark = deeper impression)
from PIL import Image
img = (255 - (h / BOSS_H) * 200).astype(np.uint8)
Image.fromarray(img).resize((400, 400), Image.LANCZOS).save(OUT.replace(".stl", "_face.png"))
