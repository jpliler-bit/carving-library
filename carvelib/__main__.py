"""Command line:

    python -m carvelib build recipes/kamakura_test_section.yaml   -> designs/<name>/ (svg, pdf, previews, check)
    python -m carvelib build recipes/*.yaml                        -> every design
    python -m carvelib catalog                                     -> catalog/ (catalog.pdf + one SVG per element)
    python -m carvelib list                                        -> element names and size ranges
"""
import os
import re
import sys

from .assemble import load
from .element import REGISTRY


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = argv[0]
    if cmd == "list":
        for name, el in sorted(REGISTRY.items()):
            print(f"{name:14} {el.category:8} size {el.size_min}-{el.size_max}\" ({el.size_note})")
        return
    if cmd == "build":
        from .outputs import tracing, relief, check
        for rp in argv[1:]:
            d = load(rp)
            out = os.path.join("designs", slug(d.name))
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, "design.svg"), "w") as fh:
                fh.write(d.svg())
            tracing.pdf(d, os.path.join(out, "tracing.pdf"))
            relief.preview(d, os.path.join(out, "relief.png"))
            report = check.run(d, os.path.join(out, "check.png"))
            with open(os.path.join(out, "check.txt"), "w") as fh:
                fh.write(report)
            print(f"{d.name}: wrote {out}/\n{report}")
        return
    if cmd == "catalog":
        from .outputs import catalog
        catalog.build("catalog")
        return
    print(f"unknown command {cmd!r}")
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
