# Exec this file in Glyphs' Scripting Window (Window > Scripting Window —
# in Glyphs 3: Window > Macro Panel, ⌥⌘M — then Run) to rebuild
# <repo>/MONOLITH.glyphs from src/monolith/design.py — SPAC masters,
# native per-master kerning (Window > Kerning shows the 1101 pairs) — and
# export the static binaries into <repo>/fonts/. The window has no
# __file__, so the checkout is derived from the frontmost document: open
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
print("checkout: %s" % REPO)

# The Macro Panel caches imported modules between Runs (possibly from
# another checkout): reload(build) alone rebinds `from monolith.design
# import ...` against the STALE cached modules, mixing new build.py with
# old design/kerning data. Purge the package so this Run imports fresh.
for _mod in [m for m in sys.modules if m == "monolith" or m.startswith("monolith.")]:
    del sys.modules[_mod]

import monolith.build as build  # noqa: E402

f = build.run()

# --- statics -----------------------------------------------------------------
# ExtraBold carries the "Remove Features: kern" custom parameter, so the
# static cut ships unkerned (pure block look) even though the doc has
# native kerning.
static = next(i for i in f.instances if i.name == "ExtraBold")
static.generate("TTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.ttf"))
static.generate("OTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.otf"))
print("statics exported (unkerned)")

# --- final steps (outside Glyphs) --------------------------------------------
# The variable font is assembled outside Glyphs: Glyphs 4.1's VF export
# rejects this doc ("Invalid axis range for axis: Spacing", no file — even
# on a fresh document and app relaunch), and SPAC is metric-only, so
# monolith.variable assembles the base VF from the static with fontTools
# varLib and monolith.kern_axis finishes it (KERN axis + HVAR + Tight).
print("NOW RUN, in the repo:")
print("  uv run python -m monolith.variable   # base VF from the static (varLib)")
print("  uv run python -m monolith.kern_axis  # KERN axis + HVAR -> MONOLITH-Variable.ttf")
print("REGEN + EXPORT DONE")
