"""The Crew's inserts: what Mission Deep Sea's and Journey to the Ends of the
Earth's share, which is all but a corner. Each is one piece for the whole box,
under the manuals.

    from designs.crew import contents, insert, pieces

x is across the box, y along it, z up, from the insert's own corner.

Along the box:
1. The main cards, sleeved, in one stack lying across the box in a corner at
   its end (y = 0), on a floor raised by `bump`, or a game's own. Beside them, from side_x[0]
   to side_x[1], is each game's own: insert() takes its cuts.
2. The middle, open from the top down to the box's own bottom: the main cards
   are scooped out from here, their wall toward it open for most of its
   width, and their floor cut back under them. At its far side the round
   tokens, a game's sonar or communication tokens, lie in a stack, flush with
   the top, in a round well whose side toward the middle is gone: to lift out
   as many as are wanted. The well goes well over half way round them, solid
   from there to the cards' walls, so they don't slide out. The rail at the
   other side dips, to get a finger under the manuals.
3. The task cards in two stacks along the box, one at each side. Between them
   the box is open to its bottom again, on from the middle, and each stack's
   wall open onto that, its floor cut back.
4. At the far end, the task cards' labels, each by its stack: TODO and DONE,
   read from the middle.

Every stack of cards' well is the insert's full height.

The insert prints as it lies, in one color, with the labels inlaid in its top
in two more.
"""

from collections.abc import Mapping

from build123d import (
    Align,
    Circle,
    Cylinder,
    FontStyle,
    Location,
    Part,
    Pos,
    Sketch,
    Text,
)

from build.cad import Piece, sketch
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
# The round tokens: across, thick, and how many.
token_d = 28.1
token_t = 2.06
token_n = 5
# The round tokens' stack comes this far short of the top.
under = 0.5
# Room round the round tokens, across: little, as their well's side is open.
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
# The round tokens' well is solid to the cards' walls at each side for this far
# past the tokens' middle, to keep them from sliding out: they only lift out.
token_wrap = 10
# Where the well's wall ends at its opening, it's rounded by this.
token_lip_r = 1

# The main cards' well, across the box, in the corner at the origin.
main_well = (sleeve[1] + stack_clear, sleeve[0] + stack_clear)
main_at = (wall, wall)
# Its wall toward the middle, inside, and its opening: its middle, and across.
main_face = main_at[1] + main_well[1]
main_x = main_at[0] + main_well[0] / 2
main_open = main_well[0] - 2 * main_post

# Beside the main cards, a game's own: what's left of the box's width, between
# walls, and the middle of it along the box.
side_x = (main_at[0] + main_well[0] + wall, size[0] - wall)
side_y = main_at[1] + main_well[1] / 2

# The task cards' wells, along the box, at each side, the labels beyond them.
task_well = (task[0] + stack_clear, task[1] + stack_clear)
task_y = size[1] - label_strip - task_well[1]
task_xs = (wall, size[0] - wall - task_well[0])
task_open = task_well[1] - 2 * task_post
# Between them, open: from, to.
gap_x = (task_xs[0] + task_well[0] + wall, task_xs[1] - wall)

# The middle: from the main cards' wall to the task cards'.
middle_y = (main_face + wall, task_y - wall)

# The round tokens' well, in the middle, at its far side: its middle, and its
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

assert wall - max(token_bite, 0) >= 0.9, "the round tokens' well leaves too little wall"
assert token_face - pinch_top_r >= main_x + main_open / 2 + pinch_top_r, (
    "the round tokens are in the way of the main cards' opening"
)
assert token_open <= token_d - 2.5, "the round tokens' well is open too wide"
assert gap_x[1] - gap_x[0] >= 20, "no room for fingers between the task cards"


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


def main_cuts(bump: float = bump) -> list[Part]:
    """The main cards' well, its floor raised by `bump`, and its opening."""
    wx, wy = main_well
    main_floor = floor_t + bump
    return [
        Pos(*main_at) * well(wx, wy, main_floor, h),
        *opening(main_x, main_face, (0, 1), main_open, main_floor),
    ]


def token_plan() -> Sketch:
    """The round tokens' well with the end of the middle before it, the
    corners between them rounded: the ends of the well's wall."""
    cx, cy = token_at
    x = cx - token_wrap
    # Short of the middle's sides, which the middle itself cuts.
    half = (middle_y[1] - middle_y[0]) / 2 - 0.5
    plan = Pos(cx, cy) * Circle(token_r) + rect(x - 6, cy - half, x, cy + half)
    return grown(grown(plan, token_lip_r), -token_lip_r)


def middle_cuts() -> list[Part]:
    """The middle, open down through the floor: from the rail to the flat
    face under the round tokens' floor, and on between the task cards. Its
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
    """The round tokens' well: the middle takes the side of it toward
    the main cards' opening, less than half, so what's left holds the tokens
    in. Their floor's edge there is flush with the ends of the well's wall.
    The floor meets that wall square: OCCT can't round it into the wall and
    round its edge too, where the one runs into the other at the wall's
    ends."""
    return [up(token_plan(), token_floor, h + 1 - token_floor)]


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


def insert(side: list[Part], bump: float = bump) -> Part:
    """The insert, less a game's own cuts, `side`, the main cards' floor
    raised by `bump`. Cut square, then every edge
    eased at once; the labels' pockets after, which stay sharp, for the
    inlays."""
    cuts = main_cuts(bump) + token_cuts() + side + task_cuts() + middle_cuts()
    body = eased(carve(up(octagon(*size), 0, h), cuts), foot=foot_c)
    return carve(body, [inlay(i, cut=True) for i in range(len(labels))])


def pieces(insert: Part) -> list[Piece]:
    """An insert, and the labels inlaid in it."""
    out = [Piece(insert, "insert", body_color, filaments[body_color])]
    for i, name in enumerate(labels):
        color = label_colors[name]
        out.append(Piece(inlay(i), name.lower(), color, filaments[color]))
    return out


def contents(
    objects: Mapping[str, list[Piece]], tokens: str, bump: float = bump
) -> list[Piece]:
    """The insert, with the cards and the round tokens, a game's `tokens`, in
    it: the main cards on a floor raised by `bump`."""
    cards = [("main cards", *main_at, *main_well, floor_t + bump)] + [
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
            Piece(
                token,
                f"{tokens} token {i + 1}",
                "steelblue",
                parent=f"contents/{tokens}",
            )
        )
    return out
