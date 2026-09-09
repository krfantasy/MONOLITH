# MONOLITH ExtraBold - brutalist block font generator for Glyphs 3
# DEPRECATED — do not use: this recreates the deleted component lowercase
# (a-z/a.spaced-z.spaced). The builder is src/monolith/build.py; see
# scripts/macro_bootstrap.py.
# Run inside Glyphs: Window > Macro Panel > exec this file > Run
import math
from GlyphsApp import (
    Glyphs,
    GSPath,
    GSNode,
    GSGlyph,
    GSLayer,
    GSComponent,
    GSLINE,
    GSFeature,
    GSAxis,
    GSInstance,
)

F = Glyphs.font
if F is None and len(Glyphs.fonts):
    F = Glyphs.fonts[0]
if F is None:
    raise RuntimeError("no font document open")

master = F.masters[0]
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
    master.weightValue = 800
except Exception:
    try:
        master.weight = "ExtraBold"
    except Exception:
        pass

LT = GSLINE


def orient(pts, ccw):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    if (s > 0) != ccw:
        pts = list(reversed(pts))
    return pts


def mkpath(pts, ccw):
    p = GSPath()
    p.closed = True
    for x, y in orient(pts, ccw):
        nd = GSNode()
        nd.type = LT
        nd.position = (x, y)
        p.nodes.append(nd)
    return p


