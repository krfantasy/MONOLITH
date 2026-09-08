"""SPAC variable-font assembly. Pure fontTools - no Glyphs required."""
from pathlib import Path

import pytest
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from monolith import variable
from monolith.design import DES, SPACED_LSB, TIGHT_OVERLAP, spaced_advance, tight_advance

REPO_ROOT = Path(__file__).resolve().parents[1]
FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"

pytestmark = pytest.mark.skipif(
    not FONT.exists(), reason="font not built yet (export from Glyphs first)"
)


def test_axis_constants_derived_from_design() -> None:
    assert variable.SPAC_MAX == 2 * SPACED_LSB + TIGHT_OVERLAP == 130
    assert variable.TOUCHING == TIGHT_OVERLAP == 30
    assert (variable.SPAC_MIN, variable.SPAC_DEFAULT) == (0, 0)
    assert variable.INSTANCES == ((0, "Tight"), (30, "Touching"), (130, "Spaced"))


@pytest.fixture(scope="module")
def vf_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return variable.build_variable(
        FONT, tmp_path_factory.mktemp("vf") / "MONOLITH-Variable.ttf"
    )


def test_variable_font_declares_spac_axis(vf_path: Path) -> None:
    font = TTFont(str(vf_path))
    assert "fvar" in font and "HVAR" in font
    axis = font["fvar"].axes[0]
    assert axis.axisTag == "SPAC"
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (0, 0, 130)
    assert font["name"].getDebugName(axis.axisNameID) == "Spacing"


def test_named_instances(vf_path: Path) -> None:
    font = TTFont(str(vf_path))
    got = {
        font["name"].getDebugName(i.subfamilyNameID): i.coordinates["SPAC"]
        for i in font["fvar"].instances
    }
    assert got == {"Tight": 0, "Touching": 30, "Spaced": 130}


def _contours(font: TTFont, gname: str) -> list:
    pen = RecordingPen()
    font.getGlyphSet()[gname].draw(pen)
    return pen.value


def test_instance_advances_match_design_math(vf_path: Path) -> None:
    # 0 -> tight, TOUCHING -> natural width (ink edges touch), SPAC_MAX -> .spaced
    expected = {
        0: {n: tight_advance(n) for n in DES},
        variable.TOUCHING: {n: tight_advance(n) + variable.TOUCHING for n in DES},
        variable.SPAC_MAX: {n: spaced_advance(n) if n != "space"
                            else tight_advance("space") + variable.SPAC_MAX
                            for n in DES},
    }
    for v, want in expected.items():
        inst = variable.instance_at_spac(vf_path, v)
        assert "fvar" not in inst, v
        for n, adv in want.items():
            assert inst["hmtx"][n][0] == adv, (v, n)


def test_spaced_alternates_get_the_same_delta(vf_path: Path) -> None:
    inst = variable.instance_at_spac(vf_path, variable.SPAC_MAX)
    assert inst["hmtx"]["zero.spaced"][0] == spaced_advance("zero") + variable.SPAC_MAX


def test_outlines_identical_at_every_position(vf_path: Path) -> None:
    static = TTFont(str(FONT))
    at_max = variable.instance_at_spac(vf_path, variable.SPAC_MAX)
    for gname in ("A", "V", "one", "zero", "a"):
        ref = _contours(static, gname)
        assert _contours(TTFont(str(vf_path)), gname) == ref, gname
        assert _contours(at_max, gname) == ref, gname
