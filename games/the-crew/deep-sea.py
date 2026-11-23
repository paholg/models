"""The Crew: Mission Deep Sea: a one-piece insert for the whole box, under the
manuals.

x is across the box, y along it, z up, from the insert's own corner.

Along the box:
1. The main cards, sleeved, in one stack lying across the box in a corner at
   its end (y = 0), on a floor raised by `bump`. Beside them the two cardboard
   tokens stand on edge, together, in one slot along the box, against the
   cards' wall, its floor following the two of them, the half round and the
   oval. They're pinched by their faces: through an opening in the cards'
   wall, once the cards are out, and from a finger pocket on their other side.
2. The middle, open from the top down to the box's own bottom: the main cards
   are scooped out from here, their wall toward it open for most of its
   width, and their floor cut back under them. At its far side the sonar
   tokens lie in a stack, flush with the top, in a round well whose side
   toward the middle is gone: to lift out as many as are wanted. The well goes
   well over half way round them, solid from there to the cards' walls, so
   they don't slide out. The rail at the other side dips, to get a finger
   under the manuals.
3. The task cards in two stacks along the box, one at each side. Between them
   the box is open to its bottom again, on from the middle, and each stack's
   wall open onto that, its floor cut back.
4. At the far end, the task cards' labels, each by its stack: TODO and DONE,
   read from the middle.

Every stack of cards' well is the insert's full height.

The insert prints as it lies, in one color, with the labels inlaid in its top
in two more. The view is the insert with what goes in it.
"""

from collections.abc import Mapping
from functools import cache
from math import cos, pi, sin

from build123d import (
    Align,
    Circle,
    Cylinder,
    Ellipse,
    FontStyle,
    Location,
    Part,
    Plane,
    Pos,
    Sketch,
    Text,
    extrude,
)

from build.cad import Object, Piece, View, project, sketch
from designs.tray import (
    Slot,
    carve,
    cuboid,
    eased,
    fillet_r,
    grown,
    notch,
    octagon,
    pinch,
    pinch_top_r,
    polygon,
    rect,
    toward_minus_x,
    toward_minus_y,
    toward_plus_x,
    up,
    well,
)

# Box

# Inside, measured.
box = (122, 172, 38)
# The insert, across and along: a millimeter less each side was loose.
size = (121.5, 172)
# Left over the insert, for the manuals.
manuals = 4
h = box[2] - manuals

wall = 1.2
floor_t = 1.2
# The chamfer round the foot of everything: OCCT can't make it of all the
# foot's edges at once much wider.
foot_c = 0.4
# Room round a stack in its well.
stack_clear = 1.5

# Contents

# The main cards, in their sleeves: width, length.
sleeve = (59, 93)
# A task card, unsleeved: width, length.
task = (44, 68)
# The sonar tokens, round: across, thick, and how many.
token_d = 28.1
token_t = 2.06
token_n = 5
# The two cardboard tokens that stand in one slot, side by side, each as thick
# as a sonar token. Measured off a photo of them by a ruler, but for the half
# round's length and the oval's width, which are measured.
# The half round, with a slot in it: along its straight edge, from that to the
# bottom of its curve, and how full the curve is, as a superellipse's
# exponent: 2 is half an ellipse.
half_round = (56, 21)
half_round_n = 2.3
# The oval, an ellipse, lying on its side: long, across.
oval = (42, 28)
# Room round them in their slot.
tile_clear = 0.5
# The sonar tokens' stack comes this far short of the top.
under = 0.5
# Room round the sonar tokens, across: little, as their well's side is open.
token_clear = 0.7

# The middle, and the decks' openings

# What's left at the side of the middle, to hold the ends together.
rail = 2
# A dip in the top of it, to get a finger under the manuals that lie over the
# insert: across, down from the top, and the round-over of its sides.
lift = (20, 12)
lift_r = 4
# How much of a deck's wall stays at each side of its opening, below the
# opening's round-over.
main_post = 12
task_post = 12
# The main cards' floor is this much higher than the others', to get a finger
# under them more easily.
bump = 2
# The decks' floors stop this far inside the cards' edge at their openings.
under_cards = 6
cut_back = stack_clear / 2 + under_cards
# The task cards' labels' strip, at the far end.
label_strip = 8