def R(x0, y0, x1, y1):
    return mkpath([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)


def Cc(x0, y0, x1, y1):  # counter / slit (hole)
    return mkpath([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], False)


def Q(*pts):
    return mkpath(list(pts), True)


def CT(*pts):  # counter polygon
    return mkpath(list(pts), False)


def TAIL(x0, y0, x1, y1, t):  # thick diagonal stroke
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * t / 2.0, dx / L * t / 2.0
    return mkpath(
        [(x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny), (x0 + nx, y0 + ny)], True
    )


# (natural right edge, parts). width = natural - 30 -> letters overlap by 30
DES = {}
# --- capitals ---
DES["A"] = (620, [R(0, 0, 620, 700), CT((190, 220), (430, 220), (310, 520))])
DES["B"] = (620, [R(0, 0, 620, 700), Cc(300, 410, 520, 560), Cc(300, 140, 520, 290)])
DES["C"] = (620, [R(0, 0, 620, 700), Cc(200, 310, 620, 390)])
DES["D"] = (620, [R(0, 0, 620, 700), Cc(340, 100, 440, 600)])
DES["E"] = (620, [R(0, 0, 620, 700), Cc(260, 420, 620, 540), Cc(260, 140, 620, 260)])
DES["F"] = (620, [R(0, 0, 620, 700), Cc(260, 440, 620, 540), Cc(260, 0, 620, 300)])
DES["G"] = (620, [R(0, 0, 620, 700), Cc(200, 310, 620, 390), R(420, 0, 520, 390)])
DES["H"] = (620, [R(0, 0, 260, 700), R(360, 0, 620, 700), R(260, 270, 360, 430)])
DES["I"] = (260, [R(0, 0, 260, 700)])
DES["J"] = (620, [R(360, 0, 620, 700), R(120, 0, 620, 220)])
DES["K"] = (
    620,
    [
        R(0, 0, 260, 700),
        Q((260, 180), (620, 520), (620, 700), (260, 700)),
        Q((260, 520), (620, 180), (620, 0), (260, 0)),
    ],
)
DES["L"] = (620, [R(0, 0, 260, 700), R(0, 0, 620, 200)])
DES["M"] = (
    620,
    [
        R(0, 0, 190, 700),
        R(430, 0, 620, 700),
        Q((150, 700), (290, 700), (360, 60), (260, 60)),
        Q((330, 700), (470, 700), (360, 60), (260, 60)),
    ],
)
DES["N"] = (
    620,
    [R(0, 0, 260, 700), R(360, 0, 620, 700), Q((260, 700), (620, 340), (620, 120), (260, 480))],
)
DES["O"] = (620, [R(0, 0, 620, 700), Cc(230, 240, 390, 460)])
DES["P"] = (620, [R(0, 0, 260, 700), R(260, 300, 620, 700), Cc(360, 420, 500, 580)])
DES["Q"] = (
    620,
    [
        Q((0, 0), (340, 0), (620, 280), (620, 700), (0, 700)),
        Q((414, 0), (620, 0), (620, 206)),
        Cc(230, 300, 390, 480),
    ],
)
DES["R"] = (
    620,
    [
        R(0, 0, 260, 700),
        R(260, 300, 620, 700),
        Cc(360, 420, 500, 580),
        Q((260, 300), (620, 0), (620, 180), (260, 480)),
    ],
)
DES["S"] = (620, [R(0, 0, 620, 700), Cc(200, 400, 620, 480), Cc(0, 220, 420, 300)])
DES["T"] = (620, [R(0, 440, 620, 700), R(180, 0, 440, 700)])
DES["U"] = (620, [R(0, 0, 260, 700), R(360, 0, 620, 700), R(0, 0, 620, 220)])
DES["V"] = (
    620,
    [Q((0, 700), (240, 700), (430, 0), (190, 0)), Q((380, 700), (620, 700), (430, 0), (190, 0))],
)
DES["W"] = (
    620,
    [
        Q((0, 700), (190, 700), (250, 0), (60, 0)),
        Q((230, 700), (390, 700), (230, 0), (70, 0)),
        Q((230, 700), (390, 700), (550, 0), (390, 0)),
        Q((430, 700), (620, 700), (560, 0), (370, 0)),
    ],
)
DES["X"] = (
    620,
    [Q((0, 0), (620, 440), (620, 700), (0, 260)), Q((0, 440), (620, 0), (620, 260), (0, 700))],
)
DES["Y"] = (
    620,
    [
        Q((0, 700), (240, 700), (400, 290), (160, 290)),
        Q((380, 700), (620, 700), (460, 290), (220, 290)),
        R(180, 0, 440, 460),
    ],
)
DES["Z"] = (
    620,
    [R(0, 480, 620, 700), R(0, 0, 620, 220), Q((250, 220), (420, 220), (590, 480), (420, 480))],
)
# --- figures ---
DES["zero"] = (
    620,
    [R(0, 0, 620, 700), Cc(215, 180, 405, 520), Q((215, 520), (215, 400), (405, 180), (405, 300))],
)
DES["one"] = (350, [R(90, 0, 350, 700), R(0, 480, 350, 700)])
DES["two"] = (620, [R(0, 0, 620, 700), Cc(0, 400, 420, 480), Cc(200, 240, 620, 320)])
DES["three"] = (620, [R(0, 0, 620, 700), Cc(0, 400, 300, 480), Cc(0, 220, 300, 300)])
DES["four"] = (620, [R(0, 440, 260, 700), R(0, 240, 620, 440), R(360, 0, 620, 700)])
DES["five"] = (
    620,
    [R(0, 480, 420, 700), R(0, 140, 260, 480), R(0, 140, 620, 300), R(260, 0, 620, 140)],
)
DES["six"] = (620, [R(0, 0, 620, 700), Cc(300, 480, 620, 560), Cc(300, 140, 460, 320)])
DES["seven"] = (620, [R(0, 480, 620, 700), R(360, 0, 620, 480)])
DES["eight"] = (620, [R(0, 0, 620, 700), Cc(230, 400, 390, 560), Cc(230, 140, 390, 300)])
DES["nine"] = (620, [R(0, 0, 620, 700), Cc(0, 140, 320, 220), Cc(160, 380, 320, 560)])
# --- punctuation ---
DES["period"] = (200, [R(0, 0, 200, 200)])
DES["comma"] = (240, [R(0, 0, 220, 200), TAIL(180, 80, 60, -160, 160)])
DES["colon"] = (200, [R(0, 0, 200, 160), R(0, 420, 200, 580)])
DES["semicolon"] = (240, [R(0, 0, 200, 160), R(0, 420, 200, 580), TAIL(160, 80, 40, -160, 160)])
DES["exclam"] = (200, [R(0, 220, 200, 700), R(0, 0, 200, 160)])
DES["question"] = (
    460,
    [R(0, 500, 460, 700), R(260, 340, 460, 500), R(160, 160, 360, 340), R(160, 0, 360, 120)],
)
DES["quotesingle"] = (160, [R(0, 420, 160, 700)])
DES["quotedbl"] = (400, [R(0, 420, 160, 700), R(240, 420, 400, 700)])
DES["hyphen"] = (400, [R(0, 290, 400, 410)])
DES["endash"] = (500, [R(0, 290, 500, 410)])
DES["emdash"] = (620, [R(0, 290, 620, 410)])
DES["parenleft"] = (
    460,
    [
        Q((300, 700), (460, 700), (340, 350), (180, 350)),
        Q((180, 350), (340, 350), (460, 0), (300, 0)),
    ],
)
DES["parenright"] = (
    460,
    [Q((160, 700), (0, 700), (120, 350), (280, 350)), Q((280, 350), (120, 350), (0, 0), (160, 0))],
)
DES["bracketleft"] = (440, [R(60, 0, 200, 700), R(60, 0, 440, 140), R(60, 560, 440, 700)])
DES["bracketright"] = (440, [R(240, 0, 380, 700), R(0, 0, 380, 140), R(0, 560, 380, 700)])
DES["braceleft"] = (
    460,
    [R(340, 0, 460, 700), R(180, 560, 460, 700), R(180, 0, 460, 140), R(0, 300, 360, 400)],
)
DES["braceright"] = (
    460,
    [R(0, 0, 120, 700), R(0, 560, 280, 700), R(0, 0, 280, 140), R(100, 300, 460, 400)],
)
DES["slash"] = (620, [Q((0, 0), (160, 0), (620, 700), (460, 700))])
DES["backslash"] = (620, [Q((460, 0), (620, 0), (160, 700), (0, 700))])
DES["bar"] = (160, [R(0, -60, 160, 760)])
DES["asterisk"] = (
    530,
    [
        R(230, 430, 390, 700),
        R(90, 505, 530, 625),
        Q((120, 480), (210, 480), (500, 650), (410, 650)),
        Q((410, 480), (500, 480), (210, 650), (120, 650)),
    ],
)
DES["plus"] = (620, [R(230, 170, 390, 530), R(10, 270, 610, 430)])
DES["equal"] = (620, [R(60, 380, 560, 500), R(60, 200, 560, 320)])
DES["less"] = (
    500,
    [
        Q((140, 350), (480, 610), (480, 700), (140, 510)),
        Q((140, 190), (480, 0), (480, 90), (140, 350)),
    ],
)
DES["greater"] = (
    500,
    [
        Q((480, 350), (140, 610), (140, 700), (480, 510)),
        Q((480, 190), (140, 0), (140, 90), (480, 350)),
    ],
)
DES["numbersign"] = (
    620,
    [R(100, 0, 260, 700), R(420, 0, 580, 700), R(0, 220, 620, 360), R(0, 460, 620, 600)],
)
DES["percent"] = (
    620,
    [
        R(0, 480, 200, 700),
        Cc(60, 540, 140, 620),
        R(420, 0, 620, 220),
        Cc(480, 60, 560, 140),
        Q((40, 0), (160, 0), (580, 700), (460, 700)),
    ],
)
DES["dollar"] = (
    620,
    [R(0, 0, 620, 700), Cc(200, 400, 620, 480), Cc(0, 220, 420, 300), R(260, -60, 360, 760)],
)
DES["ampersand"] = (
    620,
    [R(0, 380, 620, 700), Cc(260, 460, 620, 540), R(0, 0, 540, 380), Cc(180, 90, 400, 240)],
)
DES["at"] = (
    620,
    [
        Q((0, 0), (620, 0), (620, 300), (540, 300), (540, 400), (620, 400), (620, 700), (0, 700)),
        Cc(80, 80, 540, 620),
        R(180, 180, 440, 520),
        Cc(260, 300, 440, 380),
    ],
)
DES["asciicircum"] = (
    620,
    [Q((0, 440), (240, 440), (310, 520), (380, 440), (620, 440), (400, 700), (220, 700))],
)
DES["underscore"] = (620, [R(0, -60, 620, 40)])
DES["grave"] = (400, [Q((240, 560), (400, 560), (260, 700), (100, 700))])
DES["asciitilde"] = (620, [R(0, 380, 620, 620), Cc(0, 380, 420, 460), Cc(200, 540, 620, 620)])
DES["space"] = (240, [])

KEEP = set(DES.keys()) | set("abcdefghijklmnopqrstuvwxyz")


def master_layer(g):
    for l in g.layers:
        if l.associatedMasterId == master.id:
            return l
    if len(g.layers):
        return g.layers[0]
    nl = GSLayer()
    nl.associatedMasterId = master.id
    g.layers.append(nl)
    return nl


def remove_glyph(g):
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


# drop anything outside the requested set
removed = 0
for g in list(F.glyphs):
    if g.name not in KEEP:
        if remove_glyph(g):
            removed += 1
        else:
            print("could not remove", g.name)
print("removed glyphs:", removed)


def clear_shapes(l):
    errors = []
    try:
        for i in reversed(range(len(l.shapes))):
            del l.shapes[i]
        return
    except Exception as e:
        errors.append(repr(e))
    try:
        for i in reversed(range(len(l.paths))):
            del l.paths[i]
        return
    except Exception as e:
        errors.append(repr(e))
    raise RuntimeError("clear failed: %s" % errors)


def set_unicode(g, name):
    try:
        info = Glyphs.glyphInfoForName(name)
        if info is not None and info.unicode:
            g.unicodes = [info.unicode]
    except Exception:
        pass


created = 0
for name in sorted(DES.keys()):
    nat, parts = DES[name]
    g = F.glyphs[name]
    if g is not None:
        if remove_glyph(g):
            g = None
        else:
            layer = master_layer(g)
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
    layer = master_layer(g)
    for p in parts:
        layer.paths.append(p)
    if name == "space":
        layer.width = nat
    else:
        layer.width = max(60, nat - 30)
    set_unicode(g, name)
print("letters/figures/punct drawn, new glyphs:", created)

for lo, up in zip("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    g = F.glyphs[lo]
    if g is not None:
        if remove_glyph(g):
            g = None
        else:
            layer = master_layer(g)
            clear_shapes(layer)
    if g is None:
        g = GSGlyph(lo)
        F.glyphs.append(g)
        created += 1
    layer = master_layer(g)
    try:
        layer.components.append(GSComponent(up))
    except Exception as e:
        print("component", lo, e)
    layer.width = master_layer(F.glyphs[up]).width
    set_unicode(g, lo)
print("lowercase mapped to caps, total glyphs:", len(F.glyphs))

# --- "Loose spacing" alternates, toggled via ss01 / salt features ---
SP = 50  # sidebearings of the spaced alternates (default letters overlap by 30)


def fresh_glyph(name):
    g = F.glyphs[name]
    if g is not None and not remove_glyph(g):
        g = None
    if g is None:
        g = GSGlyph(name)
        F.glyphs.append(g)
    return g


def clone_paths(parts):
    # DES stores live GSPath objects; appending the same object to two layers
    # aliases them (an LSB shift on one would move the other). Clone instead.
    out = []
    for src in parts:
        p = GSPath()
        p.closed = True
        for nd in src.nodes:
            n = GSNode()
            n.type = nd.type
            n.position = (nd.position.x, nd.position.y)
            p.nodes.append(n)
        out.append(p)
    return out


for name in sorted(DES.keys()):
    if name == "space":
        continue
    nat, parts = DES[name]
    g = fresh_glyph(name + ".spaced")
    layer = master_layer(g)
    for p in clone_paths(parts):
        layer.paths.append(p)
    try:
        layer.LSB = SP
    except Exception:
        for p in layer.paths:
            for nd in p.nodes:
                x, y = nd.position
                nd.position = (x + SP, y)
    layer.width = nat + 2 * SP
print("spaced alternates drawn:", len(DES) - 1)

for lo, up in zip("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    g = fresh_glyph(lo + ".spaced")
    layer = master_layer(g)
    try:
        layer.components.append(GSComponent(up + ".spaced"))
    except Exception as e:
        print("component", lo, e)
    layer.width = master_layer(F.glyphs[up + ".spaced"]).width

subs = ["sub %s by %s.spaced;" % (n, n) for n in sorted(DES.keys()) if n != "space"]
subs += ["sub %s by %s.spaced;" % (l, l) for l in "abcdefghijklmnopqrstuvwxyz"]
feature_code = 'featureNames {\n  name "Loose spacing";\n};\n' + "\n".join(subs)


def set_feature(fname, fcode):
    for f in F.features:
        if f.name == fname:
            f.code = fcode
            return
    nf = GSFeature()
    nf.name = fname
    nf.code = fcode
    F.features.append(nf)


set_feature("ss01", feature_code)
set_feature("salt", "\n".join(subs))
print("features ss01/salt written with %d substitutions" % len(subs))

# --- Weight axis + ExtraBold instance: required for Text Preview / interpolation.
# Note: GSInstance has no weightValue in this API; axis location lives in .axes.
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


def winding_at(layer, px, py):
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


o_layer = master_layer(F.glyphs["O"])
w_wall = winding_at(o_layer, 60.0, 350.0)
w_hole = winding_at(o_layer, 310.0, 350.0)
print("winding check O: wall=%s hole=%s" % (w_wall, w_hole))
if w_wall != 1 or w_hole != 0:
    flipped = 0
    for g in F.glyphs:
        for l in g.layers:
            for p in l.paths:
                p.reverse()
                flipped += 1
    print("REVERSED %s paths (direction fix)" % flipped)
    o_layer = master_layer(F.glyphs["O"])
    print(
        "after fix: wall=%s hole=%s"
        % (winding_at(o_layer, 60.0, 350.0), winding_at(o_layer, 310.0, 350.0))
    )

try:
    F.save("/Users/krfantasy/Developer/bold/MONOLITH.glyphs")
    print("saved /Users/krfantasy/Developer/bold/MONOLITH.glyphs")
except Exception as e:
    print("save failed:", e)
print("DONE")
