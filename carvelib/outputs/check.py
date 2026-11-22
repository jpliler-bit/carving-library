"""Carvability check.

Looks at the open ground and the raised motifs at 200 dpi and flags:
  RED     ground gaps too narrow for any backgrounder (< min_gap): redesign, or just bevel them
  ORANGE  ground the knife-mark stamp can't reach (< stamp_reach): use a small backgrounder there
  BLUE    raised parts thinner than min_feature: fragile, hard to bevel cleanly
Tool sizes are in inches and can be changed per recipe under `check:`.
"""
import numpy as np
from PIL import Image
from scipy import ndimage
from ..geometry import BG, MARK, f
from .common import rasterize, uniquify

DEFAULTS = {"min_gap": 0.04, "stamp_reach": 0.22, "min_feature": 0.05}
DPI = 200


def _disk(r):
    r = max(1, int(round(r)))
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def run(d, out_png):
    cfg = {**DEFAULTS, **d.r.get("check", {})}
    body = uniquify(d.body(), "_c")
    # ground black, motifs white, every line white (lines are cuts, not ground or raised area)
    mask_body = body.replace(BG, "#000000").replace(MARK, "#000000")
    mask_body = mask_body.replace('stroke="#111"', 'stroke="#fff"').replace('fill="#111"', 'fill="#fff"')
    for c in ("#c0392b", "#777", "#555"):
        mask_body = mask_body.replace(f'stroke="{c}"', 'stroke="none"')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(d.Lp/100)}in" height="{f(d.W/100)}in" '
           f'viewBox="0 0 {f(d.Lp)} {f(d.W)}"><rect width="{f(d.Lp)}" height="{f(d.W)}" fill="#fff"/>{mask_body}</svg>')
    m = np.asarray(Image.open(rasterize(svg, DPI)).convert("L"), float)
    ground = m < 128
    # raised = white pixels inside the carved panel (not the plain strap outside it)
    panel = ndimage.binary_fill_holes(ndimage.binary_closing(ground, _disk(DPI * 0.08)))
    raised = (~ground) & panel

    px = lambda inches: inches * DPI
    tight = ground & ~ndimage.binary_opening(ground, _disk(px(cfg["min_gap"]) / 2))
    stamp_ok = ndimage.binary_opening(ground, _disk(px(cfg["stamp_reach"]) / 2))
    small_tool = ground & ~stamp_ok & ~tight
    thin = raised & ~ndimage.binary_opening(raised, _disk(px(cfg["min_feature"]) / 2))
    # ignore specks a pixel or two wide (anti-aliasing)
    tight = ndimage.binary_opening(tight, _disk(1))
    thin = ndimage.binary_opening(thin, _disk(1))

    # overlay on the line drawing
    line = np.asarray(Image.open(rasterize(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(d.Lp/100)}in" height="{f(d.W/100)}in" viewBox="0 0 {f(d.Lp)} {f(d.W)}">'
        f'<rect width="{f(d.Lp)}" height="{f(d.W)}" fill="#fff"/>{uniquify(body, "_o")}</svg>', DPI)).convert("RGB"), float)
    out = line * 0.55 + 255 * 0.45
    for mask, col in ((small_tool, (245, 160, 40)), (tight, (220, 30, 30)), (thin, (40, 110, 230))):
        out[mask] = out[mask] * 0.25 + np.array(col) * 0.75
    Image.fromarray(out.astype(np.uint8)).save(out_png)

    if ground.sum() == 0:
        return "Carvability check: no carved panel with open ground in this design (fills and stamped areas only).\n"
    g = ground.sum()
    tool = ("the knife-mark stamp" if d.r.get("panel", {}).get("ground", "knife_marks") == "knife_marks"
            else "a standard backgrounder")
    n_tight = ndimage.label(tight)[1]
    n_thin = ndimage.label(thin)[1]
    lines = [
        f"Carvability check (tools: min gap {cfg['min_gap']}\", stamp reach {cfg['stamp_reach']}\", min raised width {cfg['min_feature']}\")",
        f"  Ground reachable with {tool}: {100 * (ground & stamp_ok).sum() / g:.0f}%",
        f"  Ground needing a small backgrounder (orange): {100 * small_tool.sum() / g:.0f}%",
        f"  Gaps too tight for any backgrounder (red): {n_tight} spot(s), {100 * tight.sum() / g:.1f}% of ground",
        f"  Thin raised parts (blue): {n_thin} spot(s) - mostly scroll tails and petal tips; bevel these lightly",
    ]
    return "\n".join(lines) + "\n"
