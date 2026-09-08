"""The shipped SPAC variable font: axis metadata, advances, outline invariance.

Generation is Glyphs-only, so these tests read fonts/MONOLITH-Variable.ttf
(the Glyphs export) instead of assembling anything with fontTools.
"""

from pathlib import Path

import pytest
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from monolith import variable
from monolith.design import DES, SPACED_LSB, TIGHT_OVERLAP, spaced_advance, tight_advance

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


@pytest.fixture(scope="module")
def vf() -> TTFont:
    return TTFont(str(VF))


def test_variable_font_declares_spac_axis(vf: TTFont) -> None:
    assert "HVAR" in vf
    axis = vf["fvar"].axes[0]
    assert axis.axisTag == "SPAC"
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (0, 0, 130)
    assert vf["name"].getDebugName(axis.axisNameID) == "Spacing"


def test_fvar_carries_only_spac(vf: TTFont) -> None:
    # a constant axis (e.g. single-master wght) would be dead weight in fvar
    assert [ax.axisTag for ax in vf["fvar"].axes] == ["SPAC"]


def test_named_instances_stay_in_range(vf: TTFont) -> None:
    locs = {i.coordinates["SPAC"] for i in vf["fvar"].instances}
    assert 0 in locs and 130 in locs
    assert all(0 <= v <= 130 for v in locs)


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
        assert "fvar" not in inst, v
        for n, adv in want.items():
            assert inst["hmtx"][n][0] == adv, (v, n)


def test_spaced_alternates_get_the_same_delta(vf: TTFont) -> None:
    inst = variable.instance_at_spac(VF, variable.SPAC_MAX)
    assert inst["hmtx"]["zero.spaced"][0] == spaced_advance("zero") + variable.SPAC_MAX


def test_outlines_identical_at_every_position(vf: TTFont) -> None:
    static = TTFont(str(FONT))
    at_max = variable.instance_at_spac(VF, variable.SPAC_MAX)
    for gname in ("A", "V", "one", "zero", "a"):
        ref = _contours(static, gname)
        assert _contours(vf, gname) == ref, gname
        assert _contours(at_max, gname) == ref, gname
