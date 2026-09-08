"""MONOLITH glyph design data - pure Python, no Glyphs dependencies.

The DSL functions return frozen dataclasses; DES is the single source of
truth for the letterforms. build.py (inside Glyphs) converts these to
GSPath objects; the tests import this module without Glyphs running.
"""

import math
from dataclasses import dataclass

Point = tuple[float, float]

# font-unit constants shared by build.py and the tests
TIGHT_OVERLAP = 30  # default advance = max(60, width - 30): letters touch/overlap
SPACED_LSB = 50  # .spaced alternates: LSB = RSB = 50

LOWERCASE = "abcdefghijklmnopqrstuvwxyz"


@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float
    hole: bool = False


@dataclass(frozen=True)
class Poly:
    points: tuple[Point, ...]
    hole: bool = False


Shape = Rect | Poly


@dataclass(frozen=True)
class Glyph:
    width: int  # natural right edge of the ink
    shapes: tuple[Shape, ...]


def R(x0: float, y0: float, x1: float, y1: float) -> Rect:
    return Rect(x0, y0, x1, y1, hole=False)


def Cc(x0: float, y0: float, x1: float, y1: float) -> Rect:  # counter / slit (hole)
    return Rect(x0, y0, x1, y1, hole=True)


def Q(*pts: Point) -> Poly:
    return Poly(tuple(pts), hole=False)


def CT(*pts: Point) -> Poly:  # counter polygon (hole)
    return Poly(tuple(pts), hole=True)


def TAIL(x0: float, y0: float, x1: float, y1: float, t: float) -> Poly:  # thick diagonal stroke
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * t / 2.0, dx / L * t / 2.0
    return Poly(
        ((x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny), (x0 + nx, y0 + ny)), hole=False
    )


