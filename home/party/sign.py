"""A table sign: "Play Music", a QR code with a note in its middle, and its
address, inlaid in black, flush in a white panel. It stands in two feet, which
slot onto its bottom edge, and pack into pockets in its back, held there by
magnets: three of 5 x 1 mm glued into each foot, and one over each of them in
its pocket's floor, each in a hole with crush ribs. Or it hangs, feet packed,
by a keyhole in its back, on a screw's head.

The panel prints face down, its pockets and keyhole open to the top, the feet
flat beside it, a left and a right.

x is right and y is up, as it reads; z is out of the face, the back at z = 0.

The view "assembly" is how it stands on a table.
"""

from math import cos, radians, sin
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Circle,
    Compound,
    FontStyle,
    Kind,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    Shape,
    Sketch,
    SlotCenterToCenter,
    Text,
    TextAlign,
    chamfer,
    extrude,
    import_svg,
    mirror,
    offset,
    scale,
)

from build.cad import Object, Piece, View, part, project, sketch

# Panel

w = 100
# Panel thickness: the feet's pockets, the magnets over them, and a skin.
t = 6.2
corner_r = 4
edge_chamfer = 0.8
# Panel edge to the text, at the top and bottom.
margin = 9

# Face

# How deep the black goes into the white.
inlay_d = 0.6
# One square of the code.
module_w = 2.4
# Clear white around the code, in squares. Scanners want four.
quiet = 4
# The squares cleared from the code's middle, and the note's size in them.
clear_n = 9
note_n = 7
font = "TeX Gyre Schola"
# Text sizes are about a capital's height, as OpenSCAD has them, which the
# sign was laid out in: the font's em is the size / 0.72.
title = "Play Music"
title_size = 10.4
url = "https://party.paholg.com"
url_size = 4.5

# Feet

# Each foot's place on the bottom edge, from the panel's center, standing.
feet_x = 30
foot_t = 3.2
# How far back the sign leans.
lean = 15
# The foot on the table, ahead of the panel's face and behind it.
foot_front = 12
foot_back = 45
# Under the panel's edge.
base_t = 3
# How far up the panel's back the foot goes, and up its face: the address
# starts at `margin`.
back_h = 32
jaw_h = 6.5
# The front jaw's thickness, and the width of the bars the rest is made of.
jaw_w = 5
bar = 5
# The slot, over the panel's thickness, and how far the bumps on each of its
# walls stand in: twice that, less the first, is what holds the panel.
slot_clear = 0.3
grip = 0.2

# Magnets

magnet_d = 5
magnet_h = 1
# Room for glue: around the magnet, and under it.
magnet_gap = 0.15
magnet_deep = 0.2
# Crush ribs down each hole's wall, and how far into the magnet they reach.
magnet_ribs = 4
magnet_rib_w = 0.8
magnet_rib_press = 0.1
# Foot around its magnet.
magnet_wall = 1.35
# How much deeper the pockets' holes are: the magnets that far apart, for a
# foot to come out by a finger.
magnet_sink = 0.4
# Their places along the foot's base, from the panel's face, and up its back,
# from the slot's floor.
magnet_base = [20, 34]
magnet_up = [18]

# Pockets

# Around a stowed foot, and how far under the panel's back it lies.
gap = 0.3
top_gap = 0.2
# The pockets' bottom, from the panel's, and the wall between the two.
stow_y = 24
stow_wall = 6
# The scoop for a finger, and how far past the feet's heels its middle is.
finger_r = 8
finger_up = 2
# How far short of the heels' ends the wall between the pockets stops, for a
# finger to reach both heels.
wall_back = 12
# Off the feet's edges, top and bottom, and the mouths of what's cut in the
# panel's back.
bed_chamfer = 0.4

# Keyhole

