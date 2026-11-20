"""A ghost for the end of a wand, with its one last vote in its mouth, in a slot,
to take when it's spent.

The wand is a hexagonal pencil, pressed into a socket in the ghost's hem and
pulled out again to put away: three thin walls in the socket spring against
three of its flats. The ghost prints standing, the vote face down.

The vote has a magnet or steel sealed in its middle, and disc magnets above
the slot hold it. The ghost and the vote are separate prints, and each pauses
for what goes in it, then prints over.

The ghost's face is white with black eyes inlaid, and its mouth is sunk into
it, black at the back. The slot leaves the mouth's back, sheathed in black so
that no white shows down it.

The ghost faces -y, standing on z = 0, its axis the z axis. In the vote's own
frame its face is at z = 0, and the end that goes in the mouth is at -x.

"fit" is the socket alone, at each of `fit_press`, to try on a pencil: the dots
on each count from the loosest. The view "assembly" is the ghost on its pencil,
holding its vote.
"""

from functools import cache
from math import cos, exp, radians, sin, sqrt

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Edge,
    Ellipse,
    Face,
    FontStyle,
    GeomType,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    RegularPolygon,
    Rot,
    Sketch,
    Solid,
    Text,
    Vector,
    Vertex,
    Wire,
    chamfer,
    extrude,
    fillet,
    make_hull,
    mirror,
    scale,
)

from build.cad import Object, Piece, project

# Ghost

# Across the shoulders, where the dome starts.
d = 28
h = 40
shoulder = 25
# A bell: the body is this much wider each side at the hem, and the power sets
# how late it flares.
bell = 4.5
bell_power = 1.8
# The hem ripples below this height.
hem_h = 10
hem_ripple = 1.2
hem_lobes = 6
# Folds in the sheet, from the crown to the hem: how deep, how many, and how
# far they wind round on the way down, in degrees. They fade out over the face.
fold = 0.9
fold_n = 7
fold_twist = 40
foot_chamfer = 0.4

# Eyes

eye_x = 5
eye_z = 31
eye_w = 3.6
eye_h = 5.2
eye_depth = 0.8

# Wand

# The pencil, across its flats and across its corners.
pencil_flats = 7.0
pencil_corners = 8.0
wand_l = 180
# The pencil goes in by its plain end, its dipped end out.
socket_depth = 11
# Around the pencil's corners.
socket_c = 0.15
# Each spring is a wall across the socket, the socket's whole depth, held at
# its ends, with room behind to bend into.
spring_t = 0.5
spring_span = 8
spring_gap = 0.6
# How far the pencil pushes each spring back.
press = 0.15
fit_press = [0, 0.1, 0.2, 0.3]

# Mouth

mouth_z = 18.8
mouth_w = 25
mouth_h = 12
# How far the mouth is sunk into the face, and how thick its black back is.
mouth_depth = 2
mouth_back = 2
# Rounds the mouth's rim over. OCCT can't fillet it by 0.8, where the face
# meets the mouth's sides at a sharp angle, curving away at its corners.
mouth_round = 0.7
# The slot leaves the face this far above the mouth's middle: the vote's
# corners leave it lower, where the face curves away.
slot_rise = 1.2
# The vote sticks out of the mouth this far above level.
slot_angle = 30
slot_depth = 10
# The black around the slot, inside the ghost.
slot_wall = 0.6
slot_c = 0.35
# On the slot's edges, at the back of the mouth: its long edges chamfered,
# its ends further, to lead the vote in from either side. Chamfered, not
# rounded: OCCT can't fillet the ends.
slot_chamfer = 0.5
slot_end_chamfer = 1.5

# Vote

vote_w = 27.4
vote_h = 14.7
vote_t = 3.4
vote_corner = 1.5
vote_chamfer = 0.4
# What's sealed in the vote: a bar magnet for now, and later two steel strike
# plates, 25.4 x 12.7 x 2 in all.
insert = (18.4, 9, 2.5)
# Around the insert's edges, and over it. The pocket is in the vote's middle,
# and with this its floor and its top fall between layers 0.1 high, whether
# the first is 0.2 or 0.25: on one, the slicer could take either side.
insert_c = 0.2
insert_gap = 0.15
label = "VOTE"
font = "Liberation Sans"
# The capitals' height. They're about 0.72 of the font's em.
text_size = 5.5
# Less than the skin over the insert.
inlay = 0.2

