"""A Feast for Odin + The Norwegians: an insert for the whole box.

x is along the box's length, y across it, z up, from the box's inside corner.

Bottom to top:
1. The big boards, in a frame that fills the box round them, and the
   rulebooks on top of those.
2. Two identical half trays of the small, often-used tiles and money, one per
   end of the table, side by side; each half tray is two pieces, a and b, to
   fit the bed.
3. The special tiles' boards.
4-6. The rest, in columns of trays that all come to one height:
   - The front strip, under the card trays (not ours: see card-trays/README.md):
     the mountain strips, in two stacks. At its end: the boat market and the
     misc bin (4), and over them the VP and penalty tokens and the 2x5 money
     (6), beside a spacer.
   - The back, in two stacks. A square one at the end of the box: the setup
     buildings, and a riser behind them (4); the islands (5); the in-game
     buildings (6). Beside it, the rest of the length: the wooden goods and
     the vikings, side by side and deep (4-5), and the big tiles over them
     (6).

Tile bins are shallow, each with a curved scoop up the front wall to slide
tiles out on; a bin that would be packed tighter than `max_fill` says so.
Cardboard stacks sit in wells with finger notches to lift them out whole.

Each tray is drawn as it lies in the box, from its own corner, and prints that
way up, but for the in-game buildings' tray, which stands on an end wall, and
its cap, which lies on its outside face. A tray is one color: `game` for what
comes out in play, and `setup` for what only comes out to set up, along with
the frame, the islands, the vikings and the fillers, which don't. Icons are inlaid in black, the special boards' pocket floors
in a color of their own, and the forge board's icon in black and orange.

The special boards' layout is special_layout.json, which pack_special.py
writes from manifest.md. The view is the insert in the box.
"""

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import cache
from math import atan, ceil, cos, hypot, pi, sin, sqrt, tan
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Compound,
    Edge,
    Face,
    Keep,
    Kind,
    Location,
    Mesher,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    RegularPolygon,
    Rot,
    Shape,
    Sketch,
    Solid,
    Vector,
    Vertex,
    Wire,
    chamfer,
    extrude,
    fillet,
    import_svg,
    make_hull,
    mirror,
    offset,
    revolve,
    scale,
    split,
)
from shapely import MultiPoint

from build.cad import Object, Piece, View, part, project, sketch

HERE = Path(__file__).parent

# Box

# Inside, measured.
box = (306, 218, 119)
# What the inserts leave of the box, in all, along each of x and y. They sit
# touching: no gap is drawn between them.
box_clear = 1.5
inner = (box[0] - box_clear, box[1] - box_clear)
# Cardboard: see board_stack.
card_t = 2.25
# The rulebooks lie flat on the boards and their frame. Roughly: the player
# boards' length, and 25 mm wider.
rulebooks = (299, 215, 2.5)
# Player boards, action board, round overview.
board_layers = 8
board_stack_h = board_layers * card_t + 0.75
# The printer's bed.
bed = 270

# Trays

unit = 11
tile_t = 2.25
wall = 1.2
# Corner posts of the open cardboard trays.
post_t = 2
floor_t = 1.2
# The half trays.
half_h = 26.2
scoop_min = 8
scoop_max = 15
# Warn when a bin's tiles, as solid cardboard, fill more of it than this:
# they're thrown in loose.
max_fill = 0.5

# Chamfers

# Well and pocket rims.
rim_c = 0.4
# Outside top and bottom edges.
chamfer_out = 0.6
# Outside vertical corners.
chamfer_corner = 1
# Inside corners and floor edges of wells.
fillet_r = 1

# Colors, and the filaments they stand for: the preview's colors aren't the
# real ones.
game = "lightsteelblue"
setup = "tan"
pocket_floor = "darkslategray"
forge_orange = "darkorange"
icon_color = "black"
filaments = {
    game: "main",
    setup: "setup",
    pocket_floor: "pocket floor",
    forge_orange: "orange",
    icon_color: "black",
}

# Room round a cardboard stack in its well.
stack_clear = 1.5
# Front to back, the buildings' and the strips' stacks get less.
card_clear_y = 1
# Where a neat stack's well is open at the side, the floor stops this far
# inside the stack's edge, to get a fingertip under the stack.
floor_inset = wall

# Shapes


def rect(x0: float, y0: float, x1: float, y1: float) -> Rectangle:
    """Corner to corner, either way round."""
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    return Pos(x0, y0) * Rectangle(x1 - x0, y1 - y0, align=(Align.MIN, Align.MIN))


def cuboid(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> Box:
    """Corner to corner."""
    return Pos(x0, y0, z0) * Box(
        x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN)
    )


def octagon(x: float, y: float, c: float = chamfer_corner) -> Polygon:
    """A rectangle from the origin, its corners cut off at 45°, c along each
    side."""
    return Polygon(
        (c, 0), (x - c, 0), (x, c), (x, y - c), (x - c, y), (c, y), (0, y - c), (0, c),
        align=None,
    )  # fmt: skip


def polygon(points: Iterable[Vector | tuple[float, float]]) -> Sketch:
    """A polygon facing up, whichever way round its points go: one facing down
    doesn't merge with the others in a union, and offsets fail on it."""
    face = Polygon(*[Vector(p) for p in points], align=None).face()
    return sketch(Sketch() + (face if face.normal_at().Z > 0 else -face))


def up(face: Shape, z0: float, height: float) -> Part:
    """A face, drawn up from z0."""
    return Pos(0, 0, z0) * extrude(sketch(face), height, (0, 0, 1))


def slab(
    outline: Shape,
    h: float,
    foot: float = chamfer_out,
    top: float = chamfer_out,
) -> Part:
    """An outline, h tall, its edges chamfered round its foot and its top."""
    body = extrude(sketch(outline), h)
    body = chamfer(body.faces().sort_by(Axis.Z).first.edges(), foot)
    return part(chamfer(body.faces().sort_by(Axis.Z).last.edges(), top))


def block(x: float, y: float, h: float, top: float = chamfer_out) -> Part:
    """A tray's body, from the origin: every outside edge chamfered, its top
    ones by `top`."""
    return slab(octagon(x, y), h, chamfer_out, top)


def grown(face: Shape, d: float, kind: Kind = Kind.ARC) -> Sketch:
    """Grown by d, or shrunk for a d below 0: with Kind.ARC its convex corners
    rounded, growing, or its concave ones, shrinking."""
    return sketch(offset(sketch(face), d, kind=kind))


def flare(face: Shape, c: float, normal: Vector) -> Part:
    """A 45° chamfer's cut round the edge of a hole whose outline, `face`, is
    on a face of the part: the outline grown by c, drawn in along `normal`, the
    way into the part, closing to the outline itself c in. It starts a little
    outside the face, so as to cross it rather than lie on it."""
    out = 0.5
    return Pos(-out * normal) * extrude(grown(face, c + out), c + out, normal, taper=45)


def carve(body: Part, cuts: Iterable[Part]) -> Part:
    """The body less each of the cuts in turn. Cut all at once, tools whose
    faces touch each other's can leave OCCT an invalid solid."""
    for c in cuts:
        body = part(body - c)
    return body


def round_corners(
    face: Shape, corners: Iterable[tuple[float, float]], r: float
) -> Sketch:
    """A face with its corners at these points rounded by r."""
    near = [
        v
        for v in face.vertices()
        if any(hypot(v.X - x, v.Y - y) < 1e-6 for x, y in corners)
    ]
    return sketch(fillet(near, r))


def wall_plane(x: float, y: float, normal: tuple[float, float]) -> Plane:
    """A plane on a wall's face at (x, y), facing `normal` level, its local x
    across the wall and y up: so a profile drawn on it is a section across the
    wall, z up. Across, it reads mirrored from one side to the other."""
    n = Vector(normal[0], normal[1], 0)
    return Plane((x, y, 0), x_dir=Vector(0, 0, 1).cross(n), z_dir=n)


def swap_xy(shape: Compound) -> Compound:
    """Mirrored in the plane x = y: x and y trade places."""
    return mirror(shape, Plane((0, 0, 0), z_dir=(1, -1, 0)))


# Wells


def well(
    x: float, y: float, floor: float, top: float, front: float = 0, back: float = 0
) -> Part:
    """A rectangular well, x by y from the origin, from its floor up past top:
    its vertical corners and floor edges rounded by fillet_r, and its floor's
    front edge (y = 0) rounded by `front` instead where that's more, a scoop to
    slide tiles up and out on, and the back one by `back`."""
    r = fillet_r
    h = top + 1 - floor
    section = rect(0, 0, y, h)
    for at, s in ((0, front), (y, back)):
        if s > r:
            section = round_corners(section, [(at, 0)], s)
    tool = Pos(0, 0, floor) * extrude(Plane.YZ * section, x)
    # The ends' edges, and any floor edge along x that isn't a scoop.
    ends = tool.faces().filter_by(Axis.X)
    edges = [e for f in ends for e in f.edges() if e.center().Z < top]
    for at, s in ((0, front), (y, back)):
        if s <= r:
            edges += [
                e
                for e in tool.edges().filter_by(Axis.X)
                if abs(e.center().Y - at) < 1e-6 and abs(e.center().Z - floor) < 1e-6
            ]
    return part(fillet(edges, r))


def bowl(x: float, y: float, floor: float, top: float, s: float, r: float) -> Part:
    """A well x by y scooped up all four walls, from the origin: the scoops,
    of radius s, run round its corners on a ball of that radius, and from
    there its corners draw in to the rim's, rounded by r."""
    low = cuboid(0, 0, floor, x, y, floor + 2 * s)
    low = fillet(
        low.edges().filter_by(Axis.Z) + low.faces().sort_by(Axis.Z).first.edges(), s
    )
    low &= cuboid(-1, -1, floor, x + 1, y + 1, floor + s)
    align = (Align.MIN, Align.MIN)
    rims = [
        Pos(0, 0, floor + s) * RectangleRounded(x, y, s, align=align),
        Pos(0, 0, top) * RectangleRounded(x, y, r, align=align),
    ]
    walls = Solid.make_loft([f.faces()[0].outer_wire() for f in rims], ruled=True)
    return part(low + walls + up(rims[1], top, 1))


def rim(x: float, y: float, top: float, c: float = rim_c, r: float = fillet_r) -> Part:
    """The chamfer round a well's rim, x by y from the origin, its corners
    rounded by r, at the top of a body `top` high."""
    outline = RectangleRounded(x, y, r, align=(Align.MIN, Align.MIN))
    return Pos(0, 0, top) * flare(outline, c, Vector(0, 0, -1))


# Pinch slots


# The usual pinch slot's round-over at the top, and its floor's fillets.
pinch_top_r = 4
pinch_fillet = 3


def pinch(w: float, bottom: float, top: float, r: float = pinch_top_r) -> Sketch:
    """A pinch slot's opening, as a section across its wall, centered on x = 0:
    w wide, from `bottom` up past `top`, where the wall rounds over into it
    on a radius of r, which leaves it w + 2r wide at the top. Above the part's
    foot, its floor's corners are filleted."""
    opening = rect(-w / 2, bottom, w / 2, top + 1)
    if bottom > 0:
        opening = round_corners(
            opening, [(-w / 2, bottom), (w / 2, bottom)], pinch_fillet
        )
    rounds = [
        rect(sx * w / 2, top - r, sx * (w / 2 + r), top + 1)
        - Pos(sx * (w / 2 + r), top - r) * Circle(r)
        for sx in (-1, 1)
    ]
    return sketch(Sketch() + opening + rounds)


