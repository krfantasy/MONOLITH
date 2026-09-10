"""Seam-metric kern table invariants."""

from monolith import kerning as K
from monolith.design import DES, TIGHT_OVERLAP


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
    # exact-count tripwire: the punct-scope fix landed at 2866 (the 1101
    # blind-spot table byte-identical + 1765 punct pairs), and the prose
    # claims it exactly (README Spacing/Kerning sections, kern_axis.py
    # docstring, macro_bootstrap.py header; monolith-spac.html's spans
    # regenerate via scripts/extract_html_kern.py). If you retune the
    # metric, update the count in all five places together (this test +
    # the four prose places).
    assert len(K.KERN_PAIRS) == 2866
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


INKED = (
    "ampersand",
    "at",
    "backslash",
    "bar",
    "braceleft",
    "braceright",
    "bracketleft",
    "bracketright",
    "colon",
    "comma",
    "dollar",
    "exclam",
    "greater",
    "less",
    "numbersign",
    "parenleft",
    "parenright",
    "percent",
    "period",
    "question",
    "semicolon",
    "slash",
    "underscore",
)


def test_band_blind_set_is_exactly_the_eleven() -> None:
    # TODO.org "Metric blind spots": these 11 glyphs have no ink in the
    # baseline band and kern via the shared-ink-span fallback.
    blind = tuple(n for n in sorted(DES) if n != "space" and not K._has_band_ink(n))
    assert blind == BLIND
    assert all(not K._has_band_ink(n) for n in BLIND)
    assert all(K._has_band_ink(n) for n in K.BASE)
    assert all(K._has_band_ink(n) for n in INKED)


def test_punct_scope_covers_every_non_space_glyph() -> None:
    # TODO.org "Missing: all punctuation/symbols (34 glyphs, 0 pairs today)":
    # the scope decision — kern everything except space; the metric, not the
    # glyph list, decides which pairs get values.
    assert K.KERNABLE == tuple(n for n in sorted(DES) if n != "space")
    assert all(n in K.KERNABLE for n in INKED)
    assert "space" not in K.KERNABLE


def test_punct_pairs_match_the_review() -> None:
    # the seams the kern review shaped and found dead (TODO.org bullet 2);
    # values probe-verified against the unchanged metric on f6fe511
    assert K.kern_for("H", "question") == -160
    assert K.kern_for("question", "H") == -100
    assert K.kern_for("H", "slash") == -80
    assert K.kern_for("slash", "H") == -160
    assert K.kern_for("H", "backslash") == -160
    assert K.kern_for("backslash", "H") == -80
    assert K.kern_for("H", "parenleft") == -160
    assert K.kern_for("parenleft", "H") == -40
    assert K.kern_for("H", "parenright") == -40
    assert K.kern_for("parenright", "H") == -160
    assert K.kern_for("V", "period") == -160
    assert K.kern_for("period", "V") == -160
    assert K.kern_for("H", "less") == -160
    assert K.kern_for("less", "H") == -60
    assert K.kern_for("H", "greater") == -160
    assert K.kern_for("greater", "H") == -160
    assert K.kern_for("H", "numbersign") == -100
    assert K.kern_for("numbersign", "H") == -40
    assert K.kern_for("H", "percent") == -110


def test_punct_absent_when_already_fused() -> None:
    # "correctly absent (gap -30, do not blanket-add)" (TODO.org bullet 3):
    # baseline-sitting marks after a solid stem stay fused, and percent+H's
    # seam pull is below MIN_PULL — the rule must not blanket-add
    assert K.kern_for("H", "period") == 0
    assert K.kern_for("H", "comma") == 0
    assert K.kern_for("H", "colon") == 0
    assert K.kern_for("H", "exclam") == 0
    assert K.kern_for("percent", "H") == 0


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


# Smoke pins for the pre-punct table (the 486 letter pairs and the 615
# band-blind pairs). Value drift with an UNCHANGED pair count would slip past
# both the count tripwire in test_table_invariants and the source-mirror
# equality in test_glyphs_source.py, so these representative pairs pin every
# distinct value the metric produced for the old table, in both directions.
# A deliberate retune that moves one must update it here consciously.
PRIOR_VALUE_PINS: dict[tuple[str, str], int] = {
    # letters + digits (the 486-pair era)
    ("A", "W"): -60,  # W as right: the smallest kept pull family
    ("W", "A"): -60,
    ("H", "W"): -60,
    ("W", "W"): -120,
    ("B", "J"): -120,
    ("W", "one"): -150,
    ("W", "J"): -160,
    ("A", "T"): -160,
    ("A", "five"): -160,
    ("seven", "T"): -160,
    # band-blind symbols read in their own ink span (the 1101-pair era)
    ("A", "equal"): -60,
    ("grave", "asciitilde"): -60,
    ("Z", "quotesingle"): -70,
    ("V", "quotedbl"): -80,
    ("hyphen", "one"): -90,
    ("W", "equal"): -100,
    ("K", "quotedbl"): -110,
    ("V", "hyphen"): -110,
    ("emdash", "V"): -110,
    ("asciicircum", "equal"): -110,
    ("equal", "equal"): -120,
    ("Q", "equal"): -130,
    ("X", "hyphen"): -130,
    ("R", "hyphen"): -140,
    ("asterisk", "A"): -140,
    ("equal", "one"): -150,
}


def test_prior_values_smoke_pins() -> None:
    for pair, want in PRIOR_VALUE_PINS.items():
        assert K.KERN_PAIRS.get(pair) == want, (pair, K.KERN_PAIRS.get(pair), want)