# Magnets

# Discs in the ghost, stacked.
mag_d = 6
mag_h = 2
mag_n = 2
mag_c = 0.1
# From the vote's end to the ghost's magnets.
mag_inset = 1
# Between the slot and the ghost's magnet.
mag_skin = 0.6
# Open above the magnets' pocket, under what bridges it.
mag_over = 0.2

r = d / 2
slot_t = vote_t + 2 * slot_c
slot_h = vote_h + 2 * slot_c
mag_r = mag_d / 2 + mag_c
mag_depth = mag_n * mag_h + 2 * mag_c
# What's left hollow in the vote, in its middle, and the skin under it, which
# is the same as over it.
hollow = (insert[0] + 2 * insert_c, insert[1] + 2 * insert_c, insert[2] + insert_gap)
hollow_z = (vote_t - hollow[2]) / 2

assert inlay < hollow_z, "the vote's inlay reaches its insert"


# The skin


def body_r(z: float) -> float:
    """The body's radius below the shoulder, without the ripples or folds."""
    return r + bell * max(0, 1 - z / shoulder) ** bell_power


def radius(z: float, a: float) -> float:
    """The skin's distance from the axis, z high and a degrees round from +x."""
    # Two sets of folds, out of step, so that no two are alike, fading out
    # over the face and toward the crown.
    turn = fold_twist * (1 - z / h)
    off_face = min(abs(a - 270), 360 - abs(a - 270))
    face = 1 - exp(-((off_face / 55) ** 2))
    folds = (
        fold
        * (1 - z / h) ** 0.6
        * face
        * (
            0.6 * cos(radians(fold_n * (a + turn)))
            + 0.4 * cos(radians((fold_n + 4) * (a - 0.6 * turn) + 40))
        )
    )
    if z >= shoulder:
        return folds + r * sqrt(max(0, 1 - ((z - shoulder) / (h - shoulder)) ** 2))
    hem = max(0, 1 - z / hem_h) ** 2
    return folds + body_r(z) + hem_ripple * cos(radians(hem_lobes * a)) * hem


def ring(z: float, inset: float = 0) -> Wire:
    """The skin round at height z, drawn in by `inset`. Every ring is a spline
    by the same parameters, so that the loft through them is one smooth sheet."""
    n = 96
    points = [
        (q * cos(radians(a)), q * sin(radians(a)), z)
        for a in (360 * j / n for j in range(n))
        for q in [radius(z, a) - inset]
    ]
    params = [j / n for j in range(n + 1)]
    return Wire([Edge.make_spline(points, periodic=True, parameters=params)])


@cache
def skin() -> Part:
    """The ghost's whole outside, solid: a 45° chamfer at the foot, the body
    lofted up through rings, and the dome closing to a point at the crown."""
    body_zs = [foot_chamfer] + [1 + 1.5 * k for k in range(16)]
    dome_zs = [shoulder + (h - shoulder) * sin(radians(a)) for a in range(0, 88, 6)]
    foot = Solid.make_loft([ring(0, foot_chamfer), ring(foot_chamfer)], ruled=True)
    body = Solid.make_loft([ring(z) for z in body_zs + dome_zs] + [Vertex(0, 0, h)])
    return Part() + [foot, body]


def inner(depth: float) -> Part:
    """The skin, this far in: shrunk about the shoulder's middle."""
    f = 1 - depth / r
    return Pos(0, 0, shoulder * (1 - f)) * scale(skin(), f)


# Eyes and mouth: holes into the face, from the axis out


def into_face(x: float, z: float, w: float, tall: float) -> Part:
    """An ellipse w across and `tall` high, its middle at (x, z), straight out
    the face from y = 0."""
    return extrude(Plane.XZ * Pos(x, z) * Ellipse(w / 2, tall / 2), d)


