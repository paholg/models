"""An upright box for a deck of cards standing on end, with a lift-off lid held
on by magnets.

    from designs.card_box import Art, CardBox, to_print

    crest = Art("crest", "yellow", Pos(0, 30) * crest_sketch)
    box = CardBox(sleeve=(66.5, 92.5), stack=40, front=[crest])
    project(
        __file__,
        objects={"panels": to_print(box.panels, "Every panel, outside down")},
        views={
            "assembly": View(lambda o: box.closed(o["panels"]), "Closed", ["panels"])
        },
    )

x is across the cards, centered; y is front (0) to back; z is up. The seam is
level across the front and back and slopes up between them along the sides.

Ten flat panels, glued: the floor, the top, and a body and a lid piece of each
wall. Each prints outside down, so every face is off the bed and inlays print
flat. To glue the body, or the lid: tape its panels up dry, outside, then run
thin CA along the inside corners.

The joint is a mitred rabbet. The mitre runs through the outer `mitre` of the
wall, so the seam falls on the box's edge. Inside it, one panel ends square in
the other's rabbet: the front and back between the sides, the floor and top in
all four walls. Every panel goes on from outside, so none is trapped, and
nothing overhangs as printed. CA wicks through the rabbet and stops at the
glue break, a trough under the mitre's inner end.

A panel's last layers flare a little past its edges, so the inside edges that
meet another piece are chamfered by `ease`: the top of a rabbet's wall, the
seam's edges, and (by `relief`) the end of a panel in a rabbet. The rabbet's
wall squares the joint: leave most of it.

Bar magnets stand on edge in pockets in the front and back walls, each facing
its partner across the seam, behind a cover of plastic one line wide, so the
seam bears on plastic. They're magnetized through their thickness: glue one of
each pair in flipped. A trapezoid key on each wall's seam locates the lid.

Art is inlaid flush in the front, back and top: each a list of `Art`, later
layers covering earlier ones. Each is drawn in 2D as it reads from outside:
  front  x across, y up, 0 at the bottom center
  back   the same, seen from behind
  top    x across, y to the back, 0 at the center
`size` and `seam` are there to fit it by: draw it for a box without art, and
`dataclasses.replace()` it in. It's trimmed to its panel: on the front and
back, the body's piece.

`to_print` makes an object of any of these, with the layers the joints fit
at, and what's to set by hand. `panels` is every panel, each an
object of its own in Orca, with its art, to print one at a time; with more
colors than the printer has heads, print `body` and `lid` apart.

`seam_test` and `magnet_test` are coupons of the seam and the magnet pockets
at a few fits, to try before printing a box: test/card_box/fits.py prints them.
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

from build.audit import any_sharp
from build.cad import Object, Piece

SETTINGS = {
    # The joints fit at 0.08 mm layers over a 0.2 mm first one, as test coupons
    # found; at 0.2 mm the mitres' steps stand proud and lever the joints out
    # of square. Every thickness in the panels ends on one of those layers, so
    # its face falls midway between Orca's slicing planes.
    "process": "0.08 High Quality",
    "layer_height": 0.08,
    "initial_layer_print_height": 0.2,
    # Prints the magnets' covers as one line; classic walls silently leave
    # them out.
    "wall_generator": "arachne",
    # The wall surfaces are set up to match the panels.
    "align_infill_direction_to_model": True,
    # A guess at why the panels lift off the bed: the preset fills the first
    # layer at 105 mm/s, and Snapmaker suggests no more than 50. Untested.
    "initial_layer_infill_speed": 30,
    # And the preset goes straight to full speed on the second layer, 0.28 mm
    # up: ease into it instead. Also untested.
    "slow_down_layers": 5,
}

# What SETTINGS can't say, being the filaments' settings.
# Both fans come on in full on the second layer, 0.28 mm up, which may be what
# lifts the panels' corners. Untested.
NOTES = """
    Set each filament's cooling by hand:
      No cooling for the first: 6 layers
      Full fan speed at layer: 15
      Auxiliary part cooling fan: 0%
