# Exec this file in Glyphs' Macro Panel (Window > Macro Panel, then Run)
# to rebuild <repo>/MONOLITH.glyphs from src/monolith/design.py.
# The ONLY machine-specific line is the path below.
import sys
sys.path.insert(0, "/Users/krfantasy/Developer/bold/src")

from monolith import build

build.run()

# Optional, after build.run(): (re)export the binary fonts.
# f = Glyphs.font
# f.instances[0].generate("TTF", "/Users/krfantasy/Developer/bold/fonts/MONOLITH-ExtraBold.ttf")
# f.instances[0].generate("OTF", "/Users/krfantasy/Developer/bold/fonts/MONOLITH-ExtraBold.otf")
