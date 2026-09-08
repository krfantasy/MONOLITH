# Exec this file in Glyphs' Macro Panel (Window > Macro Panel, ⌥⌘M, then Run)
# to rebuild <repo>/MONOLITH.glyphs from src/monolith/design.py — including
# the SPAC masters and the kern feature — and export every binary into
# <repo>/fonts/. The Macro Panel has no __file__, so the one line to adjust
# is below.
__file__ = "/Users/krfantasy/Developer/bold/.worktrees/spac-axis/scripts/macro_bootstrap.py"
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import importlib  # noqa: E402
import monolith.build as build  # noqa: E402

importlib.reload(build)  # the Macro Panel caches modules between runs

f = build.run()

static = next(i for i in f.instances if i.name == "ExtraBold")
static.generate("TTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.ttf"))
static.generate("OTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.otf"))
print("statics exported")

# The variable font cannot be scripted in Glyphs 3.5: instance.generate(
# Format=VARIABLE) returns bogus "." paths and writes nothing. Export by
# hand: File > Export (Cmd+E) > Variable Fonts tab (.ttf) > Next > this
# repo's fonts/ folder. Glyphs names the file MONOLITHVF.ttf — then:
#   mv fonts/MONOLITHVF.ttf fonts/MONOLITH-Variable.ttf
print("NOW EXPORT THE VF BY HAND: File > Export > Variable Fonts")
print("into %s, then rename MONOLITHVF.ttf -> MONOLITH-Variable.ttf" % (REPO / "fonts"))
print("REGEN + EXPORT DONE")
