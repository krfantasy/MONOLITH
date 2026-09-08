"""The shipped variable font: SPAC + KERN axes, advances, outline invariance.

The shipped font is the Glyphs VF export (fonts/MONOLITH-Variable-raw.ttf)
post-processed by monolith.kern_axis, which adds the KERN axis with a GPOS
VariationStore built from the same KERN_PAIRS the Kerning window shows.
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
VF = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"

pytestmark = pytest.mark.skipif(
    not (FONT.exists() and VF.exists()), reason="fonts not exported from Glyphs yet"
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


def _contours(font: TTFont, gname: str) -> list:
    pen = RecordingPen()
    font.getGlyphSet()[gname].draw(pen)
    return pen.value


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
    # the default. KERN is GPOS-only, so gvar never moves an outline for it.
    # (Outlines are NOT byte-equal to the statics — Glyphs' VF export keeps
    # overlapping contours where static exports remove them — but they
    # rasterize identically, which the shaping/specimen tests cover.)
    at_max = variable.instance_at_spac(VF, variable.SPAC_MAX)
    for gname in ("A", "V", "one", "zero", "a"):
        ref = _contours(vf, gname)
        assert _contours(at_max, gname) == ref, gname
