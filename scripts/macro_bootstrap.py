# Exec this file in Glyphs' Scripting Window (Window > Scripting Window —
# in Glyphs 3: Window > Macro Panel, ⌥⌘M — then Run) to rebuild
# <repo>/MONOLITH.glyphs from src/monolith/design.py — SPAC masters,
# native per-master kerning (Window > Kerning shows the 742 pairs) — and
# export the binaries into <repo>/fonts/. The window has no __file__, so
# the checkout is derived from the frontmost document: open
# <repo>/MONOLITH.glyphs before pressing Run. Close other fonts first —
# the frontmost document decides which checkout gets rebuilt.
import sys
from pathlib import Path

_doc_path = ""
try:
    _raw = Glyphs.font.filepath  # noqa: F821 — Macro Panel global
    _doc_path = str(_raw() if callable(_raw) else _raw or "")
except (NameError, AttributeError):
    pass
if not _doc_path:
    raise SystemExit(
        "Open <repo>/MONOLITH.glyphs in Glyphs (frontmost tab), then Run:"
        " the checkout is derived from that document's path."
    )

REPO = Path(_doc_path).resolve().parent
sys.path.insert(0, str(REPO / "src"))

import importlib  # noqa: E402

import monolith.build as build  # noqa: E402

importlib.reload(build)  # the Macro Panel caches modules between runs

f = build.run()

# --- statics -----------------------------------------------------------------
# ExtraBold carries the "Remove Features: kern" custom parameter, so the
# static cut ships unkerned (pure block look) even though the doc has
# native kerning.
static = next(i for i in f.instances if i.name == "ExtraBold")
static.generate("TTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.ttf"))
static.generate("OTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.otf"))
print("statics exported (unkerned)")

# --- final step (outside Glyphs) --------------------------------------------
# Do NOT export a variable font here: Glyphs 4.1's scripted VF export
# crashes the app (both the hand-wired GSExportInstanceOperation and a
# VARIABLE-type instance's generate()). The variable font is assembled
# outside with fontTools — SPAC is metric-only, so the loose master is
# just the static with +130 advances.
print("NOW RUN: uv run python -m monolith.kern_axis")
print("  (builds the variable font from the static with fontTools and adds")
print("   the KERN 0-100 axis + HVAR -> fonts/MONOLITH-Variable.ttf)")
print("REGEN + EXPORT DONE")
