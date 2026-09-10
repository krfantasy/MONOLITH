"""Build MONOLITH.glyphs from the pure design data.

IMPORT ONLY INSIDE GLYPHS (Macro Panel / Glyphs script): GlyphsApp exists
only in Glyphs' embedded Python. Run via scripts/macro_bootstrap.py.
"""

import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from GlyphsApp import (
    GSComponent,
    GSFeature,
    GSGlyph,
    GSInstance,
    GSLINE,
    GSLayer,
    GSNode,
    GSAxis,
    GSFontMaster,
    GSPath,
    Glyphs,
)

from monolith.design import (
    DES,
    LOWERCASE,
    SPACED_LSB,
    TIGHT_OVERLAP,
    Point,
    Rect,
    Shape,
    grid_order,
    substitution_names,
    tight_advance,
)
from monolith.kerning import KERN_PAIRS

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAVE = REPO_ROOT / "MONOLITH.glyphs"

KEEP = set(DES)


def _signed_area(pts: Sequence[Point]) -> float:
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s


def _shape_points(shape: Shape) -> list[Point]:
    if isinstance(shape, Rect):
        return [
            (shape.x0, shape.y0),
            (shape.x1, shape.y0),
            (shape.x1, shape.y1),
            (shape.x0, shape.y1),
        ]
    return list(shape.points)


def adapt(shape: Shape) -> GSPath:
    """Pure design shape -> a FRESH GSPath (ink CCW, holes CW).

    Always builds new objects: design data is shared between the regular
    glyphs and the .spaced alternates, so returning a shared GSPath would
    alias them (the old clone_paths bug).
    """
    pts = _shape_points(shape)
    ccw = not shape.hole
    if (_signed_area(pts) > 0) != ccw:
        pts = list(reversed(pts))
    p = GSPath()
    p.closed = True
    for x, y in pts:
        nd = GSNode()
        nd.type = GSLINE
        nd.position = (x, y)
        p.nodes.append(nd)
    return p


def setup_font(F: Any, master: Any) -> None:
    F.familyName = "MONOLITH"
    try:
        F.upm = 1000
    except Exception:
        try:
            F.unitsPerEm = 1000
        except Exception as e:
            print("upm:", e)
    for attr, val in (("capHeight", 700), ("xHeight", 700), ("ascender", 800), ("descender", -200)):
        try:
            setattr(master, attr, val)
        except Exception as e:
            print("metric %s: %s" % (attr, e))
    try:
        master.weightValue = (
            800  # does not exist in Glyphs 3.5; the axes block below is the real mechanism
        )
    except Exception:
        try:
            master.weight = "ExtraBold"
        except Exception:
            pass
    # Keep .spaced alternates next to their base glyphs in the grid instead
    # of fragmenting the category groups. GSFont.keepAlternatesTogether is
    # getter-only in Glyphs 4.1 and has no GUI surface; the ObjC setter
    # persists it as the font-level "Keep Alternates Together" parameter.
    F.setKeepAlternatesTogether_(True)


def master_layer(F: Any, master: Any, g: GSGlyph) -> GSLayer:
    for ly in g.layers:
        if ly.associatedMasterId == master.id:
            return ly
    if len(g.layers):
        return g.layers[0]
    nl = GSLayer()
    nl.associatedMasterId = master.id
    # Glyphs 4: the layer proxy has no append — insertAtIndex is the mutator
    g.layers.insert(len(g.layers), nl)
    return nl


def remove_glyph(F: Any, g: GSGlyph) -> bool:
    name = g.name
    try:
        F.glyphs.remove(g)
        return True
    except Exception:
        pass
    try:
        del F.glyphs[name]
        return True
    except Exception:
        pass
    try:
        for i, gg in enumerate(F.glyphs):
            if gg.name == name:
                del F.glyphs[i]
                return True
    except Exception:
        pass
    return False


def clear_shapes(layer: GSLayer) -> None:
    # Glyphs 4: layer.shapes is the one mutable collection — layer.paths and
    # layer.components are iterate-only proxies now (GSProxyShapes), and
    # shapes holds paths and components alike.
    for i in reversed(range(len(layer.shapes))):
        del layer.shapes[i]


