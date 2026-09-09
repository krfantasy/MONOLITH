"""SPAC-axis constants and read-side helpers for the MONOLITH variable font.

The variable font itself is exported by Glyphs: the Scripting-Window
bootstrap (scripts/macro_bootstrap.py) drives a VARIABLE-type instance's
generate() and writes the raw VF — fvar SPAC + gvar, no KERN axis — to
fonts/MONOLITH-Variable-raw.ttf. monolith.kern_axis then finishes it
outside Glyphs (the one sanctioned fontTools step): KERN axis 0-100
(default 0 = kerning off) as a GPOS VariationStore, a measured HVAR, and
the Tight instance name. The statics ship unkerned via the ExtraBold
instance's "Remove Features: kern" parameter. This module keeps the axis
constants in one place and reads the exported fonts, for specimens and
tests.
"""

from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from monolith.design import SPACED_LSB, TIGHT_OVERLAP

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VARIABLE_FONT = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"
RAW_VARIABLE_FONT = REPO_ROOT / "fonts" / "MONOLITH-Variable-raw.ttf"

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


def instance_at_spac(font_path: str | Path, spac: int) -> TTFont:
    """Static font pinned at the given SPAC value (fvar removed, advances baked)."""
    return instantiateVariableFont(TTFont(str(font_path)), {AXIS_TAG: spac})
