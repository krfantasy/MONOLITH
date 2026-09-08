# Exec this file in Glyphs' Macro Panel (Window > Macro Panel, ⌥⌘M, then Run)
# to rebuild <repo>/MONOLITH.glyphs from src/monolith/design.py — including
# the pair kerning — and re-export the binary fonts into <repo>/fonts/.
# The Macro Panel has no __file__, so the one line to adjust is below.
__file__ = "/Users/krfantasy/Developer/bold/.worktrees/spac-axis/scripts/macro_bootstrap.py"
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import importlib  # noqa: E402
import monolith.build as build  # noqa: E402
importlib.reload(build)  # the Macro Panel caches modules between runs

f = build.run()
f.instances[0].generate("TTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.ttf"))
f.instances[0].generate("OTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.otf"))
print("REGEN + EXPORT DONE")