# The screw's head goes in at the bottom, and its shank slides up the slot.
hang_head_d = 9
hang_shank_d = 4.4
# What the head hangs on, and the room behind that for it: the lip prints as
# a ceiling, so the room narrows to the slot at 45 degrees, as a countersunk
# head does.
hang_lip = 1.4
hang_head_h = 3
# How far the screw slides.
hang_len = 8
# The screw's place once hung, from the panel's top.
hang_top = 16

# How far each of the code's squares reaches past its neighbors, so that those
# touching only at a corner are one solid.
hair = 0.01

# The code for `url`, version 3-H, top row first. From segno:
#   segno.make("https://party.paholg.com", error="h", micro=False, boost_error=False)
# H mends 30% of it, which is what lets the note take its middle.
qr = [
    "11111110101010011011001111111",
    "10000010001100010001101000001",
    "10111010001110011011001011101",
    "10111010111011101010101011101",
    "10111010000011001101001011101",
    "10000010001010011111101000001",
    "11111110101010101010101111111",
    "00000000011011001111000000000",
    "00101110101010100010110001001",
    "11010100111100111100111000101",
    "01101111010001110000000100011",
    "01111000101100001010011010010",
    "11010011101100101100101101000",
    "01111100111100001110111100011",
    "01101110000100101010110100101",
    "00110001011101001011010100000",
    "01001111111110111100111001000",
    "01001001110101001010111001011",
    "10110011100011010010110010111",
    "01010101111110000110101110010",
    "10100111011110111111111110000",
    "00000000100010111000100010001",
    "11111110011000111011101010111",
    "10000010111001000100100010010",
    "10111010110111100100111111011",
    "10111010010111101100110011000",
    "10111010111011011011000111101",
    "10000010010110111001100100010",
    "11111110001001001000110010011",
]

qr_n = len(qr)
qr_w = qr_n * module_w
quiet_w = quiet * module_w

# Bottom up: the address, the code, the title.
url_y = margin
qr_y = url_y + url_size + quiet_w
title_y = qr_y + qr_w + quiet_w
# The title's "y" hangs below its line, into the quiet zone's spare room.
h = title_y + title_size + margin

slot_w = t + slot_clear
pocket_d = foot_t + top_gap
heel_h = 4
round_r = 1.2
bump_r = 0.6

hole_d = magnet_d + 2 * magnet_gap
hole_h = magnet_h + magnet_deep
boss_r = hole_d / 2 + magnet_wall
# A magnet's center, in from its bar's outer edge: the boss stands into the
# foot's middle, not out of it.
magnet_in = max(boss_r, bar / 2)
# How far short of a magnet hole's mouth its ribs stop, for the magnet to
# start in.
rib_short = 0.2
# The keyhole's room, from the head's width to the shank's.
hang_taper = (hang_head_d - hang_shank_d) / 2


def slot_xy(v: float, u: float) -> tuple[float, float]:
    """A foot's side is drawn standing: x back along the table, y up from it.
    The slot leans in it, and has a frame of its own: v from the wall at the
    panel's face to the one at its back, u up the panel from the slot's floor."""
    s, c = sin(radians(lean)), cos(radians(lean))
    return (v * c + u * s, base_t + slot_w * s - v * s + u * c)


# Each magnet's place in the foot's side, and the turn from the foot's y to the
# way across the bar it is in.
magnets = [((x, magnet_in), 0.0) for x in magnet_base] + [
    (slot_xy(slot_w + magnet_in, u), 90.0 - lean) for u in magnet_up
]

assert t - pocket_d - magnet_sink - hole_h - inlay_d >= 0.5, (
    "the white under the magnets is too thin"
)
assert foot_t - hole_h >= 0.8, "the foot under its magnet is too thin"
assert t - hang_lip - hang_head_h - inlay_d >= 0.6, (
    "the white under the keyhole is too thin"
)
assert hang_taper <= hang_head_h, (
    "the keyhole's room is too shallow to narrow to its slot"
)
assert (
    h - hang_top - hang_len - hang_head_d / 2
    > stow_y + foot_front + foot_back + finger_up + finger_r + 2
), "the keyhole runs into the pockets"
assert jaw_h < margin - url_size * 0.4, "the front jaw would cover the address"
assert qr_w + 2 * quiet_w <= w, "the code's quiet zone is wider than the panel"


