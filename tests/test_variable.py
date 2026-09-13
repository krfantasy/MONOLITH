"""The shipped variable font: SPAC + KERN axes, advances, outline invariance.

monolith.variable assembles the base VF from the exported static with
fontTools varLib (metric-only SPAC: fvar + HVAR, no GPOS — Glyphs 4.1's VF
export rejects this doc, so the exporter is not on the pipeline's critical
path), tracked as MONOLITH-Variable-raw.ttf, and monolith.kern_axis
finishes it, adding the KERN axis with a GPOS VariationStore built from
the same KERN_PAIRS the Kerning window shows.
"""

from pathlib import Path

import pytest
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from monolith import variable
from monolith.design import DES, SPACED_LSB, TIGHT_OVERLAP, spaced_advance, tight_advance
from monolith.kerning import KERN_PAIRS

REPO_ROOT = Path(__file__).resolve().parents[1]
FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"
RAW_VF = REPO_ROOT / "fonts" / "MONOLITH-Variable-raw.ttf"
VF = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"

pytestmark = pytest.mark.skipif(
    not (FONT.exists() and RAW_VF.exists() and VF.exists()),
    reason="fonts not exported from Glyphs yet",
)


def test_axis_constants_derived_from_design() -> None:
    assert variable.SPAC_MAX == 2 * SPACED_LSB + TIGHT_OVERLAP == 130
    assert variable.TOUCHING == TIGHT_OVERLAP == 30
    assert (variable.SPAC_MIN, variable.SPAC_DEFAULT) == (0, 0)
    assert variable.INSTANCES == ((0, "Tight"), (30, "Touching"), (130, "Spaced"))
    assert (variable.KERN_MIN, variable.KERN_DEFAULT, variable.KERN_MAX) == (0, 0, 100)


@pytest.fixture(scope="module")
def vf() -> TTFont:
    return TTFont(str(VF))


def test_fvar_declares_spac_then_kern(vf: TTFont) -> None:
    tags = [ax.axisTag for ax in vf["fvar"].axes]
    assert tags == ["SPAC", "KERN"]

    spac = vf["fvar"].axes[0]
    assert (spac.minValue, spac.defaultValue, spac.maxValue) == (0, 0, 130)
    assert vf["name"].getDebugName(spac.axisNameID) == "Spacing"

    kern = vf["fvar"].axes[1]
    assert (kern.minValue, kern.defaultValue, kern.maxValue) == (0, 0, 100)
    assert vf["name"].getDebugName(kern.axisNameID) == "Kern"


def test_named_instances_stay_in_range_and_kern_off(vf: TTFont) -> None:
    locs = {i.coordinates["SPAC"] for i in vf["fvar"].instances}
    assert 0 in locs and 130 in locs
    assert all(0 <= v <= 130 for v in locs)
    # KERN defaults off: no named instance turns kerning on
    assert all(i.coordinates["KERN"] == 0 for i in vf["fvar"].instances)


def test_named_instances_pinned_by_name(vf: TTFont) -> None:
    """The instance set is Tight/Touching/Spaced — the Glyphs export calls
    the default "ExtraBold" (its static instance), and kern_axis renames it."""
    got = {
        vf["name"].getDebugName(i.subfamilyNameID): (
            float(i.coordinates["SPAC"]),
            float(i.coordinates["KERN"]),
        )
        for i in vf["fvar"].instances
    }
    assert got == {"Tight": (0.0, 0.0), "Touching": (30.0, 0.0), "Spaced": (130.0, 0.0)}


def test_hvar_carries_spac_advances(vf: TTFont) -> None:
    """Advances live in HVAR (delta index = glyph ID). The metric-only
    construction makes the delta uniformly +130 for every glyph —
    .notdef and space included."""
    store = vf["HVAR"].table.VarStore
    assert store is not None
    data = store.VarData[0]
    assert data.ItemCount == len(vf.getGlyphOrder())
    by_delta: dict[int, int] = {}
    for item in data.Item:
        by_delta[item[0]] = by_delta.get(item[0], 0) + 1
    # uniform +130 for every glyph: keep the uniformity assertion, derive
    # the count from the font instead of hardcoding it as a magic number.
    assert by_delta == {130: len(vf.getGlyphOrder())}


