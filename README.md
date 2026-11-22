# Carving Library

A library of leather-carving elements (flowers, leaves, scrolls, fills) and short **recipes** that
assemble them into finished patterns: belts, test pieces, and later wallets, sheaths and more.
Every recipe builds an actual-size tracing PDF, a simulated carved-and-finished preview, and a
carvability check.

- **Browse the elements:** [`catalog/catalog.pdf`](catalog/catalog.pdf), or the single-element SVGs in [`catalog/svg/`](catalog/svg/)
- **Browse the designs:** [`designs/`](designs/), one folder per recipe:
  Kamakura test section, Kamakura peony belt, camellia and cloud section, Sakura Ryūsui belt,
  Sheridan rose section, basket-weave name belt

## What's in a design folder

| File | What it is |
|---|---|
| `tracing.pdf` | Actual-size pattern on US Letter. **Print at 100%** and check the 1" square. Long designs are split into 10" segments that overlap by ½"; line up the ruler numbers. |
| `relief.png` | Simulated carving in three finishes: A red + black antique (hikuchi-nuri look), B oxblood + black, C natural + antique. A mock-up, not a photo. |
| `check.png` / `check.txt` | Carvability check. **Red**: ground gaps too tight for any backgrounder. **Orange**: ground the knife-mark stamp can't reach, so use a small backgrounder. **Blue**: raised parts thin enough to be fragile. |
| `design.svg` | The full design as vector art (laser, plotter, or edits). |

## Build

Needs Python 3 and `rsvg-convert` (librsvg).

```
pip install -r requirements.txt
python -m carvelib build recipes/kamakura_test_section.yaml   # one design
python -m carvelib build recipes/*.yaml                        # all designs
python -m carvelib catalog                                     # element catalog
python -m carvelib list                                        # elements and size ranges
python tools/knife_mark_stamp.py                               # regenerate the texture stamp STL
python tools/preview_element.py camellia [size]               # one element, large, with relief
```

## Recipes

A recipe is a short YAML file in `recipes/`. All measurements are in **inches**.
`x` runs from the left end of the product (the buckle end of a belt). `y` is measured from the
strap's centreline, positive **down**.

```yaml
name: Kamakura peony belt 1.5 x 36
product: {type: belt, width: 1.5, length: 36, tip: round,
          buckle_slot: 1.5, keeper: 2.5, holes: {first: 29, count: 5, spacing: 1.0}}
panel:   {start: 5.0, border: 0.16, ends: square, ground: knife_marks}   # ends: square|pointed|round|ogee; ground: knife_marks|matte|none
repeat:
  length: 4.6
  count: 5
  stems:                         # lines through the repeat; joined into one across repeats
    - {points: [[0, 0], [2.3, 0], [4.6, 0]], width: 0.125}          # style: ribbon for flowing water
  place:                         # elements; inside a repeat, x is from the repeat's start
    - {id: peony, element: peony_open, at: [2.30, -0.03], size: 1.30}
    - {element: botan_leaf, at: [1.46, -0.02], rotate: -52.4}
    - {element: kiku, at: [1.23, 0], every: 2, offset: 1}             # only in repeats 2, 4, ...
  connect:                       # curved stalks that flow into an element's anchor
    - {from: [1.50, 0.01], to: bud_low.base, start_dir: 90, width: 0.06}
extras:                          # placed once, outside the repeat
  - {element: seigaiha, at: [3.6, 0], size: 1.2}
cuts: [1.71, 3.49]               # red cut lines (finish-test pieces)
finishes: [natural_antique, saddle_tan, medium_brown]   # relief preview finishes
```

- `repeat_from: other.yaml` borrows another recipe's repeat. The 36" Kamakura belt uses the
  test section's repeat, so improving the test section updates the belt too.
- Placement options: `rotate` (degrees), `flip_x`, `flip_y`, `size` (inches, checked against the
  element's carvable range), `layer` (stacking order), `every`/`offset`/`skip_first`.
- Finishes for `relief.png`: `red_black`, `oxblood_black`, `natural_antique`, `saddle_tan`, `medium_brown`, `dark_brown`.
- `check:` overrides tool sizes for the carvability check, for example `{min_gap: 0.04, stamp_reach: 0.22, min_feature: 0.05}`.

## Elements

Each element lives in `carvelib/elements/` and follows one format (`carvelib/element.py`):

- **Draws at a real size, never stretched.** Line weights and seeder dots stay carvable. A size
  outside the element's range is refused.
- **Anchors**: named connection points with a direction, so stems flow into the element
  instead of butting against it.
- **Layer**: default stacking order (pommels < stalks < buds < stem < leaves < sheath < flower).
- **Flow points**: where the knife-mark ground ripples around the element.

**Japanese / Kamakura-bori inspired**

| Element | What it is |
|---|---|
| `peony_open` | Open peony, three-quarter view, cupped, seeded centre (focal flower) |
| `camellia` | Camellia (tsubaki): round petals, cupped inner ring, stamen tube; simpler to carve than the peony |
| `peony_bud` | Closed peony bud with sepals |
| `botan_leaf` | Three-lobed peony leaf |
| `guri_pommel` | Guri "sword-pommel" heart: paired scroll arms curling into spirals |
| `guri_scroll` | One guri arm (also works as a Western C-scroll) |
| `sheath` | Pointed bract where a stem branches |
| `cloud_scroll` | Kamakura-bori cloud: curled lobes with spiral cuts and a streaming tail |
| `karakusa_tendril` | Thin vine with two small leaves ending in a curl (filler) |
| `wave_curl` | Free water swirl |
| `sakura`, `sakura_petal` | Cherry blossom and falling petal |
| `ume` | Plum blossom: five round petals, long stamens; carves well small |
| `kiku` | Chrysanthemum |

**Western / Sheridan**

| Element | What it is |
|---|---|
| `sheridan_rose` | Wild rose: rolled-edge outer petals, cupped inner petals, crown and seeded centre |
| `sheridan_leaf` | Curved leaf, smooth back, four swept lobes, tip that flips up |
| `rose_bud` | Pointed bud sitting in a calyx |

**Fills and frames**

| Element | What it is |
|---|---|
| `seigaiha` | Wave-scale panel |
| `asanoha` | Hemp-leaf star panel |
| `basketweave` | Basket-weave layout panel (stamp with a basket stamp) |
| `mokko_cartouche` | Four-lobed name frame for initials or a name (option `text` shows a grey placement guide) |

To add an element: copy a class from `carvelib/elements/`, give it a new `name`, draw it around
the origin at `size`, declare its size range, anchors and layer, and run `python -m carvelib catalog`.

## Notes

- "Kamakura-bori inspired", never "Kamakura-bori". That name is reserved for urushi lacquerware
  made in Kamakura.
- Knife-mark texture stamp: `stamps/knife_mark_texture_stamp.stl` (10 × 10 mm face, four gouge
  strokes, 60 mm shaft).