# The cardboard tokens' pinch: across it, the round-over of its walls, and how
# far down from the top it goes.
tile_grip = 24
tile_grip_r = 3
tile_grip_d = 20
# The sonar tokens' well is solid to the cards' walls at each side for this far
# past the tokens' middle, to keep them from sliding out: they only lift out.
token_wrap = 10
# Where the well's wall ends at its opening, it's rounded by this.
token_lip_r = 1

# The main cards' well, across the box, in the corner at the origin.
main_well = (sleeve[1] + stack_clear, sleeve[0] + stack_clear)
main_at = (wall, wall)
main_floor = floor_t + bump
# Its wall toward the middle, inside, and its opening: its middle, and across.
main_face = main_at[1] + main_well[1]
main_x = main_at[0] + main_well[0] / 2
main_open = main_well[0] - 2 * main_post

# Beside the main cards, the cardboard tokens: what's left of the box's width,
# between walls.
side_x = (main_at[0] + main_well[0] + wall, size[0] - wall)
side_y = main_at[1] + main_well[1] / 2
# Their slot, along the box, against the main cards' wall: across it, along
# it, and its deepest.
tile_slot = (2 * token_t + 0.6, half_round[0] + 2 * tile_clear)
tile_depth = oval[1] + tile_clear
tile_x = (side_x[0], side_x[0] + tile_slot[0])

# The task cards' wells, along the box, at each side, the labels beyond them.
task_well = (task[0] + stack_clear, task[1] + stack_clear)
task_y = size[1] - label_strip - task_well[1]
task_xs = (wall, size[0] - wall - task_well[0])
task_open = task_well[1] - 2 * task_post
# Between them, open: from, to.
gap_x = (task_xs[0] + task_well[0] + wall, task_xs[1] - wall)

# The middle: from the main cards' wall to the task cards'.
middle_y = (main_face + wall, task_y - wall)

# The sonar tokens' well, in the middle, at its far side: its middle, and its
# floor. If it's wider than the middle, it takes that from the walls.
token_r = (token_d + token_clear) / 2
token_at = (size[0] - wall - token_r, (middle_y[0] + middle_y[1]) / 2)
token_floor = h - under - token_n * token_t
token_bite = token_r - (middle_y[1] - middle_y[0]) / 2
# Half way round the ends of the tokens' well's wall, where they're nearest
# each other: how far short of the tokens' middle, and how far apart they are.
token_lip = token_wrap - token_lip_r
# The tokens' floor runs as far as those ends do, to a flat face below it.
token_face = token_at[0] - token_wrap
token_open = 2 * (((token_r + token_lip_r) ** 2 - token_lip**2) ** 0.5 - token_lip_r)

# Labels

font = "Orbitron"
# Each by its stack, as read from the middle of the box: so TODO is on that
# reader's left, at the near x.
labels = ("TODO", "DONE")
# The most a label takes of its strip: along x, and along y.
label_size = (24, label_strip - 2.5)
# Inlaid this deep in the top: three 0.2 mm layers.
label_d = 0.6
label_y = size[1] - label_strip / 2

# Colors, and the filaments they stand for.
body_color = "white"
label_colors = {"TODO": "gold", "DONE": "limegreen"}
filaments = {body_color: "main", "gold": "todo", "limegreen": "done"}

assert side_x[1] - tile_x[1] >= 15, "no room for a finger beside the cardboard tokens"
assert tile_slot[1] <= main_well[1], "the cardboard tokens' slot is too long"
assert h - tile_depth >= floor_t, "the cardboard tokens are too tall"
assert wall - max(token_bite, 0) >= 0.9, "the sonar tokens' well leaves too little wall"
assert token_face - pinch_top_r >= main_x + main_open / 2 + pinch_top_r, (
    "the sonar tokens are in the way of the main cards' opening"
)
assert token_open <= token_d - 2.5, "the sonar tokens' well is open too wide"
assert gap_x[1] - gap_x[0] >= 20, "no room for fingers between the task cards"


