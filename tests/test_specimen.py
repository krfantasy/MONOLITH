"""Specimen renderer smoke test. Skips when the font hasn't been exported."""
from pathlib import Path

import pytest

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
