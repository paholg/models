"""A ghost for the end of a wand, with its one last vote in its mouth, in a slot,
to take when it's spent.

The wand is a hexagonal pencil, pressed into a socket in the ghost's hem and
pulled out again to put away: three thin walls in the socket spring against
three of its flats. The ghost prints standing, the vote face down.

Under the hem, the ghost stands on a rim that follows its edge and on a boss
round the socket, with a groove between that rises to a rounded peak, higher
under the hem's ripples, its sides at 45° to print without support.

The vote has a steel plate sealed in its middle, and a disc magnet above
the slot holds it. The ghost and the vote are separate prints, and each pauses
for what goes in it, then prints over.

The ghost's face is white with black eyes and a black mouth inlaid, flush
with it. The slot leaves the mouth, its lips rounded over into the face, its
sides a long way to lead the vote in at an angle, and is lined with black, so
that no white shows down it.

The ghost faces -y, standing on z = 0, its axis the z axis. In the vote's own
frame its face is at z = 0, and the end that goes in the mouth is at -x.

Each ghost has a `Style`: its eyes, its mouth and its sheet's texture, each
named from EYES, MOUTHS and TEXTURES. Every mouth takes in the whole of the
slot's opening, and the slot is drawn against the plain sheet's face, so it's
the same whatever the style. The folds fade out round the eyes and mouth. "ghost" is the plain
one; each sample, "eyes-angry" say, is the plain one but for one thing, and
the views "eyes", "mouths" and "textures" set each kind's samples in a row.

"fit" is the socket alone, at each of `fit_press`, to try on a pencil: the dots
on each count from the loosest. The view "assembly" is the ghost on its pencil,
holding its vote.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import cache
from math import asin, atan2, cos, degrees, exp, pi, radians, sin, sqrt

import shapely
from build123d import (
    Align,
    Axis,
    Box,
    CenterArc,
    Circle,
    Cylinder,
    Edge,
    Ellipse,
    Face,
    FontStyle,
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
    SlotArc,
    SlotCenterToCenter,
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
    revolve,
    scale,
)

from build.cad import Object, Piece, View, part, project, sketch

# Ghost

# Across the shoulders, where the dome starts.
d = 28
h = 40
shoulder = 25
# A bell: the body is this much wider each side at the hem, and the power sets
# how late it flares.
bell = 4.5
bell_power = 1.8


@dataclass(frozen=True)
class Texture:
    """The sheet's folds and the hem's ripples."""

    # Folds, from the crown to the hem: how deep, how many, and how far they
    # wind round on the way down, in degrees, and how late in the way down
    # they do: 1 evenly, more nearer the hem.
    fold: float = 0.9
    fold_n: int = 7
    twist: float = 40
    twist_power: float = 1
    # A second set of folds, out of step with the first, so that no two are
    # alike: its share of the depth, and how it winds, for each turn of the
    # first's.
    second: float = 0.4
    second_twist: float = -0.6
    # The hem ripples below this height.
    hem_h: float = 10
    hem_ripple: float = 1.2
    hem_lobes: int = 6


TEXTURES = {
    "folds": Texture(),
    # Wound round most of a turn, like a sheet wrung out.
    "swirl": Texture(fold=1.1, fold_n=6, twist=220, second=0),
    # Straight down, close together.
    "pleats": Texture(fold=0.9, fold_n=13, twist=0, second=0),
    # Few, deep and blown round at the hem.
    "windswept": Texture(fold=1.4, fold_n=5, twist=150, twist_power=2.5, second=0.3),
    # Two sets as deep, winding opposite ways, crossing.
    "crossed": Texture(fold=1.1, fold_n=5, twist=160, second=0.5, second_twist=-1),
    # No folds, and a hem of big, slow waves.
    "smooth": Texture(fold=0, hem_h=13, hem_ripple=1.8, hem_lobes=5),
    # A ragged hem of many deep scallops, and the folds.
    "tatters": Texture(hem_h=13, hem_ripple=1.6, hem_lobes=11),
}
# The folds fade out round the eyes and mouth, seen from in front: none
# within `clear_rim` of their outlines, so that the face round them is
# smooth, and all of them `clear_fade` further out.
clear_rim = 1.2
clear_fade = 5
# The slot is drawn against the plain sheet as it was first drawn, with no
# folds this many degrees each side of the face's middle, past the mouth's
# corners: so it's the same whatever the style, and the face, within the
# mouth, is as it was.
slot_clear = 50


@dataclass(frozen=True)
class Style:
    """Which of EYES, MOUTHS and TEXTURES a ghost has."""

    eyes: str = "oval"
    mouth: str = "oval"
    texture: str = "folds"


PLAIN = Style()
foot_chamfer = 0.4
# The groove under the hem: from this radius on the bed, outside the socket's
# springs (about 6.1), out to a rim this wide that follows the hem, its sides
# at 45°, and its peak rounded.
groove_in = 8.5
groove_rim = 2
groove_round = 1

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
# About how thick the mouth's black is: its back is round the axis, where the
# face is nearly. It's thick enough to hold the slot's rounds.
mouth_back = 5.5
# The middle of the slot's thickness leaves the face this high, and the vote
# sticks out of it this far above level.
slot_z = 22
slot_angle = 30
# From the face to the slot's end, along its middle.
slot_depth = 12
# Around the vote: on its faces, and at its sides.
slot_c = 0.4
slot_side_c = 0.5
slot_corner = 0.4
# Where the slot meets the face, its edges round over into it: its
# sides a long way, to lead in a vote coming at an angle, its top and bottom
# a little, and its corners round between.
slot_side_round = 3.25
slot_lip = 0.8
slot_opening_corner = 2.8
# The black lining the slot, inside the white.
lining = 0.6

# Vote

# About 1 mm of wall round the insert's hollow, on its sides and at its
# corners.
vote_w = 28
vote_h = 15.2
vote_corner = 1
# Over the insert, and under it with the gap over it as well, so that the
# steel is in the vote's middle, which can go in the mouth either way up:
# thin, to keep the steel near the ghost's magnets, but six of the vote's
# layers, and more than the inlay.
vote_skin = 0.6
vote_chamfer = 0.4
# What's sealed in the vote: a steel plate, as measured.
insert = (25.5, 12.7, 1.0)
# Around the insert's edges, and over it. The gap over it is more than two of
# the vote's layers (see `vote_settings`): the pause can come a layer early,
# and the hollow's faces can each slice a layer either way, but the insert is
# still at least two layers under the walls' top when it goes in. At 0.15 it
# sat a layer under them, and the floor's top and the steel made that up.
insert_c = 0.2
insert_gap = 0.25
label = "VOTE"
font = "Liberation Sans"
# The capitals' height. They're about 0.72 of the font's em.
text_size = 5.5
# Less than the skin over the insert.
inlay = 0.2

# Magnets

# Discs in the ghost, stacked: one, as wide as fits. Wider holds better than
# taller, across the gap to the steel.
mag_d = 12
mag_h = 3
mag_n = 1
mag_c = 0.1
# From the slot's end to the magnets' axis. As far out as left 1 of wall
# between their pocket and the mouth when it was sunk 2 into the face, in
# front of the pocket's lower edge, so a third of them is off the steel, back
# past the slot's end.
mag_x = 3.5
# Between the slot and the ghost's magnet: thin, to keep them near the
# vote's steel, but each layer of it, sloping with the slot, is 0.8 wide: two
# of a 0.4 nozzle's lines. Less than the slot's lining, so the magnets' pocket
# starts within it, not on its face.
mag_skin = 0.4
# Open above the magnets, under what bridges them. Their pocket is open straight
# up to the pause, so whatever the layers, the first to cover it is this far
# above them or more.
mag_over = 0.2

r = d / 2
# What's left hollow in the vote, how high it starts, and the vote's thickness
# round it, the insert on the hollow's floor in the vote's middle.
hollow = (insert[0] + 2 * insert_c, insert[1] + 2 * insert_c, insert[2] + insert_gap)
hollow_z = vote_skin + insert_gap
vote_t = hollow_z + hollow[2] + vote_skin
slot_t = vote_t + 2 * slot_c
slot_h = vote_h + 2 * slot_side_c
mag_r = mag_d / 2 + mag_c
mag_depth = mag_n * mag_h + 2 * mag_c

assert inlay < hollow_z, "the vote's inlay reaches its insert"
assert mag_skin < lining, "the magnets' pocket starts on the lining's face"


# The skin


def body_r(z: float) -> float:
    """The body's radius below the shoulder, without the ripples or folds."""
    return r + bell * max(0, 1 - z / shoulder) ** bell_power


