"""The tracked Glyphs source: masters/instances must stay VF-exportable.

Glyphs derives the exported fvar axis range from "Axis Location" custom
parameters when any are present, instead of from the masters' design
coordinates. Glyphs 4.1 materializes them with Location = 0, which
collapses the Spacing axis to a 0-0 range and makes VF export fail with
"Invalid axis range for axis: Spacing". build.strip_axis_locations
removes them before saving; these tests keep the committed file honest
between regenerations. For this font design space == user space, so NO
Axis Location parameter is ever legitimate — the range must come from
the masters' axesValues alone.
"""

import plistlib
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "MONOLITH.glyphs"

pytestmark = [
    pytest.mark.skipif(not SOURCE.exists(), reason="MONOLITH.glyphs not present"),
    pytest.mark.skipif(shutil.which("plutil") is None, reason="plutil not available"),
]


@pytest.fixture(scope="module")
def font() -> dict:
    # .glyphs is an OpenStep plist; plistlib only reads XML/binary
    xml = subprocess.run(
        ["plutil", "-convert", "xml1", "-o", "-", str(SOURCE)],
        check=True,
        capture_output=True,
    ).stdout
    return plistlib.loads(xml)


def test_no_axis_location_parameters(font: dict) -> None:
    for kind in ("fontMaster", "instances"):
        for obj in font.get(kind, []):
            params = obj.get("customParameters", [])
            names = [p.get("name") for p in params]
            assert "Axis Location" not in names, (kind, obj.get("name"), names)


def test_master_locations_span_the_spac_axis(font: dict) -> None:
    values = sorted(int(v) for m in font["fontMaster"] for v in m["axesValues"])
    assert values == [0, 130]


def test_caps_carry_double_unicodes(font: dict) -> None:
    glyphs = {g["glyphname"]: g for g in font.get("glyphs", [])}
    assert "a" not in glyphs
    assert "a.spaced" not in glyphs
    a = glyphs["A"]
    # Glyphs writes double-encodings under the SINGULAR `unicode` key
    # holding an array (`unicode = (65, 97);`); single-encoded glyphs keep
    # a plain string. Normalize to a list either way.
    raw = a.get("unicodes", a.get("unicode"))
    unicodes = list(raw) if isinstance(raw, (list, tuple)) else ([raw] if raw else [])
    values: set[int] = set()
    for u in unicodes:
        s = str(u)
        values.add(int(s))
        try:
            values.add(int(s, 16))
        except ValueError:
            pass
    assert {65, 97} <= values
