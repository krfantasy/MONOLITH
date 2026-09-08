"""Metric-only variable font (SPAC axis) assembled from the exported static TTF.

The SPAC axis adds `v` font units to every advance width: 0 is the shipped
tight look (letters overlap by 30), 30 makes ink edges exactly touch, and
130 reproduces the .spaced alternates. Outlines never vary, so the whole
axis lives in fvar + HVAR; no Glyphs re-export is involved.
"""
import tempfile
from pathlib import Path

from fontTools.designspaceLib import (AxisDescriptor, DesignSpaceDocument,
                                      InstanceDescriptor, SourceDescriptor)
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont

from monolith.design import SPACED_LSB, TIGHT_OVERLAP

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"
DEFAULT_OUT = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"

AXIS_TAG = "SPAC"
AXIS_NAME = "Spacing"
SPAC_MIN = 0
SPAC_DEFAULT = 0
TOUCHING = TIGHT_OVERLAP
SPAC_MAX = 2 * SPACED_LSB + TIGHT_OVERLAP
INSTANCES: tuple[tuple[int, str], ...] = (
    (SPAC_DEFAULT, "Tight"), (TOUCHING, "Touching"), (SPAC_MAX, "Spaced"),
)


def build_variable(tight_path: str | Path | None = None,
                   out_path: str | Path | None = None) -> Path:
    """Assemble fonts/MONOLITH-Variable.ttf; returns the written path."""
    tight_path = Path(tight_path) if tight_path else DEFAULT_FONT
    out_path = Path(out_path) if out_path else DEFAULT_OUT
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # second master: same outlines, every advance wider by SPAC_MAX
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
        # locations are keyed by axis NAME (not tag) or varLib maps every
        # source to the default and rejects the doc ("more than one base
        # master"). Tight first: it sits at the default location.
        for fname, style, v in ((str(tight_path), "Tight", SPAC_DEFAULT),
                                (str(loose_path), "Loose", SPAC_MAX)):
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
        out_path.parent.mkdir(parents=True, exist_ok=True)
        vf.save(str(out_path))
    return out_path


def instance_at_spac(font_path: str | Path, spac: int) -> TTFont:
    """Static font pinned at the given SPAC value (fvar removed, advances baked)."""
    return instantiateVariableFont(TTFont(str(font_path)), {AXIS_TAG: spac})
