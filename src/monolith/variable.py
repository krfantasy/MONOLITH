"""Metric-only variable font (SPAC axis) assembled from the exported static TTF.

The SPAC axis adds `v` font units to every advance width: 0 is the shipped
tight look (letters overlap by 30), 30 makes ink edges exactly touch, and
130 reproduces the .spaced alternates. Outlines never vary, so the whole
axis lives in fvar + HVAR; no Glyphs re-export is involved.
"""

import tempfile
from pathlib import Path

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.varLib import build as varlib_build
from fontTools.varLib.instancer import instantiateVariableFont

from monolith.design import SPACED_LSB, TIGHT_OVERLAP
from monolith.kerning import KERN_PAIRS

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
    (SPAC_DEFAULT, "Tight"),
    (TOUCHING, "Touching"),
    (SPAC_MAX, "Spaced"),
)


def build_variable(
    tight_path: str | Path | None = None, out_path: str | Path | None = None
) -> Path:
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
        apply_kerning(vf)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        vf.save(str(out_path))
    return out_path


def _kern_feature_present(font: TTFont) -> bool:
    if "GPOS" not in font or font["GPOS"].table.FeatureList is None:
        return False
    return any(fr.FeatureTag == "kern" for fr in font["GPOS"].table.FeatureList.FeatureRecord)


def apply_kerning(font: TTFont) -> None:
    """Write KERN_PAIRS as a GPOS pair-position 'kern' feature.

    Idempotent: a font that already carries a kern feature (e.g. re-exported
    from Glyphs after build.py added kerning) is left untouched, so kern
    values can never apply twice.
    """
    if _kern_feature_present(font):
        return
    glyph_order = set(font.getGlyphOrder())
    pairs: dict[str, list[tuple[str, int]]] = {}
    for (lg, rg), v in KERN_PAIRS.items():
        if lg in glyph_order and rg in glyph_order:
            pairs.setdefault(lg, []).append((rg, v))
    if not pairs:
        return

    pair_pos = otTables.PairPos()
    pair_pos.Format = 1
    pair_pos.ValueFormat1 = 0x0004  # XAdvance only
    pair_pos.ValueFormat2 = 0x0000
    pair_pos.Coverage = otTables.Coverage()
    pair_pos.Coverage.glyphs = sorted(pairs)
    pair_pos.PairSet = []
    for lg in sorted(pairs):
        pair_set = otTables.PairSet()
        pair_set.PairValueRecord = []
        for rg, v in sorted(pairs[lg]):
            pvr = otTables.PairValueRecord()
            pvr.SecondGlyph = rg
            pvr.Value1 = otTables.ValueRecord()
            pvr.Value1.XAdvance = v
            pair_set.PairValueRecord.append(pvr)
        pair_set.PairValueCount = len(pair_set.PairValueRecord)
        pair_pos.PairSet.append(pair_set)
    pair_pos.PairSetCount = len(pair_pos.PairSet)

    lookup = otTables.Lookup()
    lookup.LookupType = 2  # pair positioning
    lookup.LookupFlag = 0
    lookup.SubTable = [pair_pos]
    lookup.LookupCount = 1

    feature = otTables.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [0]
    feature.LookupCount = 1

    lang_sys = otTables.LangSys()
    lang_sys.LookupOrder = None
    lang_sys.ReqFeatureIndex = 0xFFFF
    lang_sys.FeatureIndex = [0]
    lang_sys.FeatureCount = 1
    script = otTables.Script()
    script.DefaultLangSys = lang_sys
    script.LangSysRecord = []
    script.LangSysCount = 0
    script_record = otTables.ScriptRecord()
    script_record.ScriptTag = "DFLT"
    script_record.Script = script
    script_list = otTables.ScriptList()
    script_list.ScriptRecord = [script_record]
    script_list.ScriptCount = 1

    feature_record = otTables.FeatureRecord()
    feature_record.FeatureTag = "kern"
    feature_record.Feature = feature
    feature_list = otTables.FeatureList()
    feature_list.FeatureRecord = [feature_record]
    feature_list.FeatureCount = 1

    lookup_list = otTables.LookupList()
    lookup_list.Lookup = [lookup]
    lookup_list.LookupCount = 1

    gpos = otTables.GPOS()
    gpos.Version = 0x00010000
    gpos.ScriptList = script_list
    gpos.FeatureList = feature_list
    gpos.LookupList = lookup_list

    gpos_table = newTable("GPOS")
    gpos_table.table = gpos
    font["GPOS"] = gpos_table


def instance_at_spac(font_path: str | Path, spac: int) -> TTFont:
    """Static font pinned at the given SPAC value (fvar removed, advances baked)."""
    return instantiateVariableFont(TTFont(str(font_path)), {AXIS_TAG: spac})
