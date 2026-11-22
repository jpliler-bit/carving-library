import re
import subprocess
import tempfile
import os


def uniquify(markup, sfx):
    """Give every id in a chunk of SVG markup a suffix so the chunk can be used more than once per file."""
    for i in set(re.findall(r'id="([^"]+)"', markup)):
        markup = markup.replace(f'id="{i}"', f'id="{i}{sfx}"').replace(f"url(#{i})", f"url(#{i}{sfx})")
    return markup


def rasterize(svg_text, dpi, out_png=None):
    fd, svg_path = tempfile.mkstemp(suffix=".svg")
    with os.fdopen(fd, "w") as fh:
        fh.write(svg_text)
    png = out_png or svg_path[:-4] + ".png"
    subprocess.run(["rsvg-convert", "-d", str(dpi), "-p", str(dpi), svg_path, "-o", png], check=True)
    os.remove(svg_path)
    return png


def to_pdf(svg_pages, out_pdf):
    paths = []
    for k, s in enumerate(svg_pages):
        fd, p = tempfile.mkstemp(suffix=f"_{k}.svg")
        with os.fdopen(fd, "w") as fh:
            fh.write(s)
        paths.append(p)
    subprocess.run(["rsvg-convert", "-f", "pdf", *paths, "-o", out_pdf], check=True)
    for p in paths:
        os.remove(p)
