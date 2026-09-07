# MONOLITH

A brutalist extra-bold, all-slabs-and-slits display sans. Every letterform is
straight lines: rectangles, polygons, and diagonal slabs — no curves anywhere.
Adjacent letters overlap by design; enable **Loose spacing** (below) if you
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

## Loose spacing (ss01)

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

**Regenerate the font source** (requires [Glyphs](https://glyphsapp.com)):

1. Open Glyphs, then Window ▸ Macro Panel (⌥⌘M).
2. Paste the contents of [`scripts/macro_bootstrap.py`](scripts/macro_bootstrap.py)
   (adjust the one path line to your checkout) and press **Run**.
   `MONOLITH.glyphs` is rewritten in place.
3. Export via File ▸ Export (or uncomment the `generate(...)` lines in the
   bootstrap to export straight into `fonts/`).

**Regenerate the specimen images** (no Glyphs needed):

```sh
uv sync
uv run monolith-specimen        # writes specimens/specimen{,-spaced}.png
```

## Development

```sh
uv sync
uv run pytest          # design invariants (runs without Glyphs) + render smoke test
uv run ruff check .
```

`tests/test_design.py` guards the invariants that keep the font legible:
full printable-ASCII coverage, a minimum-thickness tripwire on diagonal
strokes, counter presence for the confusable-prone letters, and the
tight/spaced advance math.

## License

- **The font** (`MONOLITH.glyphs`, `fonts/*`): [SIL Open Font License 1.1](LICENSE.txt)
  — "MONOLITH" is a Reserved Font Name.
- **The code** (`src/`, `scripts/`, `tests/`): [MIT](LICENSE-CODE)