def eye_holes() -> Part:
    return Part() + [into_face(s * eye_x, eye_z, eye_w, eye_h) for s in (-1, 1)]


def mouth_hole() -> Part:
    return into_face(0, mouth_z, mouth_w, mouth_h)


# The slot


def slot_frame() -> Location:
    """The slot's own frame: x runs out of the mouth from the slot's end, y
    across the vote, and z up through it, from the slot's floor."""
    c, n = cos(radians(slot_angle)), sin(radians(slot_angle))
    z = mouth_z + slot_rise
    out, up = Vector(0, -c, n), Vector(0, n, c)
    o = Vector(0, -body_r(z), z) - slot_depth * out - slot_t / 2 * up
    return Location(Plane(o, x_dir=out, z_dir=up))


def in_slot(x: float, y: float, z: float) -> Vector:
    """A point in the slot's frame, in the ghost's."""
    return (slot_frame() * Pos(x, y, z)).position


def slot_box(x0: float, x1: float, w: float, z0: float, z1: float) -> Part:
    """A box in the slot's frame: x from x0 to x1, w across, z from z0 to z1."""
    align = (Align.MIN, Align.CENTER, Align.MIN)
    return slot_frame() * Pos(x0, 0, z0) * Box(x1 - x0, w, z1 - z0, align=align)


def slot() -> Part:
    """Out through the face, and well past it."""
    return slot_box(0, slot_depth + d, slot_h, 0, slot_t)


def sheath() -> Part:
    """The black around the slot, from its end out to the face: the vote's
    corners pass the mouth's rim."""
    w = slot_wall
    return slot_box(-w, slot_depth + 1, slot_h + 2 * w, -w, slot_t + w)


def before_sheath() -> Part:
    """All that's in front of the sheath, out to the face and past it: within
    the mouth, it would be an island of white in each layer."""
    w = slot_wall
    ends, out = (-w, slot_t + w), slot_depth + 1
    corners = [in_slot(-w, 0, z) for z in ends] + [
        in_slot(out, 0, z) for z in ends[::-1]
    ]
    # The sheath's side, in y and z, and the same d further out, toward -y.
    side = [Polygon(*[(p.Y - k, p.Z) for p in corners], align=None) for k in (0, d)]
    hull = make_hull([e for f in side for e in f.edges()])
    return extrude(Plane.YZ * hull, slot_h / 2 + w, both=True)