# (natural right edge, shapes). default advance = width - TIGHT_OVERLAP
DES: dict[str, Glyph] = {
    # --- capitals ---
    "A": Glyph(620, (R(0, 0, 620, 700), CT((190, 220), (430, 220), (310, 520)))),
    "B": Glyph(620, (R(0, 0, 620, 700), Cc(300, 410, 520, 560), Cc(300, 140, 520, 290))),
    "C": Glyph(620, (R(0, 0, 620, 700), Cc(200, 310, 620, 390))),
    "D": Glyph(620, (R(0, 0, 620, 700), Cc(340, 100, 440, 600))),
    "E": Glyph(620, (R(0, 0, 620, 700), Cc(260, 420, 620, 540), Cc(260, 140, 620, 260))),
    "F": Glyph(620, (R(0, 0, 620, 700), Cc(260, 440, 620, 540), Cc(260, 0, 620, 300))),
    "G": Glyph(620, (R(0, 0, 620, 700), Cc(200, 310, 620, 390), R(420, 0, 520, 390))),
    "H": Glyph(620, (R(0, 0, 260, 700), R(360, 0, 620, 700), R(260, 270, 360, 430))),
    "I": Glyph(260, (R(0, 0, 260, 700),)),
    "J": Glyph(620, (R(360, 0, 620, 700), R(120, 0, 620, 220))),
    "K": Glyph(
        620,
        (
            R(0, 0, 260, 700),
            Q((260, 180), (620, 520), (620, 700), (260, 700)),
            Q((260, 520), (620, 180), (620, 0), (260, 0)),
        ),
    ),
    "L": Glyph(620, (R(0, 0, 260, 700), R(0, 0, 620, 200))),
    "M": Glyph(
        620,
        (
            R(0, 0, 190, 700),
            R(430, 0, 620, 700),
            Q((150, 700), (290, 700), (360, 60), (260, 60)),
            Q((330, 700), (470, 700), (360, 60), (260, 60)),
        ),
    ),
    "N": Glyph(
        620,
        (R(0, 0, 260, 700), R(360, 0, 620, 700), Q((260, 700), (620, 340), (620, 120), (260, 480))),
    ),
    "O": Glyph(620, (R(0, 0, 620, 700), Cc(230, 240, 390, 460))),
    "P": Glyph(620, (R(0, 0, 260, 700), R(260, 300, 620, 700), Cc(360, 420, 500, 580))),
    "Q": Glyph(
        620,
        (
            Q((0, 0), (340, 0), (620, 280), (620, 700), (0, 700)),
            Q((414, 0), (620, 0), (620, 206)),
            Cc(230, 300, 390, 480),
        ),
    ),
    "R": Glyph(
        620,
        (
            R(0, 0, 260, 700),
            R(260, 300, 620, 700),
            Cc(360, 420, 500, 580),
            Q((260, 300), (620, 0), (620, 180), (260, 480)),
        ),
    ),
    "S": Glyph(620, (R(0, 0, 620, 700), Cc(200, 400, 620, 480), Cc(0, 220, 420, 300))),
    "T": Glyph(620, (R(0, 440, 620, 700), R(180, 0, 440, 700))),
    "U": Glyph(620, (R(0, 0, 260, 700), R(360, 0, 620, 700), R(0, 0, 620, 220))),
    "V": Glyph(
        620,
        (
            Q((0, 700), (240, 700), (430, 0), (190, 0)),
            Q((380, 700), (620, 700), (430, 0), (190, 0)),
        ),
    ),
    "W": Glyph(
        620,
        (
            Q((0, 700), (190, 700), (250, 0), (60, 0)),
            Q((230, 700), (390, 700), (230, 0), (70, 0)),
            Q((230, 700), (390, 700), (550, 0), (390, 0)),
            Q((430, 700), (620, 700), (560, 0), (370, 0)),
        ),
    ),
    "X": Glyph(
        620,
        (Q((0, 0), (620, 440), (620, 700), (0, 260)), Q((0, 440), (620, 0), (620, 260), (0, 700))),
    ),
    "Y": Glyph(
        620,
        (
            Q((0, 700), (240, 700), (400, 290), (160, 290)),
            Q((380, 700), (620, 700), (460, 290), (220, 290)),
            R(180, 0, 440, 460),
        ),
    ),
    "Z": Glyph(
        620,
        (R(0, 480, 620, 700), R(0, 0, 620, 220), Q((250, 220), (420, 220), (590, 480), (420, 480))),
    ),
    # --- figures ---
    "zero": Glyph(
        620,
        (
            R(0, 0, 620, 700),
            Cc(215, 180, 405, 520),
            Q((215, 520), (215, 400), (405, 180), (405, 300)),
        ),
    ),
    "one": Glyph(350, (R(90, 0, 350, 700), R(0, 480, 350, 700))),
    "two": Glyph(620, (R(0, 0, 620, 700), Cc(0, 400, 420, 480), Cc(200, 240, 620, 320))),
    "three": Glyph(620, (R(0, 0, 620, 700), Cc(0, 400, 300, 480), Cc(0, 220, 300, 300))),
    "four": Glyph(620, (R(0, 440, 260, 700), R(0, 240, 620, 440), R(360, 0, 620, 700))),
    "five": Glyph(
        620, (R(0, 480, 420, 700), R(0, 140, 260, 480), R(0, 140, 620, 300), R(260, 0, 620, 140))
    ),
    "six": Glyph(620, (R(0, 0, 620, 700), Cc(300, 480, 620, 560), Cc(300, 140, 460, 320))),
    "seven": Glyph(620, (R(0, 480, 620, 700), R(360, 0, 620, 480))),
    "eight": Glyph(620, (R(0, 0, 620, 700), Cc(230, 400, 390, 560), Cc(230, 140, 390, 300))),
    "nine": Glyph(620, (R(0, 0, 620, 700), Cc(0, 140, 320, 220), Cc(160, 380, 320, 560))),
    # --- punctuation ---
    "period": Glyph(200, (R(0, 0, 200, 200),)),
    "comma": Glyph(240, (R(0, 0, 220, 200), TAIL(180, 80, 60, -160, 160))),
    "colon": Glyph(200, (R(0, 0, 200, 160), R(0, 420, 200, 580))),
    "semicolon": Glyph(240, (R(0, 0, 200, 160), R(0, 420, 200, 580), TAIL(160, 80, 40, -160, 160))),
    "exclam": Glyph(200, (R(0, 220, 200, 700), R(0, 0, 200, 160))),
    "question": Glyph(
        460,
        (R(0, 500, 460, 700), R(260, 340, 460, 500), R(160, 160, 360, 340), R(160, 0, 360, 120)),
    ),
    "quotesingle": Glyph(160, (R(0, 420, 160, 700),)),
    "quotedbl": Glyph(400, (R(0, 420, 160, 700), R(240, 420, 400, 700))),
    "hyphen": Glyph(400, (R(0, 290, 400, 410),)),
    "endash": Glyph(500, (R(0, 290, 500, 410),)),
    "emdash": Glyph(620, (R(0, 290, 620, 410),)),
    "parenleft": Glyph(
        460,
        (
            Q((300, 700), (460, 700), (340, 350), (180, 350)),
            Q((180, 350), (340, 350), (460, 0), (300, 0)),
        ),
    ),
    "parenright": Glyph(
        460,
        (
            Q((160, 700), (0, 700), (120, 350), (280, 350)),
            Q((280, 350), (120, 350), (0, 0), (160, 0)),
        ),
    ),
    "bracketleft": Glyph(440, (R(60, 0, 200, 700), R(60, 0, 440, 140), R(60, 560, 440, 700))),
    "bracketright": Glyph(440, (R(240, 0, 380, 700), R(0, 0, 380, 140), R(0, 560, 380, 700))),
    "braceleft": Glyph(
        460, (R(340, 0, 460, 700), R(180, 560, 460, 700), R(180, 0, 460, 140), R(0, 300, 360, 400))
    ),
    "braceright": Glyph(
        460, (R(0, 0, 120, 700), R(0, 560, 280, 700), R(0, 0, 280, 140), R(100, 300, 460, 400))
    ),
    "slash": Glyph(620, (Q((0, 0), (160, 0), (620, 700), (460, 700)),)),
    "backslash": Glyph(620, (Q((460, 0), (620, 0), (160, 700), (0, 700)),)),
    "bar": Glyph(160, (R(0, -60, 160, 760),)),
    "asterisk": Glyph(
        530,
        (
            R(230, 430, 390, 700),
            R(90, 505, 530, 625),
            Q((120, 480), (210, 480), (500, 650), (410, 650)),
            Q((410, 480), (500, 480), (210, 650), (120, 650)),
        ),
    ),
    "plus": Glyph(620, (R(230, 170, 390, 530), R(10, 270, 610, 430))),
    "equal": Glyph(620, (R(60, 380, 560, 500), R(60, 200, 560, 320))),
    "less": Glyph(
        500,
        (
            Q((140, 350), (480, 610), (480, 700), (140, 510)),
            Q((140, 190), (480, 0), (480, 90), (140, 350)),
        ),
    ),
    "greater": Glyph(
        500,
        (
            Q((480, 350), (140, 610), (140, 700), (480, 510)),
            Q((480, 190), (140, 0), (140, 90), (480, 350)),
        ),
    ),
    "numbersign": Glyph(
        620, (R(100, 0, 260, 700), R(420, 0, 580, 700), R(0, 220, 620, 360), R(0, 460, 620, 600))
    ),
    "percent": Glyph(
        620,
        (
            R(0, 480, 200, 700),
            Cc(60, 540, 140, 620),
            R(420, 0, 620, 220),
            Cc(480, 60, 560, 140),
            Q((40, 0), (160, 0), (580, 700), (460, 700)),
        ),
    ),
    "dollar": Glyph(
        620,
        (R(0, 0, 620, 700), Cc(200, 400, 620, 480), Cc(0, 220, 420, 300), R(260, -60, 360, 760)),
    ),
    "ampersand": Glyph(
        620, (R(0, 380, 620, 700), Cc(260, 460, 620, 540), R(0, 0, 540, 380), Cc(180, 90, 400, 240))
    ),
    "at": Glyph(
        620,
        (
            Q(
                (0, 0),
                (620, 0),
                (620, 300),
                (540, 300),
                (540, 400),
                (620, 400),
                (620, 700),
                (0, 700),
            ),
            Cc(80, 80, 540, 620),
            R(180, 180, 440, 520),
            Cc(260, 300, 440, 380),
        ),
    ),
    "asciicircum": Glyph(
        620, (Q((0, 440), (240, 440), (310, 520), (380, 440), (620, 440), (400, 700), (220, 700)),)
    ),
    "underscore": Glyph(620, (R(0, -60, 620, 40),)),
    "grave": Glyph(400, (Q((240, 560), (400, 560), (260, 700), (100, 700)),)),
    "asciitilde": Glyph(620, (R(0, 380, 620, 620), Cc(0, 380, 420, 460), Cc(200, 540, 620, 620))),
    "space": Glyph(240, ()),
}


def tight_advance(name: str) -> int:
    """Default advance: letters overlap by TIGHT_OVERLAP; space keeps its width."""
    g = DES[name]
    return g.width if name == "space" else max(60, g.width - TIGHT_OVERLAP)


def spaced_advance(name: str) -> int:
    """.spaced alternate advance (never used for space, which has no alternate)."""
    return DES[name].width + 2 * SPACED_LSB


def substitution_names() -> list[str]:
    """Glyph set covered by the ss01/salt substitution lists."""
    return sorted(n for n in DES if n != "space") + list(LOWERCASE)
