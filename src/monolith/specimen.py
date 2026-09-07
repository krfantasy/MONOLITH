"""Render the MONOLITH specimen PNGs (tight + loose ss01) from the exported TTF."""
from collections.abc import Callable, Sequence
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw

from monolith.design import Point

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FONT = REPO_ROOT / "fonts" / "MONOLITH-ExtraBold.ttf"
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
        font = TTFont(str(font_path))
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self._cache: dict[str | None, list[list[Point]]] = {}

    def contours(self, gname: str | None) -> list[list[Point]]:
        if gname in self._cache:
            return self._cache[gname]
        pen = RecordingPen()
        if gname is not None and gname in self.gs:
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

    def render(self, showcase: str, rows: Sequence[str],
               resolver: Callable[["SpecimenRenderer", str], str | None],
               space_adv: float, show_scale: float, scale: float,
               show_track: float, track: float, out: str | Path) -> None:
        """resolver(renderer, ch) -> glyph name; spaces advance by space_adv."""
        gs = self.gs

        def gname_of(ch: str) -> str | None:
            return None if ch == " " else resolver(self, ch)

        def adv(gname: str | None) -> float:
            return gs[gname].width if gname in gs else 600

        def line_extent(text: str, sc: float, tr: float) -> float:
            w = 0
            for ch in text:
                w += (space_adv if ch == " " else adv(gname_of(ch))) * sc + tr
            return w - (tr if text else 0)

        margin = 50
        line_h = int(700 * scale) + 70
        show_line_h = int(700 * show_scale) + 90
        W = int(max([line_extent(s, show_scale, show_track) for s in showcase] +
                    [line_extent(r, scale, track) for r in rows])) + 2 * margin
        H = margin + show_line_h + len(rows) * line_h + margin

        img = Image.new("RGB", (W, H), BG)
        mask = Image.new("L", (W, H), 0)

        def draw_line(text: str, x: float, y_base: float, sc: float, tr: float) -> float:
            for ch in text:
                if ch == " ":
                    x += space_adv * sc + tr
                    continue
                gname = resolver(self, ch)
                if gname is None:
                    continue
                cs = self.contours(gname)
                if cs:
                    # ink vs hole by winding: holes wind opposite to the body
                    areas = [signed_area(c) for c in cs]
                    body = max(range(len(cs)), key=lambda i: abs(areas[i]))
                    tmp = Image.new("L", (W, H), 0)
                    td = ImageDraw.Draw(tmp)
                    for i, c in enumerate(cs):
                        td.polygon([(x + p[0] * sc, y_base - p[1] * sc) for p in c],
                                   fill=0 if (areas[i] < 0) != (areas[body] < 0) else 255)
                    mask.paste(ImageChops.lighter(mask.crop((0, 0, W, H)), tmp), (0, 0))
                x += adv(gname) * sc + tr
            return x

        y = margin + int(700 * show_scale)
        x = margin
        for ch in showcase:
            x = draw_line(ch, x, y, show_scale, show_track) + show_track + 40

        y = margin + show_line_h + int(700 * scale)
        for row in rows:
            draw_line(row, margin, y, scale, track)
            y += line_h

        img.paste(FG, (0, 0), mask)
        img.save(str(out))
        print("saved", out, img.size)


def tight(r: SpecimenRenderer, ch: str) -> str | None:
    return r.cmap.get(ord(ch))


def spaced(r: SpecimenRenderer, ch: str) -> str | None:
    n = r.cmap.get(ord(ch))
    return (n + ".spaced") if n and (n + ".spaced") in r.gs else n


def build_rows(cmap: dict[int, str]) -> list[str]:
    # every non-alphanumeric, non-space character the font maps
    PUNCT = "".join(chr(c) for c in sorted(cmap) if c >= 33 and not chr(c).isalnum())
    PUNCT_ROWS = [PUNCT[i:i + 12] for i in range(0, len(PUNCT), 12)]
    return ["MONOLITH",
            "EXTRA BOLD BRUTALISM",
            "ABCDEFGHIJ",
            "KLMNOPQRS",
            "TUVWXYZ",
            "0123456789"] + PUNCT_ROWS


def main(font_path: str | Path | None = None,
         out_dir: str | Path | None = None) -> None:
    font_path = Path(font_path) if font_path else DEFAULT_FONT
    out_dir = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
    if not font_path.exists():
        raise SystemExit(f"font not found: {font_path}\n"
                         "Export MONOLITH-ExtraBold.ttf from Glyphs first (see README).")
    r = SpecimenRenderer(font_path)
    rows = build_rows(r.cmap)
    out_dir.mkdir(parents=True, exist_ok=True)
    # tight variant: font's default tight advances, extra negative tracking
    r.render(SHOWCASE, rows, tight, 240, 0.34, 0.22, 140, -40,
             out_dir / "specimen.png")
    # spaced variant: .spaced alternates (+130 advance), no extra tracking
    r.render(SHOWCASE, rows, spaced, 240 + 130, 0.34, 0.22, 140, 0,
             out_dir / "specimen-spaced.png")
