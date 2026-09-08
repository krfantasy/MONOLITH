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

try:
    from GlyphsApp import VARIABLE
except ImportError:
    VARIABLE = "variable"
try:
    kwargs: dict[str, object] = {"Fontpath": str(REPO / "fonts" / "MONOLITH-Variable.ttf")}
    try:
        from GlyphsApp import PLAIN

        kwargs["Containers"] = [PLAIN]
    except ImportError:
        pass
    static.generate(Format=VARIABLE, **kwargs)
    print("VARIABLE FONT EXPORTED")
except Exception as e:
    print("VF export via API failed: %s" % e)
    print("export manually: File > Export (Cmd+E) > Variable, save as")
    print("  %s" % (REPO / "fonts" / "MONOLITH-Variable.ttf"))
print("REGEN + EXPORT DONE")
