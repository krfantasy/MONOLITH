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
    args = ap.parse_args(argv)
    specimen.main(font_path=args.font, out_dir=args.out)


if __name__ == "__main__":
    main()
