"""Rebuild designs/_overview.png: finish A of every design's relief preview on one sheet."""
import glob, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from PIL import Image, ImageDraw, ImageFont
from carvelib.assemble import load
from carvelib.__main__ import slug

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
tiles = []
for rp in sorted(glob.glob("recipes/*.yaml")):
    d = load(rp)
    n = slug(d.name)
    im = Image.open(f"designs/{n}/relief.png")
    w, h = im.size
    im = im.crop((0, 0, w // 3 + 12, h)) if d.W > d.Lp * 0.8 else im.crop((0, 0, w, h // 3 + 8))
    im.thumbnail((370, 260))
    tiles.append((d.name, im))
W, x, y, rowh = 1180, 10, 10, 0
sheet = Image.new("RGB", (W, 5000), (247, 244, 238))
dr = ImageDraw.Draw(sheet)
for name, im in tiles:
    if x + im.size[0] > W:
        x, y, rowh = 10, y + rowh + 34, 0
    dr.text((x, y), name[:44], fill=(40, 40, 40), font=font)
    sheet.paste(im, (x, y + 22))
    x += im.size[0] + 18
    rowh = max(rowh, im.size[1])
sheet.crop((0, 0, W, y + rowh + 34)).save("designs/_overview.png")
print("designs/_overview.png")