def test_kern_axis_build_is_deterministic(tmp_path: Path) -> None:
    """Two builds from the same raw VF must land on identical tables, one
    "Kern" name record and exactly two axes."""
    from monolith import kern_axis

    once = kern_axis.build_kern_axis(RAW_VF, tmp_path / "once.ttf")
    twice = kern_axis.build_kern_axis(RAW_VF, tmp_path / "twice.ttf")

    for font in (once, twice):
        assert [ax.axisTag for ax in font["fvar"].axes] == ["SPAC", "KERN"]
        assert len(font["fvar"].instances) == 3
        kern_ids = {r.nameID for r in font["name"].names if r.toUnicode() == "Kern"}
        assert len(kern_ids) == 1, kern_ids
    a, b = (
        TTFont(str(tmp_path / "once.ttf"), lazy=True),
        TTFont(str(tmp_path / "twice.ttf"), lazy=True),
    )
    reader_a, reader_b = a.reader, b.reader
    assert reader_a is not None and reader_b is not None
    for tag in sorted(set(a.keys()) - {"head", "GlyphOrder"}):
        assert reader_a[tag] == reader_b[tag], tag
    a.close()
    b.close()


def test_kern_wiring_store_and_feature(vf: TTFont) -> None:
    """GDEF must carry the delta store and GPOS a kern lookup driven by it."""
    store = vf["GDEF"].table.VarStore
    assert store is not None
    var_data = store.VarData[0]
    assert var_data.ItemCount == len(KERN_PAIRS)
    # deltas are the seam-metric values themselves (applied at KERN peak 1.0)
    assert sorted(d[0] for d in var_data.Item)[:3] == sorted(v for v in KERN_PAIRS.values())[:3]

    gpos = vf["GPOS"].table
    assert "kern" in [fr.FeatureTag for fr in gpos.FeatureList.FeatureRecord]
    pp = gpos.LookupList.Lookup[0].SubTable[0]
    assert pp.Format == 1
    assert pp.ValueFormat1 & 0x0040  # X_ADVANCE_DEVICE bit: values vary via GDEF
    devices = [
        rec.Value1.XAdvDevice
        for ps in pp.PairSet
        for rec in ps.PairValueRecord
        if rec.Value1.XAdvDevice
    ]
    assert len(devices) == len(KERN_PAIRS)
    assert all(d.DeltaFormat == 0x8000 for d in devices)  # VariationIndex format


def test_kern_gpos_serves_latn_script(vf: TTFont) -> None:
    """GPOS kern must be reachable under latn, not just DFLT.

    HarfBuzz falls back latn->DFLT, but Word/Adobe/CoreText resolve
    latn-first; a DFLT-only kern lookup is an interop risk for the
    flagship axis. Both records share the one kern lookup."""
    tags = [rec.ScriptTag for rec in vf["GPOS"].table.ScriptList.ScriptRecord]
    assert "DFLT" in tags
    assert "latn" in tags


def _contours(font: TTFont, gname: str) -> list:
    pen = RecordingPen()
    font.getGlyphSet()[gname].draw(pen)
    return pen.value


def test_instance_at_spac_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        variable.instance_at_spac(VF, -1)
    with pytest.raises(ValueError):
        variable.instance_at_spac(VF, variable.SPAC_MAX + 1)


def test_build_variable_font_produces_spac_base_vf() -> None:
    """The varLib assembly step is the pipeline's base-VF producer
    (macro_bootstrap.py ends with `python -m monolith.variable`): pin
    its contract — SPAC-only fvar, HVAR present, default master at the
    tight advances — so it never ships untested."""
    vf = variable.build_variable_font(FONT)
    assert [ax.axisTag for ax in vf["fvar"].axes] == ["SPAC"]
    spac = vf["fvar"].axes[0]
    assert (spac.minValue, spac.defaultValue, spac.maxValue) == (0, 0, 130)
    assert "HVAR" in vf
    static = TTFont(str(FONT))
    for name in ("A", "one", "space"):
        assert vf["hmtx"][name][0] == static["hmtx"][name][0], name