def sheet(z: float, a: float, texture: Texture, folded: float) -> float:
    """The skin's distance from the axis, z high and a degrees round from +x,
    with `folded` of its folds there."""
    # Two sets of folds, out of step, fading out toward the crown.
    t = texture
    turn = t.twist * (1 - z / h) ** t.twist_power
    folds = (
        t.fold
        * (1 - z / h) ** 0.6
        * folded
        * (
            (1 - t.second) * cos(radians(t.fold_n * (a + turn)))
            + t.second * cos(radians((t.fold_n + 4) * (a + t.second_twist * turn) + 40))
        )
    )
    return folds + plain(z, a, t)


def plain(z: float, a: float, t: Texture) -> float:
    """The sheet without its folds."""
    if z >= shoulder:
        return profile(z)
    hem = max(0, 1 - z / t.hem_h) ** 2
    return body_r(z) + t.hem_ripple * cos(radians(t.hem_lobes * a)) * hem


def radius(z: float, a: float, style: Style) -> float:
    """The skin, its folds fading out round the eyes and mouth."""
    t = TEXTURES[style.texture]
    off_face = (a - 270 + 180) % 360 - 180
    around = profile(z) * radians(off_face)
    return sheet(z, a, t, face_clear(style.eyes, style.mouth)(around, z))


