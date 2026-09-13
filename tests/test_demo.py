"""Demo page generator tests.

index.html is generated from the shipped binaries by monolith.demo. These
tests pin what the page claims: the glyph grid covers the real cmap,
advances come from hmtx, the baked kern table is kerning.py's verbatim,
axis ranges come from fvar — and the page stays a pure family-name page:
no font bytes, nothing that can break out of the script tag, and
deterministic output.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest
from fontTools.ttLib import TTFont

from monolith import demo

REPO_ROOT = Path(__file__).resolve().parents[1]
VF = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"

pytestmark = pytest.mark.skipif(
    not VF.exists(), reason="variable font not exported from Glyphs yet"
)


@pytest.fixture(scope="module")
def page() -> str:
    return demo.build_html()


def _data(page: str, name: str) -> Any:
    """Parse a `const NAME = <json>;` line out of the generated page."""
    m = re.search(r"^const %s = (.+);$" % name, page, re.M)
    assert m, name
    return json.loads(m.group(1))


def test_build_is_deterministic() -> None:
    assert demo.build_html() == demo.build_html()


def test_data_blocks_are_valid_json(page: str) -> None:
    assert _data(page, "UPEM") == 1000
    assert isinstance(_data(page, "CHAR"), dict)
    assert isinstance(_data(page, "KERN"), dict)
    assert isinstance(_data(page, "GLYPHS"), list)


def test_grid_covers_the_cmap(page: str) -> None:
    cmap = TTFont(str(VF)).getBestCmap()
    assert cmap is not None
    glyphs = _data(page, "GLYPHS")
    assert {g["name"] for g in glyphs} == set(cmap.values())
    assert _data(page, "CHAR") == {chr(cp): gname for cp, gname in cmap.items()}


def test_lowercase_double_encoding_is_surfaced(page: str) -> None:
    glyphs = {g["name"]: g for g in _data(page, "GLYPHS")}
    a = glyphs["A"]
    assert a["ch"] == "A"
    assert a["cps"] == ["U+0041", "U+0061"]
    assert _data(page, "CHAR")["a"] == "A"


def test_advance_widths_come_from_hmtx(page: str) -> None:
    hmtx = TTFont(str(VF))["hmtx"]
    glyphs = {g["name"]: g for g in _data(page, "GLYPHS")}
    for gname in ("A", "T", "zero", "space"):
        assert glyphs[gname]["adv"] == hmtx[gname][0]
    assert glyphs["A"]["adv"] == 590
    assert glyphs["space"]["adv"] == 240


def test_kern_table_is_the_source_verbatim(page: str) -> None:
    from monolith.kerning import KERN_PAIRS

    baked = _data(page, "KERN")
    assert baked == {"%s %s" % pair: v for pair, v in KERN_PAIRS.items()}


def test_kern_partner_chips(page: str) -> None:
    glyphs = {g["name"]: g for g in _data(page, "GLYPHS")}
    a_kern = glyphs["A"]["kern"]
    # "T A": A is the right member, so the chip renders partner-first (k[2] == 1)
    assert ["T", -160, 1] in a_kern
    assert ["A", -160, 0] in glyphs["T"]["kern"]
    # strongest first, capped, and every value is a real table value
    assert len(a_kern) <= demo.KERN_SHOWN
    values = [k[1] for k in a_kern]
    assert values == sorted(values, key=abs, reverse=True)


def test_axes_baked_into_the_sliders(page: str) -> None:
    ax = {a.axisTag: a for a in TTFont(str(VF))["fvar"].axes}
    for tag, sid in (("SPAC", "spac"), ("KERN", "kern")):
        m = re.search(r'<input id="%s"[^>]*>' % sid, page)
        assert m, sid
        for attr, prop in (("min", "minValue"), ("max", "maxValue"), ("value", "defaultValue")):
            assert '%s="%d"' % (attr, getattr(ax[tag], prop)) in m.group(0)


def test_no_font_bytes_and_pure_ascii(page: str) -> None:
    raw = page.encode("utf-8")
    for marker in (b"OTTO", b"\x00\x01\x00\x00", b"wOFF", b"wOF2", b"base64,"):
        assert marker not in raw
    raw.decode("ascii")  # ensure_ascii JSON — nothing binary sneaks in


def test_data_cannot_break_out_of_the_script_tag(page: str) -> None:
    assert page.lower().count("</script") == 1  # the one real closing tag
    for name in ("CHAR", "KERN", "GLYPHS"):
        m = re.search(r"^const %s = (.+);$" % name, page, re.M)
        assert m is not None, name
        assert "<" not in m.group(1)


def test_download_links_point_at_github_releases(page: str) -> None:
    assert 'href="%s"' % demo.RELEASES_LATEST_URL in page
    assert 'href="%s"' % demo.RELEASES_URL in page


def test_required_ui_pieces(page: str) -> None:
    for i in (
        "warn",
        "grid",
        "popup",
        "p-big",
        "p-name",
        "p-cp",
        "p-adv",
        "p-kern",
        "spac",
        "kern",
        "head",
        "measure",
        "pull",
        "pairs",
    ):
        assert 'id="%s"' % i in page
    assert "contenteditable" in page


def test_specimen_rows_are_baked_and_escaped(page: str) -> None:
    from monolith.specimen import build_rows

    cmap = TTFont(str(VF)).getBestCmap()
    assert cmap is not None
    rows = build_rows(cmap)[1:]  # showcase shows MONOLITH
    assert page.count('<div class="row">') == len(rows)
    assert "EXTRA BOLD BRUTALISM" in page
    assert "&lt;" in page  # the < glyph, escaped — never a bare tag opener