@dataclass
class Slot:
    """A pinch slot through one or more walls along a line: from (x, y), along
    `along`, a unit vector, for `depth`. The faces it crosses are each
    (distance along it, which way the wall is from there: 1 on, -1 back),
    chamfered by chamfer_out where they're outside, or by rim_c, where they're
    inside a well whose floor is at `floor`, from there up."""

    x: float
    y: float
    along: tuple[float, float]
    depth: float
    opening: Sketch
    outside: tuple[tuple[float, int], ...] = ()
    inside: tuple[tuple[float, int, float], ...] = ()
    # Without, only its faces' chamfers: something else cuts the opening.
    through: bool = True

    def plane(self, d: float, way: int) -> Plane:
        ax, ay = self.along
        return wall_plane(self.x + d * ax, self.y + d * ay, (way * ax, way * ay))

    def cuts(self) -> list[Part]:
        out = []
        if self.through:
            out.append(extrude(self.plane(-0.5, 1) * self.opening, self.depth + 1))
        # The chamfers are drawn flat and moved onto the wall: OCCT's tapered
        # extrude fails on some openings drawn on a wall's plane.
        normal = Vector(0, 0, 1)
        for d, way in self.outside:
            plane = self.plane(d, way)
            out.append(plane.location * flare(self.opening, chamfer_out, normal))
        for d, way, floor in self.inside:
            plane = self.plane(d, way)
            eased = plane.location * flare(self.opening, rim_c, normal)
            out.append(part(eased & cuboid(-1000, -1000, floor, 1000, 1000, 1000)))
        return out


def notch(
    length: float, through: float, inset: float, floor: float, at: Location
) -> list[Part]:
    """Where a pinch slot goes down through a well's floor, the floor is cut
    back from it to inset inside the well, to get a fingertip under the stack.
    In its own frame, the wall's inside face is y = 0, the well in +y, the
    wall `through` thick, the opening from x = 0 to length. The notch's
    corners start where the floor's fillet into the wall ends; it takes that
    fillet with it, and its bottom edge, and the floor's new top edge, are
    chamfered."""
    plan = round_corners(
        rect(0, -through - 1, length, inset),
        [(0, inset), (length, inset)],
        inset - fillet_r,
    )
    top = plan & rect(-1, fillet_r, length + 1, inset + 1)
    return [
        at * up(plan, -1, 1 + floor + fillet_r),
        at * flare(plan, chamfer_out, Vector(0, 0, 1)),
        at * (Pos(0, 0, floor) * flare(top, rim_c, Vector(0, 0, -1))),
    ]


# Turning a notch's frame: the well in -y, in +x, and in -x.
toward_minus_y = Rot(0, 0, 180)
toward_plus_x = Rot(0, 0, -90)
toward_minus_x = Rot(0, 0, 90)

# Icons: a tile's cells as (col, row), col across, drawn on an icon_cell grid
# in icon_line wide lines, centered. A "grid" is outlined squares, and money,
# "coin", linked octagons.

icon_cell = 4
icon_line = 0.8
# Inlaid icon_d deep, icon_top below the rim.
icon_d = 0.4
icon_top = 2.5


@dataclass(frozen=True)
class Icon:
    kind: str  # "grid" or "coin"
    cells: tuple[tuple[int, int], ...]

    @property
    def size(self) -> tuple[int, int]:
        return (
            max(c for c, _ in self.cells) + 1,
            max(r for _, r in self.cells) + 1,
        )

    def sketch(self) -> Sketch:
        nx, ny = self.size
        k, w = icon_cell, icon_line
        shapes = []
        for c, r in self.cells:
            x, y = (c - nx / 2 + 0.5) * k, (r - ny / 2 + 0.5) * k
            if self.kind == "grid":
                shapes.append(
                    Pos(x, y) * (Rectangle(k + w, k + w) - Rectangle(k - w, k - w))
                )
            else:
                # Flat to flat one cell, so neighbors share an edge.
                ring = [
                    RegularPolygon((k / 2 + s * w / 2) / cos(pi / 8), 8, rotation=22.5)
                    for s in (1, -1)
                ]
                shapes.append(Pos(x, y) * (ring[0] - ring[1]))
        return sketch(Sketch() + shapes)

    def z(self, h: float) -> float:
        """Its middle's height, on a tray h tall."""
        return h - icon_top - (self.size[1] * icon_cell + icon_line) / 2


def cells(c: int, r: int) -> tuple[tuple[int, int], ...]:
    return tuple((x, y) for y in range(r) for x in range(c))


def grid(c: int, r: int) -> Icon:
    return Icon("grid", cells(c, r))


def coin(c: int, r: int) -> Icon:
    return Icon("coin", cells(c, r))


u_icon = Icon("grid", ((0, 0), (1, 0), (2, 0), (0, 1), (2, 1)))


def front_icon(icon: Icon, x: float, h: float, cut: bool = False) -> Part:
    """An icon in a tray's front face (y = 0), centered on x: or, cut, what to
    cut from the tray for it, which runs on out of the face."""
    face = Plane.XZ * Pos(x, icon.z(h)) * icon.sketch()
    out = 1 if cut else 0
    return Pos(0, -out, 0) * extrude(face, icon_d + out, (0, 1, 0))


# Bin trays


@dataclass
class Bin:
    """A bin in a tray: `width` None shares what's left of its row equally.
    Its tiles' footprint sizes its scoops and the check on how full it is.
    With an icon, a bin in the front row shows it on the tray's front face."""

    name: str
    width: float | None
    tile: tuple[float, float]
    count: int = 0
    icon: Icon | None = None
    # Its back wall square, wherever the tray scoops its back walls.
    front_only: bool = False


@dataclass
class Row:
    """A row of bins: `depth` None shares what's left of the tray."""

    depth: float | None
    bins: list[Bin]


def shares(sizes: list[float | None], room: float, walls: float) -> list[float]:
    """Each of sizes, a None sharing what's left of the room equally, with a
    wall of `walls` between each and round them all."""
    fixed = sum(s for s in sizes if s is not None)
    n = sum(1 for s in sizes if s is None)
    fill = (room - walls * (len(sizes) + 1) - fixed) / max(1, n)
    out = [fill if s is None else s for s in sizes]
    assert min(out) > 0, "a row's bins don't fit"
    return out


@dataclass
class Tray:
    """A tray of bins, x by y, h tall, from the origin. Every bin's scoop has
    the radius `scoop`, or if None one that leaves its tile room to lie flat,
    within scoop_min and scoop_max. `back` scoops the back walls too; `sides`
    scoops the left and right walls instead of the front and back, and `bowl`
    all four, a bowl of radius bowl_r at the rim."""

    name: str
    x: float
    y: float
    h: float
    rows: list[Row]
    scoop: float | None = None
    back: bool = False
    sides: bool = False
    bowl: bool = False
    wall: float = wall
    rim: float = rim_c
    # The chamfer on the body's top edges.
    top: float = chamfer_out
    # Its tiles are thrown in loose, so it says if they'd be packed tight.
    loose: bool = True

    def bins(self) -> Iterable[tuple[int, Bin, float, float, float, float]]:
        """Each bin: its row, and its corner and size."""
        depths = shares([r.depth for r in self.rows], self.y, self.wall)
        y = self.wall
        for i, (row, d) in enumerate(zip(self.rows, depths)):
            x = self.wall
            for b, w in zip(
                row.bins, shares([b.width for b in row.bins], self.x, self.wall)
            ):
                yield i, b, x, y, w, d
                x += w + self.wall
            y += d + self.wall

    def scoop_for(self, depth: float, tile: float) -> float:
        if self.scoop is not None:
            return self.scoop
        return min(scoop_max, max(scoop_min, depth - tile))

    def cuts(self) -> list[Part]:
        out = []
        for _, b, x, y, w, d in self.bins():
            if self.bowl:
                assert self.scoop is not None
                hollow = bowl(w, d, floor_t, self.h, self.scoop, bowl_r)
            elif self.sides:
                s = self.scoop_for(w, b.tile[0])
                hollow = part(swap_xy(well(d, w, floor_t, self.h, s, s)))
            else:
                s = self.scoop_for(d, b.tile[1])
                back = s if self.back and not b.front_only else 0
                hollow = well(w, d, floor_t, self.h, s, back)
            r = bowl_r if self.bowl else fillet_r
            out += [Pos(x, y) * hollow, Pos(x, y) * rim(w, d, self.h, self.rim, r)]
        return out

    def icons(self, cut: bool = False) -> list[Part]:
        return [
            front_icon(b.icon, x + w / 2, self.h, cut)
            for row, b, x, _, w, _ in self.bins()
            if row == 0 and b.icon
        ]

    def check(self) -> None:
        """Say which bins would be packed tight with their tiles thrown in."""
        for _, b, _, _, w, d in self.bins():
            if not b.count or not self.loose:
                continue
            s = self.scoop_for(d, b.tile[1])
            scoops = (2 if self.back else 1) * (1 - pi / 4) * s * s * w
            room = w * d * (self.h - floor_t) - scoops
            fill = b.count * b.tile[0] * b.tile[1] * tile_t / room
            if fill > max_fill:
                print(f"  tight: {self.name} {b.name} is {fill:.0%} full")

    def body(self) -> Part:
        self.check()
        body = block(self.x, self.y, self.h, self.top)
        return carve(body, self.cuts() + self.icons(True))


# Bowls' corners at the rim, rounder than a square bin's, to read as a bowl.
bowl_r = 4


def t(x: int, y: int) -> tuple[float, float]:
    return (x * unit, y * unit)


# The layers over the special boards, all zone_h tall

# The card trays are imported, not modeled here: "Remixed A Feast for Odin
# card trays" by DewLeen (@DewLeen_91662 on Printables),
# https://www.printables.com/model/1145265-remixed-a-feast-for-odin-card-trays,
# a remix of "A Feast for Odin (+exp) Organizer / Insert" by RiftForge 3D
# (@RiftForge3D3). Licensed CC BY-NC-SA 4.0; see card-trays/README.md. The
# STLs here are as downloaded; deck_tray() adapts them (shorter, and a lip at
# each end), and what's exported is under their license. Cards stand on their
# long edges, the deck running along the tray.


@dataclass(frozen=True)
class Deck:
    name: str
    stl: str
    # How much is cut out of its length: the decks are shorter than the trays.
    cut: float
    setup: bool = False


decks = [
    Deck("setup occupations", "weapon_cards_tray_x2.stl", 5, setup=True),
    Deck("occupations", "occupation_cards_tray.stl", 10),
    Deck("weapons", "weapon_cards_tray_x2.stl", 5),
]
# The trays, as they come: across, along, up.
deck_size = {
    "weapon_cards_tray_x2.stl": (74, 57.5),
    "occupation_cards_tray.stl": (74, 115),
}
# Where the cut is, from the tray's front, as a share of its length: in the
# plain stretch between the thumb notch and the sloped back.
deck_cut_at = 0.5
# Sleeved cards stand this tall on the trays' 1 mm floors.
card_w = 46
deck_floor = 1
# A lip across the floor at each end, this high over it.
deck_lip = 4

# The card trays, in a row along the front, set the front strip's depth, and
# their height (the cards stand a little proud of them) most of the zone's.
up_h = deck_floor + card_w + 0.5
front_y = deck_size[decks[0].stl][0]
deck_len = [deck_size[d.stl][1] - d.cut for d in decks]
decks_x = sum(deck_len)
# Behind the front strip.
back_y = inner[1] - front_y
# The top two tiers at the back are half the card trays' height each.
tier_h = up_h / 2
# Under the card trays, and under the big tiles: as tall as the setup
# buildings' stack.
setup_n = 6
base_h = floor_t + setup_n * card_t
zone_h = base_h + up_h
# The front strip's end, past the card trays.
corner_x = inner[0] - decks_x

# The half trays: small, often-used tiles, one copy per end of the table,
# half counts. Food in front, equipment behind. Columns run roughly smallest
# to biggest tile, the U last, the same in every row, so food and equipment
# line up as an upgrade path. Tiles lie long side along x.

half = (inner[0], inner[1] / 2)
half_cols = [28, 36, 32, 47, 37, 41, 37]
half_shapes = [
    ("1x2", t(2, 1), grid(2, 1)),
    ("1x3", t(3, 1), grid(3, 1)),
    ("2x2", t(2, 2), grid(2, 2)),
    ("1x4", t(4, 1), grid(4, 1)),
    ("2x3", t(3, 2), grid(3, 2)),
    ("3x3", t(3, 3), grid(3, 3)),
    ("U", t(3, 2), u_icon),
]
half_counts = {
    "food": [18, 10, 10, 10, 9, 8, 12],
    "equipment": [24, 15, 15, 10, 10, 9, 11],
}
# Each half tray is two pieces to fit the bed: a, the first half_split
# columns, and b, the rest, with the money.
half_split = 4