def profile(z: float) -> float:
    """The sheet's radius z high, without the hem's ripples or the folds."""
    if z >= shoulder:
        return r * sqrt(max(0, 1 - ((z - shoulder) / (h - shoulder)) ** 2))
    return body_r(z)


def slot_radius(z: float, a: float) -> float:
    """The skin that the slot is drawn against (see `slot_clear`)."""
    off_face = min(abs(a - 270), 360 - abs(a - 270))
    face = 1 - exp(-((max(0, off_face - slot_clear) / 30) ** 2))
    return sheet(z, a, TEXTURES["folds"], face)


@cache
def face_clear(eyes: str, mouth: str) -> Callable[[float, float], float]:
    """How much of the folds there are at a point on the sheet: none near the
    eyes and mouth, all further out, and between, a smooth step of the
    distance from their outlines. The point is so far round the sheet from the
    face's middle, to the right, and z high: the outlines, which are seen
    from in front, are unrolled likewise, so that the distance is about as
    it is on the sheet, and grows all the way round to the back."""

    def unrolled(x: float, z: float) -> tuple[float, float]:
        q = profile(z)
        return q * asin(max(-1, min(1, x / q))), z

    outlines = [MOUTHS[mouth](), *eye_outlines(eyes)]
    features = shapely.unary_union(
        [
            shapely.Polygon(
                [
                    unrolled(v.X, v.Y)
                    for v in (
                        face.outer_wire().position_at(i / 400) for i in range(400)
                    )
                ]
            )
            for outline in outlines
            for face in outline.faces()
        ]
    )
    shapely.prepare(features)

    def clear(x: float, z: float) -> float:
        k = (shapely.distance(features, shapely.Point(x, z)) - clear_rim) / clear_fade
        k = min(1.0, max(0.0, k))
        return k * k * (3 - 2 * k)

    return clear


def ring(z: float, inset: float, style: Style) -> Wire:
    """The skin round at height z, drawn in by `inset`. Every ring is a spline
    by the same parameters, so that the loft through them is one smooth sheet."""
    n = 96
    points: list[Vector | Sequence[float]] = [
        (q * cos(radians(a)), q * sin(radians(a)), z)
        for a in (360 * j / n for j in range(n))
        for q in [radius(z, a, style) - inset]
    ]
    params = [j / n for j in range(n + 1)]
    return Wire([Edge.make_spline(points, periodic=True, parameters=params)])


