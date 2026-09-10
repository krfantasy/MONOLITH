"""End-to-end shaping checks: a real shaper must apply SPAC + the KERN axis.

These guard the two layout features where a structurally-valid table could
still be silently ignored (wrong script/langsys, feature never wired up):
HarfBuzz is the reference for what text engines will actually do.

Contract: everything ships UNKERNED by default — the statics have no kern
at all, the variable font's kern lives behind the KERN axis (default 0).
"""

from pathlib import Path

import pytest
import uharfbuzz as hb

REPO_ROOT = Path(__file__).resolve().parents[1]
FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"
VF = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"

pytestmark = pytest.mark.skipif(
    not (FONT.exists() and VF.exists()), reason="fonts not exported from Glyphs yet"
)

AV_KERN = 160  # the seam-metric kern for A/V, applied at KERN=100


@pytest.fixture(scope="module")
def vf_path() -> Path:
    return VF


def _shaped_positions(
    font_path: Path,
    text: str,
    spac: int | None = None,
    kern: int | None = None,
) -> list[int]:
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    font = hb.Font(face)
    variations: dict[str, float] = {}
    if spac is not None:
        variations["SPAC"] = spac
    if kern is not None:
        variations["KERN"] = kern
    if variations:
        font.set_variations(variations)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    return [pos.x_advance for pos in buf.glyph_positions]


def test_static_ships_kern_free() -> None:
    from fontTools.ttLib import TTFont

    ft = TTFont(str(FONT))
    gpos = ft.get("GPOS")
    tags = sorted({fr.FeatureTag for fr in gpos.table.FeatureList.FeatureRecord}) if gpos else []
    assert tags == [], "statics are the unkerned block cut"
    assert sum(_shaped_positions(FONT, "AV")) == 1180  # 590 + 590, no kern


def test_vf_default_is_kern_free(vf_path: Path) -> None:
    # KERN axis default 0: the variable font renders the block look too
    assert _shaped_positions(vf_path, "AV") == [590, 590]


def test_kern_axis_100_kerns_AV(vf_path: Path) -> None:
    av = _shaped_positions(vf_path, "AV", kern=100)
    hh = _shaped_positions(vf_path, "HH", kern=100)
    # the -160 kern lands on one of the two advances (Value1 -> first glyph);
    # the line total is what layout sees
    assert sum(av) == sum(hh) - AV_KERN
    assert sorted(av) == [430, 590]


def test_kern_axis_interpolates(vf_path: Path) -> None:
    full = sum(_shaped_positions(vf_path, "AV", kern=100))
    base = sum(_shaped_positions(vf_path, "AV", kern=0))
    for kern, want_delta in ((25, -40), (50, -80), (75, -120)):
        got = sum(_shaped_positions(vf_path, "AV", kern=kern))
        assert got == base + (full - base) * kern // 100, kern


def test_kern_and_spac_compose(vf_path: Path) -> None:
    kerned65 = _shaped_positions(vf_path, "AV", spac=65, kern=100)
    plain65 = _shaped_positions(vf_path, "HH", spac=65, kern=100)
    assert sum(kerned65) == sum(plain65) - AV_KERN
    assert plain65 == [655, 655]  # SPAC 65 added to every advance


def test_solid_pair_unaffected(vf_path: Path) -> None:
    assert _shaped_positions(vf_path, "HH", kern=100) == [590, 590]


def test_lowercase_shapes_as_caps(vf_path: Path) -> None:
    assert _shaped_positions(vf_path, "a") == _shaped_positions(vf_path, "A")
    assert _shaped_positions(vf_path, "av", kern=100) == _shaped_positions(vf_path, "AV", kern=100)


def test_kern_axis_kerns_blind_symbols(vf_path: Path) -> None:
    # Metric blind spots: hyphen/plus/equal/quotedbl have no baseline-band
    # ink; their pairs read in the symbol's own band (T+hyphen gap 150 ->
    # capped -160). "T-T" kerns BOTH seams via the hyphen; in "T-H" the
    # trailing H fuses the hyphen (gap -30, no pair) so only seam 1 kerns.
    assert _shaped_positions(vf_path, "T-H", kern=0) == [590, 370, 590]
    assert _shaped_positions(vf_path, "T-H", kern=100) == [430, 370, 590]
    assert _shaped_positions(vf_path, "T-T", kern=100) == [430, 210, 590]
    assert _shaped_positions(vf_path, "T+", kern=100) == [430, 590]
    assert _shaped_positions(vf_path, "V=", kern=100) == [430, 590]
    assert _shaped_positions(vf_path, 'T"', kern=100) == [430, 370]
