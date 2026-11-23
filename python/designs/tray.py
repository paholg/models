"""What the box inserts' trays are made of: bodies chamfered all round, wells
for stacks, and pinch slots to get the stacks out by.

    from designs.tray import block, carve, pinch, rim, well, Slot

A tray is drawn from its own corner, z up from the bed: a block(), less a
well() and its rim() for each stack, less the cuts() of a Slot through a wall
beside it, and a notch() where that slot goes down through the floor.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from math import hypot

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Compound,
    Kind,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    Shape,
    Sketch,
    Solid,
    Vector,
    chamfer,
    extrude,
    fillet,
    mirror,
    offset,
    revolve,
)

from build.cad import part, sketch

# Chamfers

# Well and pocket rims.
rim_c = 0.4
# Outside top and bottom edges.
chamfer_out = 0.6
# Outside vertical corners.
chamfer_corner = 1
# Inside corners and floor edges of wells.
fillet_r = 1


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
    inside a well whose floor is at `floor`, from the top of its fillet into
    the wall up."""

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
            # From where the floor's fillet into the wall ends: lower, it
            # would cut into that fillet beside the slot. A notch() chamfers
            # the edge from there down.
            above = cuboid(-1000, -1000, floor + fillet_r, 1000, 1000, 1000)
            out.append(part(eased & above))
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
    # The floor's new edge, chamfered, as far as its fillet into the wall: cut
    # off there, as the chamfer's own end would go on round the corner, into
    # that fillet beside the notch.
    top = plan & rect(-1, fillet_r, length + 1, inset + 1)
    edge = Pos(0, 0, floor) * flare(top, rim_c, Vector(0, 0, -1))
    edge &= cuboid(-inset, fillet_r, floor - 1, length + inset, 2 * inset, floor + 1)
    # From there the edge goes up the fillet at each end, to the wall, and the
    # chamfer with it: its section, running on a little out of the part, turned
    # about the fillet's axis. It ends as the chamfer of the slot's own edge up
    # the wall begins (see Slot).
    c, out = rim_c, 0.5
    axis = Axis((0, fillet_r, floor + fillet_r), (-1, 0, 0))
    across = Plane((0, fillet_r, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    ends = [
        revolve(
            (
                across
                * polygon(
                    [
                        (x - way * (c + out), floor + out),
                        (x + way * out, floor + out),
                        (x + way * out, floor - c - out),
                    ]
                )
            ).faces(),
            axis,
            90,
        )
        for x, way in ((0, 1), (length, -1))
    ]
    return [
        at * up(plan, -1, 1 + floor + fillet_r),
        at * flare(plan, chamfer_out, Vector(0, 0, 1)),
        at * part(edge),
        *[at * part(end) for end in ends],
    ]


# Turning a notch's frame: the well in -y, in +x, and in -x.
toward_minus_y = Rot(0, 0, 180)
toward_plus_x = Rot(0, 0, -90)
toward_minus_x = Rot(0, 0, 90)