def up(face: Shape, z0: float, height: float) -> Part:
    """A face, drawn up from z0."""
    return Pos(0, 0, z0) * extrude(sketch(face), height, (0, 0, 1))


def grown(face: Shape, d: float, kind: Kind = Kind.INTERSECTION) -> Sketch:
    """Grown by d, or shrunk, for less than nothing: corners kept sharp, or
    with Kind.ARC the convex ones rounded."""
    return sketch(offset(sketch(face), d, kind=kind))


def rounded(face: Shape, r: float) -> Sketch:
    """Its convex corners rounded to r, its concave ones kept sharp."""
    return grown(grown(face, -r), r, Kind.ARC)


# The feet


def foot_2d() -> Sketch:
    """A foot's side: a jaw ahead of the panel, and a triangle of bars behind
    it, up its back."""
    outline = Polygon(
        (-foot_front, 0),
        (foot_back, 0),
        (foot_back, heel_h),
        slot_xy(slot_w + bar, back_h),
        slot_xy(slot_w, back_h),
        slot_xy(slot_w, 0),
        slot_xy(0, 0),
        slot_xy(0, jaw_h),
        slot_xy(-jaw_w, jaw_h),
        (-foot_front, base_t),
        align=None,
    )
    triangle = Polygon(
        (slot_xy(slot_w, 0)[0], 0),
        slot_xy(slot_w, back_h),
        slot_xy(slot_w + bar, back_h),
        (foot_back, heel_h),
        (foot_back, 0),
        align=None,
    )
    shape = rounded(outline, round_r) - grown(grown(triangle, -bar - 2), 2, Kind.ARC)
    # Bumps to hold the panel: a pair near the floor, and one up the back for
    # the panel to lean on.
    bumps = [slot_xy(slot_w + bump_r - grip, u) for u in (3.5, back_h - 4)]
    bumps.append(slot_xy(grip - bump_r, 3.5))
    shape += [Pos(*b) * Circle(bump_r) for b in bumps]
    # Around each magnet, should the bars be narrower than it wants.
    shape += [Pos(*at) * Circle(boss_r) for at, _ in magnets]
    return sketch(shape)


def magnet_hole(depth: float) -> Part:
    """A magnet's hole, its mouth at z = 0, `depth` deep up from it. Crush ribs
    run down its wall, stopping short of the mouth for the magnet to start in."""
    ribs = [
        Rot(0, 0, i * 360 / magnet_ribs)
        * Pos(magnet_d / 2 - magnet_rib_press + 0.5, 0)
        * Rectangle(1, magnet_rib_w)
        for i in range(magnet_ribs)
    ]
    ribbed = Sketch() + Circle(hole_d / 2) - ribs
    return part(
        up(Circle(hole_d / 2), 0, rib_short) + up(ribbed, rib_short, depth - rib_short)
    )


def magnet_holes(z: float, depth: float, mouth_up: bool) -> Part:
    """A hole for each magnet in a foot's side, its mouth at z."""
    hole = magnet_hole(depth)
    if mouth_up:
        hole = part(mirror(hole, Plane.XY))
    return part(Part() + [Pos(x, y, z) * Rot(0, 0, a) * hole for (x, y), a in magnets])


