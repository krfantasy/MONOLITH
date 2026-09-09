"""Rebuild MONOLITH.glyphs headlessly (glyphs-cli), no GUI macro needed.

Run from the repo root on a Mac with Glyphs 4.1 + the `glyphs` uv group:

    glyphs run scripts/rebuild_cli.py --input MONOLITH.glyphs

Optional `--save` writes the rebuilt source elsewhere (default: save back
to the opened document's own path, same as the GUI macro's in-place save):

    glyphs run scripts/rebuild_cli.py --input MONOLITH.glyphs -- --save /tmp/MONOLITH.glyphs

The GUI path (Window > Scripting Window + scripts/macro_bootstrap.py) keeps
working unchanged — both share only monolith.build.run. GlyphsApp/monolith
imports live inside main() so plain pytest collection never needs Glyphs.
"""

import argparse
from pathlib import Path


def resolve_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--save",
        type=Path,
        default=None,
        help="rebuilt .glyphs output (default: the opened document's own path)",
    )
    return ap.parse_args(argv)


def repo_for(save: Path | None, doc_path: str) -> Path:
    """Checkout dir: explicit --save wins, else the opened document's folder."""
    if save is not None:
        return save.resolve().parent
    if not doc_path:
        raise SystemExit(
            "no --save and the opened document has no path; save the file in Glyphs first"
        )
    return Path(doc_path).resolve().parent


def main(argv: list[str] | None = None) -> None:
    import sys

    args = resolve_args(argv)
    # Host-injected global: present when run under Glyphs / `glyphs run`,
    # absent everywhere else. globals().get keeps static checkers quiet
    # (a bare `Glyphs` reference trips reportUndefinedVariable) with
    # identical runtime semantics either way.
    host = globals().get("Glyphs")
    if host is None:
        raise SystemExit("Run via: glyphs run scripts/rebuild_cli.py --input MONOLITH.glyphs")
    font = host.font
    raw = font.filepath
    doc_path = str(raw() if callable(raw) else raw or "")
    save_path = Path(args.save) if args.save else (Path(doc_path) if doc_path else None)
    if save_path is None:
        raise SystemExit(
            "no --save and the opened document has no path; save the file in Glyphs first"
        )
    repo = repo_for(args.save, doc_path)
    sys.path.insert(0, str(repo / "src"))
    for mod in [m for m in sys.modules if m == "monolith" or m.startswith("monolith.")]:
        del sys.modules[mod]
    import monolith.build as build  # noqa: E402

    build.run(font, save_path)
    print("REBUILD DONE: %s" % save_path)


if __name__ == "__main__":
    main()
