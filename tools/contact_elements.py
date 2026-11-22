"""Preview several elements in one image (line + relief for each):
    python tools/contact_elements.py out.png momiji ginkgo tombo ..."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from carvelib.element import REGISTRY
from carvelib import elements  # noqa: F401
from carvelib.outputs.catalog import element_svg
from carvelib.outputs.common import rasterize
from carvelib.outputs.relief import render

out, names = sys.argv[1], sys.argv[2:]
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
rows = []
for n in names:
    el = REGISTRY[n]
    size = el.size_default
    dpi = int(380 / max(size, 0.35))
    line = Image.open(rasterize(element_svg(el, size), dpi)).convert("RGB")
    svg = element_svg(el, size, anchors=False).replace('fill="#fff"/>', 'fill="#1a1a1a"/>', 1)
    g = Image.open(rasterize(svg, dpi)).convert("L")
    soft = np.asarray(g.filter(ImageFilter.GaussianBlur(dpi * 0.012)), float) / 255
    crisp = np.asarray(g.filter(ImageFilter.GaussianBlur(dpi * 0.003)), float) / 255
    rel = render(0.75 * soft + 0.25 * crisp, dpi, (176, 52, 36), (28, 14, 12))
    for im in (line, rel):
        im.thumbnail((520, 360))
    rows.append((n, line, rel))
W = 1080
H = sum(max(a.size[1], b.size[1]) + 40 for _, a, b in rows)
sheet = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(sheet)
y = 0
for n, a, b in rows:
    d.text((10, y + 6), n, fill=(30, 30, 30), font=font)
    sheet.paste(a, (10, y + 36))
    sheet.paste(b, (550, y + 36))
    y += max(a.size[1], b.size[1]) + 40
sheet.save(out)
print(out, sheet.size)