"""


def to_print(draw: Callable[[], list[Piece]], description: str) -> Object:
    """Something of a box's as an object to print, with how these print."""
    # Sharp on purpose: the seam, which closes flush outside; the magnets'
    # pockets, which they fill; and the mitres' ends at the box's corners. So
    # only slivers are looked for, as art's cuts may leave.
    return Object(
        draw, description, settings=SETTINGS, notes=NOTES, skip_audit=[any_sharp]
    )


# On the bed: between a wall's body and lid pieces, and between panels.
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
    """A counter-clockwise polygon grown by d, its corners mitred. Point for
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
    """The side from a to b moved d outward: a point, and its direction."""
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
    """One layer of a face's inlay, in the face's frame (see the module's
    docstring)."""

    name: str  # its piece's
    color: str
    shape: Compound  # a Sketch, or what build123d's operators make of one
    # Its bottom surface pattern, or none for its panel's lines, turned by
    # `turn`, counter-clockwise from outside.
    pattern: str = ""
    turn: float = 0


@dataclass(frozen=True)
class Magnets:
    """Bar magnets in the seam, and the pockets they're glued into."""

    # Length, height, thickness.
    size: tuple[float, float, float] = (18.4, 9, 2.5)
    # Pocket clearance on the thickness.
    clearance: float = 0.12
    # Room on the magnet's height. Loose: a tight magnet bows the cover out
    # at the seam, and its partner's pull seats it anyway.
    slack: float = 0.3
    # Gap for excess glue past a magnet's ends and far edge, crossed by crush
    # ribs and stop pads.
    glue_gap: float = 0.4
    # How far each end's crush ribs bite.
    crush: float = 0.1
    # A crush rib's width at its root and at its flat tip. A pointed rib
    # printed about 0.1 mm short, and a 0.15 mm crush gripped nothing.
    rib_width: float = 1.2
    rib_tip_width: float = 0.4
    # Plastic outside a pocket.
    skin: float = 0.84
    # Plastic between a magnet and the seam.
    cover: float = 0.4
    # Either side of center.
    offset: float = 20

    @property
    def depth(self) -> float:
        """A pocket's, into the wall."""
        return self.size[2] + self.clearance / 2

    @property
    def reach(self) -> float:
        """From the seam face to the pads at a magnet's far edge."""
        return self.cover + self.size[1] + self.slack


