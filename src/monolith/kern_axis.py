"""Finish the MONOLITH variable font: KERN axis (0-100, default 0), the
Tight instance name, and a measured HVAR.

monolith.variable assembles the base variable font from the exported
static with fontTools varLib — metric-only SPAC: fvar + gvar, no GPOS —
and writes fonts/MONOLITH-Variable-raw.ttf. This module finishes it:

- fvar gains a KERN axis: min 0, DEFAULT 0 (kern off unless asked), max 100.
- GDEF gains an ItemVariationStore with one region (KERN peak 100) and one
  delta per seam-metric pair from monolith.kerning.KERN_PAIRS — the same
  1101 pairs (written to each of the 2 masters) shown in the Glyphs Kerning window.
- A GPOS `kern` feature (default-on in every shaper) holds PairPos records
  whose XAdvance is 0 plus a VariationIndex device into that store, so a
  KERN coordinate of t applies each kern scaled by t/100.
- The outlines are unioned (fontTools removeOverlaps) and gvar is rebuilt:
  a decomposed overlap (one Glyphs-exporter pathology for E: the full
  glyph box minus boundary-coincident notch holes) renders with hairline
  box outlines in Apple rasterizers; the rebuilt gvar carries zero outline
  deltas plus the SPAC advance deltas on the phantom points (fontTools'
  glyf instancer reads advances from there).
- HVAR carries the SPAC advance deltas (one delta per glyph, +130).
- The default named instance is renamed to "Tight" (Tight/Touching/Spaced).

Run after monolith.variable: `python -m monolith.kern_axis`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.removeOverlaps import removeOverlaps
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib.builder import buildVarData, buildVarRegionList, buildVarStore

from monolith import variable
from monolith.kerning import KERN_PAIRS

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_VF = REPO_ROOT / "fonts" / "MONOLITH-Variable-raw.ttf"
SHIPPED_VF = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"

# KERN axis range + name live in monolith.variable (single source); used
# below as variable.KERN_MIN / KERN_DEFAULT / KERN_MAX / KERN_NAME.
TIGHT_INSTANCE_NAME = "Tight"


def _new_name_id(font: TTFont) -> int:
    name = font["name"]
    used = {rec.nameID for rec in name.names}
    return max(used) + 1


def _add_name(font: TTFont, text: str, name_id: int) -> None:
    name = font["name"]
    name.setName(text, name_id, 3, 1, 0x409)
    name.setName(text, name_id, 1, 0, 0)


def _add_kern_axis_to_fvar(font: TTFont) -> int:
    """Add the KERN axis — or find the existing one — and return its axisNameID.

    The returned ID is the single "Kern" name record, shared with the STAT
    update below so a re-run never allocates a duplicate.
    """
    existing = next((a for a in font["fvar"].axes if a.axisTag == "KERN"), None)
    if existing is not None:
        print("fvar already has KERN")
        return existing.axisNameID
    fvar = font["fvar"]
    name_id = _new_name_id(font)
    _add_name(font, variable.KERN_NAME, name_id)
    axis = type(fvar.axes[0])()  # must be the _f_v_a_r.Axis struct, not otTables.Axis
    axis.axisTag = "KERN"
    axis.axisNameID = name_id
    axis.flags = 0
    axis.minValue = variable.KERN_MIN
    axis.defaultValue = variable.KERN_DEFAULT
    axis.maxValue = variable.KERN_MAX
    fvar.axes.append(axis)
    for inst in fvar.instances:
        inst.coordinates["KERN"] = variable.KERN_DEFAULT
    print(
        "fvar: KERN axis added (%d-%d-%d), %d instances pinned to default"
        % (variable.KERN_MIN, variable.KERN_DEFAULT, variable.KERN_MAX, len(fvar.instances))
    )
    return name_id


def _rename_default_instance(font: TTFont) -> None:
    """Name the VF's default named instance "Tight".

    A base VF assembled from the static carries the static instance's name
    ("ExtraBold" in the Glyphs-exported raw VF), but the shipped instance
    set is Tight(0)/Touching(30)/Spaced(130) and the static files keep
    their own name — so the rename lives here, in the VF-finishing step.
    Idempotent: a re-run finds the name in place.
    """
    for inst in font["fvar"].instances:
        if inst.coordinates.get("SPAC") == 0:
            current = font["name"].getDebugName(inst.subfamilyNameID)
            if current == TIGHT_INSTANCE_NAME:
                return
            name_id = _new_name_id(font)
            _add_name(font, TIGHT_INSTANCE_NAME, name_id)
            inst.subfamilyNameID = name_id
            print("fvar: default instance %r renamed to %r" % (current, TIGHT_INSTANCE_NAME))
            return


def _add_kern_axis_to_stat(font: TTFont, axis_name_id: int) -> None:
    stat_table = font.get("STAT")
    if stat_table is None:
        print("no STAT table, skipping STAT update")
        return
    st = stat_table.table
    if any(a.AxisTag == "KERN" for a in st.DesignAxisRecord.Axis):
        print("STAT already has KERN")
        return
    axis_index = len(st.DesignAxisRecord.Axis)
    rec = ot.AxisRecord()
    rec.AxisTag = "KERN"
    rec.AxisNameID = axis_name_id
    rec.AxisOrdering = axis_index
    st.DesignAxisRecord.Axis.append(rec)
    if st.AxisValueArray is None:
        st.AxisValueArray = ot.AxisValueArray()
        st.AxisValueArray.AxisValue = []
    unkerned_name_id = _new_name_id(font)
    _add_name(font, "Unkerned", unkerned_name_id)
    kerned_name_id = _new_name_id(font)
    _add_name(font, "Kerned", kerned_name_id)
    for value, name_id, flags in (
        (variable.KERN_DEFAULT, unkerned_name_id, 0x2),
        (variable.KERN_MAX, kerned_name_id, 0x0),
    ):
        av = ot.AxisValue()
        av.Format = 1
        av.AxisIndex = axis_index
        av.Flags = flags
        av.ValueNameID = name_id
        av.Value = value
        st.AxisValueArray.AxisValue.append(av)
    print("STAT: KERN axis record + Unkerned/Kerned values added")


def _build_variation_store(font: TTFont) -> ot.ItemVariationStore:
    """One region (KERN peak at max), one delta item per kern pair.

    axisTags must list every fvar axis in fvar order — each VarRegion
    carries a (0,0,0) entry for SPAC so only KERN drives the deltas.
    """
    axis_tags = [a.axisTag for a in font["fvar"].axes]
    # region coords are NORMALIZED: KERN 100 == +1.0 (axis default 0 == 0.0)
    region_list = buildVarRegionList([{"KERN": (0.0, 1.0, 1.0)}], axis_tags)
    deltas = sorted(KERN_PAIRS.items())
    var_data = buildVarData([0], [[v] for _, v in deltas], optimize=False)
    return buildVarStore(region_list, [var_data])


def _variation_device(outer: int, inner: int) -> ot.Device:
    d = ot.Device()
    d.StartSize = outer
    d.EndSize = inner
    d.DeltaFormat = 0x8000
    return d


def _add_hvar(font: TTFont, deltas: list[int]) -> None:
    """Dedicated advance-metrics variation for SPAC.

    One region (SPAC peak), one delta per glyph, delta index = glyph ID
    (no AdvWidthMap): with HVAR present, shapers take advances from here
    instead of interpolating gvar phantom points. KERN never moves an
    advance, so it gets a neutral entry in the single region.
    """
    axis_tags = [a.axisTag for a in font["fvar"].axes]
    region_list = buildVarRegionList([{"SPAC": (0.0, 1.0, 1.0)}], axis_tags)
    var_data = buildVarData([0], [[d] for d in deltas], optimize=False)
    store = buildVarStore(region_list, [var_data])
    hvar = ot.HVAR()
    hvar.Version = 0x00010000
    hvar.VarStore = store
    hvar.AdvWidthMap = None
    hvar.LsbMap = None
    hvar.RsbMap = None
    table = newTable("HVAR")
    table.table = hvar
    font["HVAR"] = table
    print("HVAR: SPAC advance deltas attached (%d glyphs)" % len(deltas))


def _build_pair_pos(font: TTFont) -> ot.PairPos:
    """PairPos Format 1: XAdvance 0 + VariationIndex per pair (delta=full)."""
    glyph_order = font.getGlyphOrder()
    order = {name: i for i, name in enumerate(glyph_order)}

    lefts: dict[str, list[tuple[str, int]]] = {}
    for inner, ((lg, rg), _v) in enumerate(sorted(KERN_PAIRS.items())):
        lefts.setdefault(lg, []).append((rg, inner))

    lefts_sorted = sorted(lefts, key=lambda g: order[g])
    coverage = ot.Coverage()
    coverage.glyphs = lefts_sorted

    pair_sets: list[ot.PairSet] = []
    for lg in lefts_sorted:
        pairs = sorted(lefts[lg], key=lambda t: order[t[0]])
        records: list[ot.PairValueRecord] = []
        for rg, inner in pairs:
            pvr = ot.PairValueRecord()
            pvr.SecondGlyph = rg
            vr = ot.ValueRecord()
            vr.XAdvance = 0
            vr.XAdvDevice = _variation_device(0, inner)  # fontTools field name
            pvr.Value1 = vr
            records.append(pvr)
        ps = ot.PairSet()
        ps.PairValueRecord = records
        pair_sets.append(ps)

    pp = ot.PairPos()
    pp.Format = 1
    pp.Coverage = coverage
    pp.ValueFormat1 = 0x0004 | 0x0040  # X_ADVANCE + X_ADVANCE_DEVICE
    pp.ValueFormat2 = 0x0000
    pp.PairSet = pair_sets
    return pp


def _add_gpos(font: TTFont, pair_pos: ot.PairPos) -> None:
    gpos_table = newTable("GPOS")
    gpos = ot.GPOS()
    gpos.Version = 0x00010000

    lang_sys = ot.LangSys()
    lang_sys.LookupOrder = None
    lang_sys.ReqFeatureIndex = 0xFFFF
    lang_sys.FeatureIndex = [0]

    script = ot.Script()
    script.DefaultLangSys = lang_sys
    script.ScriptLangSys = []
    srec = ot.ScriptRecord()
    srec.ScriptTag = "DFLT"
    srec.Script = script

    # latn-first engines (Word/Adobe/CoreText) must reach the same kern
    # lookup; HarfBuzz falls back latn->DFLT, so HarfBuzz-only testing
    # never catches a DFLT-only table. Separate LangSys object with the
    # same single-lookup content (sharing one object risks double-compile).
    latn_lang_sys = ot.LangSys()
    latn_lang_sys.LookupOrder = None
    latn_lang_sys.ReqFeatureIndex = 0xFFFF
    latn_lang_sys.FeatureIndex = [0]
    latn_script = ot.Script()
    latn_script.DefaultLangSys = latn_lang_sys
    latn_script.ScriptLangSys = []
    latn_rec = ot.ScriptRecord()
    latn_rec.ScriptTag = "latn"
    latn_rec.Script = latn_script

    script_list = ot.ScriptList()
    script_list.ScriptRecord = [srec, latn_rec]

    feature = ot.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [0]
    frec = ot.FeatureRecord()
    frec.FeatureTag = "kern"
    frec.Feature = feature
    feature_list = ot.FeatureList()
    feature_list.FeatureRecord = [frec]

    lookup = ot.Lookup()
    lookup.LookupType = 2
    lookup.LookupFlag = 0
    lookup.SubTable = [pair_pos]
    lookup_list = ot.LookupList()
    lookup_list.Lookup = [lookup]

    gpos.ScriptList = script_list
    gpos.FeatureList = feature_list
    gpos.LookupList = lookup_list
    gpos_table.table = gpos
    font["GPOS"] = gpos_table
    print("GPOS: DFLT+latn kern lookup with %d VariationIndex pairs" % len(KERN_PAIRS))


def _attach_store_to_gdef(font: TTFont, store: ot.ItemVariationStore) -> None:
    # A fresh ot.GDEF is required: reusing the decompiled container trips
    # fontTools' propagated-count assert when the VarStore is attached to it.
    gdef_table = font.get("GDEF")
    old = gdef_table.table if gdef_table is not None else None
    gdef = ot.GDEF()
    gdef.Version = 0x00010003
    for field in (
        "GlyphClassDef",
        "AttachList",
        "LigCaretList",
        "MarkAttachClassDef",
        "MarkGlyphSetsDef",
    ):
        setattr(gdef, field, getattr(old, field, None) if old is not None else None)
    gdef.VarStore = store  # fontTools' GDEF attr for ItemVariationStore
    gdef_table = newTable("GDEF")
    gdef_table.table = gdef
    font["GDEF"] = gdef_table
    print("GDEF: ItemVariationStore attached (%d delta items)" % len(KERN_PAIRS))


def _rebuild_gvar(font: TTFont, spac_max: int) -> None:
    """Fresh gvar for the unioned outlines: zero outline deltas (the SPAC
    axis is metric-only) plus a +spac_max delta on each glyph's advance
    phantom point. fontTools' instancer only applies HVAR to hmtx for
    CFF2 fonts — for glyf fonts it uses gvar phantom points, so a glyf
    VF without gvar would instance to wrong advances ("faulty font" per
    fontTools). HVAR below mirrors the same deltas for shapers."""
    from fontTools.ttLib.tables._g_v_a_r import TupleVariation

    axes = {"SPAC": (0.0, 1.0, 1.0), "KERN": (0.0, 0.0, 0.0)}
    variations = {}
    for gname in font.getGlyphOrder():
        glyph = font["glyf"][gname]
        if glyph.isComposite():
            count = len(glyph.components)
        elif glyph.numberOfContours > 0:
            count = len(glyph.coordinates)
        else:
            count = 0
        # per-point zeros, then the four phantoms: lsb, ADVANCE, tsb, vadv
        deltas = [(0, 0)] * count + [(0, 0), (spac_max, 0), (0, 0), (0, 0)]
        variations[gname] = [TupleVariation(dict(axes), deltas)]
    gvar = newTable("gvar")
    gvar.version = 1
    gvar.reserved = 0
    gvar.axisCount = len(font["fvar"].axes)
    gvar.variations = variations
    font["gvar"] = gvar
    print("gvar: rebuilt for unioned outlines (phantom advance +%d)" % spac_max)


def build_kern_axis(src: str | Path = RAW_VF, out: str | Path = SHIPPED_VF) -> TTFont:
    """Raw varLib VF -> finished variable font (SPAC + KERN axes). Saved to out."""
    font = TTFont(str(src))
    # Union overlapping contours before shipping: a decomposed overlap (the
    # Glyphs VF exporter once wrote E as the full glyph box minus
    # boundary-coincident notch holes) renders with hairline box outlines in
    # Apple rasterizers (CoreText: Safari, Font Book, Affinity). The varLib
    # path starts from the static's outlines, which are already unioned, so
    # this is a no-op safeguard there. Drop the raw gvar either way: the
    # union changes point counts, so _rebuild_gvar (after the KERN axis
    # exists) replaces it.
    del font["gvar"]
    removeOverlaps(font)
    kern_name_id = _add_kern_axis_to_fvar(font)
    _rename_default_instance(font)
    stat_table = font.get("STAT")
    if stat_table is not None:
        _add_kern_axis_to_stat(font, kern_name_id)
    store = _build_variation_store(font)
    _attach_store_to_gdef(font, store)
    pair_pos = _build_pair_pos(font)
    _add_gpos(font, pair_pos)
    # every advance moves +SPAC_MAX along SPAC by construction (the Spaced
    # master is the tight one plus SPAC_MAX). HVAR — not the raw VF's gvar
    # phantoms — defines advances once present, which also pins .notdef
    # (Glyphs auto-boxes it and its phantom delta can disagree). Deliberate:
    # the delta is uniform for every glyph ID including .notdef and space.
    # the instancer tests pin advances end-to-end at 0/30/130 for all glyphs
    _add_hvar(font, [variable.SPAC_MAX] * len(font.getGlyphOrder()))
    _rebuild_gvar(font, variable.SPAC_MAX)
    font.save(str(out))
    print("saved", out)
    return font


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=RAW_VF, help="raw Glyphs VF input")
    parser.add_argument("--out", type=Path, default=SHIPPED_VF, help="shipped VF output")
    args: argparse.Namespace = parser.parse_args()
    font = build_kern_axis(args.src, args.out)
    axes = [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in font["fvar"].axes]
    print("axes:", axes)


if __name__ == "__main__":
    main()
