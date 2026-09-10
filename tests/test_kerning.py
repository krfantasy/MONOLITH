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
    # exact-count tripwire: the blind-spot fix landed at 1101 (486 letter
    # pairs unchanged + 615 band-blind pairs), and the prose claims it
    # exactly (README Spacing/Kerning sections, kern_axis.py docstring,
    # macro_bootstrap.py header; monolith-spac.html's spans regenerate via
    # scripts/extract_html_kern.py). If you retune the metric, update the
    # count in all five places together (this test + the four prose places).
    assert len(K.KERN_PAIRS) == 1101
    letters = {(lg, rg): v for (lg, rg), v in K.KERN_PAIRS.items() if lg in K.BASE and rg in K.BASE}
    assert len(letters) == 486  # the letter table is untouched by the fix
    for (lg, rg), v in K.KERN_PAIRS.items():
        assert -160 <= v <= -40, (lg, rg, v)
        assert v % 10 == 0, (lg, rg, v)
        # every kern is justified by a real gap in its reading band
        # (kern_for's lowercase fallback is covered by the tests above)
        gap = K.band_gap(lg, rg)
        assert gap is not None and gap >= K.MIN_PULL + K.TARGET, (lg, rg, gap)


def test_baseline_solid_left_edges_do_not_kern() -> None:
    # E's lower notch starts above the baseline band; EA stays at default
    assert K.kern_for("E", "A") == 0
    assert K.kern_for("E", "V") == -160  # V's own receding edge still kerns
    # P's baseline is stem-only (bowl starts at y=300): classic P-kerning
    assert K.kern_for("P", "A") == -160


BLIND = (
    "asciicircum",
    "asciitilde",
    "asterisk",
    "emdash",
    "endash",
    "equal",
    "grave",
    "hyphen",
    "plus",
    "quotedbl",
    "quotesingle",
)


def test_band_blind_set_is_exactly_the_eleven() -> None:
    # TODO.org "Metric blind spots": these 11 glyphs have no ink in the
    # baseline band and kern via the widened fallback; band-inked punct
    # stays out pending the separate punct-scope decision.
    assert tuple(n for n in K.KERNABLE if n not in K.BASE) == BLIND
    assert all(not K._has_band_ink(n) for n in BLIND)
    assert all(K._has_band_ink(n) for n in K.BASE)


def test_blind_pairs_read_their_own_band() -> None:
    # the exact gaps the kern review quoted (TODO.org)
    assert abs(K.band_gap("T", "hyphen") - 150.0) < 1e-9
    assert abs(K.band_gap("T", "plus") - 380.0) < 1e-9
    assert abs(K.band_gap("V", "equal") - 1160 / 7) < 1e-9
    assert abs(K.band_gap("T", "quotedbl") - 150.0) < 1e-9
    for lg, rg in (
        ("T", "hyphen"),
        ("hyphen", "T"),
        ("T", "plus"),
        ("V", "equal"),
        ("T", "quotedbl"),
    ):
        assert K.kern_for(lg, rg) == -160, (lg, rg)


def test_blind_pairs_absent_when_already_fused() -> None:
    # solid letters overlap the marks by the standard fusion already:
    # no blanket kerns (mirrors "correctly absent" in the review)
    assert K.kern_for("H", "hyphen") == 0
    assert K.kern_for("hyphen", "H") == 0
    assert K.kern_for("A", "hyphen") == 0
    assert K.kern_for("H", "quotesingle") == 0


def test_baseline_band_stays_authoritative() -> None:
    # mid-height notches stay ignored by design (TODO.org second bullet):
    # E+A reads in the baseline band (-30 fusion), never at its y=140 notch
    assert K.kern_for("E", "A") == 0
    assert K.band_gap("E", "A") == K.TARGET
