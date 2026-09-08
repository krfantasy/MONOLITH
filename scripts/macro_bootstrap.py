# Exec this file in Glyphs' Macro Panel (Window > Macro Panel, ⌥⌘M, then Run)
# to rebuild <repo>/MONOLITH.glyphs from src/monolith/design.py — SPAC masters,
# native per-master kerning (Window > Kerning shows the 742 pairs) — and
# export the binaries into <repo>/fonts/. The Macro Panel has no __file__,
# so the checkout is derived from the frontmost document: open
# <repo>/MONOLITH.glyphs before pressing Run.
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
# The scripting VF export runs the same ObjC operation as File > Export >
# Variable Fonts: GSExportInstanceOperation + GSOutlineFormatVariableTT.
# (.generate(Format=VARIABLE) is broken in 3.5, and no .export method is
# exposed to Python in this build.) Quirk: the operation names the output
# after the INSTANCE, so it lands at fonts/ExtraBold.ttf — hence the export
# happens BEFORE the statics and is renamed immediately.
import os  # noqa: E402

from Foundation import NSClassFromString, NSURL  # noqa: E402
from GlyphsApp import GlyphsApp  # noqa: E402

vf_dir = REPO / "fonts"
inst = next(i for i in f.instances if i.name == "ExtraBold")
exporter = (
    NSClassFromString("GSExportInstanceOperation")
    .alloc()
    .initWithFont_instance_outlineFormat_containers_(
        f, inst, GlyphsApp.GSOutlineFormatVariableTT, [GlyphsApp.PLAIN]
    )
)
exporter.setInstallFontURL_(NSURL.fileURLWithPath_(str(vf_dir / "MONOLITH-Variable.ttf")))
exporter.setAutohint_(False)
exporter.setRemoveOverlap_(False)
exporter.setUseSubroutines_(False)
exporter.setUseProductionNames_(False)
delegate = GlyphsApp._ExporterDelegate_.new()
exporter.setDelegate_(delegate)
exporter.main()
if not (vf_dir / "ExtraBold.ttf").exists():
    raise SystemExit("VF export failed (delegate result: %s)" % delegate.result)
os.rename(vf_dir / "ExtraBold.ttf", vf_dir / "MONOLITH-Variable-raw.ttf")
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