def test_variable_main_writes_to_explicit_out(tmp_path: Path) -> None:
    from monolith import variable

    out = tmp_path / "cli-raw.ttf"
    variable.main(["--src", str(FONT), "--out", str(out)])
    assert out.exists()
    probe = TTFont(str(out))
    assert [ax.axisTag for ax in probe["fvar"].axes] == ["SPAC"]


def test_instance_advances_match_design_math(vf: TTFont) -> None:
    # 0 -> tight, TOUCHING -> natural width (ink edges touch), SPAC_MAX -> .spaced
    expected = {
        0: {n: tight_advance(n) for n in DES},
        variable.TOUCHING: {n: tight_advance(n) + variable.TOUCHING for n in DES},
        variable.SPAC_MAX: {
            n: spaced_advance(n) if n != "space" else tight_advance("space") + variable.SPAC_MAX
            for n in DES
        },
    }
    for v, want in expected.items():
        inst = variable.instance_at_spac(VF, v)
        # SPAC is baked; KERN stays variable (pinned instances only remove
        # axes that were actually pinned)
        assert [ax.axisTag for ax in inst["fvar"].axes] == ["KERN"], v
        for n, adv in want.items():
            assert inst["hmtx"][n][0] == adv, (v, n)


def test_spaced_alternates_get_the_same_delta(vf: TTFont) -> None:
    inst = variable.instance_at_spac(VF, variable.SPAC_MAX)
    assert inst["hmtx"]["zero.spaced"][0] == spaced_advance("zero") + variable.SPAC_MAX


def test_outlines_identical_at_every_position(vf: TTFont) -> None:
    # the SPAC axis must be metric-only: outlines at SPAC 130 == outlines at
    # the default. KERN is GPOS-only, so no variation table moves an outline.
    at_max = variable.instance_at_spac(VF, variable.SPAC_MAX)
    for gname in ("A", "V", "one", "zero"):
        ref = _contours(vf, gname)
        assert _contours(at_max, gname) == ref, gname


def test_shipped_outlines_are_unioned_like_the_static(vf: TTFont) -> None:
    """The shipped VF's outlines must be overlap-free unions matching the
    statics. Glyphs 4.1's raw VF export decomposes glyphs (E) into the full
    glyph box minus boundary-coincident notch holes — valid TrueType, but
    Apple rasterizers (CoreText: Safari, Font Book, Affinity) render the
    shared edges as hairline box outlines. kern_axis unions the contours;
    this pins that (regions compared as sorted per-contour area + bounds,
    robust to vertex order and curve segmentation)."""

    def regions(font: TTFont, gname: str) -> tuple:
        from fontTools.pens.areaPen import AreaPen
        from fontTools.pens.boundsPen import BoundsPen

        glyph_set = font.getGlyphSet()
        rec = RecordingPen()
        glyph_set[gname].draw(rec)
        out, contour = [], None
        for op, args in rec.value:
            if op == "moveTo":
                contour = [args[0]]
            elif op in ("lineTo", "qCurveTo", "curveTo") and contour is not None:
                contour.extend(pt for pt in args if pt is not None)
            elif op in ("closePath", "endPath") and contour:
                area_pen, bounds_pen = AreaPen(), BoundsPen(glyph_set)
                area_pen.moveTo(contour[0])
                bounds_pen.moveTo(contour[0])
                for pt in contour[1:]:
                    area_pen.lineTo(pt)
                    bounds_pen.lineTo(pt)
                area_pen.closePath()
                out.append((round(area_pen.value, 1), bounds_pen.bounds))
                contour = None
        return tuple(sorted(out))

    static = TTFont(str(FONT))
    for gname in ("A", "E", "F", "H", "O", "R", "one", "zero", "zero.spaced"):
        assert regions(vf, gname) == regions(static, gname), gname


def test_lowercase_double_encodes_to_caps(vf: TTFont) -> None:
    import string

    cmap = vf.getBestCmap()
    assert cmap is not None
    order = vf.getGlyphOrder()
    for lo in string.ascii_lowercase:
        up = lo.upper()
        assert cmap[ord(lo)] == up, lo
        assert lo not in order, lo
        assert lo + ".spaced" not in order, lo
    assert cmap[ord("a")] == "A"
    assert cmap[ord("z")] == "Z"
    assert "a" not in vf.getGlyphOrder()
    assert "a.spaced" not in vf.getGlyphOrder()
