#!/bin/bash
# Headless `glyphs` runner for this repo (run from the repo root).
#
# Forwards everything to `glyphs-cli` (via the `glyphs` uv group) with two
# quality-of-life fixes for headless runs on macOS:
#
# 1. Auto-injects `--python` from $GLYPHS_PYTHON_FW when the caller didn't
#    pass one (this Mac's Glyphs has no framework configured; Macs that do
#    can leave the variable unset and rely on Glyphs Settings).
# 2. Filters Glyphs' Bugsnag telemetry spam — hundreds of identical,
#    harmless stderr lines the headless engine emits — while preserving
#    every other output line and the real exit code.
#
# Usage:
#   export GLYPHS_PYTHON_FW=/opt/homebrew/Frameworks/Python.framework/Versions/3.14/Python
#   scripts/glyphs-run.sh run --app 4 scripts/rebuild_cli.py --input MONOLITH.glyphs

fw="${GLYPHS_PYTHON_FW:-}"
if [ -n "$fw" ] && [ ! -e "$fw" ]; then
  echo "glyphs-run: warning: GLYPHS_PYTHON_FW=$fw does not exist; ignoring" >&2
  fw=""
fi

have_python=0
for a in "$@"; do
  if [ "$a" = "--python" ]; then
    have_python=1
    break
  fi
done

# NOTE: `--python` is a *subcommand* option (`glyphs run --python ...`), not a
# global one, so it is inserted after the subcommand, never at the front.
if [ "$have_python" -eq 0 ] && [ -n "$fw" ] && [ "$#" -gt 0 ]; then
  first="$1"
  shift
  set -- "$first" --python "$fw" "$@"
fi

out=$(uv run --group glyphs -- glyphs "$@" 2>&1)
rc=$?
printf '%s\n' "$out" | grep -v "Bugsnag" || true
exit "$rc"
