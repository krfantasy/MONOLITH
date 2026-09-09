"""Re-extract the demo page's KERN table from the kerning source of truth.

Regenerates `const KERN` in monolith-spac.html from
src/monolith/kerning.py::KERN_PAIRS (the same table the shipped variable
font's GPOS is built from), refreshes the static pair-count spans, and maps
a-z to A-Z in `const CHAR`. Run after any kern retune or encoding change:

    uv run python scripts/extract_html_kern.py
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from monolith.kerning import KERN_PAIRS  # noqa: E402

PAGE = REPO / "monolith-spac.html"


def main() -> None:
    text = PAGE.read_text(encoding="utf-8")
    table = ", ".join('"%s %s": %d' % (lg, rg, v) for (lg, rg), v in sorted(KERN_PAIRS.items()))
    updated, n = re.subn(r"const KERN = \{.*?\};", "const KERN = {%s};" % table, text, count=1)
    assert n == 1
    text = updated
    # lowercase types as the caps (double-unicode): remap only inside
    # const CHAR (const NAME's lowercase keys are dead display entries for
    # deleted glyphs — left untouched). Keep every other CHAR entry identical.
    m = re.search(r"const CHAR = \{.*?\};", text, re.S)
    assert m
    char, n = re.subn(
        r'"([a-z])": "\1"', lambda m: '"%s": "%s"' % (m.group(1), m.group(1).upper()), m.group(0)
    )
    assert n == 26, n
    text = text[: m.start()] + char + text[m.end() :]
    text = text.replace(
        '<span id="npairs">932</span>', '<span id="npairs">%d</span>' % len(KERN_PAIRS)
    )
    text = text.replace(
        '<span id="npairs2">932</span>', '<span id="npairs2">%d</span>' % len(KERN_PAIRS)
    )
    PAGE.write_text(text, encoding="utf-8")
    print("KERN table: %d entries, CHAR a-z mapped to caps" % len(KERN_PAIRS))


if __name__ == "__main__":
    main()
