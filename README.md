# Carving Library

A library of leather-carving elements (flowers, leaves, scrolls, fills, frames) and short **recipes**
that place them on **any product**: belts, straps, wallets, card holders, sheaths, notebook covers,
coasters, key fobs, or any outline you give it. Every recipe builds an actual-size tracing PDF, a
simulated carved-and-finished preview, and a carvability check.

- **Browse the elements and products:** [`catalog/catalog.pdf`](catalog/catalog.pdf) (last page = products), single-element SVGs in [`catalog/svg/`](catalog/svg/)
- **Browse the designs:** [`designs/`](designs/), one folder per recipe

## What's in a design folder

| File | What it is |
|---|---|
| `tracing.pdf` | Actual-size pattern on US Letter. **Print at 100%** and check the 1" square. Narrow pieces are split into 10" strips; tall pieces (sheaths, notebook covers) are tiled in both directions with rulers on two edges, plus an overview page. |
| `relief.png` | Simulated carving in three finishes, cut to the product's shape. A mock-up, not a photo. |
| `check.png` / `check.txt` | Carvability check. **Red**: ground gaps too tight for any backgrounder. **Orange**: needs a small backgrounder. **Blue**: raised parts thin enough to be fragile. |
| `design.svg` | The full design as vector art (laser, plotter, or edits). |

## Build

Needs Python 3 and `rsvg-convert` (librsvg).

```
pip install -r requirements.txt
python -m carvelib build recipes/card_holder_camellia.yaml     # one design
python -m carvelib build recipes/*.yaml                        # all designs
python -m carvelib catalog                                     # element + product catalog
python -m carvelib list                                        # elements and size ranges
python tools/render_recipe.py recipes/x.yaml                   # quick look while designing
python tools/preview_element.py camellia [size]                # one element, large, with relief
python tools/knife_mark_stamp.py                               # regenerate the texture stamp STL
```

## Products

| `type` | Measurements (inches) | Built-in panels | Notes |
|---|---|---|---|
| `belt` | `width`, `length`, `tip: round\|point\|square`, `buckle_slot`, `keeper`, `holes: {first, count, spacing}` | — (use a strap panel) | crease along the edges |
| `strap` | `width`, `length`, `ends: round\|point\|square`, `holes`, `rivets: [x, ...]` | `main` | guitar strap, collar, watch band, bag strap |
| `blank` | `width`, `length` | `main` | test strips |
| `panel` | `width`, `height`, `corner`, `margin`, `stitch: none\|all\|no_top` | `main` | any flat rectangle |
| `card_holder` | `width`, `height`, `corner`, `margin` | `main` | stitched sides and bottom |
| `bifold_wallet` | `width`, `height` (laid flat) | `back`, `front`, `whole` | centre fold |
| `notebook_cover` | `width`, `height`, `spine` | `back`, `front` | spine folds |
| `coaster` | `width` (= diameter), `margin`, `stitch` | `main` (circle) | |
| `key_fob` | `width`, `height` (laid flat) | `face`, `back` | centre fold, rivet marks |
| `pancake_sheath` | `width`, `height`, `margin`, `slots` | `main` | belt slots, stitch line open at the top |
| `custom` | `points: [[x, y], ...]` from the top-left, `margin`, `stitch`, `smooth` | `main` | any outline |

## Recipes

A recipe is a short YAML file in `recipes/`. All measurements are in **inches**. `x` runs from the
product's left edge; `y` is measured from the product's horizontal **centreline**, positive **down**.

```yaml
name: Card holder - camellia
product: {type: card_holder, width: 4.25, height: 3.0}
panels:                          # carving areas (built-in names, or shapes - see below)
  main: {ground: knife_marks, border_style: double}
finishes: [red_black, oxblood_black, natural_antique]
layout:                          # groups of elements; coordinates inside a group are local to it
  - type: single
    origin: [2.125, 0]
    place:
      - {element: camellia, at: [0, 0.04], size: 1.30}
  - type: mirror                 # drawn once, copied left-right about the panel centre
    axis: x
    place:
      - {element: karakusa_tendril, at: [0.55, -0.06], rotate: -22, size: 0.88}
```

**Panels.** Under `panels:`, a key that names a built-in panel uses it (`front: {ground: matte}`).
Otherwise give a shape:
`{shape: rect, x: [x0, x1], y: [y0, y1], radius}`, `{shape: circle, center: [x, y], r}`,
`{shape: oval, center, rx, ry}`, `{shape: inset, margin}` (product outline shrunk), or
`{shape: strap, start, length, border, ends: square|pointed|round|ogee}` for belts and straps.
Each panel takes `ground: knife_marks|matte|none` and `border_style: line|double|beaded|rope|none`.

