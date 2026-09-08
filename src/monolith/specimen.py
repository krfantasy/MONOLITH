"""Render the MONOLITH specimen PNGs from the exported binaries.

Layout is HarfBuzz shaping — the same class of engine browsers and
layout apps run — so the PNGs show the font's real spacing: default
advances with GPOS kern for the shipped look, ss01 substitution for the
loose look, SPAC variations for the variable renders. No advance,
kern, or tracking math is done here; if it isn't in the binary, it
isn't in the PNG.
"""

from collections.abc import Sequence
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw

from monolith.design import Point

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"
DEFAULT_VARIABLE_FONT = REPO_ROOT / "fonts" / "MONOLITH-Variable.ttf"
DEFAULT_OUT_DIR = REPO_ROOT / "specimens"

BG = "#161616"
FG = "#e8e4da"
SHOWCASE = "QDAO"


def signed_area(c: Sequence[Point]) -> float:
    s = 0
    for i in range(len(c)):
        x0, y0 = c[i]
        x1, y1 = c[(i + 1) % len(c)]
        s += x0 * y1 - x1 * y0
    return s / 2


class SpecimenRenderer:
    def __init__(self, font_path: str | Path) -> None:
        self.font_path = Path(font_path)
        font = TTFont(str(font_path))
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.order = font.getGlyphOrder()
        self._cache: dict[str, list[list[Point]]] = {}

    def contours(self, gname: str) -> list[list[Point]]:
        if gname in self._cache:
            return self._cache[gname]
        pen = RecordingPen()
        self.gs[gname].draw(pen)
        cs, cur = [], []
        for op, args in pen.value:
            pts = [(a[0], a[1]) for a in args]
            if op == "moveTo":
                cur = pts
            elif op in ("lineTo", "qCurveTo", "curveTo"):
                cur.extend(pts)
            elif op == "closePath":
                cs.append(cur)
        self._cache[gname] = cs
        return cs

    def shape(
        self,
        text: str,
        features: dict[str, bool] | None = None,
        variations: dict[str, float] | None = None,
    ) -> list[tuple[str, float, float, float]]:
        """Shape text with HarfBuzz: [(glyph_name, x_advance, x_offset, y_offset)]."""
        blob = hb.Blob.from_file_path(str(self.font_path))
        face = hb.Face(blob)
        font = hb.Font(face)
        if variations:
            font.set_variations(variations)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, features)
        return [
            (self.order[info.codepoint], pos.x_advance, pos.x_offset, pos.y_offset)
            for info, pos in zip(buf.glyph_infos, buf.glyph_positions)
        ]

    def render(
        self,
        showcase: str,
        rows: Sequence[str],
        scale: float,
        show_scale: float,
        out: str | Path,
        features: dict[str, bool] | None = None,
        variations: dict[str, float] | None = None,
    ) -> None:
        """Draw every string as a shaped run; spacing is whatever the font yields."""
        margin = 50

        def run_width(text: str, sc: float) -> float:
            return sum(a for _, a, _, _ in self.shape(text, features, variations)) * sc

        line_h = int(700 * scale) + 70
        show_line_h = int(700 * show_scale) + 90
        W = (
            int(max([run_width(showcase, show_scale)] + [run_width(r, scale) for r in rows]))
            + 2 * margin
        )
        H = margin + show_line_h + len(rows) * line_h + margin

        img = Image.new("RGB", (W, H), BG)
        mask = Image.new("L", (W, H), 0)

        def draw_shaped(text: str, x: float, y_base: float, sc: float) -> float:
            for gname, adv, xo, yo in self.shape(text, features, variations):
                cs = self.contours(gname)
                if cs:
                    # ink vs hole by winding: holes wind opposite to the body
                    areas = [signed_area(c) for c in cs]
                    body = max(range(len(cs)), key=lambda i: abs(areas[i]))
                    tmp = Image.new("L", (W, H), 0)
                    td = ImageDraw.Draw(tmp)
                    for i, c in enumerate(cs):
                        td.polygon(
                            [(x + xo * sc + p[0] * sc, y_base - yo * sc - p[1] * sc) for p in c],
                            fill=0 if (areas[i] < 0) != (areas[body] < 0) else 255,
                        )
                    mask.paste(ImageChops.lighter(mask.crop((0, 0, W, H)), tmp), (0, 0))
                x += adv * sc
            return x

        y = margin + int(700 * show_scale)
        draw_shaped(showcase, margin, y, show_scale)

        y = margin + show_line_h + int(700 * scale)
        for row in rows:
            draw_shaped(row, margin, y, scale)
            y += line_h

        img.paste(FG, (0, 0), mask)
        img.save(str(out))
        print("saved", out, img.size)

    def render_ramp(
        self,
        text: str,
        axis_tag: str,
        values: Sequence[int],
        scale: float,
        label_scale: float,
        out: str | Path,
    ) -> None:
        """One labeled row per axis value: an axis as a single picture.

        Labels (e.g. "KERN 30") are shaped in MONOLITH itself at label_scale,
        at the default variations; every row's spacing comes from shaping the
        binary at {axis_tag: value}. Nothing is hand-adjusted.
        """
        margin = 50
        label_gap = 60
        runs = [(v, self.shape(text, variations={axis_tag: v})) for v in values]
        label_w = (
            max(sum(a for _, a, _, _ in self.shape(f"{axis_tag} {v}")) for v in values)
            * label_scale
        )
        row_h = int(700 * scale) + 70
        W = (
            int(max(sum(a for _, a, _, _ in run) for _, run in runs) * scale)
            + 2 * margin
            + int(label_w)
            + label_gap
        )
        H = 2 * margin + len(runs) * row_h

        img = Image.new("RGB", (W, H), BG)
        mask = Image.new("L", (W, H), 0)

        def draw_run(
            run: list[tuple[str, float, float, float]], x: float, y_base: float, sc: float
        ) -> float:
            for gname, adv, xo, yo in run:
                cs = self.contours(gname)
                if cs:
                    # ink vs hole by winding: holes wind opposite to the body
                    areas = [signed_area(c) for c in cs]
                    body = max(range(len(cs)), key=lambda i: abs(areas[i]))
                    tmp = Image.new("L", (W, H), 0)
                    td = ImageDraw.Draw(tmp)
                    for i, c in enumerate(cs):
                        td.polygon(
                            [(x + xo * sc + p[0] * sc, y_base - yo * sc - p[1] * sc) for p in c],
                            fill=0 if (areas[i] < 0) != (areas[body] < 0) else 255,
                        )
                    mask.paste(ImageChops.lighter(mask.crop((0, 0, W, H)), tmp), (0, 0))
                x += adv * sc
            return x

        for i, (v, run) in enumerate(runs):
            y_base = margin + int(700 * scale) + i * row_h
            draw_run(self.shape(f"{axis_tag} {v}"), margin, y_base, label_scale)
            draw_run(run, margin + label_w + label_gap, y_base, scale)

        img.paste(FG, (0, 0), mask)
        img.save(str(out))
        print("saved", out, img.size)


