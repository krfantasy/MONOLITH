"""monolith-variable command line entry point."""

import argparse

from monolith import variable


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="monolith-variable",
        description="Build MONOLITH-Variable.ttf (SPAC axis) from the exported static TTF.",
    )
    ap.add_argument(
        "--font", default=None, help="path to MONOLITH-ExtraBold.ttf (default: <repo>/fonts/)"
    )
    ap.add_argument(
        "--out", default=None, help="output path (default: <repo>/fonts/MONOLITH-Variable.ttf)"
    )
    args = ap.parse_args(argv)
    out = variable.build_variable(args.font, args.out)
    print("saved", out)


if __name__ == "__main__":
    main()
