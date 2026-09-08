"""Read-side helpers for the SPAC variable font.

Generation is Glyphs-only: build.py (run in the Macro Panel) sets up the
SPAC axis with two masters — SPAC 0 with the shipped tight advances, SPAC
130 with every advance wider by 130 — plus the `kern` feature, and the
variable font is exported from those masters (macro_bootstrap tries
instance.generate(Format=VARIABLE); otherwise File > Export > Variable).
Outlines never vary across the axis, so it lives entirely in fvar + HVAR.
This module only reads and pins the exported font, for specimens and tests.
"""

from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from monolith.design import SPACED_LSB, TIGHT_OVERLAP

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VARIABLE_FONT = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"

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


def instance_at_spac(font_path: str | Path, spac: int) -> TTFont:
    """Static font pinned at the given SPAC value (fvar removed, advances baked)."""
    return instantiateVariableFont(TTFont(str(font_path)), {AXIS_TAG: spac})
