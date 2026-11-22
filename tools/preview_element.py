"""Render one element large for design review:  python tools/preview_element.py camellia [size] [out.png]
Shows the line drawing (with anchors) next to a relief preview."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from PIL import Image, ImageFilter
from carvelib.element import REGISTRY
from carvelib import elements  # noqa: F401
from carvelib.outputs.catalog import element_svg, _opts
from carvelib.outputs.common import rasterize
from carvelib.outputs.relief import render

name = sys.argv[1]
el = REGISTRY[name]
size = float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else el.size_default
out = sys.argv[3] if len(sys.argv) > 3 else f"/tmp/{name}.png"
dpi = int(700 / max(size, 0.4))
line = Image.open(rasterize(element_svg(el, size), dpi)).convert("RGB")
# relief: element on a dark ground
svg = element_svg(el, size, anchors=False).replace('fill="#fff"/>', 'fill="#1a1a1a"/>', 1)
g = Image.open(rasterize(svg, dpi)).convert("L")
soft = np.asarray(g.filter(ImageFilter.GaussianBlur(dpi * 0.012)), float) / 255
crisp = np.asarray(g.filter(ImageFilter.GaussianBlur(dpi * 0.003)), float) / 255
rel = render(0.75 * soft + 0.25 * crisp, dpi, (176, 52, 36), (28, 14, 12))
w, h = line.size
sheet = Image.new("RGB", (w * 2 + 10, h), "white")
sheet.paste(line, (0, 0))
sheet.paste(rel, (w + 10, 0))
sheet.save(out)
print(out, sheet.size)
