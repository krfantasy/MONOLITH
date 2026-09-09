"""SPAC-axis assembly, constants, and read-side helpers for the variable font.

The base VF is assembled downstream of Glyphs with fontTools varLib:
SPAC is metric-only, so the loose master is simply the exported ExtraBold
static with +SPAC_MAX on every advance — outlines never vary and the axis
lives in fvar + HVAR. (Glyphs 4.1's variable-font export rejects this doc
with "Invalid axis range" and writes nothing — reproducible on a fresh
document and app relaunch, 2026-09-09 — so the exporter is not on the
pipeline's critical path.) monolith.kern_axis then finishes the base font:
KERN axis (0-100, default 0 = kerning off) as a GPOS VariationStore, the
unioned outlines + rebuilt gvar, a measured HVAR, and the Tight instance
name. The statics ship unkerned via the ExtraBold instance's "Remove
Features: kern" parameter. This module also reads the exported fonts, for
specimens and tests.
"""

import tempfile
from pathlib import Path

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont

from monolith.design import SPACED_LSB, TIGHT_OVERLAP

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VARIABLE_FONT = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"
RAW_VARIABLE_FONT = REPO_ROOT / "fonts" / "MONOLITH-Variable-raw.ttf"
STATIC_TTF = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"

AXIS_TAG = "SPAC"
AXIS_NAME = "Spacing"
SPAC_MIN = 0
SPAC_DEFAULT = 0
TOUCHING = TIGHT_OVERLAP
SPAC_MAX = 2 * SPACED_LSB + TIGHT_OVERLAP
INSTANCES: tuple[tuple[int, str], ...] = (
    (SPAC_DEFAULT, "Tight"),
    (TOUCHING, "Touching"),
    (SPAC_MAX, "Spaced"),
)

KERN_AXIS_TAG = "KERN"
KERN_MIN = 0
KERN_DEFAULT = 0  # kerning off unless a layout engine asks for it
KERN_MAX = 100
KERN_NAME = "Kern"  # single source for the KERN axis range + name;
# monolith.kern_axis imports these rather than redefining them.


def build_variable_font(tight_path: str | Path = STATIC_TTF) -> TTFont:
    """Assemble the SPAC variable font from the static TTF; returns it unsaved.

    The loose master is the same font with +SPAC_MAX on every advance, so
    the designspace varies metrics only. Locations are keyed by axis NAME
    (not tag) or varLib maps every source to the default and rejects the
    doc ("more than one base master"). varLib writes fvar + HVAR and a
    gvar whose real-point deltas are all zero.
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        loose = TTFont(str(tight_path))
        for gname in loose.getGlyphOrder():
            aw, lsb = loose["hmtx"][gname]
            loose["hmtx"][gname] = (aw + SPAC_MAX, lsb)
        loose_path = tmp / "MONOLITH-Loose.ttf"
        loose.save(loose_path)

        doc = DesignSpaceDocument()
        axis = AxisDescriptor()
        axis.tag, axis.name = AXIS_TAG, AXIS_NAME
        axis.minimum, axis.default, axis.maximum = SPAC_MIN, SPAC_DEFAULT, SPAC_MAX
        doc.addAxis(axis)
        for fname, style, v in (
            (str(tight_path), "Tight", SPAC_DEFAULT),
            (str(loose_path), "Loose", SPAC_MAX),
        ):
            src = SourceDescriptor()
            src.filename, src.name = fname, style
            src.familyName, src.styleName = "MONOLITH", style
            src.location = {AXIS_NAME: v}
            doc.addSource(src)
        for v, style in INSTANCES:
            inst = InstanceDescriptor()
            inst.familyName, inst.styleName = "MONOLITH", style
            inst.location = {AXIS_NAME: v}
            doc.addInstance(inst)
        ds_path = tmp / "MONOLITH.designspace"
        doc.path = str(ds_path)
        doc.updatePaths()
        doc.write(ds_path)

        vf, _model, _masters = varlib_build(ds_path)
    return vf


def instance_at_spac(font_path: str | Path, spac: int) -> TTFont:
    """Static font pinned at the given SPAC value (fvar removed, advances baked)."""
    if not (SPAC_MIN <= spac <= SPAC_MAX):
        raise ValueError(f"SPAC {spac} out of range {SPAC_MIN}-{SPAC_MAX}")
    return instantiateVariableFont(TTFont(str(font_path)), {AXIS_TAG: spac})


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=STATIC_TTF, help="tight static input")
    parser.add_argument("--out", type=Path, default=RAW_VARIABLE_FONT, help="raw VF output")
    args = parser.parse_args(argv)
    vf = build_variable_font(args.src)
    vf.save(str(args.out))
    print("saved", args.out)


if __name__ == "__main__":
    main()