def set_unicode(g: GSGlyph, name: str) -> None:
    try:
        info = Glyphs.glyphInfoForName(name)
        if info is not None and info.unicode:
            g.unicodes = [info.unicode]
    except Exception:
        pass


def fresh_glyph(F: Any, name: str) -> GSGlyph:
    g = F.glyphs[name]
    if g is not None and not remove_glyph(F, g):
        g = None
    if g is None:
        g = GSGlyph(name)
        F.glyphs.append(g)
    return g


def set_feature(F: Any, fname: str, fcode: str) -> None:
    for f in F.features:
        if f.name == fname:
            f.code = fcode
            return
    nf = GSFeature()
    nf.name = fname
    nf.code = fcode
    F.features.append(nf)


def drop_feature(F: Any, fname: str) -> None:
    for f in list(F.features):
        if getattr(f, "name", None) == fname:
            try:
                F.features.remove(f)
                print("removed feature %s" % fname)
            except Exception as e:
                print("could not remove feature %s: %s" % (fname, e))


def set_native_kerning(F: Any) -> None:
    """Write every seam-metric pair into Glyphs' native kerning table.

    Uses setKerningForPair — the documented integrity-checked API (the
    Glyphs 4 docu discourages writing the kerning dict directly, and a
    tuple-keyed dict here once poisoned a 3.5 document's F.save). Keys are
    plain glyph-name strings. Both masters get identical values so kerning
    stays constant along SPAC; the KERN axis post-step scales it 0-100.
    The kern feature must not coexist with this — Glyphs would compile
    both and double every kern.
    """
    sample = next(iter(KERN_PAIRS))
    for master in F.masters:
        mid = master.id
        for (lg, rg), v in sorted(KERN_PAIRS.items()):
            F.setKerningForPair(mid, lg, rg, int(v))
        got = F.kerningForPair(mid, sample[0], sample[1])
        if got != KERN_PAIRS[sample]:
            raise RuntimeError(
                "kerning read-back mismatch on %s: %s%r -> %r"
                % (master.name, sample, KERN_PAIRS[sample], got)
            )
        print("native kerning: %d pairs on master %s" % (len(KERN_PAIRS), master.name))


def winding_at(layer: GSLayer, px: float, py: float) -> int:
    w = 0
    for p in layer.paths:
        n = len(p.nodes)
        for i in range(n):
            a = p.nodes[i].position
            b = p.nodes[(i + 1) % n].position
            if (a.y > py) != (b.y > py):
                xint = a.x + (py - a.y) * (b.x - a.x) / (b.y - a.y)
                if xint > px:
                    if b.y > a.y:
                        w += 1
                    else:
                        w -= 1
    return w


def strip_axis_locations(F: Any) -> None:
    """Delete Axis Location custom parameters from every master and instance.

    In-memory defense for docs loaded from older saves: when any object
    carries one, Glyphs derives the exported fvar axis range from these
    parameters instead of the masters' axesValues, collapsing every axis
    to 0-0 ("Invalid axis range" on VF export).

    NOTE: a plain Glyphs 4.1 save RE-ADDS these parameters to the FILE
    (serializer-level; the in-memory doc never has them — verified
    2026-09-09), so this cannot keep the saved source clean. run() calls
    strip_axis_locations_in_file after every F.save for that.
    """
    stripped = 0
    for obj in list(F.masters) + list(F.instances):
        params = obj.customParameters
        for parameter in list(params.values()):
            if parameter.name == "Axis Location":
                try:
                    del params[parameter.name]
                    stripped += 1
                except Exception as e:
                    print("could not strip Axis Location on %s: %s" % (obj.name, e))
    if stripped:
        print("stripped %d Axis Location parameter(s)" % stripped)