@cache
def skin(style: Style) -> Part:
    """The ghost's whole outside, solid: a 45° chamfer at the foot, the body
    lofted up through rings, and the dome closing to a point at the crown."""
    body_zs = [foot_chamfer] + [1 + 1.5 * k for k in range(16)]
    dome_zs = [shoulder + (h - shoulder) * sin(radians(a)) for a in range(0, 88, 6)]
    foot = Solid.make_loft(
        [ring(0, foot_chamfer, style), ring(foot_chamfer, 0, style)], ruled=True
    )
    body = Solid.make_loft(
        [ring(z, 0, style) for z in body_zs + dome_zs] + [Vertex(0, 0, h)]
    )
    return part(Part() + [foot, body])


def inner(depth: float, style: Style) -> Part:
    """The skin, this far in: shrunk about the shoulder's middle."""
    f = 1 - depth / r
    return part(Pos(0, 0, shoulder * (1 - f)) * scale(skin(style), f))


def groove(style: Style) -> Part:
    """The groove under the hem, reaching below the bed to cut cleanly: inside
    the hem's outline drawn in by the rim, closing in at 45°, and outside a
    cone round the socket, opening out at 45°. Its peak is where they meet,
    higher where the hem ripples out."""
    # Above its peak, which is at most about 5. Drawn in toward the axis, not
    # offset, which would pinch where the ripples curve tightly.
    tall = 7
    rim = foot_chamfer + groove_rim
    outer = Solid.make_loft(
        [Pos(0, 0, z) * ring(0, rim + z, style) for z in (-1, tall)], ruled=True
    )
    cone = Polygon((0, -1), (groove_in - 1, -1), (groove_in + tall, tall), (0, tall))
    cut = outer - revolve((Plane.XZ * cone).faces(), Axis.Z)
    ridge = [e for e in cut.edges() if e.center().Z > 0.5]
    return part(fillet(ridge, groove_round))


# The face: outlines as seen from in front of it, x across, to the right, and
# y up, which is the ghost's z; cut into it straight out from y = 0.


def into_face(outline: Sketch) -> Part:
    return extrude(Plane.XZ * outline, d)


# Eyes, each drawn about its middle, given which side it's on: 1 on the right.


def brow(cut: float, tilt: float) -> Sketch:
    """What's above a line `cut` above an eye's middle, raised by `tilt`
    degrees on the right."""
    return sketch(
        Rot(0, 0, tilt)
        * Pos(0, cut)
        * Rectangle(20, 10, align=(Align.CENTER, Align.MIN))
    )


def bar(length: float, angle: float, w: float = 1.2) -> Sketch:
    """A stroke with round ends, `angle` from across."""
    return sketch(Rot(0, 0, angle) * SlotCenterToCenter(length - w, w))


EYES: dict[str, Callable[[int], Sketch]] = {
    "oval": lambda s: sketch(Ellipse(eye_w / 2, eye_h / 2)),
    "round": lambda s: sketch(Circle(2.2)),
    # Brows down toward the nose.
    "angry": lambda s: sketch(Ellipse(2.1, 2.8) - brow(0.5, s * 28)),
    # Brows down toward the cheeks.
    "sad": lambda s: sketch(Ellipse(2.1, 2.8) - brow(0.5, -s * 28)),
    # Lids half down.
    "sleepy": lambda s: sketch(Ellipse(2.2, 2.6) - brow(0.3, 0)),
    # Arches, ^ ^.
    "happy": lambda s: sketch(
        Pos(0, -1.2) * SlotArc(CenterArc((0, 0), 2.2, 25, 130), 1.2)
    ),
    # Big, tall and hollow.
    "hollow": lambda s: sketch(Ellipse(2.5, 3.7)),
    # One big and one small.
    "odd": lambda s: sketch(Circle(2.6) if s < 0 else Pos(0, 0.6) * Circle(1.5)),
    # Crosses, X X.
    "dead": lambda s: sketch(bar(4.6, 45) + bar(4.6, -45)),
    # Squeezed shut, > <, each pointing in.
    "squint": lambda s: sketch(
        Sketch() + [Pos(-s * 0.8, t * 1.1) * bar(3.4, t * s * 35) for t in (-1, 1)]
    ),
}


