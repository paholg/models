"""An octagonal coin, for the Magic Octagon, with an arrow inlaid in each face,
pointing at a vertex.

    from designs.coin import Coin

    coin = Coin("knurled", angles=(0, 120), bumps=12)
    project(
        __file__,
        objects={"knurled": Object(coin.pieces, "Both halves, face down")},
        views={"assembly": View(row, "Glued", ["knurled"])},
    )

It comes in three shapes: the octagon; a round coin; and a round one with a
reeded edge, like a quarter's, which has a bump where each of the octagon's
vertices would be.

Two halves, split through the coin's thickness and printed face down, so both
faces come off the bed. Each half has a pin and a crush-ribbed hole on its glue
side, placed so the halves only go together one way: with the arrows as far
apart as `angles` says.

In a half's own frame the face is at z = 0 and the glue side is up; the second
half goes on the first turned over the x axis. games/magic-octagon/rotating.py
builds on the blank and the arrows, with halves of its own.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from build123d import (
    Axis,
    Circle,
    Kind,
    Location,
    Part,
    Polygon,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    Shape,
    Sketch,
    chamfer,
    extrude,
    loft,
    offset,
)

from build.cad import Piece

SHAPES = ("octagon", "round", "knurled")

# Coin

# Across the vertices, or the knurls.
D = 40
HALF_T = 2.5
# Rounds the vertices.
corner_r = 1
face_chamfer = 0.6
# A small chamfer either side of the seam hides a little misalignment.
seam_chamfer = 0.2

# Knurling

# Reeds around the edge, as on a quarter: flat-topped, with a groove between
# each two. A multiple of the bumps, for one at each.
knurls = 96
# The grooves, at the edge and at their floors.
groove_w = 0.65
groove_floor = 0.2
groove_d = 0.4
# The bumps at the vertices: reeds that are wider, and stand this far out of
# the edge.
bump_w = 2
bump_top = 1.2
BUMP_H = 0.5
bump_r = 0.2

# Arrow

INLAY = 0.6
arrow_tail = -12
arrow_tip = 15
# A line is the arrow's shaft, as far past the centre as its tail is.
MARKS = ("arrow", "line", "")
shaft_w = 4
head_w = 12
head_l = 9
arrow_r = 0.5

# Joint

pin_d = 4
pin_h = 1.2
# From the centre, on the diagonals between the arrows.
pin_r = 11
pin_c = 0.15
pin_chamfer = 0.4
# The hole is this much deeper than the pin, for glue.
hole_extra = 0.3
ribs = 3
rib_w = 0.8
rib_press = 0.1

# Colors: each half's, and its arrow's, which is the other half's.
HALF_COLORS = ("gold", "#5c6470")
ARROW_COLORS = HALF_COLORS[::-1]
# What the slate gray stands for.
FILAMENTS = ("", "black")
# Each half's group in FreeCAD, with its arrow: named for its color, or, on a
# coin of one color, its side.
HALVES = ("gold", "black")
SIDES = ("front", "back")


def sketch(shape: Shape) -> Sketch:
    """A 2D shape's faces, as a Sketch to extrude: build123d's operators type
    what they make as a Compound."""
    return Sketch(shape.faces())


def grown(face: Shape, d: float, kind: Kind = Kind.INTERSECTION) -> Sketch:
    """Grown by d, or shrunk for a d below 0: its corners kept sharp, or with
    Kind.ARC the convex ones rounded."""
    return sketch(offset(sketch(face), d, kind=kind))


def opened(face: Shape, r: float) -> Sketch:
    """Its convex corners rounded to r, the others left sharp."""
    return grown(grown(face, -r), r, Kind.ARC)


def up(face: Shape, z0: float, height: float) -> Part:
    """A face, drawn up from z0."""
    return Pos(0, 0, z0) * extrude(sketch(face), height, (0, 0, 1))


def half_settings(shape: str) -> dict[str, object]:
    """On the face, which prints on the bed: rings around the octagon, or chords
    around the round ones."""
    pattern = "octagramspiral" if shape == "octagon" else "hilbertcurve"
    return {"bottom_surface_pattern": pattern}


def arrow_settings(angle: float) -> dict[str, object]:
    """Lines along the arrow. Angles follow the model, so that turning it in
    Orca turns the lines too."""
    return {
        "bottom_surface_pattern": "monotonic",
        "bottom_layer_direction": angle,
        "align_infill_direction_to_model": True,
    }


def flipped(z: float) -> Location:
    """Turned over the x axis, its face at z."""
    return Pos(0, 0, z) * Rot(180, 0, 0)


@dataclass(frozen=True)
class Coin:
    shape: str = "octagon"  # one of SHAPES
    # Where each face's arrow points, in its half's own frame.
    angles: tuple[float, float] = (0, 90)
    # What's inlaid in each face, of MARKS: an arrow, a line, or nothing.
    marks: tuple[str, str] = ("arrow", "arrow")
    # Each half's color, of HALF_COLORS: what's inlaid in it is the other.
    colors: tuple[str, str] = HALF_COLORS
    # The knurled coin's bumps, evenly around it, one at 0: or none.
    bumps: int = 8
    # Where the pin is, with the hole opposite it across the x axis, so that
    # turning a half over puts each over the other.
    pin_a: float = 45
    half_t: float = HALF_T

    def __post_init__(self) -> None:
        assert self.shape in SHAPES, f"no shape {self.shape}"
        assert all(m in MARKS for m in self.marks), f"no marks {self.marks}"
        assert all(c in HALF_COLORS for c in self.colors), f"no colors {self.colors}"
        assert not self.bumps or knurls % self.bumps == 0, (
            "knurls must be a multiple of the bumps"
        )

    def outline(self, inset: float = 0) -> Sketch:
        if self.shape == "octagon":
            return grown(
                grown(RegularPolygon(D / 2, 8), -corner_r - inset), corner_r, Kind.ARC
            )
        return Sketch(Circle(D / 2 - inset))

    def chamfered(self, outline) -> Part:
        """A convex outline, chamfered at the face and the seam: `outline(inset)`
        draws it inset smaller."""
        t = self.half_t
        return loft(
            [
                outline(face_chamfer),
                Pos(0, 0, face_chamfer) * outline(0),
                Pos(0, 0, t - seam_chamfer) * outline(0),
                Pos(0, 0, t) * outline(seam_chamfer),
            ],
            ruled=True,
        )

    def bump_2d(self, inset: float) -> Sketch:
        """A vertex's bump at +x, chamfered by leaning in, as the edge under it
        does."""
        bump = Polygon(
            (-1, bump_w / 2),
            (0, bump_w / 2),
            (BUMP_H, bump_top / 2),
            (BUMP_H, -bump_top / 2),
            (0, -bump_w / 2),
            (-1, -bump_w / 2),
        )
        return Pos(D / 2 - inset) * opened(bump, bump_r)

    def blank(self) -> Shape:
        body = self.chamfered(self.outline)
        if self.shape != "knurled":
            return body
        # A groove between each two reeds. The faces' chamfers are deeper than
        # it, so it runs out before the face and leaves a rim.
        groove = Pos(D / 2) * Polygon(
            (1, groove_w / 2 + 1),
            (0, groove_w / 2),
            (-groove_d, groove_floor / 2),
            (-groove_d, -groove_floor / 2),
            (0, -groove_w / 2),
            (1, -groove_w / 2 - 1),
        )
        grooves = Sketch() + [
            Rot(0, 0, (i + 0.5) * 360 / knurls) * groove for i in range(knurls)
        ]
        body -= up(grooves, -1, self.half_t + 2)
        if not self.bumps:
            return body
        bump = self.chamfered(self.bump_2d)
        return body + [
            Rot(0, 0, i * 360 / self.bumps) * bump for i in range(self.bumps)
        ]

    def arrow_2d(self, i: int) -> Sketch:
        """Half i's arrow, or its line, as it is in its face."""
        line = self.marks[i] == "line"
        shaft_tip = -arrow_tail if line else arrow_tip - head_l + 1
        shaft = Polygon(
            (arrow_tail, -shaft_w / 2),
            (shaft_tip, -shaft_w / 2),
            (shaft_tip, shaft_w / 2),
            (arrow_tail, shaft_w / 2),
        )
        if line:
            return Rot(0, 0, self.angles[i]) * opened(shaft, arrow_r)
        head = Polygon(
            (arrow_tip, 0),
            (arrow_tip - head_l, head_w / 2),
            (arrow_tip - head_l, -head_w / 2),
        )
        return Rot(0, 0, self.angles[i]) * opened(shaft + head, arrow_r)

    def arrow(self, i: int) -> Part:
        """Half i's, inlaid in its face."""
        return extrude(self.arrow_2d(i), INLAY)

    def at_pin(self, sign: int) -> Location:
        """On the glue side, at the pin (1) or the hole (-1)."""
        return Rot(0, 0, sign * self.pin_a) * Pos(pin_r, 0, self.half_t)

    def half(self, i: int) -> Shape:
        """Half i, in its own frame, without what's inlaid in it."""
        pin = extrude(Circle(pin_d / 2), pin_h)
        pin = chamfer(pin.faces().sort_by(Axis.Z).last.edges(), pin_chamfer)
        hole_r = pin_d / 2 + pin_c
        depth = pin_h + hole_extra
        # Crush ribs, stopping short of the mouth's chamfer.
        ribbed = (
            Sketch()
            + Circle(hole_r)
            - [
                Rot(0, 0, k * 360 / ribs)
                * Pos(pin_d / 2 - rib_press + 0.5, 0)
                * Rectangle(1, rib_w)
                for k in range(ribs)
            ]
        )
        hole = (
            up(ribbed, -depth, depth - pin_chamfer)
            + up(Sketch() + Circle(hole_r), -pin_chamfer, 1)
            + Pos(0, 0, -pin_chamfer)
            * extrude(Circle(hole_r), pin_chamfer, (0, 0, 1), taper=-45)
        )
        body = self.blank() - self.at_pin(-1) * hole + self.at_pin(1) * pin
        if not self.marks[i]:
            return body
        # The arrow, cut through the face from under it.
        return body - up(self.arrow_2d(i), -1, 1 + INLAY)

    def pieces(self) -> list[Piece]:
        """Both halves and what's inlaid in them: printed face down, side by
        side, and glued, the second half turned over onto the first."""
        pitch = D + 2 * BUMP_H + 5
        at = (Location(), flipped(2 * self.half_t))
        filaments = dict(zip(HALF_COLORS, FILAMENTS))
        groups = SIDES if self.colors[0] == self.colors[1] else HALVES
        pieces = []
        for i, (color, mark) in enumerate(zip(self.colors, self.marks)):
            where = {"parent": groups[i], "at": at[i], "place": Pos(i * pitch)}
            pieces.append(
                Piece(
                    self.half(i),
                    f"half {i}",
                    color,
                    filaments[color],
                    half_settings(self.shape),
                    **where,
                )
            )
            if mark:
                inlaid = HALF_COLORS[1 - HALF_COLORS.index(color)]
                pieces.append(
                    Piece(
                        self.arrow(i),
                        f"{mark} {i}",
                        inlaid,
                        filaments[inlaid],
                        arrow_settings(self.angles[i]),
                        **where,
                    )
                )
        return pieces


def row(coins: Mapping[str, list[Piece]]) -> list[Piece]:
    """Coins side by side, each its pieces where they sit, named for it,
    in a group of each."""
    pitch = D + 2 * BUMP_H + 5
    return [
        replace(
            p,
            shape=Pos(k * pitch) * p.shape,
            name=f"{name} {p.name}",
            parent=f"{name}/{name} {p.parent}",
        )
        for k, (name, pieces) in enumerate(coins.items())
        for p in pieces
    ]
