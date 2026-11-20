"""An upright box for a deck of cards standing on end, with a lift-off lid held
on by magnets.

    from designs.card_box import SETTINGS, Art, CardBox

    crest = Art("crest", "yellow", Pos(0, 30) * crest_sketch)
    box = CardBox(sleeve=(66.5, 92.5), stack=40, front=[crest])
    project(
        __file__,
        objects={"panels": Object(box.panels, "Every panel, outside down")},
        views={"assembly": Object(box.assembly, "Closed")},
        orca=SETTINGS,
    )

x is across the cards, centered; y is front (0) to back; z is up. The seam is
level across the front and back walls and slopes up between them along the
sides.

The box is ten flat panels, glued, for faces off the bed all round and inlays
that print flat: the floor, the top, and a body and a lid piece of each wall.
Every panel prints with its outside face on the bed. They join in mitred
rabbets, whose seams fall on the box's edges, so no joint shows on a face. To
glue the body, or the lid: tape its panels up dry, outside, then run thin CA
along the inside corners.

The joint. A mitre runs through the outer `mitre` of the wall, so the seam
falls on the box's edge. Inside it, one panel ends square and sits in a rabbet
in the other: the front and back drop between the sides, and the floor and top
into all four walls. So every panel goes on from outside, along its own
normal; none is trapped, and squeezing the box closes every joint at once.
Printed outside down, every mating face is a wall or faces up: nothing
overhangs, so nothing droops and binds. Thin CA wicks through the rabbet and
stops at the glue break, a trough under the mitre's inner end, short of the
outside.

A panel's last layers, its inside face, flare a little past its edges. So the
inside edges that meet another piece are chamfered by `ease`: the end of a
panel that sits in a rabbet (by `relief`), the top of the rabbet's wall, which
is the box's inside corner and makes a V that holds a drop of CA on the joint,
and the seam's inside edges, keys and all, which would otherwise hold the lid
off. The rabbet's wall is what squares the joint: leave most of it.

Bar magnets stand on edge in the front and back walls, in pockets open to the
inside, each facing its partner edge to edge across the seam. A cover of
plastic stands between each magnet and the seam, so that magnets never touch
and the seam bears on plastic: a wall one line wide, as a panel prints,
stopping `ease` short of the wall's inside face, where the seam's chamfer would
leave it a feather. They're magnetized through their thickness, so glue one of
each pair in flipped, to attract. A trapezoid key on each wall's seam locates
the lid.

Art is inlaid flush in the front, the back and the top: each face's a list of
`Art`, layers of their own colors and pieces, a later one covering those
before it. Each is drawn in 2D as it reads from outside:
  front  x across, y up from the floor, 0 at the front's bottom center
  back   the same on the back, seen from behind
  top    x across, y to the back, 0 at the top's center
`size`, the box's outside, and `seam`, the seam's height at the front and at
the back, are there to fit it by: draw it for a box without art, and
`dataclasses.replace()` it in. It is trimmed to its panel: the front's and
the back's to the body's, to print with it, and the top's to the lid's.

Printing: SETTINGS, for the project, are the layers the joints fit at.
`panels` is every panel; with more colors than the printer has heads, `body`
and `lid` print apart, as objects of their own.

`seam_test` is the front wall across the seam, cut short, and `magnet_test` a
strip of magnet pockets: each at a few fits, to try before printing a box.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from functools import cached_property
from math import atan2, cos, degrees, hypot, radians, sin

from build123d import (
    Box,
    Circle,
    Compound,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    Rot,
    Shape,
    Sketch,
    Solid,
    Vector,
    Wire,
    chamfer,
    extrude,
)

from build.cad import Piece

# The joints fit as drawn at 0.08 mm layers over a 0.2 mm first one, as test
# coupons found; at 0.2 mm layers the mitres' steps stand proud and lever the
# joints out of square. Every thickness in the panels ends on one of those
# layers from the bed up (the 0.6 mm inlays, the 0.68 mm glue break, the
# 0.84 mm magnet skins, the 1 mm mitres, the 2.04 mm walls, the 3.4 mm front
# and back, and each less `ease`), so its face falls midway between Orca's
# slicing planes, at the layers' middles; the printer's own 0.25 mm first
# layer would leave the inlays' floor 0.01 mm from one. Arachne walls print
# the magnets' covers, one line wide, which classic walls leave out without a
# word. And each piece's lines (`solid_infill_direction`) turn with it, as
# plate packing may turn a panel a quarter.
SETTINGS = {
    "process": "0.08 High Quality",
    "layer_height": 0.08,
    "initial_layer_print_height": 0.2,
    "wall_generator": "arachne",
    "align_infill_direction_to_model": True,
}

# On the bed: between a wall's body piece and its lid piece, and between
# panels.
LID_GAP = 5
BED_GAP = 5

FACES = ("left", "right", "front", "back", "floor", "top")
WALLS = ("front", "back", "left", "right")
# Each face's axis, which is also its rank: along an edge, the panel of the
# higher rank ends square, in the other's rabbet.
AXIS = {"left": 0, "right": 0, "front": 1, "back": 1, "floor": 2, "top": 2}
FAR = {"right", "back", "top"}  # at the far end of its axis


def sign(face: str) -> int:
    """Which way its outside faces, along its axis."""
    return 1 if face in FAR else -1


def is_lid(panel: str) -> bool:
    return panel == "top" or panel.startswith("lid ")


def outward(face: str) -> Vector:
    v = [0.0, 0.0, 0.0]
    v[AXIS[face]] = sign(face)
    return Vector(*v)


Points = list[tuple[float, float]]


def offset_polygon(points: Points, d: float) -> Points:
    """A counter-clockwise polygon grown by d, or shrunk for d below 0, its
    corners mitred: each corner where its two sides, moved, meet. Point for
    point, so that a ruled loft between the two is planar faces."""
    out = []
    for i, p in enumerate(points):
        a, b = points[i - 1], points[(i + 1) % len(points)]
        (ax, ay), (ux, uy) = _moved(a, p, d)
        (bx, by), (vx, vy) = _moved(p, b, d)
        cross = ux * vy - uy * vx
        t = ((bx - ax) * vy - (by - ay) * vx) / cross
        out.append((ax + t * ux, ay + t * uy))
    return out


def _moved(a: tuple[float, float], b: tuple[float, float], d: float):
    """The side from a to b moved d to its right, outward: a point, and its
    direction."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = hypot(dx, dy)
    return (a[0] + d * dy / n, a[1] - d * dx / n), (dx, dy)


