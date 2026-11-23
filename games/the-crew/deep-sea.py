"""The Crew: Mission Deep Sea: a one-piece insert for the whole box, under the
manuals. It's designs.crew's, which has the lay of it, with the sonar tokens
as its round ones.

Beside the main cards the two cardboard tokens stand on edge, together, in one
slot along the box, against the cards' wall, its floor following the two of
them, the half round and the oval. They're pinched by their faces: through an
opening in the cards' wall, once the cards are out, and from a finger pocket
on their other side.

The view is the insert with what goes in it.
"""

from collections.abc import Mapping
from math import cos, pi, sin

from build123d import Ellipse, Part, Plane, Pos, Sketch, extrude

from build.cad import Object, Piece, View, project, sketch
from designs.crew import (
    contents,
    floor_t,
    h,
    insert,
    main_well,
    pieces,
    side_x,
    side_y,
    token_t,
    wall,
)
from designs.tray import Slot, pinch, polygon, rect, well

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

# The cardboard tokens' pinch: across it, the round-over of its walls, and how
# far down from the top it goes.
tile_grip = 24
tile_grip_r = 3
tile_grip_d = 20

# Their slot, along the box, against the main cards' wall: across it, along
# it, and its deepest.
tile_slot = (2 * token_t + 0.6, half_round[0] + 2 * tile_clear)
tile_depth = oval[1] + tile_clear
tile_x = (side_x[0], side_x[0] + tile_slot[0])

assert side_x[1] - tile_x[1] >= 15, "no room for a finger beside the cardboard tokens"
assert tile_slot[1] <= main_well[1], "the cardboard tokens' slot is too long"
assert h - tile_depth >= floor_t, "the cardboard tokens are too tall"


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


def assembly(objects: Mapping[str, list[Piece]]) -> list[Piece]:
    """The insert, with what goes in it."""
    out = contents(objects, "sonar")
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
    objects={
        "insert": Object(
            lambda: pieces(insert(tile_cuts())), "The insert, as it lies in the box"
        )
    },
    views={"assembly": View(assembly, "The insert, filled", ["insert"])},
    # Across a slot cut down to the bed Orca travels without retracting, after
    # infill and inner walls, and leaves a thread each time. The pinch slots go
    # down that far to reach the bottom of a stack.
    orca={"reduce_infill_retraction": 0},
)
