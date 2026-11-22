"""Quick look at a recipe while designing:  python tools/render_recipe.py recipes/x.yaml [dpi] [out.png]"""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from carvelib.assemble import load
d = load(sys.argv[1])
dpi = sys.argv[2] if len(sys.argv) > 2 else "150"
out = sys.argv[3] if len(sys.argv) > 3 else "/tmp/recipe.png"
open("/tmp/_r.svg", "w").write(d.svg())
subprocess.run(["rsvg-convert", "-d", dpi, "-p", dpi, "/tmp/_r.svg", "-o", out], check=True)
print(out)