def half_rows(a: int, b: int) -> list[Row]:
    return [
        Row(
            None,
            [
                Bin(name, half_cols[i], tile, n[i], icon)
                for i, (name, tile, icon) in enumerate(half_shapes)
                if a <= i < b
            ],
        )
        for n in half_counts.values()
    ]


def tray_x(cols: Sequence[float]) -> float:
    return sum(cols) + (len(cols) + 1) * wall


half_a = Tray(
    "half a",
    tray_x(half_cols[:half_split]),
    half[1],
    half_h,
    half_rows(0, half_split),
    back=True,
)
half_b_x = half[0] - half_a.x
# Every scoop the biggest, as the tile bins' are anyway: the 2x2 money's would
# be less, for the room its tiles leave.
half_b_tiles = Tray(
    "half b",
    tray_x(half_cols[half_split:]),
    half[1],
    half_h,
    half_rows(half_split, len(half_cols)),
    scoop=scoop_max,
    back=True,
)
# Money, in its own column at the end of each half tray, smallest in front:
# it shares the tile bins' last wall.
money_x0 = half_b_tiles.x - wall
money = Tray(
    "money",
    half_b_x - money_x0,
    half[1],
    half_h,
    [
        Row(None, [Bin("1x1", None, t(1, 1), 40, coin(1, 1))]),
        Row(None, [Bin("1x2", None, t(2, 1), 16, coin(2, 1))]),
        Row(None, [Bin("2x2", None, t(2, 2), 9, coin(2, 2))]),
    ],
    scoop=scoop_max,
    back=True,
)