def eye_outlines(eyes: str) -> list[Sketch]:
    return [Pos(s * eye_x, eye_z) * EYES[eyes](s) for s in (-1, 1)]


def eye_holes(eyes: str) -> Part:
    return part(Part() + [into_face(e) for e in eye_outlines(eyes)])


# Mouths: the oval's top, which takes in the whole of the slot's opening, and a
# lower lip of its own. The lip stays under `mouth_core` where the oval's
# lower half is wider than the core, and turns up into the oval's sides.

# Below this, the slot's opening doesn't reach the oval's sides.
mouth_core = 16.2


def lip(depth: Callable[[float], float], power: float = 2) -> Sketch:
    """The oval, but for its lower half: `depth(u)` times as far below the
    middle, u across from -1 on the left to 1 on the right, of a superellipse
    of this power, which is the oval's lower half at 2 and squarer above it."""
    a, b = mouth_w / 2, mouth_h / 2
    top = [
        (a * cos(radians(t)), mouth_z + b * sin(radians(t))) for t in range(0, 180, 5)
    ]
    bottom = []
    for t in range(180, 360, 3):
        u = cos(radians(t))
        below = (1 - abs(u) ** power) ** (1 / power)
        bottom.append((a * u, mouth_z - b * below * depth(u)))
    points: list[Vector | Sequence[float]] = [Vector(x, y) for x, y in top + bottom]
    return sketch(Face(Wire([Edge.make_spline(points, periodic=True)])))


def bump(u: float, at: float, width: float) -> float:
    return exp(-(((u - at) / width) ** 2))


MOUTHS: dict[str, Callable[[], Sketch]] = {
    "oval": lambda: sketch(Pos(0, mouth_z) * Ellipse(mouth_w / 2, mouth_h / 2)),
    # Dropped open, Oooo.
    "wail": lambda: lip(lambda u: 1.6 - 0.2 * u * u),
    # Wide and square below, like a carved pumpkin's.
    "grin": lambda: lip(lambda u: 1.3, power=4),
    # High in the middle, its corners drooping.
    "frown": lambda: lip(lambda u: 0.55 + 4 * u**6),
    # Two teeth up from the lower lip.
    "fangs": lambda: lip(
        lambda u: 1.15 - 0.5 * (bump(u, -0.38, 0.15) + bump(u, 0.38, 0.15))
    ),
    # A lower lip of waves.
    "wavy": lambda: lip(lambda u: 1.25 + 0.22 * cos(3.5 * pi * u)),
    # Dropped further on the right than the left.
    "lopsided": lambda: lip(lambda u: 1.05 + 0.35 * (1 + u)),
}


def mouth_hole(mouth: str) -> Part:
    return into_face(MOUTHS[mouth]())


# The slot: points are in its frame, (along, across, up), as in `slot_frame()`.


def slot_axes() -> tuple[Vector, Vector]:
    """Out of the slot along it, and up through the vote."""
    c, n = cos(radians(slot_angle)), sin(radians(slot_angle))
    return Vector(0, -c, n), Vector(0, n, c)


def skin_y(z: float) -> float:
    """Where the face is, in the middle, z high."""
    return -slot_radius(z, 270)


@cache
def slot_origin() -> Vector:
    """The slot's end at its floor, in the middle."""
    out, up = slot_axes()
    leave = Vector(0, skin_y(slot_z), slot_z)
    return leave - slot_depth * out - slot_t / 2 * up


def slot_frame() -> Location:
    """The slot's own frame: x runs out of the mouth from the slot's end, y
    across the vote, and z up through it, from the slot's floor."""
    out, up = slot_axes()
    return Location(Plane(slot_origin(), x_dir=out, z_dir=up))