def magnet_pocket() -> Part:
    """The ghost's magnets lie along the slot, above it, their pocket open
    straight up to the pause, to drop them in: the cylinder, and what's above
    its two ends and above its section through its axis, across the slot."""
    at = slot_frame() * Pos(mag_inset + mag_d / 2, 0, slot_t + mag_skin)
    ends = [at * Pos(0, 0, z) * Circle(mag_r) for z in (0, mag_depth)]
    middle = (
        at * Pos(0, 0, mag_depth / 2) * Rot(0, 90, 0) * Rectangle(mag_depth, 2 * mag_r)
    )
    up = Part() + [extrude(f, h, (0, 0, 1)) for f in [*ends, middle]]
    cylinder = at * extrude(Circle(mag_r), mag_depth)
    below = Box(
        2 * d, 2 * d, ghost_pause, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return (cylinder + up) & below


def magnet_top() -> float:
    """The highest point of the magnets' cylinder."""
    top = in_slot(mag_inset + mag_d / 2, 0, slot_t + mag_skin + mag_depth)
    return top.Z + mag_r * sin(radians(slot_angle))


# The magnets go in once the print is past their pocket's top.
ghost_pause = magnet_top() + mag_over
# The vote's insert, once past its hollow.
vote_pause = hollow_z + hollow[2]


# The socket


def socket_parts(press: float, springs: bool = True) -> list[Sketch]:
    """The socket's outline: a triangle of springs around the pencil, its
    corners rounded off, and the room behind each spring. Without the springs,
    the rooms reach the triangle, as above them."""
    g = pencil_flats / 2 - press
    rc = sqrt(g * g + spring_span * spring_span / 4)
    assert rc >= pencil_corners / 2 + socket_c, (
        "the springs are too short to clear the pencil's corners"
    )
    # Its sides square to 90, 210 and 330 degrees, g from the middle.
    triangle = Circle(rc) & Rot(0, 0, -90) * RegularPolygon(2 * g, 3)
    behind = g + (spring_t if springs else 0)
    rooms = [
        Rot(0, 0, 90 + 120 * i)
        * Pos(behind, 0)
        * Rectangle(
            g + spring_t + spring_gap - behind,
            spring_span,
            align=(Align.MIN, Align.CENTER),
        )
        for i in range(3)
    ]
    return [triangle, *rooms]


def socket(press: float) -> Part:
    """The pencil's socket, open at z = 0, under a roof that closes in at 45°,
    to print without support."""
    walls = Pos(0, 0, -1) * extrude(Sketch() + socket_parts(press), socket_depth + 1)
    # The outline above the springs isn't quite convex, which a taper can't
    # take: so its hull, tapered, within it.
    outline = Sketch() + socket_parts(press, False)
    hull = make_hull(outline.edges())
    rise = inradius(hull) - 0.01
    roof = extrude(hull, rise, taper=45) & extrude(outline, rise)
    return walls + Pos(0, 0, socket_depth) * roof


def inradius(convex: Sketch) -> float:
    """How far in a convex outline's sides close on its middle."""
    center = convex.center()
    return min(e.distance_to(center) for e in convex.edges())


# Settings

# The ghost's seams are scattered, not in a line.
ghost_settings = {"seam_position": "random"}
# The sheet's texture: soft bumps on the outside of the white alone, which
# leaves the socket's springs, and the black, smooth.
sheet_settings = {
    "fuzzy_skin": "external",
    "fuzzy_skin_thickness": 0.2,
    "fuzzy_skin_point_distance": 0.3,
    "fuzzy_skin_noise_type": "perlin",
    "fuzzy_skin_scale": 2.5,
    "fuzzy_skin_octaves": 2,
    "fuzzy_skin_persistence": 0.4,
}
# The vote's layers are thin, for its chamfered edges and for its insert's
# hollow to fall between layers (see `insert_c`).
vote_settings = {
    "layer_height": 0.1,
    "top_surface_pattern": "hilbertcurve",
    "bottom_surface_pattern": "hilbertcurve",
}


# The pieces


def ghost() -> list[Piece]:
    """The ghost as it prints, standing."""
    whole = skin()
    eyes = whole & (eye_holes() - inner(eye_depth))
    hole = mouth_hole()
    deep = inner(mouth_depth + mouth_back)
    sunk = hole - deep
    # What's not white about the mouth, from the face in: the black of it is
    # what's deeper than the mouth's sunk face. The sheath reaches the face,
    # and is open down to the black where it passes the mouth's rim.
    rest = sheath() + (hole & before_sheath() & deep)
    slot_cut = slot() + magnet_pocket()
    # The rest cut from the mouth once it's sunk and rounded, and none of it
    # again: cut twice, face on face with the mouth's sides, OCCT leaves no
    # solid.
    white = round_rim(whole - sunk) - eyes - rest - socket(press) - slot_cut
    mouth = (inner(mouth_depth) & (sunk + rest)) - slot_cut
    return [
        Piece(white, "ghost", "white", settings=sheet_settings),
        Piece(eyes, "eyes", "black"),
        Piece(lead_in(mouth), "mouth", "black"),
    ]


def shared(a: Face, b: Face) -> list[Edge]:
    """The edges where two faces meet."""
    return [e for e in a.edges() if any(e.is_same(k) for k in b.edges())]


def round_rim(sunk: Part) -> Part:
    """The mouth's rim rounded over, where its sides meet the face: on the skin
    with nothing but the mouth sunk into it, its rim whole. Rounded after the
    slot crosses it, OCCT fills the mouth back in."""
    face = max(sunk.faces().filter_by(GeomType.BSPLINE), key=lambda f: f.area)
    sides = sunk.faces().filter_by(GeomType.EXTRUSION)
    return fillet([e for f in sides for e in shared(f, face)], mouth_round)


def lead_in(mouth: Part) -> Part:
    """The slot's edges at the back of the mouth: its long ones chamfered, and
    its ends further, within the mouth. Each on its own, then both: OCCT can't
    chamfer the two kinds of edge in one go, where they meet."""
    back = max(mouth.faces().filter_by(GeomType.BSPLINE), key=lambda f: f.area)
    walls = slot().faces()
    edges = [
        e for e in back.edges() if any(w.distance_to(e.center()) < 1e-4 for w in walls)
    ]
    ends = [e for e in edges if e.length < slot_h / 2]
    sides = [e for e in edges if e.length >= slot_h / 2]
    assert len(ends) == 2 and len(sides) == 2, "the slot's mouth isn't four edges"
    return chamfer(sides, slot_chamfer) & chamfer(ends, slot_end_chamfer)


def vote_face() -> Sketch:
    text = Text(label, text_size / 0.72, font, font_style=FontStyle.BOLD)
    return Pos(-text.bounding_box().center()) * text


def vote_text() -> Part:
    """On both sides, in the middle. The face's is flipped, to read from below."""
    face = mirror(extrude(vote_face(), inlay), Plane.XZ)
    return face + Pos(0, 0, vote_t - inlay) * extrude(vote_face(), inlay)


def vote_body() -> Part:
    body = extrude(RectangleRounded(vote_w, vote_h, vote_corner), vote_t)
    faces = body.faces().sort_by(Axis.Z)
    body = chamfer(faces.first.edges() + faces.last.edges(), vote_chamfer)
    sealed = Pos(0, 0, hollow_z) * Box(
        *hollow, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return body - vote_text() - sealed


def vote() -> list[Piece]:
    """The vote as it prints, face down."""
    return placed_vote(Location())


def placed_vote(at: Location) -> list[Piece]:
    return [
        Piece(at * vote_body(), "vote", "firebrick"),
        Piece(at * vote_text(), "text", "white"),
    ]


def fit() -> list[Piece]:
    """The socket alone, in a collar, at each of `fit_press`, with dots to tell
    them by."""
    od = 2 * (pencil_flats / 2 + spring_t + spring_gap) + 6
    pieces = []
    for i, p in enumerate(fit_press):
        collar = extrude(Circle(od / 2), socket_depth)
        collar = chamfer(collar.edges(), 0.5)
        collar -= extrude(Sketch() + socket_parts(p), socket_depth)
        dots = [
            Rot(0, 0, j * 25 - 90)
            * Pos(od / 2 - 1.5, 0, socket_depth - 0.4)
            * extrude(Circle(0.6), 1)
            for j in range(i + 1)
        ]
        pieces.append(
            Piece(Pos(i * (od + 3), 0) * (collar - dots), f"press {p}", "white")
        )
    return pieces


def assembly() -> list[Piece]:
    """On its pencil, its vote in its mouth, face up."""
    held = slot_frame() * Pos(vote_w / 2, 0, slot_t - slot_c) * Rot(180, 0, 0)
    pencil = Pos(0, 0, socket_depth - wand_l) * extrude(
        RegularPolygon(pencil_corners / 2, 6), wand_l
    )
    return ghost() + placed_vote(held) + [Piece(pencil, "pencil", "gray20")]


project(
    __file__,
    objects={
        "ghost": Object(
            ghost,
            "Standing, pausing for its magnets",
            settings=ghost_settings,
            pauses=[ghost_pause],
        ),
        "vote": Object(
            vote,
            "Face down, pausing for its insert",
            settings=vote_settings,
            pauses=[vote_pause],
        ),
        "fit": Object(fit, "The socket alone, at each press, to try on a pencil"),
    },
    views={"assembly": Object(assembly, "On its pencil, its vote in its mouth")},
    # Apart: the vote's layers are thinner than the ghost's.
    plates=["ghost", "vote"],
)
