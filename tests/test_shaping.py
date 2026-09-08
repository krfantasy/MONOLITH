"""End-to-end shaping checks: a real shaper must apply SPAC + kern.

These guard the two layout features where a structurally-valid table could
still be silently ignored (wrong script/langsys, feature never wired up):
HarfBuzz is the reference for what text engines will actually do.
"""

from pathlib import Path

import pytest
import uharfbuzz as hb

from monolith import variable

REPO_ROOT = Path(__file__).resolve().parents[1]
FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"

pytestmark = pytest.mark.skipif(not FONT.exists(), reason="static TTF not built")


@pytest.fixture(scope="module")
def vf_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return variable.build_variable(FONT, tmp_path_factory.mktemp("hb") / "MONOLITH-Variable.ttf")


def _shaped_positions(font_path: Path, text: str, spac: int | None = None) -> list[int]:
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    font = hb.Font(face)
    if spac is not None:
        font.set_variations({"SPAC": spac})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    return [pos.x_advance for pos in buf.glyph_positions]


def test_kern_shifts_AV_in_real_shaping(vf_path: Path) -> None:
    av = _shaped_positions(vf_path, "AV")
    hh = _shaped_positions(vf_path, "HH")
    # the -160 kern lands on one of the two advances (Value1 -> first glyph);
    # the line total is what layout sees
    assert sum(av) == sum(hh) - 160
    assert sorted(av) == [430, 590]


def test_kern_and_spac_compose(vf_path: Path) -> None:
    at65 = _shaped_positions(vf_path, "AV", spac=65)
    plain65 = _shaped_positions(vf_path, "HH", spac=65)
    assert sum(at65) == sum(plain65) - 160
    assert plain65 == [655, 655]  # SPAC 65 added to every advance


def test_solid_pair_unaffected(vf_path: Path) -> None:
    assert _shaped_positions(vf_path, "HH") == [590, 590]