**Layouts** (each group takes `panel:`, `place:`, and optionally `stems:` and `connect:`):

| `type` | What it does | Local origin |
|---|---|---|
| `single` | Places elements once | `origin` (default: product left edge, centreline) |
| `repeat` | Repeats along x: `start`, `length`, `count`; stems join into one across repeats | each repeat's start, on the centreline |
| `corners` | Drawn for the top-left corner, mirrored into `corners: [tl, tr, bl, br]` | the panel's corner, x and y pointing inward |
| `mirror` | Copies across `axis: x`, `y` or `xy` | the panel centre (or `center`) |
| `radial` | Rotates `count` copies about the centre; `mirror: true` adds reflections | the panel centre; +x points outward |

Placement options: `rotate` (degrees), `flip_x`, `flip_y`, `size` (inches, checked against the
element's carvable range), `layer`, `id` (for stalks), and inside repeats `every`/`offset`/`skip_first`
or `only: [indexes]`. `connect:` draws curved stalks into an element's anchor
(`{from: [x, y], to: bud.base, start_dir: 90, width: 0.06}`). `extras:` places elements in product
coordinates outside any panel. `repeat_from: other.yaml` reuses another recipe's repeat. Older
belt recipes using `panel:` + `repeat:` still work.

- Finishes for `relief.png`: `red_black`, `oxblood_black`, `natural_antique`, `saddle_tan`, `medium_brown`, `dark_brown`.
- `check:` overrides tool sizes for the carvability check, e.g. `{min_gap: 0.04, stamp_reach: 0.22, min_feature: 0.05}`.

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
| `lotus` | Lotus (renge), side view: fan of pointed petals on a crescent receptacle |
| `momiji` | Japanese maple leaf: seven toothed lobes, veins, stem |
| `ginkgo` | Ginkgo fan leaf with a centre notch and radiating veins |
| `bamboo` | Jointed bamboo stalk with two sprays of narrow leaves |
| `nami_crest` | Wave crest: a swelling band that curls over, with foam claws |
| `tombo` | Dragonfly seen from above (the samurai "victory insect") |
| `koi` | Koi from above: curving body, scale cuts, fins, split tail |
| `tsuru` | Crane in flight: feathered wings, long neck, crown spot, trailing legs |
| `cho` | Butterfly: rounded forewings, tailed hindwings, eye spots, curled antennae |
| `usagi` | Sitting rabbit (moon rabbit), ears laid back |
| `mitsudomoe` | Three swirling commas, a classic crest (`ring: true` adds a ring) |
| `sensu` | Open folding fan with pleats, slats and pivot |

**Western / Sheridan**

| Element | What it is |
|---|---|
| `sheridan_rose` | Wild rose: rolled-edge outer petals, cupped inner petals, crown and seeded centre |
| `sheridan_leaf` | Curved leaf, smooth back, four swept lobes, tip that flips up |
| `rose_bud` | Pointed bud sitting in a calyx |
| `oak_leaf` | Lobed oak leaf with midrib and veins |
| `acorn` | Acorn with a crosshatched cap and stem |
| `daisy` | Two rings of narrow petals around a large seeded centre |
| `feather` | Curved quill, split vane, fine barb cuts |
| `horse_head` | Horse head and neck, side view, with flowing mane |
| `longhorn_skull` | Texas longhorn skull with sweeping horns |
| `lone_star` | Beveled five-point star (`ring: true` for a concho-style ring) |
| `horseshoe` | Horseshoe opening up, with groove, nail holes and calks |

**Fills and frames**

| Element | What it is |
|---|---|
| `seigaiha` | Wave-scale panel |
| `asanoha` | Hemp-leaf star panel |
| `basketweave` | Basket-weave layout panel (stamp with a basket stamp) |
| `kikko` | Tortoise-shell hexagons with inner hexagons |
| `shippo` | Overlapping circles (seven treasures) |
| `maru_ring` | Round crest frame (kamon ring); put a motif or a radial set of leaves inside |
| `hishi_frame` | Diamond frame with a raised double-line border |
| `mokko_cartouche` | Four-lobed name frame for initials or a name (option `text` shows a grey placement guide) |

To add an element: copy a class from `carvelib/elements/`, give it a new `name`, draw it around
the origin at `size`, declare its size range, anchors and layer, and run `python -m carvelib catalog`.

## Notes

- "Kamakura-bori inspired", never "Kamakura-bori". That name is reserved for urushi lacquerware
  made in Kamakura.
- Knife-mark texture stamp: `stamps/knife_mark_texture_stamp.stl` (10 × 10 mm face, four gouge
  strokes, 60 mm shaft).