def foot() -> Part:
    """A foot as it prints, and as it lies in its pocket: its magnets go in
    from the top, which is the side that faces the pocket's floor. So the two
    are a left and a right."""
    side, k = foot_2d(), bed_chamfer
    # Chamfered top and bottom by tapering, which chamfer() can't do around
    # the bumps.
    bottom = Pos(0, 0, k) * extrude(side, k, (0, 0, -1), taper=45)
    top = Pos(0, 0, foot_t - k) * extrude(side, k, (0, 0, 1), taper=45)
    body = bottom + up(side, k, foot_t - 2 * k) + top
    return part(body - magnet_holes(foot_t, hole_h, True))


def stow(s: int, shape: Sketch | Part) -> Compound:
    """A foot's place in the panel's back: side s, heel up, its base to the
    middle."""
    turned = Rot(0, 0, 90) * shape
    if s > 0:
        turned = mirror(turned, Plane.YZ)
    return Pos(s * stow_wall / 2, stow_y + foot_front) * turned


# The panel


def plate() -> Part:
    """Rounded corners, chamfered front and back, its bottom edge centered on
    the origin."""
    p = Pos(0, h / 2) * extrude(RectangleRounded(w, h, corner_r), t)
    faces = p.faces().sort_by(Axis.Z)
    return part(chamfer(faces.first.edges() + faces.last.edges(), edge_chamfer))


def pockets_2d() -> Sketch:
    """The feet's pockets, which they drop into, the magnets holding them, and
    the scoop past their heels for a finger to lift them out."""
    pocket = grown(foot_2d(), gap)
    a = stow_wall / 2 - gap
    # The wall between the pockets, its end round, short of the heels. It
    # reaches into the pockets, to be one with them.
    wall_end = Pos(0, -(wall_back + a) / 2) * Rectangle(2 * a + 0.1, wall_back + a)
    wall_end -= Pos(0, -wall_back - a) * Circle(a)
    scoop = Pos(0, stow_y + foot_front + foot_back) * (
        Pos(0, finger_up) * Circle(finger_r) + wall_end
    )
    return sketch(Sketch() + [stow(s, pocket) for s in (-1, 1)] + scoop)


def keyhole_slot(d: float) -> Sketch:
    """The keyhole's slot, d wide, from where the screw ends up, at the origin,
    down to where it goes in."""
    return sketch(Pos(0, -hang_len / 2) * SlotCenterToCenter(hang_len, d, 90))


def keyhole() -> Part:
    """Open to the panel's back: a slot for the screw's shank, a hole at its
    bottom for the head to go in by, and the room behind the lip for the head."""
    entry = Pos(0, -hang_len) * Circle(hang_head_d / 2)
    lip = up(keyhole_slot(hang_shank_d) + entry, 0, hang_lip)
    # The lip prints as a ceiling, so the room narrows from it at 45 degrees.
    narrowing = Pos(0, 0, hang_lip + hang_taper) * extrude(
        keyhole_slot(hang_head_d), hang_taper, (0, 0, -1), taper=45
    )
    room = up(
        keyhole_slot(hang_head_d), hang_lip + hang_taper, hang_head_h - hang_taper
    )
    return part(lip + narrowing + room + up(entry, hang_lip, hang_head_h))


def panel() -> Part:
    body = plate() - up(pockets_2d(), 0, pocket_d)
    body -= Part() + [
        stow(s, magnet_holes(pocket_d, magnet_sink + hole_h, False)) for s in (-1, 1)
    ]
    body -= Pos(0, h - hang_top) * keyhole()
    # The mouths of what's cut in its back, chamfered.
    back = body.faces().sort_by(Axis.Z).first
    body = chamfer(
        [e for wire in back.inner_wires() for e in wire.edges()], bed_chamfer
    )
    return part(body - inlay())


# The face