def half_round_outline(grow: float = 0) -> Sketch:
    """The half round's outline, its straight edge on y = 0, centered, and its
    curve below; grown by `grow`, but for that edge."""
    a, b, n, steps = half_round[0] / 2 + grow, half_round[1] + grow, half_round_n, 48
    curve = [
        (
            a * abs(cos(t)) ** (2 / n) * (1 if cos(t) > 0 else -1),
            -b * sin(t) ** (2 / n),
        )
        for t in (pi * i / steps for i in range(steps + 1))
    ]
    return polygon(curve)


def oval_outline(grow: float = 0) -> Sketch:
    """The oval's outline, on its side, its top at y = 0, centered; grown by
    `grow`."""
    a, b = oval[0] / 2, oval[1] / 2
    return sketch(Pos(0, -b) * Ellipse(a + grow, b + grow))


def opening(
    x: float, y: float, along: tuple[int, int], across: float, floor: float
) -> list[Part]:
    """A deck's opening: a pinch slot `across` through its wall, the middle of
    it at (x, y) on the wall's inside face, out the way `along`; and the floor
    cut back under the cards."""
    cuts = Slot(x, y, along, wall, pinch(across, -10, h)).cuts()
    half = across / 2
    frame: Location = {
        (0, 1): Pos(x + half, y) * toward_minus_y,
        (0, -1): Pos(x - half, y),
        (1, 0): Pos(x, y - half) * toward_minus_x,
        (-1, 0): Pos(x, y + half) * toward_plus_x,
    }[along]
    return cuts + notch(across, wall, cut_back, floor, frame, chamfers=False)


def main_cuts() -> list[Part]:
    """The main cards' well, its floor raised, and its opening."""
    wx, wy = main_well
    return [
        Pos(*main_at) * well(wx, wy, main_floor, h),
        *opening(main_x, main_face, (0, 1), main_open, main_floor),
    ]


def token_plan() -> Sketch:
    """The sonar tokens' well with the end of the middle before it, the
    corners between them rounded: the ends of the well's wall."""
    cx, cy = token_at
    x = cx - token_wrap
    # Short of the middle's sides, which the middle itself cuts.
    half = (middle_y[1] - middle_y[0]) / 2 - 0.5
    plan = Pos(cx, cy) * Circle(token_r) + rect(x - 6, cy - half, x, cy + half)
    return grown(grown(plan, token_lip_r), -token_lip_r)


def middle_cuts() -> list[Part]:
    """The middle, open down through the floor: from the rail to the flat
    face under the sonar tokens' floor, and on between the task cards. Its
    corners rounded. And the dip in the rail."""
    plan = rect(rail, middle_y[0], token_face, middle_y[1]) + rect(
        gap_x[0], middle_y[1] - 1, gap_x[1], size[1] - label_strip
    )
    r = fillet_r / 2
    plan = grown(grown(plan, -r), r)
    plan = grown(grown(plan, r), -r)
    y = (middle_y[0] + middle_y[1]) / 2
    dip = Slot(0, y, (1, 0), rail, pinch(lift[0], h - lift[1], h, lift_r))
    return [up(plan, -1, h + 2), *dip.cuts()]


def token_cuts() -> list[Part]:
    """The sonar tokens' round well: the middle takes the side of it toward
    the main cards' opening, less than half, so what's left holds the tokens
    in. Their floor's edge there is flush with the ends of the well's wall.
    The floor meets that wall square: OCCT can't round it into the wall and
    round its edge too, where the one runs into the other at the wall's
    ends."""
    return [up(token_plan(), token_floor, h + 1 - token_floor)]