def sketch(shape: Shape) -> Sketch:
    """A 2D shape's faces, as a Sketch to extrude: build123d's operators type
    what they make as a Compound."""
    return Sketch(shape.faces())


def box(lo: Sequence[float], hi: Sequence[float]) -> Part:
    """Corner to corner."""
    size = [h - low for low, h in zip(lo, hi)]
    center = [(low + h) / 2 for low, h in zip(lo, hi)]
    return Pos(*center) * Box(size[0], size[1], size[2])


@dataclass(frozen=True)
class Art:
    """One layer of a face's inlay, drawn as it reads from outside, in the
    face's own frame (see the module's docstring)."""

    name: str  # its piece's
    color: str
    shape: Compound  # a Sketch, or what build123d's operators make of one
    # The pattern its face prints in, on the bed, or none for lines: its
    # panel's, turned as the art is, by `turn`, counter-clockwise as seen from
    # outside.
    pattern: str = ""
    turn: float = 0


@dataclass(frozen=True)
class Magnets:
    """Bar magnets in the seam, and the pockets they're glued into."""

    # Length along the wall, height, thickness.
    size: tuple[float, float, float] = (18.4, 9, 2.5)
    # Pocket clearance on the thickness, where the pocket is open to the
    # inside.
    clear: float = 0.12
    # Room for the magnet's height, between the cover and the pads. Loose: a
    # magnet that's tight there bows the cover out at the seam, and its
    # partner's pull seats it against the cover anyway.
    slack: float = 0.3
    # Gap for excess glue, past each end of a magnet and past its far edge
    # from the seam. Crush ribs and stop pads cross it to hold the magnet in
    # place.
    glue: float = 0.4
    # How far each end's crush ribs bite into the magnet's length.
    crush: float = 0.1
    # A crush rib's width at its root, and at its tip: flat, and wide enough
    # to print at its full height. A pointed rib came out about 0.1 mm short,
    # rounded off by the nozzle, and a 0.15 mm crush gripped nothing.
    rib_w: float = 1.2
    rib_tip: float = 0.4
    # Plastic outside a pocket; with the magnet, the front's and back's
    # thickness.
    skin: float = 0.84
    # Plastic between a magnet and its seam face.
    cover: float = 0.4
    # Either side of center, on the front and the back.
    x: float = 20

    @property
    def depth(self) -> float:
        """A pocket's, into the wall from its inside face."""
        return self.size[2] + self.clear / 2

    @property
    def reach(self) -> float:
        """From the seam face to the pads at a magnet's far edge."""
        return self.cover + self.size[1] + self.slack