def in_slot(x: float, y: float, z: float) -> Vector:
    """A point in the slot's frame, in the ghost's."""
    out, up = slot_axes()
    return slot_origin() + out * x + Vector(y, 0, 0) + up * z


def behind_face(p: Vector) -> float:
    """How far p is behind the face, across from the axis: less than 0 in
    front of it."""
    x, y, z = p.X, p.Y, p.Z
    across = sqrt(x * x + y * y)
    if not 0 < z < h:
        return -across
    return slot_radius(z, degrees(atan2(y, x)) % 360) - across


def face_along(w: float, v: float) -> float:
    """How far along the slot its line w across and v up leaves the face: by
    false position, which the face's smoothness makes quick. From the slot's
    end to d along, which is out of the ghost and still below its crown."""
    lo, hi = 0.0, d
    flo, fhi = behind_face(in_slot(lo, w, v)), behind_face(in_slot(hi, w, v))
    side = 0
    for _ in range(60):
        m = (lo * fhi - hi * flo) / (fhi - flo)
        fm = behind_face(in_slot(m, w, v))
        if abs(fm) < 1e-7:
            break
        if fm > 0:
            lo, flo = m, fm
            fhi, side = (fhi / 2, 1) if side == 1 else (fhi, 1)
        else:
            hi, fhi = m, fm
            flo, side = (flo / 2, -1) if side == -1 else (flo, -1)
    return m


def opening_ring(t: float) -> list[list[tuple[float, float, float]]]:
    """Round the slot's edge, at t of the way, from 0 on its walls to 90° on
    the face: the slot's section, grown in a quarter circle by its rounds,
    each of its points that far behind the face. Its sides, top and
    bottom, and corners, each as points (across, up, along)."""
    grow_s, grow_t = (q * (1 - cos(t)) for q in (slot_side_round, slot_lip))
    a, b = slot_h / 2 + grow_s, slot_t / 2 + grow_t
    k = slot_corner + (slot_opening_corner - slot_corner) * (1 - cos(t))
    # Past the face at the end, to cross it, not to end on it.
    past = 0.4

    def point(w: float, v: float, side: float) -> tuple[float, float, float]:
        rounds = slot_side_round * side + slot_lip * (1 - side)
        behind = (rounds + past) * (1 - sin(t)) - past
        return (w, v, face_along(w, v) - behind)

    n = 6
    edges = []
    for j in range(4):
        # Counter-clockwise from the right side, each corner after its side.
        c, s = cos(pi / 2 * j), sin(pi / 2 * j)
        half_along, half_from = (b - k, a) if j % 2 == 0 else (a - k, b)
        side = 1.0 if j % 2 == 0 else 0.0
        straight = []
        for i in range(n + 1):
            f, g = half_from, half_along * (2 * i / n - 1)
            straight.append(point(f * c - g * s, slot_t / 2 + f * s + g * c, side))
        corner = []
        for i in range(n + 1):
            q = pi / 2 * (j + i / n)
            cx = (a - k) * (1 if j in (0, 3) else -1)
            cy = (b - k) * (1 if j in (0, 1) else -1)
            blend = cos(q - pi / 2 * j) ** 2 if j % 2 == 0 else sin(q - pi / 2 * j) ** 2
            corner.append(point(cx + k * cos(q), slot_t / 2 + cy + k * sin(q), blend))
        edges += [straight, corner]
    return edges


@cache
def slot() -> Part:
    """The slot, from its end out along its walls, which round over into the
    face, and on out of it: lofted through
    rings round its edge, from and to flat ends, to close the loft.

    The rounds cross the face, not meet it face on face: OCCT is slow to
    cut surfaces that touch, and can fail to."""
    out, _ = slot_axes()
    rings = [opening_ring(radians(t)) for t in range(0, 91, 15)]

    def wire(
        edges: list[list[tuple[float, float, float]]], along: float | None = None
    ) -> Wire:
        return Wire(
            [
                Edge.make_spline(
                    [in_slot(q if along is None else along, w, v) for w, v, q in e]
                )
                for e in edges
            ]
        )

    start = min(q for e in rings[0] for _, _, q in e) - 0.3
    end = max(q for e in rings[-1] for _, _, q in e) + 1
    ends = [wire(rings[0], start), wire(rings[-1], end)]
    lofted = Solid.make_loft([ends[0], *map(wire, rings), ends[1]], ruled=True)
    # Back to the slot's end, from the loft's own end, to meet it exactly.
    return part(Part() + [lofted, extrude(Face(ends[0]), start, -out)])