def tile_cuts() -> list[Part]:
    """The cardboard tokens' slot, along the box beside the main cards: its
    floor both of them. And their pinch: a slot through the main cards' wall,
    and across from it a finger pocket, from the tokens to the insert's side
    wall."""
    w, length = tile_slot
    # Both tokens, with room round them, and on up past the top: straight up
    # for the last of it, from where the half round's curve has got to, so
    # that the slot's ends meet the top squarely. The curve would leave a
    # sliver there.
    straight = 1
    curve = half_round_outline(tile_clear) & rect(-length, -h, length, -straight)
    # As drawn, which is in short lines, a little inside the curve itself.
    reach = curve.bounding_box()
    section = (
        curve + oval_outline(tile_clear) + rect(reach.min.X, -straight, reach.max.X, 1)
    )
    plane = Plane((tile_x[0], side_y, h), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    floor = h - tile_grip_d
    grip = Slot(
        side_x[0] - wall,
        side_y,
        (1, 0),
        wall,
        pinch(tile_grip, floor, h, tile_grip_r),
    ).cuts()
    # The pocket starts inside the slot, which takes its rounded end.
    x0 = tile_x[1] - 2
    at = Pos(x0, side_y - tile_grip / 2)
    return [
        extrude(plane * sketch(section), w),
        *grip,
        at * well(side_x[1] - x0, tile_grip, floor, h),
    ]


def task_cuts() -> list[Part]:
    """The task cards' wells, and their openings, each toward the other."""
    cuts = []
    wx, wy = task_well
    y = task_y + wy / 2
    for x, face, way in (
        (task_xs[0], task_xs[0] + wx, 1),
        (task_xs[1], task_xs[1], -1),
    ):
        at = Pos(x, task_y)
        cuts.append(at * well(wx, wy, floor_t, h))
        cuts += opening(face, y, (way, 0), task_open, floor_t)
    return cuts


def label(i: int) -> Sketch:
    """A stack's label, on the strip beyond it, sized to fit label_size."""
    text = Text(labels[i], 10, font, font_style=FontStyle.BOLD)
    box = text.bounding_box()
    k = min(label_size[0] / box.size.X, label_size[1] / box.size.Y)
    text = Text(labels[i], 10 * k, font, font_style=FontStyle.BOLD)
    at = (task_xs[i] + task_well[0] / 2, label_y)
    return sketch(Pos(*at) * Pos(-text.bounding_box().center()) * text)


def inlay(i: int, cut: bool = False) -> Part:
    """A label, inlaid in the top: or, cut, what to cut for it, which runs on
    up out of the top."""
    return up(label(i), h - label_d, label_d + (1 if cut else 0))


@cache
def insert() -> Part:
    """Cut square, then every edge eased at once; the labels' pockets after,
    which stay sharp, for the inlays."""
    cuts = main_cuts() + token_cuts() + tile_cuts() + task_cuts() + middle_cuts()
    body = eased(carve(up(octagon(*size), 0, h), cuts), foot=foot_c)
    return carve(body, [inlay(i, cut=True) for i in range(len(labels))])


def pieces() -> list[Piece]:
    out = [Piece(insert(), "insert", body_color, filaments[body_color])]
    for i, name in enumerate(labels):
        color = label_colors[name]
        out.append(Piece(inlay(i), name.lower(), color, filaments[color]))
    return out


def assembly(objects: Mapping[str, list[Piece]]) -> list[Piece]:
    """The insert, with what goes in it."""
    cards = [("main cards", *main_at, *main_well, main_floor)] + [
        (f"{name.lower()} cards", x, task_y, *task_well, floor_t)
        for name, x in zip(labels, task_xs)
    ]
    c = stack_clear / 2
    out = list(objects["insert"])
    for name, x, y, wx, wy, floor in cards:
        stack = cuboid(x + c, y + c, floor, x + wx - c, y + wy - c, h - 4)
        out.append(Piece(stack, name, "lightslategray", parent="contents"))
    for i in range(token_n):
        token = Pos(*token_at, token_floor + i * token_t) * Cylinder(
            token_d / 2, token_t, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        out.append(
            Piece(token, f"sonar token {i + 1}", "steelblue", parent="contents/sonar")
        )
    # The half round and the oval, side by side, standing on the slot's floor.
    for k, (name, outline) in enumerate(
        (("half round", half_round_outline()), ("oval", oval_outline()))
    ):
        x = tile_x[0] + 0.3 + k * token_t
        plane = Plane((x, side_y, h - tile_clear), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        out.append(
            Piece(
                extrude(plane * outline, token_t), name, "steelblue", parent="contents"
            )
        )
    return out


project(
    __file__,
    objects={"insert": Object(pieces, "The insert, as it lies in the box")},
    views={"assembly": View(assembly, "The insert, filled", ["insert"])},
    # Across a slot cut down to the bed Orca travels without retracting, after
    # infill and inner walls, and leaves a thread each time. The pinch slots go
    # down that far to reach the bottom of a stack.
    orca={"reduce_infill_retraction": 0},
)
