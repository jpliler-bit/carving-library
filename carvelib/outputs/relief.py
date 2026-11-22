"""Simulated carved-and-finished preview. Raised motifs get rounded (Gotō-style) edges, cut lines
become grooves, the ground sits low with gouge texture; dye colours the high spots and antique
pools in the recesses. A mock-up to judge a design by, not a photo."""
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from ..geometry import BG, MARK, f
from .common import rasterize, uniquify

FINISHES = {
    "A  Red + black antique (hikuchi-nuri look)": ((176, 52, 36), (28, 14, 12)),
    "B  Oxblood + black antique": ((98, 30, 30), (22, 12, 10)),
    "C  Natural + dark antique": ((214, 176, 132), (70, 44, 26)),
}


def height_map(d, dpi):
    body = uniquify(d.body(), "_h").replace(BG, "#1a1a1a").replace(MARK, "#3a3a3a")
    for c in ("#c0392b", "#777", "#555"):     # reference marks don't exist in leather
        body = body.replace(f'stroke="{c}"', 'stroke="none"')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(d.Lp/100)}in" height="{f(d.W/100)}in" '
           f'viewBox="0 0 {f(d.Lp)} {f(d.W)}"><rect width="{f(d.Lp)}" height="{f(d.W)}" fill="#fff"/>{body}</svg>')
    g = Image.open(rasterize(svg, dpi)).convert("L")
    soft = np.asarray(g.filter(ImageFilter.GaussianBlur(dpi * 0.012)), float) / 255
    crisp = np.asarray(g.filter(ImageFilter.GaussianBlur(dpi * 0.003)), float) / 255
    return 0.75 * soft + 0.25 * crisp


def render(h, dpi, high, low):
    gy, gx = np.gradient(h)
    shade = np.clip(0.80 + 9.0 * (gx * -0.6 + gy * -0.8), 0.35, 1.25)
    cav = np.asarray(Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(dpi * 0.02)), float) / 255
    recess = np.clip((cav - h) * 4 + (1 - h) * 0.9, 0, 1)
    hi, lo = np.array(high, float) / 255, np.array(low, float) / 255
    col = (hi * (1 - recess[..., None]) + lo * recess[..., None]) * shade[..., None]
    return Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))


def preview(d, out_png, dpi=None, finishes=FINISHES):
    dpi = dpi or (240 if d.Lp <= 1200 else 90)
    h = height_map(d, dpi)
    imgs = [(name, render(h, dpi, *cols)) for name, cols in finishes.items()]
    pad, lab = 24, 40
    w, ht = imgs[0][1].size
    sheet = Image.new("RGB", (w + 2 * pad, len(imgs) * (ht + lab) + pad), (247, 244, 238))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for i, (name, im) in enumerate(imgs):
        y = pad + i * (ht + lab)
        dr.text((pad, y), name, fill=(30, 30, 30), font=font)
        sheet.paste(im, (pad, y + lab - 6))
    sheet.save(out_png)
    return out_png
