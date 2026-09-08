"""Specimen renderer smoke test. Skips when the font hasn't been exported.

The renderer shapes with HarfBuzz, so these also pin the layout contract:
a rendered line's spacing comes from the binary (advances, the KERN axis,
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

    The static is the unkerned block cut, so both static renders are equal
    width. Kerning comes from the VF's KERN axis: at KERN=100 the AV render
    is ~35 px narrower than at the default, and the shaped run width must
    equal the sum of HarfBuzz advances.
    """
    if not FONT.exists():
        pytest.skip("font not built yet (export from Glyphs first)")
    if not VF.exists():
        pytest.skip("variable font not exported from Glyphs yet")
    from monolith.specimen import SpecimenRenderer

    r = SpecimenRenderer(FONT)
    out_a = tmp_path / "a.png"
    r.render("AV", ["AV"], 0.22, 0.22, out_a)
    shaped = r.shape("AV")
    assert sum(a for _, a, _, _ in shaped) == 1180  # 590 + 590, unkerned

    rv = SpecimenRenderer(VF)
    out_kerned = tmp_path / "kerned.png"
    rv.render("AV", ["AV"], 0.22, 0.22, out_kerned, variations={"KERN": 100})
    delta = Image.open(out_a).size[0] - Image.open(out_kerned).size[0]
    assert delta in (35, 36)  # 160 units at scale 0.22
    shaped = rv.shape("AV", variations={"KERN": 100})
    assert sum(a for _, a, _, _ in shaped) == 1020  # 590 + 590 - 160


def test_render_axis_ramps(tmp_path: Path) -> None:
    """The ramp sheets render one labeled row per 10-unit step."""
    if not VF.exists():
        pytest.skip("variable font not exported from Glyphs yet")
    from monolith.specimen import SpecimenRenderer

    r = SpecimenRenderer(VF)
    kern_ramp = tmp_path / "kern-ramp.png"
    spac_ramp = tmp_path / "spac-ramp.png"
    r.render_ramp("WAVE AVATAR TROUGH", "KERN", range(0, 101, 10), 0.22, 0.05, kern_ramp)
    r.render_ramp("MONOLITH", "SPAC", range(0, 131, 10), 0.22, 0.05, spac_ramp)
    assert kern_ramp.exists() and kern_ramp.stat().st_size > 0
    assert spac_ramp.exists() and spac_ramp.stat().st_size > 0
    # the SPAC ramp really spans the axis: 8 glyphs x 130 units end to end
    w0 = sum(a for _, a, _, _ in r.shape("MONOLITH", variations={"SPAC": 0}))
    w130 = sum(a for _, a, _, _ in r.shape("MONOLITH", variations={"SPAC": 130}))
    assert w130 - w0 == 130 * 8
