"""Design-data invariants. Pure Python - no Glyphs required.

These encode lessons already paid for: full ASCII coverage, the
thin-diagonal regression class (N/Z/V/W/Y), counter presence, and the
spacing math the features/alternates depend on.
"""

import math

from fontTools.agl import AGL2UV

from monolith import design
from monolith.design import DES, LOWERCASE, Glyph, Point, Poly, Rect, substitution_names

# unicode -> AGL glyph names (multiple names can share a codepoint, so keep a set)
UV2NAMES = {}
for _name, _uv in AGL2UV.items():
    UV2NAMES.setdefault(_uv, set()).add(_name)


def test_full_printable_ascii_coverage() -> None:
    names = set(DES) | set(LOWERCASE)
    covered = {uv for uv, ns in UV2NAMES.items() if ns & names}
    missing = [chr(c) for c in range(0x21, 0x7F) if c not in covered]
    assert missing == []


def test_every_glyph_well_formed() -> None:
    for name, g in DES.items():
        assert isinstance(g, Glyph), name
        assert g.width > 0, name
        assert isinstance(g.shapes, tuple), name
        for s in g.shapes:
            if isinstance(s, Rect):
                assert s.x0 < s.x1 and s.y0 < s.y1, name
            else:
                assert isinstance(s, Poly) and len(s.points) >= 3, name
                for x, y in s.points:
                    assert math.isfinite(x) and math.isfinite(y), name


def _perp_dist(a: Point, b: Point, p: Point) -> float:
    """Distance from point p to the line through a-b."""
    (ax, ay), (bx, by), (px, py) = a, b, p
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    return abs(dy * (px - ax) - dx * (py - ay)) / L


def test_quad_parallel_edge_pairs_at_least_100_units() -> None:
    """Thin-diagonal tripwire: any 4-point poly with a parallel edge pair
    must be >= 100 units thick between those edges. Catches the N/Z/V/W/Y
    thin-wedge regression class (illegible at 12pt).

    GRANDFATHERED (controller ruling, task 2): three intentional thin
    strokes already shipped in the font and transcribed 1:1 from
    glyph_gen.py - zero's diagonal slash (78u, commit f1d5067) and the
    two asterisk arms (45u). Everything else still needs >= 100u.
    """
    grandfathered = {
        ("asterisk", ((120, 480), (210, 480), (500, 650), (410, 650))),
        ("asterisk", ((410, 480), (500, 480), (210, 650), (120, 650))),
        ("zero", ((215, 520), (215, 400), (405, 180), (405, 300))),
    }
    for name, g in DES.items():
        for s in g.shapes:
            if not isinstance(s, Poly) or len(s.points) != 4:
                continue
            pts = list(s.points)
            if (name, tuple(pts)) in grandfathered:
                continue
            edges = [(pts[i], pts[(i + 1) % 4]) for i in range(4)]
            for i in range(4):
                for j in range(i + 1, 4):
                    (a, b), (c, d) = edges[i], edges[j]
                    e1 = (b[0] - a[0], b[1] - a[1])
                    e2 = (d[0] - c[0], d[1] - c[1])
                    l1, l2 = math.hypot(*e1), math.hypot(*e2)
                    if l1 == 0 or l2 == 0:
                        continue
                    if abs((e1[0] * e2[1] - e1[1] * e2[0]) / (l1 * l2)) < 1e-6:
                        mid = ((c[0] + d[0]) / 2, (c[1] + d[1]) / 2)
                        assert _perp_dist(a, b, mid) >= 100, (name, pts)


def test_counter_spot_checks() -> None:
    for n in ("A", "B", "D", "G", "O", "eight", "zero"):
        assert any(s.hole for s in DES[n].shapes), n
    for n in ("I", "L", "T", "X", "V", "W"):
        assert not any(s.hole for s in DES[n].shapes), n


def test_advance_math_pinned_values() -> None:
    # tight: letters overlap by TIGHT_OVERLAP (A: 620 -> 590); space keeps natural width
    assert design.tight_advance("A") == 590
    assert design.tight_advance("one") == 320  # 350 - 30
    assert design.tight_advance("space") == 240
    # spaced alternates: LSB/RSB 50 on both sides (A: 620 -> 720)
    assert design.spaced_advance("A") == 720
    assert design.spaced_advance("space") == 340  # formula applies; space is never drawn as .spaced


def test_substitution_names_complete() -> None:
    subs = set(substitution_names())
    expected = {n for n in DES if n != "space"} | set(LOWERCASE)
    assert subs == expected
    assert "space" not in subs