# Big tiles and animals: one shared copy, full counts. Animals in front,
# equipment behind. Each bin is one tile wide, with big_clear to spare, and
# scooped front and back. The 2-wide tiles stand on edge, long side down,
# leaning, in a stack running front to back. The 3x4 are too tall for that:
# they lie flat, in two stacks, one behind the other, filling their bins, so
# those are scooped at the front only: the back stack lies flat against the
# square back wall, and the front one, the shorter, up the scoop.
# The islands' tray is in the square stack beside it, square, as they are, and
# as deep as the back of the box; the big tiles take the rest of its length,
# which is where big_clear comes from.
island = 129
island_n = 8
islands_size = (back_y, back_y)
big_size = (inner[0] - islands_size[0], back_y)
big_clear = (big_size[0] - 4 * wall - 13 * unit) / 3
# (kind, tile, stacks deep: 0 on edge)
big_kinds = [("2x4", t(4, 2), 0), ("3x4", t(4, 3), 2), ("2x5", t(5, 2), 0)]
big_counts = {"A": [18, 15, 21], "E": [20, 15, 14]}
big = Tray(
    "big",
    *big_size,
    tier_h,
    [
        Row(
            None,
            [
                # What lies on its floor: every flat stack.
                Bin(
                    p + kind,
                    tile[0] + big_clear,
                    (tile[0], tile[1] * max(1, deep)),
                    n,
                    grid(round(tile[0] / unit), round(tile[1] / unit)),
                    front_only=deep > 0,
                )
                for (kind, tile, deep), n in zip(big_kinds, counts)
            ],
        )
        for p, counts in big_counts.items()
    ],
    scoop=scoop_max,
    back=True,
    loose=False,
)
assert abs(sum(b.width or 0 for b in big.rows[0].bins) + 4 * wall - big.x) < 0.01, (
    "the big tiles' columns don't fill their tray"
)
# Their stacks: on edge, front to back, or flat, on the floor.
for _, b, _, _, _, d in big.bins():
    _, tile, deep = next(k for k in big_kinds if b.name.endswith(k[0]))
    if deep:
        assert -(-b.count // deep) * tile_t <= big.h - floor_t, f"{b.name} too tall"
        assert tile[1] * deep <= d, f"{b.name}'s stacks don't fit"
    else:
        assert b.count * tile_t <= d, f"{b.name}'s stack doesn't fit"

# The islands' tray is a tier tall, standing on the setup buildings and the
# riser: what the islands don't need of that is floor, and the tray, big and
# open and lifted out full, is the stiffer for it.
islands_h = tier_h
islands_floor = islands_h - island_n * card_t
assert islands_floor >= floor_t, "the islands' tray is too low for its stack"
assert islands_size[0] >= island + stack_clear + 2 * post_t, (
    "the islands don't fit beside the big tiles"
)

# The setup buildings, 6 of them, in one stack, in an open tray. They run
# along the square stack, which only just fits them: so the tray is as long as
# the square, with thinner posts at the ends, and the stack gets what's left.
building = (139, 54.5)
setup_post_x = wall
setup_clear_x = back_y - building[0] - 2 * setup_post_x
assert setup_clear_x >= 1, "the setup buildings don't fit the square stack"
setup_bld = (back_y, building[1] + card_clear_y + 2 * post_t)

# Boats: a market of stacks, like mini decks. Each well fits its tile
# lengthwise (long side front to back), with a pinch slot through the front
# and back walls. The slots leave a lip each side to hold the stack in.
# A boat is bigger than the tiles it's named for: the 4-long ones are 46 long,
# their widths the tiles', and the 2x3 is 26 x 34. (label, footprint, count),
# left to right.
boat_l = 46
boats = [
    ("1x4", (unit, boat_l), 8),
    ("2x3", (26, 34), 10),
    ("2x4", (2 * unit, boat_l), 12),
    ("2x4", (2 * unit, boat_l), 10),
]
boat_clear = 1
# Between its sides; the round-overs widen it at the rim.
boat_slot_w = 15
# The 1x4 well's slot, through the side wall, where there's more room.
boat_side_slot_w = 25
# Smaller than the usual round-over, to leave more wall between neighboring
# slots.
boat_slot_r = 2
boat_slot_lip = 2
boat_wells = [(b[0] + boat_clear, b[1] + boat_clear) for _, b, _ in boats]
# Just tall enough for the tallest stack.
boat_h = floor_t + max(n for *_, n in boats) * tile_t
# As long as the front strip's end: the walls between wells take up the slack.
boat_size = (corner_x, max(y for _, y in boat_wells) + 2 * wall)
boat_wall = (boat_size[0] - sum(x for x, _ in boat_wells)) / (len(boats) + 1)


def boat_floor(i: int) -> float:
    """Raised so its full stack comes flush with the top."""
    return max(floor_t, boat_h - boats[i][2] * tile_t)


def boat_x(i: int) -> float:
    return boat_wall + sum(boat_wells[j][0] + boat_wall for j in range(i))


# Behind the boats, a bin for the moose (35 x 30 x 11), the d8 and d12, and the
# cube: all setup-only. The d12 is 22 across and 18.8 tall, and the bin no
# wider than the boats leave: so thinner walls, and less of a chamfer each side
# of their top, to leave a rim between the two.
misc_size = (corner_x, front_y - boat_size[1])
misc = Tray(
    "misc",
    *misc_size,
    boat_h,
    [Row(None, [Bin("misc", None, (16, 16))])],
    sides=True,
    wall=0.8,
    rim=0.2,
    top=0.2,
)

# The VP tray, over the boats. VP tokens, 25 mm square: 2x 4 VP, 6x 3 VP, 8x 2
# VP, standing on edge in one row, biggest first at the front (x = 0), as you
# only ever need the next one. A well per value, walls as tall as the tokens;
# one pinch slot runs through the front face and every divider, to slide the
# front token up and out. Behind them, in the tray's corner, a round well
# holds the 7 penalty tokens (30 mm round) in a stack, flush with the top. The
# corner itself is open: the quarter of the well's wall that faces it is gone,
# down to the bottom, and the floor there stops short of the stack's edge.
vp_token = 25
vp_counts = [2, 6, 8]
vp_slack = 1.5  # per value, so the tokens can lean
vp_clear = 1.5  # across
vp_wall_h = vp_token + 0.5
vp_slot_w = 16
vp_slot_bottom = 4
# Smaller than the usual round-over, to leave more of the dividers.
vp_slot_r = 2
pen_clear = 1.5
pen_n = 7
pen_r = (30 + pen_clear) / 2
vp_groups = [n * tile_t + vp_slack for n in vp_counts]
vp_xs = [wall + sum(g + wall for g in vp_groups[:i]) for i in range(len(vp_counts) + 1)]
vp_in_y = vp_token + vp_clear
# The stacks' block, front to back; the penalty well shares its back wall.
vp_block_y = vp_in_y + 2 * wall
# The 2x5 money, in a stack of its own down the tray's other side, like a
# boat's.
money5_n = 5
money5_well = (2 * unit + 1, 5 * unit + 1)
money5_slot_w = 25
# As long as it needs; a spacer takes the rest of the front strip's end. From
# the boats to the zone's top: more than the tokens need, so their wells'
# floor is thick, and the tokens stand flush with the top.
vp_size = (72.5, front_y)
vp_h = zone_h - boat_h
vp_floor = vp_h - vp_wall_h
assert vp_floor >= floor_t, "the VP tray is too low for its tokens"
assert vp_xs[-1] + money5_well[0] + wall <= vp_size[0], "the VP tray is too short"
assert vp_block_y + 2 * pen_r + wall <= vp_size[1], "the VP tray is too shallow"
assert money5_well[1] + 2 * wall <= vp_size[1], "the VP tray is too shallow"
# The penalty well's middle: a wall's thickness from the tray's side and back.
pen_c = (wall + pen_r, vp_size[1] - wall - pen_r)
# Beside the VP tray, a spacer: see honeycomb().
spacer_size = (corner_x - vp_size[0], front_y)

# The wooden goods and the vikings share the rectangle beside the square
# stack, under the big tiles: as tall as the setup buildings and the islands
# together.
deep_h = base_h + tier_h
# Their walls, thicker than the usual, as they're that much taller.
deep_wall = 1.6

# Vikings: one tray beside the square stack, a bin per player color, in a row
# front to back, each scooped up its short ends, as the wood's are.
vikings_size = (72, back_y)
viking_scoop = 15

# The wooden goods: a bin each, front to back, beside the vikings, at the end
# of the box, scooped up their long sides. Ore and stone are as deep as each
# other; wood has the rest.
wood_bin = 40

# The riser fills the gap behind the setup buildings' tray, as long as it is,
# for the islands to sit on.
riser_size = (setup_bld[0], back_y - setup_bld[1])

# 9 mountain strips: eight 169 mm ones and a 192 mm one. Under the card trays
# they lie in two stacks, in one solid tray: four short ones in the front
# well, and four with the long one on top in the back well, each well's floor
# as high as brings its stack flush with the top. What room the wells leave is
# between them, and at their ends. The back well is the long strip's length,
# for one strip's depth; under that it's the short ones' length, so the long
# one rests on a ledge past their end.
strip = (169, 30)
long_strip = (192, 30)
strips_size = (decks_x, front_y)
strips_n = (4, 4)

# Open trays: a plain floor and an L-shaped post at each well corner, no walls
# between. Stacks lift straight out, gripped from the open sides, where the
# floor is cut back to under the stack's edge.
# Each leg of a post, past the corner.
post_l = 15
# Every edge of the posts and floors rounded by this.
post_r = 0.6


# The in-game buildings, in one tray: a stack per kind, each leaning on its
# own ramp, like shingles, all at one angle. A stack's low edge is on the
# floor, against a stop; its high half lies over the next stack, whose ramp
# carries it. A ramp stops short of its stack's high edge, to get a finger
# under and lift, and reaches a little over the low edge of the stack before
# it; the front wall has a lip that does the same for the last stack. So a
# building comes out up its ramp, and the stacks over it stay put.
# The tray is one section from end to end, between two end walls, and prints
# standing on one of them, with no overhangs. The other is a cap, glued on.
# Its section is drawn in (u, v): u from the tray's front to its back, v up.

# Buildings a stack, back stack first: the one with nothing under it.
bld_stacks = [3, 3, 5]
# How much of a covered stack shows, of a building's width. More, and the tray
# is deeper and leans less, so it's lower: this much brings it under the
# tier's height.
bld_show = 0.75
bld_ramp_t = 1.2
# Between a stack and the ramp, or lip, over it.
bld_over = 0.6
# A ramp stops this short of its buildings' high edge. The back stack's too:
# the back wall stands under its ramp's end, with the buildings' overhang
# behind it.
bld_grip = 8
# Under that overhang, from the back wall to the tray's edge, the tray is
# solid this far up from the floor: a face for the next tray to sit against,
# and low enough to leave the way in under the buildings.
bld_lip = 4
bld_end_t = 1.2
# Along the buildings, in all: the tray is as long as the square stack.
bld_len_clear = back_y - building[0] - 2 * bld_end_t
assert bld_len_clear >= 1, "the buildings don't fit the square stack"
# The section's own edges are rounded over by this, and filleted by that where
# its walls meet. (The end walls' outline has chamfer_corner for both.)
bld_round = 0.4
bld_fillet = 0.5
# The cap's plugs: how tall, their fit in the hollows each side, and how far
# their crush ribs stand out.
bld_plug_h = 4
bld_plug_clear = 0.2
bld_rib = 0.35
# The hollows under the ramps are closed off just below the plugs, making each
# a socket. A plug is glued by its end alone, to its socket's floor, which it
# stops bld_glue_gap short of; what glue is pushed aside has the room round
# the end's chamfer (bld_plug_lead). The socket's floor is bld_socket_floor
# thick, on a roof that closes in from the hollow's walls at 45 degrees: no
# bridge, which the slicer would run the long way.
bld_socket_floor = 1
bld_glue_gap = 0.2
# A plug's top edge is chamfered by this, to lead it in.
bld_plug_lead = 0.6

bld_last = len(bld_stacks) - 1
bld_t = [n * card_t for n in bld_stacks]
# The thickest stack with another over it sets the angle.
bld_a = atan((max(bld_t[:-1]) + bld_over + bld_ramp_t) / (bld_show * building[1]))
# Along and square to the ramps.
bld_d = Vector(cos(bld_a), sin(bld_a))
bld_n = Vector(-sin(bld_a), cos(bld_a))
# From one stack's low corner to the next's.
bld_step = bld_show * building[1] / cos(bld_a)
# How far a ramp reaches over the stack under it, from that stack's low edge.
bld_reach = building[1] - bld_grip - bld_step * cos(bld_a)


def bld_p(i: int) -> Vector:
    """Where stack i's ramp leaves the floor, under its low edge."""
    u = wall + bld_t[bld_last] * sin(bld_a) + (bld_last - i) * bld_step
    return Vector(u, floor_t)


def bld_low(i: int) -> Vector:
    """The low corner of stack i's top."""
    return bld_p(i) + bld_t[i] * bld_n


def bld_high(i: int) -> Vector:
    """The high corner of stack i's top."""
    return bld_low(i) + building[1] * bld_d


def bld_top(i: int, u: float) -> float:
    """The height of stack i's top at u, and beyond."""
    return bld_low(i).Y + (u - bld_low(i).X) * tan(bld_a)


# The lip over the last stack: its top's low and high ends, and where its top
# line meets u = 0.
bld_front = bld_p(bld_last) + (bld_t[bld_last] + bld_over + bld_ramp_t) * bld_n
bld_front_end = bld_front + bld_reach * bld_d
bld_front_h = bld_front.Y - bld_front.X * tan(bld_a)
# How far back the buildings reach; the tray runs on past them to fill the
# square stack, so nothing behind it can shift.
bld_depth = bld_p(0).X + building[1] * bld_d.X
bld_out = back_y
assert bld_depth <= bld_out, "the buildings overhang the square stack"
# The back wall's outside face.
bld_back = bld_p(0).X + (building[1] - bld_grip) * bld_d.X
bld_in_x = building[0] + bld_len_clear
bld_size = (
    bld_in_x + 2 * bld_end_t,
    bld_out,
    max(bld_high(i).Y for i in range(bld_last + 1)),
)
assert max(bld_size[:2]) <= back_y and bld_size[2] <= tier_h, (
    f"the buildings tray doesn't fit the square stack's top: {bld_size}"
)
wood = Tray(
    "wood",
    inner[0] - islands_size[0] - vikings_size[0],
    back_y,
    deep_h,
    [
        Row(wood_bin, [Bin("ore", None, (11, 11))]),
        Row(wood_bin, [Bin("stone", None, (13, 20))]),
        Row(None, [Bin("wood", None, (14, 21))]),
    ],
    sides=True,
    wall=deep_wall,
)

# The special tiles' boards: a pocket per tile, the forge tiles on their own
# board. Layout from pack_special.py.
layout = json.loads((HERE / "special_layout.json").read_text())
# Pocket depth: the tiles sit flush with the top.
pocket_d = tile_t
pocket_clear = 0.4
# Under the ends of each tile the pocket floor drops by tilt_d, for tilt_a in
# from the tile's edge: press there and the far end tips up to grab. The tip
# angle goes as tilt_d / tilt_a (about 18 degrees), so they scale together.
tilt_d = 2.2
tilt_a = 7
# The step down is an S: rounded over at the top, where the tile pivots, and
# filleted at the bottom.
tilt_r = 1.1
assert tilt_r <= tilt_d / 2
# A side of a tile can be a press end if the tile is at least this many cells
# long that way, for leverage, and its center of mass is tilt_balance clear
# of the drop, so it rests flat. So most tiles tip from any side, a bar from
# either end.
tilt_min_cells = 2
tilt_balance = 2
# Floor under the drops; the rest of the board is thicker.
special_floor = 0.8
# The pocket floors, both levels and the step between, are pocket_floor this
# deep.
floor_skin = 0.4
special_h = special_floor + tilt_d + pocket_d
# As deep as the box, so they can't slide; the pockets are centered. The
# others' board takes what the forge's leaves of the box's length, so the
# layer is as long as the rest. Their corners are rounded by corner_r, for
# room in the box's to get a finger under them; pack_special.py keeps the
# pockets clear of them. Its boards are each 2 mm wider than their tiles'
# section, each side: 2, not 3, so the two fit the box side by side.
special_corner_r = layout["corner_r"]
special_forge_size = (layout["boards"]["forge"]["size"][0], inner[1])
special_others_size = (inner[0] - special_forge_size[0], inner[1])
assert special_others_size[0] >= layout["boards"]["others"]["size"][0], (
    "the special boards are too long for the box"
)
# The forge board's icon, inlaid in its top face: width, depth, and middle.
forge_icon_w = 32
forge_icon_d = 0.6
forge_icon_at = (45, 28)
# Test board: a few doubtful tiles, (board, index in it, where).
special_test_tiles = [
    ("forge", 1, (0, 0)),
    ("others", 7, (0, 24.8)),
    ("forge", 3, (57.8, 0)),
]
special_test_margin = 2

# The frame round the board stack: it fills the box round the player boards,
# so they can't slide, and is the stack's height, for what's above to sit on.
# Two halves, one per end of the box, each a C; print two. Under the player
# boards it's a shelf, in to the action boards: the boards' edges rest on it,
# and it stiffens the thin wall round them.
overview = (224, 96)
player_board = (299, 190)
action_board = (266, 183)  # the biggest of its layers
action_widths = [134, 162, action_board[1]]
# The layers under the player boards.
boards_under = 4
frame_clear = 1.5
frame_half_size = (inner[0] / 2, inner[1])
frame_shelf_h = boards_under * card_t
# The long sides' thickness, round the player boards.
frame_side = (frame_half_size[1] - player_board[1] - frame_clear) / 2
# Finger detents, one in each long side: their radius, the wall left outside
# them, and where along the half they sit.
frame_detent_r = 14
frame_detent_skin = 3
frame_detent_x = frame_half_size[0] / 2
assert (
    frame_detent_skin + 2 * frame_detent_r
    > frame_side + (player_board[1] - action_board[1]) / 2
), "detent doesn't reach through the shelf"

# All of it, and the lid can close.
total_h = rulebooks[2] + board_stack_h + half_h + special_h + zone_h
assert total_h <= box[2], f"the insert is {total_h} tall"

for name, size in {
    "half a": (half_a.x, half_a.y),
    "half b": (half_b_x, half[1]),
    "big": big_size,
    "boats": boat_size,
    "vp": vp_size,
    "wood": (wood.x, wood.y),
    "vikings": vikings_size,
    "islands": islands_size,
    "setup buildings": setup_bld,
    "buildings": bld_size[:2],
    "misc": misc_size,
    "strips": strips_size,
    "riser": riser_size,
    "spacer": spacer_size,
    "special forge": special_forge_size,
    "special others": special_others_size,
    "frame half": frame_half_size,
}.items():
    assert max(size) <= bed, f"{name} is too big for the bed: {size}"


# The trays


@cache
def half_a_tray() -> tuple[Part, Part]:
    return half_a.body(), part(Part() + half_a.icons())


@cache
def half_b_tray() -> tuple[Part, Part]:
    """The tile bins, and the money's column beside them, sharing a wall.
    Each money bin behind the front one has its icon too, inlaid in the wall
    in front of it, to read from the front like the outside ones."""
    tiles, cash = half_b_tiles, money
    tiles.check()
    cash.check()
    at = Pos(money_x0, 0)
    behind = [cut_icon_in_wall(cash, i) for i in range(1, len(cash.rows))]
    body = carve(
        block(half_b_x, half[1], half_h),
        tiles.cuts()
        + tiles.icons(True)
        + [at * c for c in cash.cuts() + cash.icons(True)]
        + [at * cut for cut, _ in behind],
    )
    icons = part(
        Part()
        + tiles.icons()
        + [at * i for i in cash.icons()]
        + [at * inlay for _, inlay in behind]
    )
    return body, icons


def cut_icon_in_wall(tray: Tray, row: int) -> tuple[Part, Part]:
    """A single column's bin's icon, in the face of the wall ahead of it (the
    back of the bin in front), over the scoop: what to cut, which runs on out
    into the bin in front, and the inlay, which is 0.4 deep from the scoop's
    face."""
    bins = list(tray.bins())
    _, b, _, _, _, _ = bins[row]
    _, _, x, y, w, d = bins[row - 1]
    assert b.icon
    s = tray.scoop_for(d, 0)
    hollow = Pos(x, y) * well(w, d, floor_t, tray.h, s, s)
    face = Plane.XZ * Pos(x + w / 2, b.icon.z(tray.h)) * b.icon.sketch()
    prism = Pos(0, y + d + icon_d + 1, 0) * extrude(face, s + 2 + icon_d)
    cut = part(prism & (Pos(0, icon_d, 0) * hollow))
    return cut, part(cut - hollow)


@cache
def big_tray() -> tuple[Part, Part]:
    return big.body(), part(Part() + big.icons())


@cache
def wood_tray() -> Part:
    return wood.body()


@cache
def misc_tray() -> Part:
    return misc.body()


@cache
def vikings_tray() -> Part:
    return Tray(
        "vikings",
        *vikings_size,
        deep_h,
        [Row(None, [Bin(f"viking {i + 1}", None, (21, 13))]) for i in range(4)],
        scoop=viking_scoop,
        sides=True,
        wall=deep_wall,
    ).body()


@cache
def boat_tray() -> Part:
    """The boat market. A short well leaves a thick wall front and back, which
    is cut back to the usual thickness across the well, so its slot is no
    deeper to reach into than the others': a bite out of the outline. Each
    well's floor is raised so its full stack comes flush with the top. Pinch
    slots go through the front and back walls, all the way down, the floor
    cut back from each; the skinny first well is too narrow for that, so its
    slot goes through the outer side wall instead."""
    x, y = boat_size
    outline = octagon(x, y)
    cuts = []
    for i, (wx, wy) in enumerate(boat_wells):
        # Centered front to back: a short well has thicker walls there.
        y0 = (y - wy) / 2
        x0 = boat_x(i)
        floor = boat_floor(i)
        cuts += [
            Pos(x0, y0) * well(wx, wy, floor, boat_h),
            Pos(x0, y0) * rim(wx, wy, boat_h),
        ]
        inset = boat_clear / 2 + floor_inset
        if i == 0:
            w = boat_side_slot_w
            mid = y0 + wy / 2
            cuts += Slot(
                0,
                mid,
                (1, 0),
                boat_wall,
                pinch(w, -10, boat_h, boat_slot_r),
                outside=((0, 1),),
                inside=((boat_wall, -1, floor),),
            ).cuts()
            cuts += notch(
                w, boat_wall, inset, floor, Pos(boat_wall, mid + w / 2) * toward_plus_x
            )
            continue
        w = min(boat_slot_w, wx - 2 * boat_slot_lip)
        cx = x0 + wx / 2
        bite = y0 - wall
        if bite > 0.01:
            c = chamfer_corner
            mouth = Polygon(
                (cx - wx / 2 - c, -1), (cx + wx / 2 + c, -1), (cx + wx / 2 + c, 0),
                (cx + wx / 2, c), (cx + wx / 2, bite), (cx - wx / 2, bite),
                (cx - wx / 2, c), (cx - wx / 2 - c, 0),
                align=None,
            )  # fmt: skip
            outline -= [mouth, mirror(mouth, Plane.XZ.offset(-y / 2))]
        opening = pinch(w, -10, boat_h, boat_slot_r)
        for start, way, face in ((bite, 1, y0), (y - bite, -1, y0 + wy)):
            cuts += Slot(
                cx,
                start,
                (0, way),
                wall,
                opening,
                outside=((0, 1),),
                inside=((wall, -1, floor),),
            ).cuts()
            frame = (
                Pos(cx - w / 2, face)
                if way > 0
                else Pos(cx + w / 2, face) * toward_minus_y
            )
            cuts += notch(w, wall, inset, floor, frame)
    return carve(slab(outline, boat_h), cuts)


@cache
def vp_tray() -> Part:
    x, y = vp_size
    h = vp_h
    cuts = []
    for x0, g in zip(vp_xs, vp_groups):
        cuts += [
            Pos(x0, wall) * well(g, vp_in_y, vp_floor, h),
            Pos(x0, wall) * rim(g, vp_in_y, h),
        ]
    # The tokens' slot, along x through the front face and every divider.
    walls = [(0, 1)] + [
        f for i, (x0, g) in enumerate(zip(vp_xs, vp_groups))
        for f in [(x0, -1)] + ([(x0 + g, 1)] if i < len(vp_groups) - 1 else [])
    ]  # fmt: skip
    cuts += Slot(
        0,
        vp_block_y / 2,
        (1, 0),
        vp_xs[-2],
        pinch(vp_slot_w, vp_floor + vp_slot_bottom, h, vp_slot_r),
        outside=tuple(walls),
    ).cuts()
    cuts += penalty_well()
    # The 2x5 money: its floor raised so the stack comes flush with the top,
    # and a pinch slot through the outside wall, all the way down. The floor
    # stops short of the stack's edge there.
    mx, my = money5_well
    at = (x - wall - mx, (y - my) / 2)
    floor = h - money5_n * tile_t
    cuts += [Pos(*at) * well(mx, my, floor, h), Pos(*at) * rim(mx, my, h)]
    cuts += Slot(
        x,
        y / 2,
        (-1, 0),
        wall,
        pinch(money5_slot_w, -10, h, vp_slot_r),
        outside=((0, 1),),
        inside=((wall, -1, floor),),
    ).cuts()
    inset = boat_clear / 2 + floor_inset
    frame = Pos(x - wall, (y - money5_slot_w) / 2) * toward_minus_x
    cuts += notch(money5_slot_w, wall, inset, floor, frame)
    return carve(block(x, y, h), cuts)


def penalty_well() -> list[Part]:
    """The penalty tokens' round well, in the VP tray's back corner at x = 0,
    and its corner opening: a square, from the corner to the well's middle, so
    the walls end where the well is nearest them, each end rounded over like
    a pinch slot's side. Under it the floor is cut away, but for a tongue
    under the stack, and the cut's edges chamfered."""
    x, y = vp_size
    h = vp_h
    cx, cy = pen_c
    a = wall + pen_r
    gap = pen_clear / 2 + floor_inset
    # Raised, so the stack comes flush with the top.
    floor = h - pen_n * tile_t
    section = round_corners(
        Polygon(
            (0, floor), (pen_r, floor), (pen_r, h - rim_c), (pen_r + rim_c, h),
            (pen_r + rim_c, h + 1), (0, h + 1),
            align=None,
        ),
        [(pen_r, floor)],
        fillet_r,
    )  # fmt: skip
    cuts = [Pos(cx, cy) * revolve((Plane.XZ * section).faces(), Axis.Z)]
    # The corner, walls and all: from the well's floor up, and below that,
    # all but a tongue under the stack, its corners by the walls rounded from
    # where the floor's fillet ends. One solid, as its faces are one another's.
    r = gap - fillet_r
    square = rect(-5, cy, a, y + 5)
    plan = square - Pos(cx, cy) * Circle(pen_r - gap)
    plan = grown(grown(plan, -r, Kind.INTERSECTION), r)
    cuts.append(part(up(square, floor, h + 1 - floor) + up(plan, -1, floor + 1)))
    # The walls' ends rounded over at the top, each as one side of a pinch slot
    # twice as wide, which also has them chamfered.
    rise = vp_slot_r
    ends = [
        rect(cy - rise, h - rise, cy + 1, h + 1)
        - Pos(cy - rise, h - rise) * Circle(rise),
        rect(a - 1, h - rise, a + rise, h + 1) - Pos(a + rise, h - rise) * Circle(rise),
    ]
    cuts += [
        extrude(sketch(Plane.YZ.offset(-1) * ends[0]), wall + fillet_r + 1),
        extrude(sketch(Plane.XZ.offset(-y - 1) * ends[1]), wall + fillet_r + 1),
    ]
    opening = pinch(2 * a, -10, h, vp_slot_r)
    for along in ((1, 0), (0, -1)):
        cuts += Slot(
            0,
            y,
            along,
            wall,
            opening,
            outside=((0, 1),),
            inside=((wall, -1, floor),),
            through=False,
        ).cuts()
    # The floor's cut edges: its foot, and the tongue's top.
    top = plan & rect(wall + fillet_r, 0, x, y - wall - fillet_r)
    cuts += [
        flare(plan, chamfer_out, Vector(0, 0, 1)),
        Pos(0, 0, floor) * flare(top, rim_c, Vector(0, 0, -1)),
    ]
    return cuts


@cache
def strips_tray() -> Part:
    """The mountain strips. A stack is pinched through a slot in its outside
    wall and one in the wall between the two. Each goes down through the
    floor, which is cut back from it to just under the stack's edge, to get a
    fingertip under.
    The setup buildings' tray stands behind this one, from the box's end, with
    a post at each front corner and an opening between them. The back wall's
    slot is that opening exactly: as wide, and its sides rounded over at the
    top as the posts' ends are, so the two trays' walls run on from each
    other. The front wall's is the same slot, turned half round with the
    tray, which can then go in either way round. The wells are set so each
    slot leaves a post's length of wall at its well's end: the back one from
    one end of the tray, the front one from the other."""
    x, y = strips_size
    h = base_h
    short = (strip[0] + stack_clear, strip[1] + card_clear_y)
    long = (long_strip[0] + stack_clear, long_strip[1] + card_clear_y)
    # The wells' corners: the front one's end at the high end of x, the back
    # one's at the low end.
    xs = [x - setup_post_x - short[0], setup_post_x]
    ys = [wall, y - wall - short[1]]
    floors = [h - strips_n[0] * card_t, h - (strips_n[1] + 1) * card_t]
    ledge = h - card_t
    assert min(floors) >= floor_t, "the strips' stacks are too tall for their tray"
    inset = card_clear_y / 2 + floor_inset
    # The outside slots: their span at the wall's foot, from the end the setup
    # buildings start at, and the radius their sides round over on at the top.
    # The posts'.
    slot = (setup_post_x + post_l, setup_bld[0] - setup_post_x - post_l)
    slot_w = slot[1] - slot[0]
    slot_r = post_l / 2
    out_x = [x - (slot[0] + slot[1]) / 2, (slot[0] + slot[1]) / 2]
    # Between the wells, where both run, less a post's length at each end.
    mid = (max(xs) + post_l, min(xs) + short[0] - post_l)
    mid_w = mid[1] - mid[0]
    mid_t = ys[1] - ys[0] - short[1]
    for k in (0, 1):
        assert xs[k] + post_l - 0.01 <= out_x[k] - slot_w / 2, (
            "a slot runs past its well"
        )
        assert out_x[k] + slot_w / 2 <= xs[k] + short[0] - post_l + 0.01, (
            "a slot runs past its well"
        )
    c = rim_c
    # The ledge's edge, where the short strips' well ends.
    edge = Plane.XZ.offset(-ys[1]) * Polygon(
        (xs[1] + short[0], ledge - c), (xs[1] + short[0] + c, ledge), (xs[1] + short[0], ledge),
        align=None,
    )  # fmt: skip
    cuts = [
        Pos(xs[0], ys[0]) * well(*short, floors[0], h),
        Pos(xs[0], ys[0]) * rim(*short, h),
        Pos(xs[1], ys[1]) * well(*short, floors[1], h),
        Pos(xs[1], ys[1]) * well(*long, ledge, h),
        Pos(xs[1], ys[1]) * rim(*long, h),
        extrude(edge, short[1], (0, 1, 0)),
    ]
    opening = pinch(slot_w, -10, h, slot_r)
    for k, (start, way) in enumerate(((0, 1), (y, -1))):
        cuts += Slot(
            out_x[k],
            start,
            (0, way),
            wall,
            opening,
            outside=((0, 1),),
            inside=((wall, -1, floors[k]),),
        ).cuts()
        frame = (
            Pos(out_x[k] - slot_w / 2, wall)
            if way > 0
            else Pos(out_x[k] + slot_w / 2, y - wall) * toward_minus_y
        )
        cuts += notch(slot_w, wall, inset, floors[k], frame)
    # The slot between the wells, and the floor's notch into each.
    mx = (mid[0] + mid[1]) / 2
    y0 = ys[0] + short[1]
    cuts += Slot(
        mx,
        y0,
        (0, 1),
        mid_t,
        pinch(mid_w, -10, h, slot_r),
        inside=((0, 1, floors[0]), (mid_t, -1, floors[1])),
    ).cuts()
    cuts += notch(mid_w, mid_t / 2, inset, floors[0], Pos(mid[1], y0) * toward_minus_y)
    cuts += notch(mid_w, mid_t / 2, inset, floors[1], Pos(mid[0], ys[1]))
    return carve(block(x, y, h), cuts)


# Open trays


def post_leg(h: float, t: float, back: float) -> Part:
    """A post's leg along x, from a well's corner at the origin, outside the
    well, which lies in +x, +y: t thick, reaching `back` past the corner to
    cover the other leg's end. Its free end is one side of a pinch slot:
    rounded over at the top on a radius of half its reach, leaving a flat on
    top, and straight down from there, to run on into the side of the floor's
    notch. On a short post the round-over shrinks to fit. Every edge is
    rounded, less on a thin leg."""
    r = min(post_l / 2, h - floor_t - 1)
    side = round_corners(rect(-back, 0, post_l, h), [(post_l, h)], r)
    leg = extrude(Plane.XZ * side, t)
    return part(fillet(leg.edges(), min(post_r, t / 2 - 0.1)))


def open_tray(
    size: tuple[float, float],
    h: float,
    floor: float,
    well_at: tuple[float, float],
    well_size: tuple[float, float],
    clear: tuple[float, float],
) -> Part:
    """A floor `floor` thick, with an L-shaped post round each corner of a well
    (corner, size), posts thick enough to reach the tray's edges. Between the
    posts the floor is notched, from the tray's edge to floor_inset inside the
    stack, which has `clear` round it, the notches' inside corners rounded.
    The floor's edges are rounded like the posts', so the two run flush."""
    (x0, y0), (wx, wy) = well_at, well_size
    plan = rect(0, 0, *size)
    for along, (lo, hi), inset in (
        (False, (x0, x0 + wx), y0 + clear[1] / 2 + floor_inset),
        (True, (y0, y0 + wy), x0 + clear[0] / 2 + floor_inset),
    ):
        far = size[1] if not along else size[0]
        for m in (0, 1):
            cut = round_corners(
                rect(lo + post_l, -1, hi - post_l, inset),
                [(lo + post_l, inset), (hi - post_l, inset)],
                fillet_r,
            )
            if m:
                cut = mirror(cut, Plane.XZ.offset(-far / 2))
            plan -= swap_xy(cut) if along else cut
    r = min(post_r, floor / 2 - 0.1)
    body = extrude(sketch(plan), floor)
    body = part(fillet(body.edges(), r))
    leg = post_leg(h, y0, x0)
    post = leg + swap_xy(post_leg(h, x0, y0))
    for sx in (0, 1):
        for sy in (0, 1):
            p = post
            if sx:
                p = part(mirror(p, Plane.YZ))
            if sy:
                p = part(mirror(p, Plane.XZ))
            body += Pos(x0 + sx * wx, y0 + sy * wy) * p
    return part(body)


@cache
def islands_tray() -> Part:
    """One stack, beside the big tiles, over the vikings."""
    well_size = (island + stack_clear, island + stack_clear)
    at = ((islands_size[0] - well_size[0]) / 2, (islands_size[1] - well_size[1]) / 2)
    return open_tray(
        islands_size,
        islands_h,
        islands_floor,
        at,
        well_size,
        (stack_clear, stack_clear),
    )


@cache
def setup_buildings_tray() -> Part:
    well_size = (building[0] + setup_clear_x, building[1] + card_clear_y)
    return open_tray(
        setup_bld,
        base_h,
        base_h - setup_n * card_t,
        (setup_post_x, post_t),
        well_size,
        (setup_clear_x, card_clear_y),
    )


# Honeycombs: a piece that only fills a gap, or holds up what's over it, is the
# outline, its outside edges chamfered top and bottom, with a border as thick
# as a wall, and inside that big cells, honey_cell from flat to flat, in walls
# thinner than the border, as all they do is hold something up.
# The cells' walls run along y, half a pitch apart, or along x if turned. The
# cells are set across those so that no wall runs close beside an edge of the
# outline, leaving a slot: of the shifts within half a pitch, the one that
# leaves the nearest wall furthest from the outline's edges that way is used.
honey_cell = 20
honey_wall = 0.8
honey_pitch = honey_cell + honey_wall


def honey_shift(edges: list[float]) -> float:
    half_pitch = honey_pitch / 2

    def nearest(s: float) -> float:
        return min(
            min(d, half_pitch - d) for e in edges for d in [(e - s) % half_pitch]
        )

    shifts = [k / 10 for k in range(int(half_pitch * 10) + 1)]
    return max(shifts, key=nearest)


def honeycomb(size: tuple[float, float], h: float, turned: bool = False) -> Part:
    """A rectangle, its corners rounded, h tall: see above."""
    x, y = size
    outline = RectangleRounded(x, y, chamfer_corner, align=(Align.MIN, Align.MIN))
    inside = rect(wall, wall, x - wall, y - wall)
    across, along = (y, x) if turned else (x, y)
    shift = honey_shift([wall, across - wall])
    row = honey_pitch * sqrt(3) / 2
    hexagon = RegularPolygon(honey_cell / sqrt(3), 6, rotation=0 if turned else 30)
    cells = []
    for j in range(-1, ceil(along / row) + 2):
        for i in range(-1, ceil(across / honey_pitch) + 2):
            a = shift + (i + (j % 2) / 2) * honey_pitch
            b = j * row
            cells.append(Pos(*((b, a) if turned else (a, b))) * hexagon)
    holes = inside & (Sketch() + cells)
    body = extrude(sketch(outline - holes), h)
    rims = [f.outer_wire().edges() for f in body.faces().filter_by(Axis.Z)]
    return part(chamfer([e for edges in rims for e in edges], chamfer_out))


@cache
def riser() -> Part:
    return honeycomb(riser_size, base_h)


@cache
def spacer() -> Part:
    """Narrow, so its cells are turned: their walls cross it."""
    return honeycomb(spacer_size, vp_h, turned=True)


# The in-game buildings' tray


def rounded(face: Sketch, convex: float, concave: float) -> Sketch:
    """Its convex corners rounded by `convex` and its concave ones by
    `concave`."""
    sharp = Kind.INTERSECTION
    face = grown(grown(face, concave, sharp), -concave)
    return grown(grown(face, -convex, sharp), convex)


@cache
def bld_outline() -> Sketch:
    """The end walls' outline: the tray's silhouette with its buildings in.
    From the front it's the lip's top, a step down to the last stack's, then
    each stack's top to the high corner of the next, where it steps straight
    up. At the back it runs on level from the back stack's high corner to the
    tray's edge, and straight down. Every corner is rounded."""
    high = bld_top(0, bld_depth)
    points = [(0, 0), (bld_out, 0), (bld_out, high), (bld_depth, high)]
    for i in range(1, bld_last + 1):
        hi = bld_high(i)
        points += [(hi.X, bld_top(i - 1, hi.X)), (hi.X, hi.Y)]
    points += [
        (bld_front_end.X, bld_top(bld_last, bld_front_end.X)),
        (bld_front_end.X, bld_front_end.Y),
        (0, bld_front_h),
    ]
    return rounded(polygon(points), chamfer_corner, chamfer_corner)


def bld_slab(p: Vector, length: float, t: float) -> Sketch:
    """A slab along the ramps' slope from p: `length` long, t thick, under the
    line."""
    e = p + length * bld_d
    return polygon([p, e, e - t * bld_n, p - t * bld_n])


@cache
def bld_section() -> Sketch:
    """The section: floor, ramps, the stops at the stacks' low edges, the
    front wall with its lip, and the back wall with the solid behind it. It's
    all within the outline, which only takes its outside corners off."""
    parts = [rect(0, 0, bld_out, floor_t)]
    for i in range(bld_last + 1):
        p = bld_p(i)
        rise = bld_step * sin(bld_a) - bld_ramp_t / 2
        # Ramp: down through the floor.
        ramp = bld_slab(p - 5 * bld_d, 5 + building[1] - bld_grip, bld_ramp_t)
        parts.append(ramp & rect(0, 0, bld_depth, bld_size[2]))
        # The stop at the stack's low edge, up into the next ramp.
        if i < bld_last:
            back = p - wall * bld_d
            parts.append(polygon([p, p + rise * bld_n, back + rise * bld_n, back]))
    # The last stack's stop is the front wall, with its lip.
    p = bld_p(bld_last)
    under = bld_front - bld_ramp_t * bld_n
    lip = under + bld_reach * bld_d
    parts.append(
        polygon([(0, 0), (p.X, 0), p, under, lip, bld_front_end, (0, bld_front_h)])
    )
    # The back wall, under the end of the back stack's ramp, and the solid
    # part behind it.
    top = bld_top(0, bld_back) - bld_t[0] / cos(bld_a) - bld_ramp_t / 2
    parts += [
        rect(bld_back - wall, 0, bld_back, top),
        rect(bld_back - wall, 0, bld_out, floor_t + bld_lip),
    ]
    return sketch(
        bld_outline() & rounded(sketch(Sketch() + parts), bld_round, bld_fillet)
    )


def bld_hollow(i: int) -> list[Vector]:
    """The hollow under ramp i: floor, ramp, and the stop (or back wall) of the
    stack before."""
    p = bld_p(i)
    a = Vector(p.X + bld_ramp_t / sin(bld_a), floor_t)
    if i == 0:
        x = bld_back - wall
        rise = (x - p.X) * tan(bld_a) - bld_ramp_t / cos(bld_a)
        return [a, Vector(x, floor_t), Vector(x, floor_t + rise)]
    q = bld_p(i - 1)
    return [
        a,
        Vector(q.X - wall / cos(bld_a), floor_t),
        q - wall * bld_d + (bld_step * sin(bld_a) - bld_ramp_t) * bld_n,
    ]


def incircle(h: list[Vector]) -> tuple[Vector, float]:
    """The circle that fits a triangle: where its sides meet if they all come
    in at one rate, and how far in that is."""
    a, b, c = ((h[2] - h[1]).length, (h[0] - h[2]).length, (h[1] - h[0]).length)
    e1, e2 = h[1] - h[0], h[2] - h[0]
    area = abs(e1.X * e2.Y - e1.Y * e2.X) / 2
    return (a * h[0] + b * h[1] + c * h[2]) / (a + b + c), 2 * area / (a + b + c)


def bld_plane(x: float) -> Plane:
    """The section's plane, x along the tray: u along y, v up."""
    return Plane.YZ.offset(x)


def along_x(
    face: Shape, x: float, length: float, way: int = 1, taper: float = 0
) -> Part:
    """A face of the section drawn from x along the tray, `way` ±1."""
    return extrude(sketch(bld_plane(x) * face), length, (way, 0, 0), taper=taper)


def bld_end_wall(x: float, facing: int) -> Part:
    """An end wall, bld_end_t thick, its outside face at x, facing ±x. Its
    outside edge is chamfered all round, by chamfer_out. Its inside edge is
    chamfered, by rim_c, where the wall stands clear of the section: where
    that meets the edge, it's left whole, to run flush. So it's drawn in
    layers: the outline tapered out to its outside face, straight, tapered in
    to the inside face, and inside that the section, filling what the taper
    takes off where the section meets the wall."""
    outline = bld_outline()
    inward = -facing
    mid = x + inward * chamfer_out
    inside = x + inward * bld_end_t
    return part(
        along_x(outline, mid, chamfer_out, facing, taper=45)
        + along_x(outline, mid, bld_end_t - chamfer_out - rim_c, inward)
        + along_x(outline, inside - inward * rim_c, rim_c, inward, taper=45)
        + along_x(bld_section(), inside, rim_c, facing)
    )


@cache
def buildings_tray() -> Part:
    """As it lies in the box, but along x: the buildings along x, u along y.
    Near the far end, the sockets' floors, and the roof under each: the hollow
    ends in a pyramid, its faces at 45°, its point over the middle."""
    body = bld_end_wall(0, -1) + along_x(bld_section(), bld_end_t, bld_in_x)
    end = bld_end_t + bld_in_x - bld_plug_h - bld_glue_gap
    for i in range(bld_last + 1):
        hollow = polygon(bld_hollow(i))
        middle, r = incircle(bld_hollow(i))
        # The hollow, filled, and grown into the walls round it.
        fill = grown(hollow, 0.6, Kind.INTERSECTION) & bld_outline()
        x0 = end - bld_socket_floor - r
        apex = Vertex(x0 + r, middle.X, middle.Y)
        base = (bld_plane(x0) * hollow).faces()[0].outer_wire()
        pyramid = Solid.make_loft([base, apex])
        body += along_x(fill, x0, r + bld_socket_floor) - pyramid
    return part(body)


def bld_plug_foot(i: int) -> Sketch:
    """A plug's foot: its hollow, 1 + bld_plug_clear in from every side, its
    corners rounded by 1."""
    inset = grown(polygon(bld_hollow(i)), -1 - bld_plug_clear, Kind.INTERSECTION)
    return grown(inset, 1)


@cache
def buildings_cap() -> Part:
    """The other end wall, on the tray's far end, with a plug into each
    socket, its end chamfered, and crush ribs in pairs on it: one on the
    floor's side and one on the ramp's, squeezing the plug between them. Two
    pairs, a fifth of the way in from each end of the plug, which starts where
    the hollow is tall enough for it: plug_from along either side from the
    hollow's point. They stand out past the clearance and taper in toward the
    plug's end. None on the short side: the plug needs no squeezing there."""
    x = bld_size[0]
    inside = x - bld_end_t
    body = bld_end_wall(x, 1)
    plug_from = (1 + bld_plug_clear) / tan(bld_a / 2)
    for i in range(bld_last + 1):
        h = bld_hollow(i)
        middle = (h[0] + h[1] + h[2]) / 3
        foot = bld_plug_foot(i)
        straight = bld_plug_h - bld_plug_lead
        body += along_x(foot, inside, straight, -1)
        body += along_x(foot, inside - straight, bld_plug_lead, -1, taper=45)
        to = min((h[1] - h[0]).length, (h[2] - h[0]).length) - 1 - bld_plug_clear
        for k in (1, 2):
            e = (h[k] - h[0]).normalized()
            v = Vector(-e.Y, e.X)
            if v.dot(middle - h[0]) < 0:
                v = -v
            for f in (0.2, 0.8):
                m = h[0] + (plug_from + f * (to - plug_from)) * e
                body += crush_rib(m, v, inside)
    return part(body)


def crush_rib(m: Vector, v: Vector, x: float) -> Part:
    """A crush rib down a plug from the cap's inside face at x, at m on its
    hollow's side, v pointing in: round, standing bld_rib past the plug's
    face, 2 mm short of the plug's end there and tapering in toward it."""
    outer = m + (bld_plug_clear + 0.5 - bld_rib) * v
    inner = m + (bld_plug_clear + 1.2) * v
    circles = [Pos(outer.X, outer.Y) * Circle(0.5), Pos(inner.X, inner.Y) * Circle(0.3)]
    rib = along_x(
        make_hull([e for c in circles for e in c.edges()]), x, bld_plug_h - 1, -1
    )
    # The taper: a slope through the outer circle's far edge, 2 short of the
    # plug's end, and the inner one's, 1 short.
    a, b = outer - 0.5 * v, inner + 0.3 * v
    rise = 1 / (b - a).length
    normal = Vector(-1, -rise * v.X, -rise * v.Y)
    at = Vector(x - (bld_plug_h - 2), a.X, a.Y)
    return part(split(rib.solids(), Plane(at, z_dir=normal), keep=Keep.BOTTOM))


# The special boards


@dataclass(frozen=True)
class Tile:
    """A special tile's pocket: its cells, as (col, row), and its cell
    origin, on its board."""

    cells: tuple[tuple[int, int], ...]
    x: float
    y: float

    @property
    def size(self) -> tuple[float, float]:
        return (
            (max(c for c, _ in self.cells) + 1) * unit,
            (max(r for _, r in self.cells) + 1) * unit,
        )

    def pocket(self) -> Sketch:
        """Its outline: outside corners rounded by the clearance, inside
        corners sharp."""
        squares = Sketch() + [
            Pos(self.x + c * unit, self.y + r * unit)
            * Rectangle(unit, unit, align=(Align.MIN, Align.MIN))
            for c, r in self.cells
        ]
        return grown(squares.clean(), pocket_clear)

    def sides(self) -> dict[str, bool]:
        """Which sides of its bounding box are press ends."""
        n = [round(s / unit) for s in self.size]
        com = [
            sum((cell[k] + 0.5) * unit for cell in self.cells) / len(self.cells)
            for k in (0, 1)
        ]
        ok = [n[k] >= tilt_min_cells for k in (0, 1)]
        far = [n[k] * unit - tilt_a - tilt_balance for k in (0, 1)]
        return {
            "left": ok[0] and com[0] >= tilt_a + tilt_balance,
            "right": ok[0] and com[0] <= far[0],
            "front": ok[1] and com[1] >= tilt_a + tilt_balance,
            "back": ok[1] and com[1] <= far[1],
        }

    def bands(self) -> Sketch:
        """Where its floor drops: a strip along each press end."""
        x, y = self.size
        strips = {
            "left": rect(-1, -1, tilt_a, y + 1),
            "right": rect(x - tilt_a, -1, x + 1, y + 1),
            "front": rect(-1, -1, x + 1, tilt_a),
            "back": rect(-1, y - tilt_a, x + 1, y + 1),
        }
        sides = self.sides()
        return sketch(
            Pos(self.x, self.y)
            * (Sketch() + [s for k, s in strips.items() if sides[k]])
        )

    def drops(self, z: float) -> Part:
        """The drops' cut, from their floor at z, along each press end: the
        tile's edge at the pocket's clearance, the S of the step tilt_a in.
        Within its own pocket: on the test board, tiles' pockets interlock."""
        x, y = self.size
        planes = {
            "left": Plane((0, y + 1, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)),
            "right": Plane((x, -1, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0)),
            "front": Plane((-1, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)),
            "back": Plane((x + 1, y, 0), x_dir=(0, -1, 0), z_dir=(-1, 0, 0)),
        }
        length = {"left": y + 2, "right": y + 2, "front": x + 2, "back": x + 2}
        sides = self.sides()
        strips = Part() + [
            extrude(planes[k] * tilt_profile(), length[k], planes[k].z_dir)
            for k in planes
            if sides[k]
        ]
        return part(
            up(self.pocket(), z, tilt_d + 1) & (Pos(self.x, self.y, z) * strips)
        )


@cache
def tilt_profile() -> Face:
    """The drop's section: the tile's edge at x = 0, the drop's floor at y = 0
    and the pocket's at y = tilt_d; past that, up into the pocket."""
    r = tilt_r
    w = tilt_a - r  # the step's wall
    s = sqrt(0.5) * r
    edges = [
        Edge.make_line((-1, 0), (w - r, 0)),
        Edge.make_three_point_arc((w - r, 0), (w - r + s, r - s), (w, r)),
        Edge.make_three_point_arc(
            (w, r), (w + r - s, tilt_d - r + s), (tilt_a, tilt_d)
        ),
        Edge.make_line((tilt_a, tilt_d), (tilt_a, tilt_d + 1)),
        Edge.make_line((tilt_a, tilt_d + 1), (-1, tilt_d + 1)),
        Edge.make_line((-1, tilt_d + 1), (-1, 0)),
    ]
    return Face(Wire(edges))


def board_tiles(name: str, at: tuple[float, float]) -> list[Tile]:
    return [
        Tile(
            tuple(tuple(c) for c in t["cells"]), t["at"][0] + at[0], t["at"][1] + at[1]
        )
        for t in layout["boards"][name]["tiles"]
    ]


def special_board(
    outline: Face | Sketch, tiles: list[Tile], inlays: Sketch | None = None
) -> tuple[Part, Part]:
    """A board with a pocket for each tile, flush, and the pocket floors' skin:
    under each pocket, floor_skin deep below the drops and the rest of its
    floor, and all of the step between them. `inlays` are cut from its top,
    for its icon. Its body and its floors."""
    h = special_h
    pockets = Sketch() + [t.pocket() for t in tiles]
    drops = Sketch() + [t.pocket() & t.bands() for t in tiles]
    rest = pockets - drops
    z_drop = h - pocket_d - tilt_d
    z_skin = z_drop - floor_skin
    z_rest = h - pocket_d - floor_skin
    floors = part(up(drops, z_skin, tilt_d + floor_skin) + up(rest, z_rest, floor_skin))
    floors = carve(floors, [t.drops(z_drop) for t in tiles])
    body = carve(slab(outline, h), [up(drops, z_skin, h), up(rest, z_rest, h)])
    # The pockets' rims: the top face's edges but its outside ones.
    top = body.faces().sort_by(Axis.Z).last
    body = chamfer([e for w in top.inner_wires() for e in w.edges()], rim_c)
    if inlays is not None:
        body -= up(inlays, h - forge_icon_d, 1)
    return part(body), floors


def board_outline(size: tuple[float, float], r: float) -> Sketch:
    """Its corners rounded by r, which can be half its width."""
    x, y = size
    corners = [Pos(cx, cy) * Circle(r) for cx in (r, x - r) for cy in (r, y - r)]
    return sketch(Sketch() + make_hull([e for c in corners for e in c.edges()]))


def centered(name: str, size: tuple[float, float]) -> tuple[float, float]:
    """Where its packed board's corner is, centered on a board of this size."""
    px, py = layout["boards"][name]["size"]
    return ((size[0] - px) / 2, (size[1] - py) / 2)


@cache
def forge_icon() -> dict[str, Sketch]:
    """forge.svg's two colors, by id, "black" and "orange": centered on
    forge_icon_at, forge_icon_w wide, and turned half round. (Scaled first:
    build123d's scale() leaves a shape's own position as it was.)"""
    faces = import_svg(HERE / "forge.svg")
    box_ = (Sketch() + list(faces)).bounding_box()
    s = forge_icon_w / box_.size.X
    place = Pos(*forge_icon_at) * Rot(0, 0, 180) * Pos(-box_.center() * s)
    return {
        label: sketch(
            place * scale(Sketch() + [f for f in faces if f.label == label], s)
        )
        for label in ("black", "orange")
    }


@cache
def special_forge() -> tuple[Part, Part, Sketch, Sketch]:
    icon = forge_icon()
    body, floors = special_board(
        board_outline(special_forge_size, special_corner_r),
        board_tiles("forge", centered("forge", special_forge_size)),
        sketch(icon["black"] + icon["orange"]),
    )
    return body, floors, icon["black"], icon["orange"]


@cache
def special_others() -> tuple[Part, Part]:
    return special_board(
        board_outline(special_others_size, special_corner_r),
        board_tiles("others", centered("others", special_others_size)),
    )


@cache
def special_test() -> tuple[Part, Part]:
    """A few doubtful tiles on a small board, to try the fit and the tip."""
    m = special_test_margin + pocket_clear
    tiles = []
    for board, i, (x, y) in special_test_tiles:
        t = layout["boards"][board]["tiles"][i]
        tiles.append(Tile(tuple(tuple(c) for c in t["cells"]), m + x, m + y))
    size_x = max(t.x + t.size[0] for t in tiles) + m
    size_y = max(t.y + t.size[1] for t in tiles) + m
    return special_board(octagon(size_x, size_y), tiles)


# The card trays


@cache
def deck_stl(stl: str) -> Solid:
    """As downloaded, its corner at the origin."""
    shape = Mesher().read(str(HERE / "card-trays" / stl))[0]
    assert isinstance(shape, Solid), f"{stl} isn't watertight"
    return Pos(-shape.bounding_box().min) * shape


@cache
def deck_tray(stl: str, cut: float) -> Part:
    """A card tray, with `cut` out of its length (its y): a slice from where
    its section is the same all along, the back part moved up to the front
    one. At each end it gets a lip across the floor, deck_lip high over it,
    from side wall to side wall: the trays come with only the floor's edge
    there, and the side walls' ends, for the next thing in the box to sit
    against. The lips' top edges are rounded, and they're trimmed to the
    tray's own outside: its corners and bottom edges are rounded over, and a
    square bar would stand proud of them."""
    whole = deck_stl(stl)
    x, y = deck_size[stl]
    z = whole.bounding_box().max.Z
    at = deck_cut_at * y
    front = cuboid(-1, -1, -1, x + 1, at, z + 1) & whole
    back = Pos(0, -cut, 0) * (cuboid(-1, at + cut, -1, x + 1, y + 1, z + 1) & whole)
    tray = front + back
    length = y - cut
    h = deck_floor + deck_lip
    # Each lip runs on past the tray's outside, below its rounded top, for the
    # trim to end it.
    lip = round_corners(rect(0, -1, wall, h), [(0, h), (wall, h)], rim_c)
    sections = [
        lip + rect(-1, -1, wall / 2, h - rim_c),
        Pos(length - wall, 0) * (lip + rect(wall / 2, -1, wall + 1, h - rim_c)),
    ]
    lips = part(
        Part() + [extrude(sketch(Plane.YZ.offset(-1) * f), x + 2) for f in sections]
    )
    # The trim: the tray's outline seen along each axis.
    points = [(v.X, v.Y, v.Z) for v in tray.vertices()]
    depth = 2 * max(x, y, z) + 2
    for plane, (a, b) in ((Plane.XY, (0, 1)), (Plane.XZ, (0, 2)), (Plane.YZ, (1, 2))):
        outline = MultiPoint([(p[a], p[b]) for p in points]).convex_hull
        seen = polygon(outline.exterior.coords[:-1])
        lips &= extrude(plane.offset(-depth / 2) * seen, depth, plane.z_dir)
    return part(tray + lips)


# Pieces


def body_piece(shape: Shape, name: str, color: str, parent: str = "") -> Piece:
    return Piece(shape, name, color, filaments[color], parent=parent)


def icons_piece(shape: Shape, tray: str, parent: str = "") -> Piece:
    return Piece(
        shape, f"{tray} icons", icon_color, filaments[icon_color], parent=parent
    )


Pieces = list[Piece]


def half_a_pieces() -> Pieces:
    body, icons = half_a_tray()
    return [body_piece(body, "half a", game), icons_piece(icons, "half a")]


def half_b_pieces() -> Pieces:
    body, icons = half_b_tray()
    return [body_piece(body, "half b", game), icons_piece(icons, "half b")]


def big_pieces() -> Pieces:
    body, icons = big_tray()
    return [
        body_piece(body, "big tray", game, "big"),
        icons_piece(icons, "big", "big"),
    ]


def special_forge_pieces() -> Pieces:
    body, floors, handles, jaws = special_forge()
    top = special_h - forge_icon_d
    group = "forge board"
    return [
        body_piece(body, "forge board panel", game, group),
        body_piece(floors, "forge pocket floors", pocket_floor, group),
        body_piece(up(handles, top, forge_icon_d), "tongs' handles", icon_color, group),
        body_piece(
            up(jaws, top, forge_icon_d), "tongs' jaws and rock", forge_orange, group
        ),
    ]


def special_others_pieces() -> Pieces:
    body, floors = special_others()
    return [
        body_piece(body, "others board panel", game, "others board"),
        body_piece(floors, "others pocket floors", pocket_floor, "others board"),
    ]


def special_test_pieces() -> Pieces:
    body, floors = special_test()
    return [
        body_piece(body, "test board panel", game, "test board"),
        body_piece(floors, "test pocket floors", pocket_floor, "test board"),
    ]


# Where each object sits in the box, from the box's corner, bottom up: 1, the
# boards, in their frame, and the rulebooks on them; 2, the half trays, one
# behind the other; 3, the special boards; 4 to 6, the columns' bottom, middle
# and top trays.
corner = Pos(box_clear / 2, box_clear / 2)
halves_at = corner * Pos(0, 0, board_stack_h + rulebooks[2])
# Turned half round: the forge board at the right, its icon at the back.
special_at = (
    corner
    * Pos(inner[0], inner[1], board_stack_h + rulebooks[2] + half_h)
    * Rot(0, 0, 180)
)
base = corner * Pos(0, 0, board_stack_h + rulebooks[2] + half_h + special_h)
back = base * Pos(0, front_y)
upper = back * Pos(0, 0, base_h + tier_h)
# Turned, its low side at the end of the box.
bld_at = upper * Pos(0, back_y) * Rot(0, 0, -90)


def placed(
    draw: Callable[[], Pieces], at: Location, place: Location | None = None
) -> Callable[[], Pieces]:
    """What `draw` draws, sitting `at` in the box, and printed at `place`, or
    as drawn."""
    return lambda: [replace(p, at=at, place=place or Location()) for p in draw()]


def single(
    draw: Callable[[], Shape], name: str, color: str, at: Location
) -> Callable[[], Pieces]:
    return placed(lambda: [body_piece(draw(), name, color)], at)


def deck(i: int) -> Callable[[], Pieces]:
    """Turned, each deck running along x, its front at the high end."""
    d = decks[i]
    color = setup if d.setup else game
    x = sum(deck_len[: i + 1])
    at = base * Pos(x, 0, base_h) * Rot(0, 0, 90)
    return single(lambda: deck_tray(d.stl, d.cut), f"{d.name} tray", color, at)


# As printed: the buildings' tray standing on its end wall, the cap on its
# outside face.
bld_standing = Rot(0, -90, 0)
cap_down = Pos(0, 0, bld_size[0]) * Rot(0, 90, 0)
buildings_pieces = placed(
    lambda: [body_piece(buildings_tray(), "buildings", game)], bld_at, bld_standing
)
cap_pieces = placed(
    lambda: [body_piece(buildings_cap(), "cap", game)], bld_at, cap_down
)


# Put together


def board_stack() -> Pieces:
    """The boards, bottom to top, one card_t layer each, within the box.
    Smallest at the bottom, the player boards, the biggest, on top: so the
    frame can be thick round the small ones, under the player boards'
    edges."""
    layers = [(overview, "round overview", "wheat")]
    layers += [
        ((action_board[0], w), f"action board {i}", "tan")
        for i, w in enumerate(action_widths, 1)
    ]
    layers += [(player_board, f"player board {i}", "burlywood") for i in range(1, 5)]
    assert len(layers) == board_layers, f"board stack has {len(layers)} layers"
    out = []
    for i, ((x, y), name, color) in enumerate(layers):
        x0, y0 = (box[0] - x) / 2, (box[1] - y) / 2
        z = i * card_t
        out.append(
            Piece(cuboid(x0, y0, z, x0 + x, y0 + y, z + card_t - 0.1), name, color)
        )
    return out


@cache
def frame_half() -> Part:
    """A C round one end of the board stack, its far end at x = inner[0] / 2:
    the action boards' well through it, and the player boards' over the
    shelf, both rims chamfered, and a finger detent in each long side: a
    round hole down through the wall and the shelf, to get a fingertip under
    the player boards' edge."""
    x, y = frame_half_size
    h = board_stack_h

    def board_well(board: tuple[float, float]) -> Rectangle:
        bx, by = board[0] + frame_clear, board[1] + frame_clear
        return rect(
            (inner[0] - bx) / 2, (y - by) / 2, (inner[0] + bx) / 2, (y + by) / 2
        )

    shelf, boards = board_well(action_board), board_well(player_board)
    down = Vector(0, 0, -1)
    cuts = [
        up(shelf, -1, h + 2),
        up(boards, frame_shelf_h, h),
        Pos(0, 0, frame_shelf_h) * flare(shelf, chamfer_out, down),
        Pos(0, 0, h) * flare(boards, rim_c, down),
    ]
    for cy in (
        frame_detent_skin + frame_detent_r,
        y - frame_detent_skin - frame_detent_r,
    ):
        hole = Pos(frame_detent_x, cy) * Circle(frame_detent_r)
        cuts += [
            up(hole, -1, h + 2),
            flare(hole, chamfer_out, Vector(0, 0, 1)),
            Pos(0, 0, h) * flare(hole, chamfer_out, down),
            # The shelf's rim, inside the boards' well.
            part(
                Pos(0, 0, frame_shelf_h) * flare(hole, chamfer_out, down)
                & up(boards, 0, h)
            ),
        ]
    return carve(block(x, y, h), cuts)


def assembly(objects: Mapping[str, Pieces]) -> Pieces:
    """The insert in the box, with the boards and the rulebooks, grouped by
    layer in FreeCAD: the objects printed twice twice, the second half trays
    behind the first, and the second frame half the first turned half round
    the box's middle."""

    def into(
        group: str, pieces: Pieces, at: Location | None = None, suffix: str = ""
    ) -> Pieces:
        """Moved by `at`, named with `suffix`, in `group`, and their own groups
        in that."""
        return [
            replace(
                p,
                shape=(at or Location()) * p.shape,
                name=p.name + suffix,
                parent=f"{group}/{p.parent}" if p.parent else group,
            )
            for p in pieces
        ]

    def layer(group: str, *names: str) -> Pieces:
        return [p for n in names for p in into(group, objects[n])]

    middle = Vector(box[0] / 2, box[1] / 2)
    turned = Pos(middle) * Rot(0, 0, 180) * Pos(-middle)
    x0, y0 = (box[0] - rulebooks[0]) / 2, (box[1] - rulebooks[1]) / 2
    z = board_stack_h
    books = cuboid(x0, y0, z, x0 + rulebooks[0], y0 + rulebooks[1], z + rulebooks[2])
    halves = objects["half_a"] + objects["half_b"]
    tray = "half trays/half tray"
    decks = ["deck_setup", "deck_occupations", "deck_weapons"]
    return (
        layer("boards", "frame_half")
        + into("boards", objects["frame_half"], turned, " 2")
        + into("boards", board_stack() + [Piece(books, "rulebooks", "ivory")])
        + into(f"{tray} 1", halves, suffix=" 1")
        + into(f"{tray} 2", halves, Pos(0, half[1]), " 2")
        + layer("special boards", "special_forge", "special_others")
        + layer("columns/bottom", "strips", "boats", "misc", "setup_buildings")
        + layer("columns/bottom", "riser", "wood", "vikings")
        + layer("columns/middle", *decks, "islands")
        + layer("columns/top", "vp", "spacer", "big", "buildings", "buildings_cap")
    )


# Settings

# The open trays' floors are thick, and only thin posts go on above them: where
# a floor's solid top layers end, they push a ridge out into the posts. Less so
# with the outside wall drawn first. No shape avoids it: the posts stand on a
# floor's top however thick the floor is, and thick posts would crowd the
# stacks.
open_tray_settings = {"wall_sequence": "outer wall/inner wall"}
# Across a slot cut down to the bed Orca travels without retracting, after
# infill and inner walls, and leaves a thread each time. The pinch slots go
# down that far to reach the bottom of a stack.
orca = {"reduce_infill_retraction": 0}


objects = {
    "half_a": Object(
        placed(half_a_pieces, halves_at), "Half a tray of goods tiles: print two"
    ),
    "half_b": Object(
        placed(half_b_pieces, halves_at * Pos(half_a.x, 0)),
        "The rest of a half tray, and its money: print two",
    ),
    "big": Object(
        placed(big_pieces, back * Pos(islands_size[0], 0, deep_h)),
        "Big tiles and animals",
    ),
    "boats": Object(
        single(boat_tray, "boats", game, base * Pos(decks_x, 0)), "The boat market"
    ),
    "vp": Object(
        single(vp_tray, "vp", game, base * Pos(decks_x, 0, boat_h)),
        "VP and penalty tokens, and the 2x5 money",
    ),
    "vikings": Object(
        single(vikings_tray, "vikings", setup, back * Pos(islands_size[0], 0)),
        "The vikings",
    ),
    "islands": Object(
        single(islands_tray, "islands", setup, back * Pos(0, 0, base_h)),
        "The islands, open",
        settings=open_tray_settings,
    ),
    "wood": Object(
        single(
            wood_tray, "wood", game, back * Pos(islands_size[0] + vikings_size[0], 0)
        ),
        "Ore, stone and wood",
    ),
    "buildings": Object(
        buildings_pieces, "The in-game buildings, standing on an end wall"
    ),
    "buildings_cap": Object(
        cap_pieces, "The buildings tray's other end wall, glued on"
    ),
    "setup_buildings": Object(
        single(setup_buildings_tray, "setup buildings", setup, back),
        "The setup buildings, open",
        settings=open_tray_settings,
    ),
    "misc": Object(
        single(misc_tray, "misc", setup, base * Pos(decks_x, boat_size[1])),
        "The moose, the dice and the cube",
    ),
    "strips": Object(single(strips_tray, "strips", setup, base), "The mountain strips"),
    "riser": Object(
        single(riser, "riser", setup, back * Pos(0, setup_bld[1])),
        "Under the islands, behind the setup buildings",
    ),
    "spacer": Object(
        single(spacer, "spacer", setup, base * Pos(decks_x + vp_size[0], 0, boat_h)),
        "Beside the VP tray",
    ),
    "frame_half": Object(
        single(frame_half, "frame half", setup, corner), "Round the boards: print two"
    ),
    "deck_setup": Object(deck(0), "The setup occupation cards"),
    "deck_occupations": Object(deck(1), "The in-game occupation cards"),
    "deck_weapons": Object(deck(2), "The weapon cards"),
    "special_forge": Object(
        placed(special_forge_pieces, special_at), "The forge's special tiles"
    ),
    "special_others": Object(
        placed(special_others_pieces, special_at * Pos(special_forge_size[0], 0)),
        "The other special tiles",
    ),
    "special_test": Object(special_test_pieces, "A few doubtful special tiles, to try"),
}


project(
    __file__,
    objects=objects,
    views={
        "assembly": View(
            assembly, "In the box", [n for n in objects if n != "special_test"]
        ),
    },
    orca=orca,
    # A line per set of filaments.
    plates=[
        "frame_half*2",
        "half_a*2 half_b*2 big",
        "setup_buildings misc strips riser spacer deck_setup islands vikings",
        "special_forge special_others",
        "buildings buildings_cap wood boats vp deck_occupations deck_weapons",
    ],
)
