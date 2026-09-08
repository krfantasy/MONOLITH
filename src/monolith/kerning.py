"""Seam fitness and pair kerning derived from the polygon design data.

MONOLITH overlaps neighbours by TIGHT_OVERLAP (advance = width - 30), which
fuses solid vertical edges but leaves canyons where an edge recedes from the
vertical (V, Y, T, L, J, one, seven). The seam gap of an ordered pair at
height y is the horizontal distance between the left glyph's rightmost ink
and the right glyph's leftmost ink once both are placed at the default
advance; positive means air, TIGHT_OVERLAP means the standard 30-unit
fusion. KERN_PAIRS is computed at import from the rule below (run
`python -m monolith.kerning` to print the table) and is the single source of
truth for build.py (native Glyphs kerning, shown in the Kerning window)
and kern_axis.py (the variable font's KERN axis GPOS VariationStore).
"""

import sys
from typing import Any

from monolith.design import DES, TIGHT_OVERLAP, Rect

CAPS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
BASE = tuple(CAPS) + DIGITS

# kern rule: close the baseline-band seam to TARGET, rounded to 10 units.
# Pairs already tighter than NO-KERN-BELOW stay untouched; deep pulls are
# capped so a receding pair never gets forced into a full-height weld.
TARGET = -30.0  # standard seam fusion
MAX_PULL = 160.0  # never kern further than this
MIN_PULL = 40.0  # ignore pairs whose correction would be smaller
ROUND_TO = 10
BAND_Y0, BAND_Y1, BAND_STEP = 20, 120, 4  # the baseline band where fusion reads


def _shape_points(shape: Any) -> list[tuple[float, float]]:
    if isinstance(shape, Rect):
        return [
            (shape.x0, shape.y0),
            (shape.x1, shape.y0),
            (shape.x1, shape.y1),
            (shape.x0, shape.y1),
        ]
    return list(shape.points)


def _ink_intervals(shapes: tuple, y: float) -> list[tuple[float, float]]:
    """Visible (body minus holes) ink intervals of a glyph at height y."""
    raw: list[tuple[float, float, bool]] = []
    for s in shapes:
        pts = _shape_points(s)
        xs = []
        n = len(pts)
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            raw.append((xs[i], xs[i + 1], s.hole))
    body = [(a, b) for a, b, hole in raw if not hole]
    for a, b, hole in raw:
        if not hole:
            continue
        nxt = []
        for a2, b2 in body:
            if b <= a2 or a >= b2:  # no overlap
                nxt.append((a2, b2))
                continue
            if a2 < a:
                nxt.append((a2, a))
            if b < b2:
                nxt.append((b, b2))
        body = nxt
    return body


def _ink_extent(shapes: tuple, y: float) -> tuple[float, float] | None:
    """(min x, max x) of visible ink at height y, or None if empty there."""
    iv = _ink_intervals(shapes, y)
    if not iv:
        return None
    return min(a for a, _ in iv), max(b for _, b in iv)


def seam_gap(left: str, right: str, y: float) -> float | None:
    """Air between the pair at height y under default tight advances."""
    l_extent = _ink_extent(DES[left].shapes, y)
    r_extent = _ink_extent(DES[right].shapes, y)
    if l_extent is None or r_extent is None:
        return None
    # the right glyph's pen position = advance of the LEFT glyph
    return (DES[left].width - TIGHT_OVERLAP + r_extent[0]) - l_extent[1]


def band_gap(left: str, right: str) -> float | None:
    """Widest seam gap in the baseline band (where fusion reads)."""
    gaps = [
        g
        for y in range(BAND_Y0, BAND_Y1 + 1, BAND_STEP)
        if (g := seam_gap(left, right, float(y))) is not None
    ]
    return max(gaps) if gaps else None


def proposed_value(gap: float) -> int | None:
    """Kern value for a seam gap; None when no meaningful correction needed.

    The pull is how far the pair must move left so the band gap reaches
    TARGET; corrections below MIN_PULL are ignored, beyond MAX_PULL capped.
    """
    pull = gap - TARGET
    if pull < MIN_PULL:
        return None
    pull = min(pull, MAX_PULL)
    return -int(round(pull / ROUND_TO) * ROUND_TO)


def compute_kerns() -> dict[tuple[str, str], int]:
    out: dict[tuple[str, str], int] = {}
    for left in BASE:
        for right in BASE:
            gap = band_gap(left, right)
            if gap is None:
                continue
            k = proposed_value(gap)
            if k is not None:
                out[(left, right)] = k
    # lowercase glyphs render as the caps, so they need the same pairs
    for (lg, rg), k in list(out.items()):
        if lg in CAPS and rg in CAPS:
            out[(lg.lower(), rg.lower())] = k
    return out


KERN_PAIRS: dict[tuple[str, str], int] = {
    (lg, rg): v for (lg, rg), v in sorted(compute_kerns().items())
}


def kern_for(left: str, right: str) -> int:
    """Lookup with zero default; falls back case-insensitively."""
    if left == " " or right == " ":
        return 0
    k = KERN_PAIRS.get((left, right))
    if k is not None:
        return k
    return KERN_PAIRS.get((left.upper(), right.upper()), 0)


def main() -> None:
    for (lg, rg), v in KERN_PAIRS.items():
        print(f'    ("{lg}", "{rg}"): {v},')
    print(f"# {len(KERN_PAIRS)} pairs", file=sys.stderr)


if __name__ == "__main__":
    main()
