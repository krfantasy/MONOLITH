"""SPAC variable-font assembly. Pure fontTools - no Glyphs required."""
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

from monolith import variable
from monolith.design import SPACED_LSB, TIGHT_OVERLAP

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