def lining_tube() -> Part:
    """Black round the slot, from its end into the mouth's black."""
    outline = RectangleRounded(
        slot_h + 2 * lining, slot_t + 2 * lining, slot_corner + lining
    )
    tube = (
        slot_frame()
        * Pos(-lining, 0, slot_t / 2)
        * Rot(0, 90, 0)
        * extrude(Rot(0, 0, 90) * outline, slot_depth)
    )
    middle = body_r(mouth_z) - mouth_back / 2
    return part(
        tube & Cylinder(middle, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )


def magnet_pocket() -> Part:
    """The ghost's magnets lie along the slot, above it, their pocket open
    straight up to the pause, to drop them in: the cylinder, and what's above
    its two ends and above its section through its axis, across the slot."""
    at = slot_frame() * Pos(mag_x, 0, slot_t + mag_skin)
    ends = [at * Pos(0, 0, z) * Circle(mag_r) for z in (0, mag_depth)]
    middle = (
        at * Pos(0, 0, mag_depth / 2) * Rot(0, 90, 0) * Rectangle(mag_depth, 2 * mag_r)
    )
    up = Part() + [extrude(f, h, (0, 0, 1)) for f in [*ends, middle]]
    cylinder = at * extrude(Circle(mag_r), mag_depth)
    below = Box(
        2 * d, 2 * d, ghost_pause, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return part(part(cylinder + up) & below)


def magnet_top() -> float:
    """The highest point of the magnets' cylinder."""
    top = in_slot(mag_x, 0, slot_t + mag_skin + mag_depth)
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
    triangle = sketch(Circle(rc) & Rot(0, 0, -90) * RegularPolygon(2 * g, 3))
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
    walls = Pos(0, 0, -1) * extrude(
        sketch(Sketch() + socket_parts(press)), socket_depth + 1
    )
    # The outline above the springs isn't quite convex, which a taper can't
    # take: so its hull, tapered, within it.
    outline = sketch(Sketch() + socket_parts(press, False))
    hull = make_hull(outline.edges())
    rise = inradius(hull) - 0.01
    roof = extrude(hull, rise, taper=45) & extrude(outline, rise)
    return part(walls + Pos(0, 0, socket_depth) * roof)


def inradius(convex: Sketch) -> float:
    """How far in a convex outline's sides close on its middle."""
    center = convex.center()
    return min(e.distance_to(center) for e in convex.edges())


# Settings

# The ghost's seams are scattered, not in a line.
ghost_settings = {"seam_position": "random"}
# The vote's layers are thin, for its chamfered edges and for the room over its
# insert to be more than a layer (see `insert_c`).
vote_settings = {
    "layer_height": 0.1,
    "top_surface_pattern": "hilbertcurve",
    "bottom_surface_pattern": "hilbertcurve",
    # What bridges the insert's hollow is a layer's height, not the nozzle's: a
    # thick bridge is a round thread the nozzle's width, 0.4, hanging that far
    # below the nozzle, down onto the insert's top, which is 0.4 under the
    # bridge's layer top.
    "thick_bridges": False,
    "thick_internal_bridges": False,
}


# The pieces


def ghost(style: Style = PLAIN) -> list[Piece]:
    """The ghost as it prints, standing."""
    # The white and the black are each cut from the same shapes, not one from
    # the other: they meet face on face, and OCCT takes tens of seconds to
    # cut one from the other there. Nor does anything cut from either meet
    # its faces face on face: each reaches past what it leaves.
    whole = skin(style)
    eye_cut = eye_holes(style.eyes) - inner(eye_depth, style)
    hole = mouth_hole(style.mouth)
    deep = hole - Cylinder(body_r(mouth_z) - mouth_back, h)
    # The slot is within its lining and the mouth's black, so the white
    # needn't be cut by it too.
    magnets = magnet_pocket()
    tube = lining_tube()
    white = whole - (deep + tube + eye_cut + socket(press) + magnets + groove(style))
    black = (part(deep + tube) & whole) - (slot() + magnets)
    return [
        Piece(white, "sheet", "white", parent="ghost"),
        Piece(whole & eye_cut, "eyes", "black", parent="ghost"),
        Piece(black, "mouth", "black", parent="ghost"),
    ]


def vote_face() -> Sketch:
    text = Text(label, text_size / 0.72, font, font_style=FontStyle.BOLD)
    return Pos(-text.bounding_box().center()) * text


def vote_text() -> Part:
    """On both sides, in the middle. The face's is flipped, to read from below."""
    face = mirror(extrude(vote_face(), inlay), Plane.XZ)
    return part(face + Pos(0, 0, vote_t - inlay) * extrude(vote_face(), inlay))


def vote_body() -> Part:
    body = extrude(RectangleRounded(vote_w, vote_h, vote_corner), vote_t)
    faces = body.faces().sort_by(Axis.Z)
    body = chamfer(faces.first.edges() + faces.last.edges(), vote_chamfer)
    sealed = Pos(0, 0, hollow_z) * Box(
        *hollow, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return part(body - vote_text() - sealed)


def vote() -> list[Piece]:
    """The vote as it prints, face down."""
    return placed_vote(Location())


def placed_vote(at: Location) -> list[Piece]:
    return [
        Piece(at * vote_body(), "body", "firebrick", parent="vote"),
        Piece(at * vote_text(), "text", "white", parent="vote"),
    ]


def fit() -> list[Piece]:
    """The socket alone, in a collar, at each of `fit_press`, with dots to tell
    them by."""
    od = 2 * (pencil_flats / 2 + spring_t + spring_gap) + 6
    pieces = []
    for i, p in enumerate(fit_press):
        collar = extrude(Circle(od / 2), socket_depth)
        collar = chamfer(collar.edges(), 0.5)
        collar -= extrude(sketch(Sketch() + socket_parts(p)), socket_depth)
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
    held = slot_frame() * Pos(slot_c + vote_w / 2, 0, slot_t - slot_c) * Rot(180, 0, 0)
    pencil = Pos(0, 0, socket_depth - wand_l) * extrude(
        RegularPolygon(pencil_corners / 2, 6), wand_l
    )
    return ghost() + placed_vote(held) + [Piece(pencil, "pencil", "gray20")]


# Samples, each the plain ghost but for one thing, in rows of each.
samples = {
    f"{kind}-{name}": replace(PLAIN, **{kind: name})
    for kind, names in [("eyes", EYES), ("mouth", MOUTHS), ("texture", TEXTURES)]
    for name in names
    if replace(PLAIN, **{kind: name}) != PLAIN
}


def row(kind: str) -> View:
    names = [n for n in samples if n.startswith(f"{kind}-")]

    def arrange(objects: Mapping[str, list[Piece]]) -> list[Piece]:
        return [
            replace(
                p,
                shape=Pos(k * (d + 2 * bell + 6)) * p.shape,
                name=f"{name} {p.name}",
                parent=f"{name}/{name} {p.parent}",
            )
            for k, (name, pieces) in enumerate(objects.items())
            for p in pieces
        ]

    return View(arrange, f"Each {kind}, beside the plain ghost", ["ghost", *names])


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
        **{
            name: Object(
                lambda style=style: ghost(style),
                f"With {style}",
                settings=ghost_settings,
                pauses=[ghost_pause],
            )
            for name, style in samples.items()
        },
    },
    views={
        "assembly": Object(assembly, "On its pencil, its vote in its mouth"),
        "eyes": row("eyes"),
        "mouths": row("mouth"),
        "textures": row("texture"),
    },
    # Apart: the vote's layers are thinner than the ghost's.
    plates=["ghost", "vote"],
)
