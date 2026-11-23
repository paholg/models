"""The Crew: Journey to the Ends of the Earth: a one-piece insert for the whole
box, under the manuals. It's designs.crew's, which has the lay of it, with the
communication tokens as its round ones.

Beside the main cards is a bin, along the box, for the rectangular tokens and
the rest: its floor scooped up both its short ends, to slide what's in it up
and out on.

The logbook lies over the insert with the manuals, its spiral binding along
the box's end, over the main cards and the bin: the walls are lower under it,
and it rests on what's in them. So the main cards' floor isn't raised, as
it is in Mission Deep Sea's.

The view is the insert with what goes in it.
"""

from collections.abc import Mapping

from build123d import Circle, Part, Plane, Pos, extrude

from build.cad import Object, Piece, View, project
from designs.crew import (
    contents,
    floor_t,
    h,
    insert,
    main_at,
    main_well,
    manuals,
    pieces,
    side_x,
    size,
    token_t,
)
from designs.tray import cuboid, rect, round_corners, well

# The rectangular tokens, which lie in the bin, along it: across, along, thick,
# and how many.
tile = (18.3, 29.9)
tile_t = token_t
tile_n = 5

# The bin: across, along.
bin_well = (side_x[1] - side_x[0], main_well[1])
# Its scoops, up its short ends: the most that leaves the rectangular tokens
# flat floor to lie on.
scoop = 15

# The logbook's spiral binding, across.
spiral = 13
# The walls' dip under it: along the box, from its end, down from the top,
# which is as far as the spiral hangs below the manuals, and a little. The
# walls rise from it in an S: the fillet at its foot, no more than the
# spiral's own turn, and the round-over at its top.
dip = (spiral + 1, spiral - manuals + 1)
dip_r = (6, 4)

assert dip_r[0] <= spiral / 2 and sum(dip_r) <= dip[1], "the dip's rounds don't fit"

assert tile[0] + 2 <= bin_well[0], "the rectangular tokens are too wide for the bin"
assert tile[1] <= bin_well[1] - 2 * scoop, "the rectangular tokens lie on the scoops"


def bin_cuts() -> list[Part]:
    """The bin, its floor scooped up both short ends."""
    at = Pos(side_x[0], main_at[1])
    return [at * well(*bin_well, floor_t, h, front=scoop, back=scoop)]


def spiral_cuts() -> list[Part]:
    """The dip under the logbook's spiral, across the whole insert at its
    end."""
    w, d = dip
    foot, top = dip_r
    section = round_corners(rect(-1, h - d, w, h + 1), [(w, h - d)], foot)
    section += rect(w, h - top, w + top, h + 1) - Pos(w + top, h - top) * Circle(top)
    return [Pos(-1, 0, 0) * extrude(Plane.YZ * section, size[0] + 2)]


def assembly(objects: Mapping[str, list[Piece]]) -> list[Piece]:
    """The insert, with what goes in it."""
    out = contents(objects, "communication", bump=0)
    # The rectangular tokens, in the middle of the bin's floor.
    x = (side_x[0] + side_x[1] - tile[0]) / 2
    y = main_at[1] + (bin_well[1] - tile[1]) / 2
    for i in range(tile_n):
        z = floor_t + i * tile_t
        token = cuboid(x, y, z, x + tile[0], y + tile[1], z + tile_t)
        out.append(
            Piece(
                token,
                f"rectangular token {i + 1}",
                "steelblue",
                parent="contents/rectangular",
            )
        )
    return out


project(
    __file__,
    objects={
        "insert": Object(
            lambda: pieces(insert(bin_cuts() + spiral_cuts(), bump=0)),
            "The insert, as it lies in the box",
        )
    },
    views={"assembly": View(assembly, "The insert, filled", ["insert"])},
    # Across a slot cut down to the bed Orca travels without retracting, after
    # infill and inner walls, and leaves a thread each time. The pinch slots go
    # down that far to reach the bottom of a stack.
    orca={"reduce_infill_retraction": 0},
)
