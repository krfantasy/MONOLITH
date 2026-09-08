"""monolith-specimen command line entry point."""
import argparse

from monolith import specimen


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="monolith-specimen",
        description="Render MONOLITH specimen PNGs from the exported TTF.")
    ap.add_argument("--font", default=None,
                    help="path to MONOLITH-ExtraBold.ttf (default: <repo>/fonts/)")
    ap.add_argument("--out", default=None,
                    help="output directory (default: <repo>/specimens/)")
    ap.add_argument("--spac", type=int, default=None, metavar="0-130",
                    help="render an extra specimen from the variable font at this SPAC value")
    ap.add_argument("--variable-font", default=None,
                    help="path to MONOLITH-Variable.ttf (default: <repo>/fonts/)")
    args = ap.parse_args(argv)
    specimen.main(font_path=args.font, out_dir=args.out, spac=args.spac,
                  variable_font_path=args.variable_font)


if __name__ == "__main__":
    main()