@dataclass(frozen=True)
class CardBox:
    """A card box, as a value: its panels are its methods, and closed()
    arranges them."""

    # A sleeved card at its largest: width, length.
    sleeve: tuple[float, float] = (66.5, 92.5)
    # The deck's thickness, with whatever goes in beside it.
    stack: float = 40
    # Margins around the deck: width, depth, height.
    margin: tuple[float, float, float] = (2.0, 0.0, 2.0)
    # Prefixes its pieces' names.
    name: str = ""
    color: str = "forestgreen"
    lid_color: str = ""  # or the body's
    front: Sequence[Art] = ()
    back: Sequence[Art] = ()
    top: Sequence[Art] = ()
    # The sides, floor and top.
    wall_thickness: float = 2.04
    # The seam's drop from back to front, and the lid's outside height at the
    # back.
    seam_drop: float = 25
    lid_back_height: float = 14
    # On the outside edges; also blunts the mitres' knife edges.
    outer_chamfer: float = 0.6
    # On the inside edges that meet another piece.
    ease: float = 0.24
    # The joint: the mitre's depth, the glue break's, and the chamfer on the
    # end of a panel in a rabbet.
    mitre: float = 1
    glue_break: float = 0.32
    relief: float = 0.24
    art_depth: float = 0.6
    magnets: Magnets = field(default_factory=Magnets)
    # The seam's keys: base width, height, each flank's lean, and clearance
    # in the lid.
    key_width: float = 14
    key_height: float = 2.5
    key_lean: float = 1.25
    key_clearance: float = 0.05

    def __post_init__(self) -> None:
        m = self.magnets
        z_top = self.size[2] - self.wall_thickness
        assert z_top - self.seam[1] >= m.reach + m.glue_gap + 1, (
            "lid too short at the back for its magnets"
        )
        assert (
            m.offset - m.size[0] / 2 - m.glue_gap - 1
            >= self.key_width / 2 + self.key_clearance
        ), "magnets crowd the key"
        assert m.offset + m.size[0] / 2 + m.glue_gap + 1 <= self.cavity[0] / 2, (
            "magnets run into the corners"
        )
        assert self.ease <= 0.5, "ease reaches under the keys"
        assert self._key()[0][0] < self.cavity[1] / 2, (
            "the sides' keys run off their seam's slope"
        )

    # Its measures

    @property
    def thickness(self) -> tuple[float, float, float]:
        """The panels' thickness, by axis: the front and back hold the
        magnets."""
        return (
            self.wall_thickness,
            self.magnets.depth + self.magnets.skin,
            self.wall_thickness,
        )

    @property
    def cavity(self) -> tuple[float, float, float]:
        return (
            self.sleeve[0] + self.margin[0],
            self.stack + self.margin[1],
            self.sleeve[1] + self.margin[2],
        )

    @property
    def size(self) -> tuple[float, float, float]:
        """The box, outside."""
        (cx, cy, cz), (tx, ty, tz) = self.cavity, self.thickness
        return (cx + 2 * tx, cy + 2 * ty, cz + 2 * tz)

    @property
    def seam(self) -> tuple[float, float]:
        """The seam's height, at the front and at the back."""
        back = self.size[2] - self.lid_back_height
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
        return self._out(face) - sign(face) * self.thickness[AXIS[face]]

    # The panels, as regions of the box

    @cached_property
    def _outer(self) -> Compound:
        bx, by, bz = self.size
        return chamfer(
            box((-bx / 2, 0, 0), (bx / 2, by, bz)).edges(), self.outer_chamfer
        )

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
        axis = AXIS[face]
        thick = self.thickness[axis]
        lo = [self._lo(k) for k in range(3)]
        hi = [self._hi(k) for k in range(3)]
        if face in FAR:
            lo[axis] = hi[axis] - thick
        else:
            hi[axis] = lo[axis] + thick
        big = 2 * max(self.size)
        mitre, ease, relief = self.mitre, self.ease, self.relief
        cuts = []
        for other in FACES:
            other_axis = AXIS[other]
            if other_axis == axis:
                continue
            if axis > other_axis:
                # This one ends square, its inside corner relieved.
                points = [
                    (-1, -1),
                    (mitre, mitre),
                    (thick - relief, mitre),
                    (thick, mitre + relief),
                    (big, mitre + relief),
                    (big, -1),
                ]
                cuts.append(self._edge(face, other, points))
            else:
                # This one has the glue break and the rabbet, its wall's top
                # eased.
                rabbet = self.thickness[other_axis]
                trough = mitre - self.glue_break
                points = [
                    (-1, -1),
                    (trough, trough),
                    (mitre, trough),
                    (mitre, mitre),
                    (rabbet, mitre),
                    (rabbet, thick - ease),
                    (rabbet + ease, thick),
                    (rabbet + ease, big),
                    (-1, big),
                ]
                cuts.append(self._edge(other, face, points))
        return box(lo, hi) - cuts

    @cached_property
    def _blanks(self) -> dict[str, Compound]:
        """Each panel's region of the box, with its chamfers."""
        return {face: self._region(face) & self._outer for face in FACES}

    # The seam

    def _key(self, clearance: float = 0) -> Points:
        """A key's outline, grown by `clearance`: (along the seam from its
        middle, up from the seam), from its right foot round to its left."""
        half, height, lean = self.key_width / 2, self.key_height, self.key_lean
        flank = hypot(lean, height)
        foot = half + clearance * flank / height
        top = half - lean + clearance * (flank - lean) / height
        peak = height + clearance
        return [(foot, 0), (top, peak), (-top, peak), (-foot, 0)]

    def _below_seam(self, wall: str, clearance: float) -> Points:
        """What the body keeps of a wall, in (along the wall, up), its keys
        grown by `clearance`; counter-clockwise."""
        big = 2 * max(self.size)
        front, back = self.seam
        key = self._key(clearance)
        if wall in ("front", "back"):
            z = front if wall == "front" else back
            return [
                (-big, -big),
                (big, -big),
                (big, z),
                *[(along, z + up) for along, up in key],
                (-big, z),
            ]
        thick = self.thickness[1]
        slope = self.seam_drop / self.cavity[1]
        mid = self.size[1] / 2
        return [
            (-big, -big),
            (big, -big),
            (big, back),
            (self.size[1] - thick, back),
            *[
                (mid + along, front + slope * (mid + along - thick) + up)
                for along, up in key
            ],
            (thick, front),
            (-big, front),
        ]

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

    def _split(self, wall: str, flare: float, clearance: float) -> Solid:
        """Below the seam, keys grown by `clearance`, through the wall. From
        `ease` short of the inside face it grows by `flare` per unit inward,
        chamfering the seam's inside edges."""
        inward = -sign(wall)
        out, inside, over = self._out(wall), self._in(wall), 0.5
        outline = self._below_seam(wall, clearance)
        return self._across(
            wall,
            [
                (outline, out - inward),
                (outline, inside - inward * self.ease),
                (
                    offset_polygon(outline, flare * (self.ease + over)),
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
                Plane(
                    (sx * self.magnets.offset, self._in(wall), z),
                    into.cross(away),
                    away,
                )
            )
            for sx in (-1, 1)
        ]

    @cached_property
    def _pocket(self) -> Shape:
        """A magnet's pocket, in its frame: oversize by `glue_gap` at both ends
        and the far edge, with two crush ribs on each end and two pads at the
        far edge. The cover is the wall left between it and the seam, stopping
        `ease` short of the inside face, where the seam's chamfer would leave
        it a feather."""
        m = self.magnets
        half = m.size[0] / 2 + m.glue_gap
        far = m.reach + m.glue_gap
        ribs = []
        for zc in (m.cover + f * m.size[1] for f in (0.25, 0.75)):
            for sx in (-1, 1):
                tip = half - m.glue_gap - m.crush
                rib = [
                    (half + 1, zc - m.rib_width / 2),
                    (half + 1, zc + m.rib_width / 2),
                    (half, zc + m.rib_width / 2),
                    (tip, zc + m.rib_tip_width / 2),
                    (tip, zc - m.rib_tip_width / 2),
                    (half, zc - m.rib_width / 2),
                ]
                ribs.append(Polygon(*[(sx * x, z) for x, z in rib], align=None))
        pads = [
            Pos(sx * m.size[0] / 4, far) * Rectangle(2, 2 * m.glue_gap)
            for sx in (-1, 1)
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
        pieces by face, their lid pieces as "lid front" and so on."""
        shells: dict[str, Compound] = {}
        for lid in (False, True):
            for wall in WALLS:
                blank = self._blanks[wall]
                if lid:
                    piece = blank - self._split(wall, 1, self.key_clearance)
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
        to its panel."""
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

    def _parent(self, panel: str) -> str:
        """A panel's group in FreeCAD: the lid or the body, and in that, its
        own, if it has art or magnets."""
        group = self._named("lid" if is_lid(panel) else "body")
        face = self._face(panel)
        if face in ("front", "back") or (face == "top" and self.top):
            group += f"/{self._named(panel)}"
        return group

    def _color(self, panel: str) -> str:
        return (self.lid_color or self.color) if is_lid(panel) else self.color

    @staticmethod
    def _face(panel: str) -> str:
        return panel.removeprefix("lid ")

    def _art_pieces(self, faces: Sequence[str]) -> list[Piece]:
        """These faces' art, each layer a piece, laid with its panel."""
        return [
            Piece(
                solid,
                self._named(a.name),
                a.color,
                settings=self._art_settings(face, a),
                orca_object=self._named(face),
                parent=self._parent(face),
                place=self._flat(face),
            )
            for face in faces
            for a, solid in zip(self._layers(face), self._inlays[face])
        ]

    def closed(self, panels: list[Piece]) -> list[Piece]:
        """The box closed: its panels, their art, and the magnets."""
        magnets = []
        for wall in ("front", "back"):
            for lid in (False, True):
                panel = f"lid {wall}" if lid else wall
                magnets.append(
                    Piece(
                        Part()
                        + [f * self._magnet() for f in self._magnet_frames(wall, lid)],
                        self._named(f"{panel} magnets"),
                        "silver",
                        parent=self._parent(panel),
                    )
                )
        return panels + magnets

    # Printing

    def _flat(self, face: str, lid: bool = False) -> Location:
        """On the bed, outside down: the front and back side by side, the left
        and right behind them, the floor and top behind those. A wall's lid
        piece lies LID_GAP beyond its body piece."""
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
        """Monotonic lines: up the box on the front and back, across it on the
        top, and along the seam on the sides, turned by `turn`,
        counter-clockwise from outside."""
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
        """The body's panels, or the lid's, on the bed, with their art."""
        pieces = []
        for p, part in self._panels.items():
            if is_lid(p) != lid:
                continue
            face = self._face(p)
            pieces.append(
                Piece(
                    part,
                    self._named(f"{p} panel"),
                    self._color(p),
                    settings=self._settings(p),
                    orca_object=self._named(p),
                    parent=self._parent(p),
                    place=self._flat(face, lid and face != "top"),
                )
            )
        faces = ("top",) if lid else ("front", "back")
        return pieces + self._art_pieces(faces)

    def body(self) -> list[Piece]:
        """The body's panels, with the front's and back's art."""
        return self._laid(lid=False)

    def lid(self) -> list[Piece]:
        """The lid's panels, with the top's art."""
        return self._laid(lid=True)

    def panels(self) -> list[Piece]:
        """Every panel, with its art."""
        return self.body() + self.lid()

    # Tests

    def seam_test(
        self,
        fits: Sequence[tuple[float, float]] = ((0.05, 0.05), (0.05, 0.1), (0.05, 0.2)),
        reach: tuple[float, float] = (-9, 31),
        height: float = 14,
    ) -> list[Piece]:
        """A coupon of the front wall across the seam, body and lid, at each
        of `fits`: (key clearance, magnet crush). Notches count its place. It
        spans `reach` along the wall and `height` from the seam, and lies with
        its seam face to the front of the bed, away from Orca's seams."""
        z, t = self.seam[0], self.thickness[1]
        stub = self.key_height + 1
        width = reach[1] - reach[0]
        coupons = []
        for i, (key_clearance, crush) in enumerate(fits):
            fit = replace(
                self,
                key_clearance=key_clearance,
                magnets=replace(self.magnets, crush=crush),
            )
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
                # The lid's seam face is its bottom, so it's turned about.
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
        """A strip with a magnet pocket at each of `crushes`, notches counting
        each one's place. It lies outside down, its seam face to the front of
        the bed."""
        m, t = self.magnets, self.thickness[1]
        pitch = m.size[0] + 2 * m.glue_gap + rim
        depth = m.reach + m.glue_gap + rim
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
        at = Pos(rim + m.size[0] / 2 + m.glue_gap, 0, t) * Rot(-90, 0, 0)
        return [Piece(at * strip, self._named("magnet test"), self.color)]
