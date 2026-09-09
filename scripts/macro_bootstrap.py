# Exec this file in Glyphs' Scripting Window (Window > Scripting Window —
# in Glyphs 3: Window > Macro Panel, ⌥⌘M — then Run) to rebuild
# <repo>/MONOLITH.glyphs from src/monolith/design.py — SPAC masters,
# native per-master kerning (Window > Kerning shows the 742 pairs) — and
# export the binaries into <repo>/fonts/. The window has no __file__, so
# the checkout is derived from the frontmost document: open
# <repo>/MONOLITH.glyphs before pressing Run. Close other fonts first —
# the frontmost document decides which checkout gets rebuilt.
import os
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

# --- variable font -----------------------------------------------------------
# Glyphs 4 exports variable fonts through a VARIABLE-TYPE instance via the
# public generate() — the same path File > Export uses (it picks the
# VariableTT outline format itself). Hand-wiring GSExportInstanceOperation
# with a static instance + VariableTT format — the 3.5 workaround — crashes
# 4.x natively. The exporter names the file after the instance, hence the
# rename fallback.
from GlyphsApp import GSInstance, INSTANCETYPEVARIABLE  # noqa: E402

vf_dir = REPO / "fonts"
target = vf_dir / "MONOLITH-Variable-raw.ttf"
var_inst = next((i for i in f.instances if i.type == INSTANCETYPEVARIABLE), None)
if var_inst is None:
    var_inst = GSInstance()
    # the Python property is getter-only in 4.x; the ObjC setter works
    var_inst.setType_(INSTANCETYPEVARIABLE)
    var_inst.name = "Variable"
    f.instances.append(var_inst)
error = var_inst.generate("TTF", str(target))
if error:
    raise SystemExit("VF export failed: %s" % error)
if not target.exists():
    produced = vf_dir / ("%s.ttf" % var_inst.name)
    if not produced.exists():
        raise SystemExit("VF export produced no file next to %s" % target)
    os.rename(produced, target)
print("raw VF exported -> fonts/MONOLITH-Variable-raw.ttf")

# --- statics -----------------------------------------------------------------
# ExtraBold carries the "Remove Features: kern" custom parameter, so the
# static cut ships unkerned (pure block look) even though the doc has
# native kerning.
static = next(i for i in f.instances if i.name == "ExtraBold")
static.generate("TTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.ttf"))
static.generate("OTF", str(REPO / "fonts" / "MONOLITH-ExtraBold.otf"))
print("statics exported (unkerned)")

# --- final step (outside Glyphs) --------------------------------------------
print("NOW RUN: uv run python -m monolith.kern_axis")
print("  (adds the KERN 0-100 axis to the VF -> fonts/MONOLITH-Variable.ttf)")
print("REGEN + EXPORT DONE")