# The exact OpenStep-plist shape Glyphs 4.1's serializer writes for the
# phantom Axis Location parameters (verified against a fresh save).
_AXIS_LOCATION_ENTRY = re.compile(
    r'\{\s*name = "Axis Location";\s*'
    r"value = \(\s*\{\s*Axis = Spacing;\s*Location = 0;\s*\}\s*\);\s*\}\s*,?"
)
_EMPTY_PARAMETER_LIST = re.compile(r"customParameters = \(\s*\)\s*;?")
# A list left ending in ",\n)" — raw newlines cannot occur inside quoted
# plist strings, so this can only match structure, never string content.
_DANGLING_LIST_COMMA = re.compile(r",(\s*\n\s*\))")


def strip_axis_locations_in_file(path: str | Path) -> int:
    """Remove phantom Axis Location parameter blocks from a saved .glyphs.

    Glyphs 4.1's serializer writes an {Axis = Spacing; Location = 0}
    parameter onto masters/instances at SAVE time (never visible in the
    live document). Any such block collapses the exported fvar range to
    0-0 — "Invalid axis range for axis: Spacing" — so the saved file must
    be cleaned AFTER every save, before anything consumes it (VF export,
    the repo). Format-preserving text surgery on the OpenStep plist.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    text, count = _AXIS_LOCATION_ENTRY.subn("", text)
    if count:
        text = _EMPTY_PARAMETER_LIST.sub("", text)
        text = _DANGLING_LIST_COMMA.sub(r"\1", text)
        path.write_text(text, encoding="utf-8")
        print("stripped %d Axis Location block(s) from %s" % (count, path.name))
    return count


def _doc_filepath(F: Any) -> Path | None:
    raw = getattr(F, "filepath", None)
    text = str(raw() if callable(raw) else raw or "")
    return Path(text) if text else None


def run(font: Any = None, save_path: str | Path | None = None) -> Any:
    F = font
    if F is None:
        F = Glyphs.font
    if F is None and len(Glyphs.fonts):
        F = Glyphs.fonts[0]
    if F is None:
        raise RuntimeError("no font document open")
    master = F.masters[0]
    setup_font(F, master)

    # drop anything outside the requested set
    removed = 0
    for g in list(F.glyphs):
        if g.name not in KEEP:
            if remove_glyph(F, g):
                removed += 1
            else:
                print("could not remove", g.name)
    print("removed glyphs:", removed)

    # draw capitals, figures, punctuation
    created = 0
    for name in sorted(DES.keys()):
        gl = DES[name]
        g = F.glyphs[name]
        if g is not None:
            if remove_glyph(F, g):
                g = None
            else:
                # fresh shapes wipe paths and components alike (Glyphs 4:
                # there is no separate components mutator any more)
                layer = master_layer(F, master, g)
                clear_shapes(layer)
        if g is None:
            g = GSGlyph(name)
            F.glyphs.append(g)
            created += 1
        layer = master_layer(F, master, g)
        for shape in gl.shapes:
            # Glyphs 4: layer.paths is iterate-only; shapes is the mutator
            layer.shapes.append(adapt(shape))
        layer.width = tight_advance(name)
        set_unicode(g, name)
    print("letters/figures/punct drawn, new glyphs:", created)

    # Double-unicode all-caps: no a-z glyphs exist. Each cap carries its
    # own codepoint plus the lowercase one (A: U+0041 + U+0061), so typing
    # lowercase resolves via cmap to the cap glyph. Stale lowercase glyphs
    # (incl. .spaced) from component-era saves are deleted.
    for lo, up in zip(LOWERCASE, LOWERCASE.upper()):
        for stale in (lo, lo + ".spaced"):
            g = F.glyphs[stale]
            if g is not None and not remove_glyph(F, g):
                print("could not remove", stale)
    for lo, up in zip(LOWERCASE, LOWERCASE.upper()):
        g = F.glyphs[up]
        upper_info = Glyphs.glyphInfoForName(up)
        lower_info = Glyphs.glyphInfoForName(lo)
        if (
            upper_info is not None
            and lower_info is not None
            and upper_info.unicode
            and lower_info.unicode
        ):
            g.unicodes = [upper_info.unicode, lower_info.unicode]
        else:
            print("unicode lookup failed for %s/%s" % (up, lo))
    print("caps double-encoded, total glyphs:", len(F.glyphs))

    # "Loose spacing" alternates, toggled via ss01 / salt
    for name in sorted(DES.keys()):
        if name == "space":
            continue
        gl = DES[name]
        g = fresh_glyph(F, name + ".spaced")
        layer = master_layer(F, master, g)
        for shape in gl.shapes:
            layer.shapes.append(adapt(shape))
        try:
            layer.LSB = SPACED_LSB
        except Exception:
            for p in layer.paths:
                for nd in p.nodes:
                    x, y = nd.position
                    nd.position = (x + SPACED_LSB, y)
        layer.width = gl.width + 2 * SPACED_LSB
    print("spaced alternates drawn:", len(DES) - 1)

    subs = ["sub %s by %s.spaced;" % (n, n) for n in substitution_names()]
    feature_code = 'featureNames {\n  name "Loose spacing";\n};\n' + "\n".join(subs)
    set_feature(F, "ss01", feature_code)
    set_feature(F, "salt", "\n".join(subs))
    print("features ss01/salt written with %d substitutions" % len(subs))

    # SPAC axis: spacing as a real axis. The second master carries the same
    # outlines with every advance wider by SPAC_MAX, so the variable export
    # reduces to fvar + HVAR. The single-master Weight axis from the Text
    # Preview experiment is dropped — a constant axis has no place in fvar.
    spac_max = 2 * SPACED_LSB + TIGHT_OVERLAP
    if not any(getattr(ax, "axisTag", "") == "SPAC" for ax in F.axes):
        ax = GSAxis()
        ax.name = "Spacing"
        ax.axisTag = "SPAC"
        F.axes.append(ax)
    for ax in list(F.axes):
        if getattr(ax, "axisTag", "") == "wght":
            try:
                F.axes.remove(ax)
                print("dropped single-master Weight axis")
            except Exception as e:
                print("could not drop Weight axis:", e)

    tight_master = F.masters[0]
    if len(F.masters) < 2:
        loose = GSFontMaster()
        loose.name = "Spaced"
        for attr in ("ascender", "descender", "capHeight", "xHeight"):
            try:
                setattr(loose, attr, getattr(tight_master, attr))
            except Exception:
                pass
        F.masters.append(loose)
    else:
        loose = F.masters[1]
    copied = 0
    for g in F.glyphs:
        for ly in list(g.layers):
            if ly.associatedMasterId == loose.id:
                g.layers.remove(ly)
        src = master_layer(F, tight_master, g)
        # g.layers[master.id] returns the REGISTERED master layer (layerId ==
        # master.id), auto-creating it. This is the only bridge access that
        # produces a master layer: copying a layer and assigning layerId does
        # NOT stick — Glyphs regenerates the id and the master ends up with
        # an empty auto-created layer, which makes every glyph incompatible
        # for variable-font export.
        dst = g.layers[loose.id]
        clear_shapes(dst)
        for p in src.paths:
            np_ = GSPath()
            np_.closed = True
            for nd in p.nodes:
                nn = GSNode()
                nn.type = nd.type
                nn.position = (nd.position.x, nd.position.y)
                np_.nodes.append(nn)
            dst.shapes.append(np_)
        for c in src.components:
            base = getattr(c, "name", None) or c.glyphName
            dst.shapes.append(GSComponent(base))
        dst.width = src.width + spac_max
        copied += 1
    registered = sum(
        1 for g in F.glyphs if any(ly.layerId == loose.id and len(ly.shapes) for ly in g.layers)
    )
    tight_master.axes = [0]
    loose.axes = [spac_max]
    print(
        "SPAC axis set: %d glyphs mirrored into the Spaced master (+%d advance)"
        % (copied, spac_max)
    )
    print("Spaced master layers holding shapes: %d of %d glyphs" % (registered, len(F.glyphs)))
    # Only glyphs with ink in the tight master must have Spaced shapes;
    # glyphs empty in both masters (space) are compatible, not missing.
    missing = sorted(
        g.name
        for g in F.glyphs
        if any(ly.layerId == tight_master.id and len(ly.shapes) for ly in g.layers)
        and not any(ly.layerId == loose.id and len(ly.shapes) for ly in g.layers)
    )
    if missing:
        print(
            "WARNING: Spaced master missing shapes for: %s — variable export will fail"
            % ", ".join(missing)
        )

    # pair kerning from the seam metric as NATIVE per-master kerning —
    # visible and editable in Window > Kerning, and it's the data Glyphs
    # itself interpolates and compiles into GPOS at export. Needs both
    # masters in place, hence after the SPAC block. The .spaced alternates
    # stay unkerned: kerning is keyed on glyph names, so a glyph
    # substituted for a .spaced alternate drops out of every pair.
    drop_feature(F, "kern")
    set_native_kerning(F)

    # instances: ExtraBold is the static export (SPAC 0 keeps the shipped
    # tight look); Touching/Spaced become the variable font's named instances.
    inst = None
    for i in F.instances:
        if i.name == "ExtraBold":
            inst = i
            break
    if inst is None:
        inst = GSInstance()
        inst.name = "ExtraBold"
        F.instances.append(inst)
    inst.axes = [0]
    # the static cut ships unkerned (pure block look): native kerning
    # compiles into the kern feature at export, so this instance drops
    # the feature — the variable font keeps it to feed the KERN axis.
    try:
        inst.customParameters["Remove Features"] = "kern"
        print("ExtraBold: Remove Features = kern (static ships unkerned)")
    except Exception as e:
        print("Remove Features parameter failed:", e)
    for iname, ival in (("Touching", TIGHT_OVERLAP), ("Spaced", spac_max)):
        found = None
        for i in F.instances:
            if i.name == iname:
                found = i
                break
        if found is None:
            found = GSInstance()
            found.name = iname
            F.instances.append(found)
        found.axes = [ival]
    print("instances: ExtraBold/Touching/Spaced at SPAC 0/%d/%d" % (TIGHT_OVERLAP, spac_max))

    # winding sanity check on O: wall=1, hole=0; else flip every path
    o_layer = master_layer(F, master, F.glyphs["O"])
    w_wall = winding_at(o_layer, 60.0, 350.0)
    w_hole = winding_at(o_layer, 310.0, 350.0)
    print("winding check O: wall=%s hole=%s" % (w_wall, w_hole))
    if w_wall != 1 or w_hole != 0:
        flipped = 0
        for g in F.glyphs:
            for ly in g.layers:
                for p in ly.paths:
                    p.reverse()
                    flipped += 1
        print("REVERSED %s paths (direction fix)" % flipped)
        o_layer = master_layer(F, master, F.glyphs["O"])
        print(
            "after fix: wall=%s hole=%s"
            % (winding_at(o_layer, 60.0, 350.0), winding_at(o_layer, 310.0, 350.0))
        )

    # Font-tab order: the draw phases leave glyphs alphabetical with all
    # .spaced alternates last, splitting the grid into repeated category
    # runs — and headless saves do not re-sort (GUI saves with Keep
    # Alternates Together did). Rebuild the glyphs array in the canonical
    # order; kerning (keyed by name) and per-glyph layers are unaffected.
    desired = grid_order(DES)
    by_name = {g.name: g for g in F.glyphs}
    extras = sorted(name for name in by_name if name not in set(desired))
    if extras:
        print("glyphs outside grid order (appended last):", extras)
        desired += extras
    if [g.name for g in F.glyphs] != desired:
        for g in list(F.glyphs):
            remove_glyph(F, g)
        for name in desired:
            F.glyphs.append(by_name[name])
        print("glyph order normalized:", len(desired), "glyphs")

    strip_axis_locations(F)

    save_path = Path(save_path) if save_path else DEFAULT_SAVE
    try:
        F.save(str(save_path))
    except Exception as e:
        raise RuntimeError("saving the rebuilt source to %s failed: %s" % (save_path, e)) from e
    print("saved %s" % save_path)
    # Glyphs 4.1's serializer writes phantom Axis Location blocks INTO the
    # file at save time (the in-memory doc never has them) — clean the file
    # or the VF export and the source regression test both fail.
    strip_axis_locations_in_file(save_path)
    print("DONE")
    return F
