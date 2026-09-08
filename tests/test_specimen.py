"""Specimen renderer smoke test. Skips when the font hasn't been exported.

The renderer shapes with HarfBuzz, so these also pin the layout contract:
a rendered line's spacing comes from the binary (advances + GPOS kern +
features), never from hand-rolled math.
"""

from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"
VF = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"


def test_render_one_row(tmp_path: Path) -> None:
    if not FONT.exists():
        pytest.skip("font not built yet (export from Glyphs first)")
    from monolith.specimen import SpecimenRenderer

    r = SpecimenRenderer(FONT)
    out = tmp_path / "tiny.png"
    r.render("Q", ["QDA", "0123"], 0.22, 0.22, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_render_spac_row(tmp_path: Path) -> None:
    if not FONT.exists():
        pytest.skip("font not built yet (export from Glyphs first)")
    if not VF.exists():
        pytest.skip("variable font not exported from Glyphs yet")
    from monolith.specimen import SpecimenRenderer

    r = SpecimenRenderer(VF)
    out = tmp_path / "tiny30.png"
    r.render("Q", ["QDA"], 0.22, 0.22, out, variations={"SPAC": 30})
    assert out.exists()
    assert out.stat().st_size > 0


def test_layout_is_shaper_truth(tmp_path: Path) -> None:
    """Kern on/off must change the canvas by exactly the GPOS delta.

    AV kerns -160 units; at scale 0.22 the kerned render is ~35 px narrower,
    and the shaped run width must equal the sum of HarfBuzz advances.
    """
    if not FONT.exists():
        pytest.skip("font not built yet (export from Glyphs first)")
    from monolith.specimen import SpecimenRenderer

    r = SpecimenRenderer(FONT)
    out_on = tmp_path / "on.png"
    out_off = tmp_path / "off.png"
    r.render("AV", ["AV"], 0.22, 0.22, out_on)
    r.render("AV", ["AV"], 0.22, 0.22, out_off, features={"kern": False})
    delta = Image.open(out_off).size[0] - Image.open(out_on).size[0]
    assert delta in (35, 36)
    # the renderer's own shaping agrees with the binary's metrics
    shaped = r.shape("AV")
    assert sum(a for _, a, _, _ in shaped) == 1020  # 590 + 590 - 160
