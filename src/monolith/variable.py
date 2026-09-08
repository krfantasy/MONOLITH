"""Read-side helpers for the MONOLITH variable font (SPAC + KERN axes).

The .glyphs source carries the SPAC masters (SPAC 0 tight advances, SPAC
130 with every advance wider by 130) and native per-master kerning — the
742 seam-metric pairs visible in Glyphs' Kerning window. The variable
font exported from it is post-processed by monolith.kern_axis, which adds
the KERN axis (0-100, default 0 = kerning off) as a GPOS VariationStore;
the ExtraBold static is exported unkerned via its "Remove Features: kern"
instance parameter. This module only reads and pins the exported fonts,
for specimens and tests.
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

KERN_AXIS_TAG = "KERN"
KERN_MIN = 0
KERN_DEFAULT = 0  # kerning off unless a layout engine asks for it
KERN_MAX = 100


def instance_at_spac(font_path: str | Path, spac: int) -> TTFont:
    """Static font pinned at the given SPAC value (fvar removed, advances baked)."""
    return instantiateVariableFont(TTFont(str(font_path)), {AXIS_TAG: spac})