@dataclass(frozen=True)
class CardBox:
    """A card box, as a value: its panels and views are its methods."""

    # A card in its sleeve, outside, at its largest: width, length.
    sleeve: tuple[float, float] = (66.5, 92.5)
    # What stands in the box, front to back: the deck, and whatever goes in
    # beside it.
    stack: float = 40
    # Room round that: across the cards, front to back, and above them, under
    # the lid. 2.5 across is what a bought deck box has.
    clear: tuple[float, float, float] = (2.5, 0.5, 0.5)
    # Goes before its pieces' names, to tell boxes apart.
    name: str = ""
    color: str = "forestgreen"
    lid_color: str = ""  # or the body's
    front: Sequence[Art] = ()
    back: Sequence[Art] = ()
    top: Sequence[Art] = ()
    # The side walls, the floor and the top.
    wall: float = 2.04
    # How far the seam drops from the back to the front, and the lid's height
    # at the back, its top included.
    seam_drop: float = 25
    lid_back_h: float = 14
    # On the outside edges, which also blunts the mitres' knife edges.
    chamfer: float = 0.6
    # The inside edges that meet another piece: the seam's, and the top of a
    # rabbet's wall.
    ease: float = 0.24
    # The joint: the mitre's depth below the outside faces, and so the
    # thickness of the tongue beside a rabbet; the glue break's depth; and the
    # chamfer on the inside end of a panel that sits in a rabbet.
    mitre: float = 1
    glue_break: float = 0.32
    relief: float = 0.24
    art_depth: float = 0.6
    magnets: Magnets = field(default_factory=Magnets)
    # The seam's keys: width at the base, height, how far each flank leans in,
    # and the clearance round a key in the lid.
    key_w: float = 14
    key_h: float = 2.5
    key_lean: float = 1.25
    key_c: float = 0.05

    def __post_init__(self) -> None:
        m = self.magnets
        z_top = self.size[2] - self.wall
        assert z_top - self.seam[1] >= m.reach + m.glue + 1, (
            "lid too short at the back for its magnets"
        )
        assert m.x - m.size[0] / 2 - m.glue - 1 >= self.key_w / 2 + self.key_c, (
            "magnets crowd the key"
        )
        assert m.x + m.size[0] / 2 + m.glue + 1 <= self.cavity[0] / 2, (
            "magnets run into the corners"
        )
        assert self.ease <= 0.5, "ease reaches under the keys"
        assert self._key()[0][0] < self.cavity[1] / 2, (
            "the sides' keys run off their seam's slope"
        )

    # Its measures

    @property
    def thick(self) -> tuple[float, float, float]:
        """The panels' thickness, by axis: the front and back hold the
        magnets."""
        return (self.wall, self.magnets.depth + self.magnets.skin, self.wall)

    @property
    def cavity(self) -> tuple[float, float, float]:
        return (
            self.sleeve[0] + self.clear[0],
            self.stack + self.clear[1],
            self.sleeve[1] + self.clear[2],
        )

    @property
    def size(self) -> tuple[float, float, float]:
        """The box, outside."""
        (cx, cy, cz), (tx, ty, tz) = self.cavity, self.thick
        return (cx + 2 * tx, cy + 2 * ty, cz + 2 * tz)

    @property
    def seam(self) -> tuple[float, float]:
        """The seam's height, at the front and at the back."""
        back = self.size[2] - self.lid_back_h
        return (back - self.seam_drop, back)

    def _lo(self, axis: int) -> float:
        return -self.size[0] / 2 if axis == 0 else 0

    def _hi(self, axis: int) -> float:
        return self.size[0] / 2 if axis == 0 else self.size[axis]

    def _out(self, face: str) -> float:
        """Where its outside face is, along its axis."""
        a = AXIS[face]
        return self._hi(a) if face in FAR else self._lo(a)

    def _in(self, face: str) -> float:
        """Where its inside face is."""
        return self._out(face) - sign(face) * self.thick[AXIS[face]]

    # The panels, as regions of the box

    @cached_property
    def _outer(self) -> Compound:
        bx, by, bz = self.size
        return chamfer(box((-bx / 2, 0, 0), (bx / 2, by, bz)).edges(), self.chamfer)

    def _edge(self, a: str, b: str, points: Points) -> Part:
        """A cut along the edge panels a and b share: points in (depth below
        a's outside face, depth below b's), extruded the edge's length."""
        ea, eb = -outward(a), -outward(b)
        origin = [0.0, self.size[1] / 2, self.size[2] / 2]
        origin[AXIS[a]] = self._out(a)
        origin[AXIS[b]] = self._out(b)
        plane = Plane(Vector(*origin), x_dir=ea, z_dir=ea.cross(eb))
        return extrude(plane * Polygon(*points, align=None), max(self.size), both=True)

    def _region(self, face: str) -> Compound:
        """All of the box that's this panel's: its face's slab, less what
        each joint gives its neighbor."""
        a, t = AXIS[face], self.thick[AXIS[face]]
        lo = [self._lo(k) for k in range(3)]
        hi = [self._hi(k) for k in range(3)]
        if face in FAR:
            lo[a] = hi[a] - t
        else:
            hi[a] = lo[a] + t
        big = 2 * max(self.size)
        m, e, brk = self.mitre, self.ease, self.glue_break
        cuts = []
        for other in FACES:
            b = AXIS[other]
            if b == a:
                continue
            if a > b:
                # This one gives up what's outside the mitre, and then past
                # its square end, its inside corner relieved.
                r = self.relief
                points = [(-1, -1), (m, m), (t - r, m), (t, m + r), (big, m + r)]
                cuts.append(self._edge(face, other, [*points, (big, -1)]))
            else:
                # This one gives up what's outside the mitre, the glue break,
                # the rabbet, as wide as the other is thick, and the top of
                # its wall.
                u = self.thick[b]
                points = [(-1, -1), (m - brk, m - brk), (m, m - brk), (m, m)]
                points += [(u, m), (u, t - e), (u + e, t), (u + e, big), (-1, big)]
                cuts.append(self._edge(other, face, points))
        return box(lo, hi) - cuts

    @cached_property
    def _blanks(self) -> dict[str, Compound]:
        """Each panel's region of the box, with its chamfers."""
        return {face: self._region(face) & self._outer for face in FACES}

    # The seam

    def _key(self, g: float = 0) -> Points:
        """A key's outline, grown by g: (along the seam from its middle, up
        from the seam), from its right foot round to its left."""
        w, h, lean = self.key_w / 2, self.key_h, self.key_lean
        flank = hypot(lean, h)
        foot = w + g * flank / h
        top = w - lean + g * (flank - lean) / h
        return [(foot, 0), (top, h + g), (-top, h + g), (-foot, 0)]

    def _below_seam(self, wall: str, g: float) -> Points:
        """What the body keeps of a wall, in the wall's own coordinates:
        (across it in the box's x, or y for a side, up), its keys grown by g;
        counter-clockwise."""
        big = 2 * max(self.size)
        front, back = self.seam
        if wall in ("front", "back"):
            z = front if wall == "front" else back
            key = [(s, z + n) for s, n in self._key(g)]
            return [(-big, -big), (big, -big), (big, z), *key, (-big, z)]
        t = self.thick[1]
        slope = self.seam_drop / self.cavity[1]
        mid = self.size[1] / 2
        key = [(mid + s, front + slope * (mid + s - t) + n) for s, n in self._key(g)]
        corners = [(-big, -big), (big, -big), (big, back), (self.size[1] - t, back)]
        return [*corners, *key, (t, front), (-big, front)]

    def _across(self, wall: str, sections: list[tuple[Points, float]]) -> Solid:
        """A ruled loft through outlines in a wall's coordinates, each where it
        is along the wall's axis."""

        def at(u: float, z: float, n: float) -> Vector:
            return Vector(u, n, z) if AXIS[wall] == 1 else Vector(n, u, z)

        wires = [
            Wire.make_polygon([at(u, z, n) for u, z in points], close=True)
            for points, n in sections
        ]
        return Solid.make_loft(wires, ruled=True)

    def _split(self, wall: str, grow: float, g: float) -> Solid:
        """Below the seam, keys grown by g, through the wall, from past its
        outside to `ease` short of its inside, and then grown by `grow` per
        unit further in, past the inside face: 45° either way, chamfering the
        seam's inside edges."""
        inward = -sign(wall)
        out, inside, over = self._out(wall), self._in(wall), 0.5
        outline = self._below_seam(wall, g)
        return self._across(
            wall,
            [
                (outline, out - inward),
                (outline, inside - inward * self.ease),
                (
                    offset_polygon(outline, grow * (self.ease + over)),
                    inside + inward * over,
                ),
            ],
        )

    # Magnets

    def _magnet_frames(self, wall: str, lid: bool) -> list[Location]:
        """Where a wall's magnets are: x along the wall, y into it from its
        inside face, z away from the seam, which is at 0."""
        into = outward(wall)
        away = Vector(0, 0, 1 if lid else -1)
        z = self.seam[0 if wall == "front" else 1]
        return [
            Location(
                Plane((sx * self.magnets.x, self._in(wall), z), into.cross(away), away)
            )
            for sx in (-1, 1)
        ]

    @cached_property
    def _pocket(self) -> Shape:
        """A magnet's pocket, in its frame: oversize by `glue` at both ends
        and at the far edge, with two crush ribs on each end, flat-tipped,
        running the way the magnet drops in, and two pads at the far edge for
        it to seat against. The cover is the wall left between it and the
        seam, which stops `ease` short of the inside face, flat."""
        m = self.magnets
        half = m.size[0] / 2 + m.glue
        far = m.reach + m.glue
        ribs = []
        for zc in (m.cover + f * m.size[1] for f in (0.25, 0.75)):
            for sx in (-1, 1):
                tip = half - m.glue - m.crush
                rib = [
                    (half + 1, zc - m.rib_w / 2),
                    (half + 1, zc + m.rib_w / 2),
                    (half, zc + m.rib_w / 2),
                    (tip, zc + m.rib_tip / 2),
                    (tip, zc - m.rib_tip / 2),
                    (half, zc - m.rib_w / 2),
                ]
                ribs.append(Polygon(*[(sx * x, z) for x, z in rib], align=None))
        pads = [
            Pos(sx * m.size[0] / 4, far) * Rectangle(2, 2 * m.glue) for sx in (-1, 1)
        ]
        room = Pos(0, (m.cover + far) / 2) * Rectangle(2 * half, far - m.cover)
        pocket = Sketch() + room - ribs - pads
        notch = Pos(0, (m.cover - 1) / 2) * Rectangle(2 * half, m.cover + 1)
        over = 0.5

        def into_wall(face: Shape, depth: float) -> Part:
            drawn = sketch(Plane.XZ * face)
            return Pos(0, -over, 0) * extrude(drawn, depth + over, (0, 1, 0))

        return into_wall(pocket, m.depth) + into_wall(notch, self.ease)

    def _magnet(self) -> Part:
        """A magnet, in its pocket's frame, against its cover."""
        x, h, t = self.magnets.size
        c = self.magnets.cover
        return box((-x / 2, 0, c), (x / 2, t, c + h))

    # The panels

    @cached_property
    def _shells(self) -> dict[str, Compound]:
        """Each panel as it is in the box, but for its art: the walls' body
        pieces by their faces' names, their lid pieces as "lid front" and so
        on, then the floor and the top."""
        shells: dict[str, Compound] = {}
        for lid in (False, True):
            for wall in WALLS:
                blank = self._blanks[wall]
                if lid:
                    piece = blank - self._split(wall, 1, self.key_c)
                else:
                    piece = blank & self._split(wall, -1, 0)
                if wall in ("front", "back"):
                    piece -= [f * self._pocket for f in self._magnet_frames(wall, lid)]
                shells[f"lid {wall}" if lid else wall] = piece
        shells["floor"] = self._blanks["floor"]
        shells["top"] = self._blanks["top"]
        return shells

    def _plane(self, face: str) -> Plane:
        """A face's art's frame, as it reads from outside."""
        _, by, bz = self.size
        if face == "front":
            return Plane.XZ
        if face == "back":
            return Plane((0, by, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
        return Plane((0, by / 2, bz), x_dir=(1, 0, 0), z_dir=(0, 0, 1))

    def _layers(self, face: str) -> list[Art]:
        return list({"front": self.front, "back": self.back, "top": self.top}[face])

    def _sunk(self, face: str, shape: Shape) -> Part:
        """Drawn into its face, `art_depth` deep, and out past it."""
        plane, over = self._plane(face), 0.5
        drawn = Pos(plane.z_dir * over) * (plane * shape)
        return extrude(sketch(drawn), self.art_depth + over, -plane.z_dir)

    @cached_property
    def _inlays(self) -> dict[str, list[Compound]]:
        """Each face's art, a solid a layer, less the layers over it, trimmed
        to its panel, its chamfers, and the front's and back's to the body."""
        inlays = {}
        for face in ("front", "back", "top"):
            layers = self._layers(face)
            inlays[face] = [
                self._sunk(
                    face, Sketch() + a.shape - [b.shape for b in layers[i + 1 :]]
                )
                & self._shells[face]
                for i, a in enumerate(layers)
            ]
        return inlays

    @cached_property
    def _panels(self) -> dict[str, Compound]:
        """The panels in the box, their art cut from them."""
        panels = dict(self._shells)
        for face in ("front", "back", "top"):
            if layers := self._layers(face):
                cut = self._sunk(face, Sketch() + [a.shape for a in layers])
                panels[face] = panels[face] - cut
        return panels

    # Pieces

    def _named(self, name: str) -> str:
        return f"{self.name} {name}" if self.name else name

    def _color(self, panel: str) -> str:
        return (self.lid_color or self.color) if is_lid(panel) else self.color

    @staticmethod
    def _face(panel: str) -> str:
        return panel.removeprefix("lid ")

    def _art_pieces(
        self, faces: Sequence[str], at: Callable[[str], Location]
    ) -> list[Piece]:
        """The art of these faces, each layer a piece, moved by at(face)."""
        return [
            Piece(
                at(face) * solid,
                self._named(a.name),
                a.color,
                settings=self._art_settings(face, a),
            )
            for face in faces
            for a, solid in zip(self._layers(face), self._inlays[face])
        ]

    def assembly(self, lift: float = 0, explode: float = 0) -> list[Piece]:
        """The box put together, closed: the lid lifted by `lift`, and the
        panels pulled `explode` apart along their faces, art and magnets with
        them."""

        def moved(face: str, lid: bool) -> Location:
            return Pos(0, 0, lift if lid else 0) * Pos(outward(face) * explode)

        pieces = [
            Piece(
                moved(self._face(p), is_lid(p)) * part,
                self._named(p),
                self._color(p),
            )
            for p, part in self._panels.items()
        ]
        magnets = Part() + [
            moved(wall, lid) * f * self._magnet()
            for wall in ("front", "back")
            for lid in (False, True)
            for f in self._magnet_frames(wall, lid)
        ]
        pieces.append(Piece(magnets, self._named("magnets"), "silver"))
        return pieces + self._art_pieces(
            ("front", "back", "top"), lambda face: moved(face, face == "top")
        )

    # Printing

    def _flat(self, face: str, lid: bool = False) -> Location:
        """On the bed, outside face down. The front and back lie side by side,
        the left and right behind them, the floor and top behind those. Each
        wall's lid piece lies beyond its body piece, the seam between them
        opened by LID_GAP."""
        bx, by, bz = self.size
        gap, h = BED_GAP, bz + LID_GAP
        y1 = h + gap
        y2 = y1 + by + gap
        x1 = bx + gap
        at = {
            "front": Pos(0, h, 0) * Rot(90, 0, 0),
            "back": Pos(x1, 0, by) * Rot(-90, 0, 0),
            "left": Pos(h, y1, 0) * Rot(0, -90, 0),
            "right": Pos(h + gap, y1, bx) * Rot(0, 90, 0),
            "floor": Pos(0, y2, 0),
            "top": Pos(x1, y2 + by, bz) * Rot(180, 0, 0),
        }[face]
        return at * Pos(bx / 2, 0, LID_GAP if lid else 0)

    def _lines(self, face: str, turn: float = 0) -> dict[str, object]:
        """Monotonic lines on the bed: up the box on the front and back, across
        it on the top, and along the seam on the sides, turned by `turn`
        counter-clockwise as seen from outside."""
        if face in ("front", "back"):
            v = Vector(0, 0, 1)
        elif face == "top":
            v = Vector(1, 0, 0)
        else:
            v = Vector(0, 1, self.seam_drop / self.cavity[1]).normalized()
        n = outward(face)
        a = radians(turn)
        v = v * cos(a) + n.cross(v) * sin(a)
        on_bed = self._flat(face) * Pos(v)
        d = on_bed.position - self._flat(face).position
        angle = round(degrees(atan2(d.Y, d.X)) % 180, 4)
        return {
            "bottom_surface_pattern": "monotonic",
            "solid_infill_direction": int(angle) if angle.is_integer() else angle,
        }

    def _settings(self, panel: str) -> dict[str, object]:
        """Concentric on the floor, which no one sees; the rest in lines."""
        if panel == "floor":
            return {"bottom_surface_pattern": "concentric"}
        return self._lines(self._face(panel))

    def _art_settings(self, face: str, art: Art) -> dict[str, object]:
        if art.pattern:
            return {"bottom_surface_pattern": art.pattern}
        return self._lines(face, art.turn)

    def _laid(self, lid: bool) -> list[Piece]:
        """The body's panels, or the lid's, on the bed, outside down, with
        their art, where they lie among all of them."""
        pieces = []
        for p, part in self._panels.items():
            if is_lid(p) != lid:
                continue
            face = self._face(p)
            at = self._flat(face, lid and face != "top")
            pieces.append(
                Piece(
                    at * part,
                    self._named(p),
                    self._color(p),
                    settings=self._settings(p),
                )
            )
        faces = ("top",) if lid else ("front", "back")
        return pieces + self._art_pieces(faces, self._flat)

    def body(self) -> list[Piece]:
        """The body's panels on the bed, with the front's and back's art."""
        return self._laid(lid=False)

    def lid(self) -> list[Piece]:
        """The lid's panels on the bed, with the top's art."""
        return self._laid(lid=True)

    def panels(self) -> list[Piece]:
        """Every panel on the bed, outside down, with its art."""
        return self.body() + self.lid()

    # Tests

    def seam_test(
        self,
        fits: Sequence[tuple[float, float]] = ((0.05, 0.05), (0.05, 0.1), (0.05, 0.2)),
        reach: tuple[float, float] = (-9, 31),
        height: float = 14,
    ) -> list[Piece]:
        """The front wall across the seam, cut short, body and lid: a coupon
        of each at each of `fits`, (key clearance, magnet crush), notches in
        its end away from the magnet counting its place. A coupon reaches
        `reach` along the wall, and `height` from the seam. Each lies outside
        down with its seam face to the front of the bed, so that Orca's seams,
        at the back, keep off it."""
        z, t = self.seam[0], self.thick[1]
        stub = self.key_h + 1
        width = reach[1] - reach[0]
        coupons = []
        for i, (key_c, crush) in enumerate(fits):
            fit = replace(self, key_c=key_c, magnets=replace(self.magnets, crush=crush))
            for lid in (False, True):
                side = 1 if lid else -1
                span = sorted((z - side * stub, z + side * height))
                notches = Sketch() + [
                    Pos(reach[0], z + side * (4 + 3.5 * n)) * Circle(1)
                    for n in range(i + 1)
                ]
                coupon = fit._shells["lid front" if lid else "front"] & box(
                    (reach[0], -1, span[0]), (reach[1], t + 1, span[1])
                )
                coupon -= extrude(sketch(Plane.XZ * notches), t + 1, both=True)
                # The body's seam face is its top, so stood down toward the
                # front; the lid's is its bottom, so turned about as well.
                if lid:
                    at = Pos(reach[1], 2 * stub + height + BED_GAP - z, 0) * Rot(
                        0, 0, 180
                    )
                else:
                    at = Pos(-reach[0], z + stub, 0)
                coupons.append(
                    Pos(i * (width + BED_GAP), 0, 0) * at * Rot(90, 0, 0) * coupon
                )
        return [Piece(Part() + coupons, self._named("seam test"), self.color)]

    def magnet_test(
        self, crushes: Sequence[float] = (0.05, 0.1, 0.2), rim: float = 3
    ) -> list[Piece]:
        """A strip of the front wall's thickness with a row of magnet pockets,
        open to the inside as in the box, at each of `crushes`, notches in its
        edge away from the seam counting each one's place. It lies outside
        down, its seam face to the front of the bed."""
        m, t = self.magnets, self.thick[1]
        pitch = m.size[0] + 2 * m.glue + rim
        depth = m.reach + m.glue + rim
        n = len(crushes)
        strip = box(
            (-pitch / 2 - rim / 2, 0, 0), ((n - 0.5) * pitch + rim / 2, t, depth)
        )
        for i, crush in enumerate(crushes):
            fit = replace(self, magnets=replace(m, crush=crush))
            notches = Sketch() + [
                Pos((k - i / 2) * 3.5, depth) * Circle(1) for k in range(i + 1)
            ]
            strip -= Pos(i * pitch, 0, 0) * (
                fit._pocket + extrude(sketch(Plane.XZ * notches), t + 1, both=True)
            )
        # In the pocket's frame, its inside face up.
        at = Pos(rim + m.size[0] / 2 + m.glue, 0, t) * Rot(-90, 0, 0)
        return [Piece(at * strip, self._named("magnet test"), self.color)]
