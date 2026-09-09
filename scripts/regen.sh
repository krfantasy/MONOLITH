#!/bin/bash
# Full MONOLITH regeneration in one command (macOS with Glyphs 4 required).
#
# Usage (from anywhere inside the checkout):
#   export GLYPHS_PYTHON_FW=/opt/homebrew/Frameworks/Python.framework/Versions/3.14/Python
#   scripts/regen.sh
#
# The export is only needed once per terminal, and only if Glyphs Settings
# has no Python framework configured. Stages below fail fast: the first
# failing command stops the script with its exit code.
set -euo pipefail

cd "$(dirname "$0")/.."

say() { printf '\n=== %s ===\n' "$1"; }

say "1/5 sync tooling"
uv sync --group glyphs

say "2/5 rebuild MONOLITH.glyphs"
scripts/glyphs-run.sh run --app 4 scripts/rebuild_cli.py --input MONOLITH.glyphs

say "3/5 export ExtraBold statics"
scripts/glyphs-run.sh run --app 4 -c 'st = next(i for i in Glyphs.font.instances if i.name == "ExtraBold"); st.generate("TTF", "fonts/MONOLITH-ExtraBold.ttf"); st.generate("OTF", "fonts/MONOLITH-ExtraBold.otf"); print("statics exported (unkerned)")' --input MONOLITH.glyphs

say "4/5 finish variable font"
uv run python -m monolith.variable
uv run python -m monolith.kern_axis

say "5/5 verify"
uv run pytest -q
uv run ruff check .

say "REGEN COMPLETE"
