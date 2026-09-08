"""Build MONOLITH.glyphs from the pure design data.

IMPORT ONLY INSIDE GLYPHS (Macro Panel / Glyphs script): GlyphsApp exists
only in Glyphs' embedded Python. Run via scripts/macro_bootstrap.py.
"""
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from GlyphsApp import (GSComponent, GSFeature, GSGlyph, GSInstance, GSLINE,
                       GSLayer, GSNode, GSAxis, GSPath, Glyphs)

from monolith.design import (DES, LOWERCASE, SPACED_LSB, Point, Rect, Shape,
                             substitution_names, tight_advance)
from monolith.kerning import KERN_PAIRS

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAVE = REPO_ROOT / "MONOLITH.glyphs"

KEEP = set(DES) | set(LOWERCASE)


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
        return [(shape.x0, shape.y0), (shape.x1, shape.y0),
                (shape.x1, shape.y1), (shape.x0, shape.y1)]
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
    for (x, y) in pts:
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
    for attr, val in (("capHeight", 700), ("xHeight", 700),
                      ("ascender", 800), ("descender", -200)):
        try:
            setattr(master, attr, val)
        except Exception as e:
            print("metric %s: %s" % (attr, e))
    try:
        master.weightValue = 800  # does not exist in Glyphs 3.5; the axes block below is the real mechanism
    except Exception:
        try:
            master.weight = "ExtraBold"
        except Exception:
            pass


def master_layer(F: Any, master: Any, g: GSGlyph) -> GSLayer:
    for ly in g.layers:
        if ly.associatedMasterId == master.id:
            return ly
    if len(g.layers):
        return g.layers[0]
    nl = GSLayer()
    nl.associatedMasterId = master.id
    g.layers.append(nl)
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
    errors = []
    try:
        for i in reversed(range(len(layer.shapes))):
            del layer.shapes[i]
        return
    except Exception as e:
        errors.append(repr(e))
    try:
        for i in reversed(range(len(layer.paths))):
            del layer.paths[i]
        return
    except Exception as e:
        errors.append(repr(e))
    raise RuntimeError("clear failed: %s" % errors)


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
                layer = master_layer(F, master, g)
                try:
                    for i in reversed(range(len(layer.components))):
                        del layer.components[i]
                except Exception as e:
                    print("component clear fail", name, e)
                clear_shapes(layer)
        if g is None:
            g = GSGlyph(name)
            F.glyphs.append(g)
            created += 1
        layer = master_layer(F, master, g)
        for shape in gl.shapes:
            layer.paths.append(adapt(shape))
        layer.width = tight_advance(name)
        set_unicode(g, name)
    print("letters/figures/punct drawn, new glyphs:", created)

    # lowercase a-z as components of the caps
    for lo, up in zip(LOWERCASE, LOWERCASE.upper()):
        g = F.glyphs[lo]
        if g is not None:
            if remove_glyph(F, g):
                g = None
            else:
                layer = master_layer(F, master, g)
                clear_shapes(layer)
        if g is None:
            g = GSGlyph(lo)
            F.glyphs.append(g)
            created += 1
        layer = master_layer(F, master, g)
        try:
            layer.components.append(GSComponent(up))
        except Exception as e:
            print("component", lo, e)
        layer.width = master_layer(F, master, F.glyphs[up]).width
        set_unicode(g, lo)
    print("lowercase mapped to caps, total glyphs:", len(F.glyphs))

    # "Loose spacing" alternates, toggled via ss01 / salt
    for name in sorted(DES.keys()):
        if name == "space":
            continue
        gl = DES[name]
        g = fresh_glyph(F, name + ".spaced")
        layer = master_layer(F, master, g)
        for shape in gl.shapes:
            layer.paths.append(adapt(shape))
        try:
            layer.LSB = SPACED_LSB
        except Exception:
            for p in layer.paths:
                for nd in p.nodes:
                    x, y = nd.position
                    nd.position = (x + SPACED_LSB, y)
        layer.width = gl.width + 2 * SPACED_LSB
    print("spaced alternates drawn:", len(DES) - 1)

    for lo, up in zip(LOWERCASE, LOWERCASE.upper()):
        g = fresh_glyph(F, lo + ".spaced")
        layer = master_layer(F, master, g)
        try:
            layer.components.append(GSComponent(up + ".spaced"))
        except Exception as e:
            print("component", lo, e)
        layer.width = master_layer(F, master, F.glyphs[up + ".spaced"]).width

    subs = ["sub %s by %s.spaced;" % (n, n) for n in substitution_names()]
    feature_code = ('featureNames {\n  name "Loose spacing";\n};\n'
                    + "\n".join(subs))
    set_feature(F, "ss01", feature_code)
    set_feature(F, "salt", "\n".join(subs))
    print("features ss01/salt written with %d substitutions" % len(subs))

    # pair kerning from the seam metric (the same table variable.py injects
    # into the variable font), written for every master so it carries into
    # all exports unchanged across axes. The .spaced alternates are not
    # kerned: fusion is not intended there.
    kern_fail = 0
    for m in F.masters:
        for (lg, rg), v in KERN_PAIRS.items():
            try:
                F.kerning[m.id][(lg, rg)] = v
            except Exception:
                kern_fail += 1
    try:
        written = sum(len(F.kerning[m.id]) for m in F.masters)
        print("kern pairs written: %s (failures: %d)" % (written, kern_fail))
    except Exception as e:
        print("kerning write failed:", e)

    # Weight axis + ExtraBold instance: required for Text Preview / interpolation.
    # GSInstance has no weightValue in this API; axis location lives in .axes.
    if not len(F.axes):
        ax = GSAxis()
        ax.name = "Weight"
        ax.axisTag = "wght"
        F.axes.append(ax)
    F.masters[0].axes = [800]
    inst = None
    for i in F.instances:
        if i.name == "ExtraBold":
            inst = i
            break
    if inst is None:
        inst = GSInstance()
        inst.name = "ExtraBold"
        F.instances.append(inst)
    inst.axes = [800]
    print("Weight axis set, instance ExtraBold located at 800")

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
        print("after fix: wall=%s hole=%s" % (winding_at(o_layer, 60.0, 350.0),
                                              winding_at(o_layer, 310.0, 350.0)))

    save_path = Path(save_path) if save_path else DEFAULT_SAVE
    try:
        F.save(str(save_path))
        print("saved %s" % save_path)
    except Exception as e:
        print("save failed:", e)
    print("DONE")
    return F
