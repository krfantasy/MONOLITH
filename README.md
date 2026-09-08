# MONOLITH

A brutalist extra-bold, all-slabs-and-slits display sans. Every letterform is
straight lines: rectangles, polygons, and diagonal slabs — no curves anywhere.
Adjacent letters overlap by design; turn the **spacing** up (below) if you
want them to breathe.

![MONOLITH specimen](specimens/specimen.png)

## Glyph set

`A–Z`, `a–z` (uppercase forms for both cases), `0–9` (the zero carries an
attached diagonal slash to stay distinct from `O` at small sizes), and full
printable ASCII punctuation & symbols plus en/em dashes — 97 glyphs, plus a
`.spaced` alternate for every glyph except the space.

## Install

Grab the built fonts from [`fonts/`](fonts/):

- `MONOLITH-ExtraBold.otf` — print / desktop
- `MONOLITH-ExtraBold.ttf` — web / apps
- `MONOLITH-Variable.ttf` — variable: continuous spacing via the `SPAC` axis

## Spacing

Two ways to loosen the default overlap (advance = width − 30):

### Variable `SPAC` axis

`MONOLITH-Variable.ttf` exposes spacing as a continuous slider. The axis
value is extra advance per glyph, in font units:

| SPAC | Look |
|------|------|
| **0** (default) | shipped tight look — letters overlap by 30 |
| **30** | ink edges exactly touch |
| **130** | fully loose — matches the `.spaced` alternates |

- **CSS:** `font-variation-settings: "SPAC" 30;`
- Named instances (*Touching*, *Spaced*) also appear in app style menus.
- Every glyph gets the same delta, `space` included; combining `SPAC` with
  ss01 double-spaces (both add their delta).

![SPAC 30 specimen](specimens/specimen-spac30.png)

### Loose spacing (ss01)

By default the letters touch and overlap (advance = width − 30). Every glyph
has a `.spaced` alternate with 50-unit sidebearings, substituted by:

- **CSS:** `font-feature-settings: "ss01" on;` (also `"salt"` works)
- **Affinity apps:** Character panel → hamburger menu → *Show Typography* →
  *Stylistic Sets* → **Loose spacing**
- **Canva:** no OpenType-feature UI — use the letter-spacing slider instead.

![Spaced specimen](specimens/specimen-spaced.png)

## Rebuilding

The font source is [`MONOLITH.glyphs`](MONOLITH.glyphs). The letterforms live
as pure Python data in [`src/monolith/design.py`](src/monolith/design.py);
the Glyphs-side builder turns that data into the `.glyphs` file.

**Regenerate the fonts** (requires [Glyphs](https://glyphsapp.com) — the whole
generation path is Glyphs; fontTools is only used downstream by tests and
specimens):

1. Open Glyphs, then Window ▸ Macro Panel (⌥⌘M).
2. Paste the contents of [`scripts/macro_bootstrap.py`](scripts/macro_bootstrap.py)
   (adjust the one path line to your checkout) and press **Run**.
   `MONOLITH.glyphs` is rewritten in place — including the two `SPAC` masters
   and the `kern` feature — and all three binaries are exported straight into
   `fonts/`: the TTF/OTF statics and `MONOLITH-Variable.ttf`. If the
   variable-font export via the API fails, export it by hand: File ▸ Export ▸
   **Variable**, save as `fonts/MONOLITH-Variable.ttf`.

**Regenerate the specimen images** (no Glyphs needed):

```sh
uv sync
uv run monolith-specimen        # writes specimens/specimen{,-spaced}.png
uv run monolith-specimen --spac 30   # + specimens/specimen-spac30.png (needs the variable font)
```

## Development

```sh
uv sync
uv run pytest          # design invariants + SPAC font + shaping + render smoke test (no Glyphs)
uv run ruff check .
```

`tests/test_design.py` guards the invariants that keep the font legible:
full printable-ASCII coverage, a minimum-thickness tripwire on diagonal
strokes, counter presence for the confusable-prone letters, and the
tight/spaced advance math. `tests/test_variable.py` guards the SPAC axis:
axis metadata, per-glyph advance math at 0/30/130, and outline invariance.
`tests/test_shaping.py` runs the exported binaries through HarfBuzz to prove
the `kern` feature and `SPAC` axis actually apply.

## License

- **The font** (`MONOLITH.glyphs`, `fonts/*`): [SIL Open Font License 1.1](LICENSE.txt)
  — "MONOLITH" is a Reserved Font Name.
- **The code** (`src/`, `scripts/`, `tests/`): [MIT](LICENSE-CODE)