def code() -> Sketch:
    """The code's black squares, less the middle ones, left out for the note:
    each row's runs of them, a hair over to join their neighbors."""
    lo = (qr_n - clear_n) // 2

    def black(row: int, col: int) -> bool:
        cleared = lo <= row < lo + clear_n and lo <= col < lo + clear_n
        return qr[row][col] == "1" and not cleared

    runs = []
    for row in range(qr_n):
        col = 0
        while col < qr_n:
            if not black(row, col):
                col += 1
                continue
            end = col
            while end + 1 < qr_n and black(row, end + 1):
                end += 1
            at = (col * module_w - qr_w / 2, (qr_n - 1 - row) * module_w + qr_y)
            size = ((end - col + 1) * module_w + hair, module_w + hair)
            runs.append(Pos(*at) * Rectangle(*size, align=(Align.MIN, Align.MIN)))
            col = end + 1
    return sketch(Sketch() + runs)


def note(s: float) -> Sketch:
    """The note, s tall, about the origin. It is Nicu Buculei's, from Open Clip
    Art, in the public domain:
    https://commons.wikimedia.org/wiki/File:Music_note.svg"""
    shape = Sketch() + import_svg(Path(__file__).with_name("note.svg"))
    # Scaled before it's moved: scale() goes wrong on a shape that has been.
    shape = scale(shape, s / shape.bounding_box().size.Y)
    return sketch(Pos(-shape.bounding_box().center()) * shape)


def text(s: str, size: float) -> Sketch:
    """Centered on the origin, its baseline on it."""
    return Text(
        s,
        size / 0.72,
        font,
        font_style=FontStyle.BOLD,
        text_align=(TextAlign.CENTER, TextAlign.BOTTOM),
    )


def inlay() -> Part:
    """The black, flush in the face."""
    drawn = (
        Sketch()
        + Pos(0, title_y) * text(title, title_size)
        + code()
        + Pos(0, qr_y + qr_w / 2) * note(note_n * module_w)
        + Pos(0, url_y) * text(url, url_size)
    )
    return up(drawn, t - inlay_d, inlay_d)


# Put together


def feet() -> list[tuple[Part, str, Location]]:
    """Each foot, its name, and where it lies in its pocket. The right is the
    left turned over, so that, stood the same way, it's the left's mirror
    image."""
    left = foot()
    right = part(Pos(0, 0, foot_t) * mirror(left, Plane.XY))
    # Into place as stow() has it, which mirrors the right.
    across = Pos(0, stow_y + foot_front)
    return [
        (left, "left foot", Pos(-stow_wall / 2, 0) * across * Rot(0, 0, 90)),
        (
            right,
            "right foot",
            Pos(stow_wall / 2, 0, foot_t) * across * Rot(0, 0, 90) * Rot(180, 0, 0),
        ),
    ]


def pieces() -> list[Piece]:
    """The panel and its inlay, and the feet. Put together, it stands in its
    feet, its back's bottom edge in their slots. Printed, the panel lies face
    down, its pockets and keyhole open to the top, and the feet as they lie in
    it, moved out beside it."""
    print(f"  Sign is {w} x {h:g} x {t} mm, and leans back {lean} degrees")
    y, z = slot_xy(slot_clear / 2 + t, 0)
    leaning = Pos(0, y, z) * Rot(90 - lean, 0, 0)
    face_down = Pos(0, 0, t) * Rot(0, 180, 0)
    # A foot's side, drawn in x and y, stands up in y and z.
    standing = Rot(0, 0, 90) * Rot(90, 0, 0) * Pos(0, 0, -foot_t / 2)
    beside = Pos(w / 2 + 50, 10 - stow_y)
    return [
        Piece(panel(), "sign", "white", at=leaning, place=face_down),
        Piece(inlay(), "text", "black", at=leaning, place=face_down),
    ] + [
        Piece(shape, name, "white", at=Pos(s * feet_x) * standing, place=beside * hole)
        for s, (shape, name, hole) in zip((-1, 1), feet())
    ]


project(
    __file__,
    objects={"print": Object(pieces, "The panel face down, and its two feet")},
    views={
        "assembly": View(
            lambda o: o["print"], "Standing in its feet, as on a table", ["print"]
        ),
    },
)