def build_rows(cmap: dict[int, str]) -> list[str]:
    # every non-alphanumeric, non-space character the font maps
    PUNCT = "".join(chr(c) for c in sorted(cmap) if c >= 33 and not chr(c).isalnum())
    PUNCT_ROWS = [PUNCT[i : i + 12] for i in range(0, len(PUNCT), 12)]
    return [
        "MONOLITH",
        "EXTRA BOLD BRUTALISM",
        "ABCDEFGHIJ",
        "KLMNOPQRS",
        "TUVWXYZ",
        "0123456789",
    ] + PUNCT_ROWS


def main(
    font_path: str | Path | None = None,
    out_dir: str | Path | None = None,
    spac: int | None = None,
    variable_font_path: str | Path | None = None,
) -> None:
    font_path = Path(font_path) if font_path else DEFAULT_FONT
    out_dir = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
    if not font_path.exists():
        raise SystemExit(
            f"font not found: {font_path}\n"
            "Export MONOLITH-ExtraBold.ttf from Glyphs first (see README)."
        )
    r = SpecimenRenderer(font_path)
    rows = build_rows(r.cmap)
    out_dir.mkdir(parents=True, exist_ok=True)
    # shipped look: default advances, exactly as apps lay it out (kern-free
    # block cut)
    r.render(SHOWCASE, rows, 0.22, 0.34, out_dir / "specimen.png")
    # loose look: ss01 — the font's own .spaced alternates and their advances
    r.render(SHOWCASE, rows, 0.22, 0.34, out_dir / "specimen-spaced.png", features={"ss01": True})
    vpath = Path(variable_font_path) if variable_font_path else DEFAULT_VARIABLE_FONT
    if not vpath.exists():
        if spac is not None:
            raise SystemExit(
                f"variable font not found: {vpath}\n"
                "Export it from Glyphs and run monolith.kern_axis (see README)"
            )
        return
    rv = SpecimenRenderer(vpath)
    if spac is not None:
        # SPAC-axis variant: the variable font shaped at `spac`
        rv.render(
            SHOWCASE,
            rows,
            0.22,
            0.34,
            out_dir / f"specimen-spac{spac}.png",
            variations={"SPAC": spac},
        )
    # kerned look: the same variable font with the KERN axis maxed
    rv.render(
        SHOWCASE,
        rows,
        0.22,
        0.34,
        out_dir / "specimen-kern100.png",
        variations={"KERN": 100},
    )
    # axis ramps: one row per 10-unit step, labeled in MONOLITH itself
    rv.render_ramp(
        "WAVE AVATAR TROUGH",
        "KERN",
        range(0, 101, 10),
        0.22,
        0.05,
        out_dir / "specimen-kern-ramp.png",
    )
    rv.render_ramp(
        "MONOLITH EXTRA BOLD 0123",
        "SPAC",
        range(0, 131, 10),
        0.22,
        0.05,
        out_dir / "specimen-spac-ramp.png",
    )
