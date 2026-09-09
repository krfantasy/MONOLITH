"""Seam-metric kern table invariants."""

from monolith import kerning as K
from monolith.design import TIGHT_OVERLAP


def test_solid_pairs_are_at_standard_fusion() -> None:
    # H/H is the reference seam: both edges solid, gap = -TIGHT_OVERLAP
    assert K.seam_gap("H", "H", 350.0) == -TIGHT_OVERLAP
    assert K.kern_for("H", "H") == 0
    assert K.kern_for("H", "O") == 0  # control pair from the review sheet


def test_hand_derived_receding_pairs() -> None:
    # V's ink starts 190*(680/700) units in at y=20: gap = that minus 30
    gap = K.seam_gap("A", "V", 20.0)
    assert gap is not None
    assert abs(gap - (190 * 680 / 700 - 30)) < 1e-9
    assert K.kern_for("A", "V") == -160
    assert K.kern_for("V", "A") == -160
    # J's ink starts at 120: gap 90 -> exactly -120
    assert K.kern_for("A", "J") == -120
    # digit pairs kern too
    assert K.kern_for("A", "one") == -90


def test_lowercase_mirrors_caps() -> None:
    assert K.kern_for("a", "v") == K.kern_for("A", "V")
    assert K.kern_for("t", "j") == K.kern_for("T", "J")


def test_lowercase_falls_back_to_caps() -> None:
    # No lowercase keys ship in the table anymore (double-unicode: `a`
    # IS glyph `A`); the lookup API still tolerates lowercase input.
    assert K.kern_for("A", "one") == -90
    assert K.kern_for("a", "one") == K.kern_for("A", "one")
    assert K.kern_for("one", "V") == -160
    assert K.kern_for("one", "v") == K.kern_for("one", "V")
    assert ("a", "one") not in K.KERN_PAIRS
    assert ("one", "v") not in K.KERN_PAIRS
    assert not any(len(n) == 1 and n.islower() for pair in K.KERN_PAIRS for n in pair)


def test_spaces_never_kern() -> None:
    assert K.kern_for(" ", "V") == 0
    assert K.kern_for("V", " ") == 0


def test_table_invariants() -> None:
    assert len(K.KERN_PAIRS) > 300
    # exact-count tripwire: the double-unicode migration landed at 486, and the
    # prose claims it exactly (README Spacing/Kerning sections,
    # kern_axis.py docstring, macro_bootstrap.py header). If you retune the
    # metric, update the count in all four places together.
    assert len(K.KERN_PAIRS) == 486
    for (lg, rg), v in K.KERN_PAIRS.items():
        assert -160 <= v <= -40, (lg, rg, v)
        assert v % 10 == 0, (lg, rg, v)
        # every kern is justified by a real baseline-band gap
        # (kern_for's lowercase fallback is covered by the tests above)
        if lg in K.BASE and rg in K.BASE:
            gap = K.band_gap(lg, rg)
            assert gap is not None and gap >= K.MIN_PULL + K.TARGET, (lg, rg, gap)


def test_baseline_solid_left_edges_do_not_kern() -> None:
    # E's lower notch starts above the baseline band; EA stays at default
    assert K.kern_for("E", "A") == 0
    assert K.kern_for("E", "V") == -160  # V's own receding edge still kerns
    # P's baseline is stem-only (bowl starts at y=300): classic P-kerning
    assert K.kern_for("P", "A") == -160
