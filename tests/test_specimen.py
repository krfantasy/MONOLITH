"""Specimen renderer smoke test. Skips when the font hasn't been exported."""

from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"


def test_render_one_row(tmp_path: Path) -> None:
    if not FONT.exists():
        pytest.skip("font not built yet (export from Glyphs first)")
    from monolith.specimen import SpecimenRenderer, tight

    r = SpecimenRenderer(FONT)
    out = tmp_path / "tiny.png"
    r.render("Q", ["QDA", "0123"], tight, 240, 0.34, 0.22, 140, -40, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_render_spac_row(tmp_path: Path) -> None:
    if not FONT.exists():
        pytest.skip("font not built yet (export from Glyphs first)")
    from monolith import variable
    from monolith.specimen import SpecimenRenderer, tight

    vf = variable.build_variable(FONT, tmp_path / "vf.ttf")
    inst = variable.instance_at_spac(vf, 30)
    r = SpecimenRenderer(vf, font=inst)
    out = tmp_path / "tiny30.png"
    r.render("Q", ["QDA"], tight, inst["hmtx"]["space"][0], 0.34, 0.22, 140, 0, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_kerns_narrow_rendered_lines(tmp_path: Path) -> None:
    if not FONT.exists():
        pytest.skip("font not built yet (export from Glyphs first)")
    from monolith.specimen import SpecimenRenderer, tight

    r = SpecimenRenderer(FONT)
    out_plain = tmp_path / "plain.png"
    out_kern = tmp_path / "kern.png"
    r.render("AV", ["AV"], tight, 240, 0.22, 0.22, 0, 0, out_plain)
    r.render("AV", ["AV"], tight, 240, 0.22, 0.22, 0, 0, out_kern, kerns=True)
    # AV kerns -160 units; at scale 0.22 the canvas shrinks by ~35 px
    delta = Image.open(out_plain).size[0] - Image.open(out_kern).size[0]
    assert delta in (35, 36)
