"""Look a drawn object over for what's easy to miss in FreeCAD: edges left
sharp, and the slivers that cuts leave where they meet.

audit() finds them, as spots; shots() draws the object, whole and close up at
each spot, as PNGs to look at. A project runs them on itself (see
cad.project()): `just audit FILE [OBJECT]` and `just shots FILE OBJECT [X,Y,Z]`.

What audit() looks for, in an object's pieces together, as they sit:

* A convex edge whose faces turn by SHARP degrees or more, and so has no
  chamfer or fillet. A chamfer's own edges turn by 45, and pass, as does the
  miter where two chamfers meet at a square corner, which turns by 60.
* A face smaller than SLIVER_AREA, or an edge shorter than SLIVER_EDGE: what's
  left between two cuts that nearly coincide.

Pieces are taken together because an inlay's pocket is sharp on purpose, and
isn't an edge of the object once the inlay is in it.

What an object leaves sharp on purpose, it lists as its `skip_audit` (see
cad.Object): each a Skip, which says of a finding whether to pass over it. on_top and
on_bottom are for the rims of holes through an object, a honeycomb's say, and
anywhere for an object not worth auditing.

    Object(riser, "A riser", skip_audit=[on_top, on_bottom])
"""

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import acos, cos, degrees, radians, sin
from pathlib import Path

from build123d import (
    Align,
    BoundBox,
    Box,
    Color,
    Compound,
    Edge,
    ExportSVG,
    Face,
    Pos,
    Shape,
    Solid,
    Sphere,
    Vector,
)

# A convex edge is sharp from this many degrees between its faces' normals.
SHARP = 65
# Shorter than this, a sharp edge is a corner of something else that's found.
SHARP_LENGTH = 0.3
# mm^2 and mm.
SLIVER_AREA = 0.01
SLIVER_EDGE = 0.05
# Findings this near each other are one spot.
SPOT = 4


@dataclass
class Finding:
    kind: str  # "sharp" or "sliver"
    at: Vector
    said: str
    # How high it reaches, from and to.
    low: float
    high: float


# Whether to pass over a finding, given the box round the object, as it sits.
type Skip = Callable[[Finding, BoundBox], bool]


def on_top(found: Finding, box: BoundBox) -> bool:
    """Lying in the object's top: the rim of a hole through it, say."""
    return found.low > box.max.Z - 1e-3


def on_bottom(found: Finding, box: BoundBox) -> bool:
    """Lying in the object's bottom."""
    return found.high < box.min.Z + 1e-3


def anywhere(found: Finding, box: BoundBox) -> bool:
    """Any at all: the object isn't audited."""
    return True


@dataclass
class Spot:
    """Findings near each other: where, and what."""

    at: Vector
    findings: list[Finding]

    def __str__(self) -> str:
        sharp = [f for f in self.findings if f.kind == "sharp"]
        slivers = len(self.findings) - len(sharp)
        said = []
        if sharp:
            said.append(f"{len(sharp)} sharp: {', '.join(f.said for f in sharp[:4])}")
            if len(sharp) > 4:
                said[-1] += ", ..."
        if slivers:
            said.append(f"{slivers} slivers")
        x, y, z = (round(v, 1) for v in tuple(self.at))
        return f"({x}, {y}, {z}): {'; '.join(said)}"


def together(shapes: Sequence[Shape]) -> list[Solid]:
    """The shapes as one, where they touch."""
    whole = shapes[0]
    for s in shapes[1:]:
        whole = whole + s
    return list(whole.solids())


def turn(edge: Edge, a: Face, b: Face) -> tuple[float, Vector, Vector]:
    """How far the faces' normals turn across the edge, at its middle, in
    degrees; where that is; and a step from there that stays in the solid only
    if the edge is concave: out from one face and in from the other, which is
    under the other face at an inside corner, and in the air past an outside
    one."""
    at = edge.position_at(0.5)
    na, nb = a.normal_at(at), b.normal_at(at)
    cos = max(-1.0, min(1.0, na.dot(nb)))
    return degrees(acos(cos)), at, (nb - na) * 0.02


def sharp_edges(
    solid: Solid, shortest: float = SHARP_LENGTH, convex: bool = True
) -> list[Edge]:
    """A solid's convex edges whose faces turn by SHARP degrees or more, as
    long as `shortest`: or, not `convex`, its concave ones, its inside
    corners."""
    faces: dict[Edge, list[Face]] = {}
    for face in solid.faces():
        for edge in face.edges():
            faces.setdefault(edge, []).append(face)
    sharp = []
    for edge, beside in faces.items():
        if len(beside) != 2 or edge.length < shortest:
            continue
        angle, at, step = turn(edge, *beside)
        if angle >= SHARP and solid.is_inside(at + step) != convex:
            sharp.append(edge)
    return sharp


def finding(kind: str, shape: Edge | Face, at: Vector, said: str) -> Finding:
    box = shape.bounding_box()
    return Finding(kind, at, said, box.min.Z, box.max.Z)


def audit(shapes: Sequence[Shape], skip: Sequence[Skip] = ()) -> tuple[list[Spot], int]:
    """What's wrong with an object, whose pieces these are, as spots; and how
    many findings `skip` passed over."""
    found: list[Finding] = []
    solids = together(shapes)
    for solid in solids:
        for face in solid.faces():
            if face.area < SLIVER_AREA:
                found.append(finding("sliver", face, face.center(), "face"))
        for edge in solid.edges():
            if edge.length < SLIVER_EDGE:
                found.append(finding("sliver", edge, edge.position_at(0.5), "edge"))
        for edge in sharp_edges(solid):
            found.append(
                finding("sharp", edge, edge.position_at(0.5), f"{edge.length:.1f} mm")
            )
    box = Compound(solids).bounding_box()
    kept = [f for f in found if not any(s(f, box) for s in skip)]
    spots: list[Spot] = []
    for f in kept:
        near = next((s for s in spots if (s.at - f.at).length < SPOT), None)
        if near is None:
            spots.append(Spot(f.at, [f]))
        else:
            near.findings.append(f)
    return spots, len(found) - len(kept)


# Views of the whole: the way to the eye, from the middle.
WHOLE = {
    "top": (0.01, -0.02, 1),
    "front-left": (-1, -1.3, 1.2),
    "front-right": (1, -1.3, 1.2),
    "back-left": (-1, 1.3, 1.2),
    "back-right": (1, 1.3, 1.2),
}
# What a close-up shows: this far each way from its spot.
REACH = 7
# Across a picture, in pixels; and as it's drawn, before that, in mm, with
# lines this wide.
PIXELS = 1600
DRAWN = 200
LINE = 0.25


def picture(shape: Compound, eye: Vector, look: Vector, out: Path, mark: bool) -> None:
    """A line drawing of the shape from `eye`, hidden lines left out, as a
    PNG; with `mark`, a red ring at `look`."""
    up = (0, 1, 0) if abs(eye.Z - look.Z) > 0.99 * (eye - look).length else (0, 0, 1)
    visible, _ = shape.project_to_viewport(tuple(eye), up, look_at=tuple(look))
    svg = ExportSVG(scale=DRAWN / shape.bounding_box().diagonal, margin=2)
    svg.add_layer("lines", line_weight=LINE)
    svg.add_shape(visible, layer="lines")
    if mark:
        ring, _ = (Pos(look) * Sphere(REACH / 15)).project_to_viewport(
            tuple(eye), up, look_at=tuple(look)
        )
        svg.add_layer("mark", line_color=Color("red"), line_weight=2 * LINE)
        svg.add_shape(ring, layer="mark")
    out.parent.mkdir(parents=True, exist_ok=True)
    drawn = out.with_suffix(".svg")
    svg.write(str(drawn))
    subprocess.run(
        ["magick", "-background", "white", "-density", "300", str(drawn), "-flatten",
         "-resize", f"{PIXELS}x{PIXELS}", str(out)],
        check=True,
    )  # fmt: skip
    drawn.unlink()


def ways(cut: Compound, at: Vector) -> list[Vector]:
    """Two ways to look at a spot from, of those all round and above it, none
    square on to a box's faces: the
    ones with the least of the shape between the spot and the eye, and, of
    those, far from each other."""
    solids = cut.solids()

    def hidden(way: Vector) -> int:
        steps = [at + way * (0.3 + i * REACH / 10) for i in range(18)]
        return sum(any(s.is_inside(p) for s in solids) for p in steps)

    around = [
        Vector(cos(radians(turn)), sin(radians(turn)), rise).normalized()
        for rise in (0.9, 1.8, 0.4)
        for turn in range(25, 385, 45)
    ]
    scored = sorted(around, key=hidden)
    first = scored[0]
    least = hidden(scored[1])
    # The other: as clear as the second best, and the farthest round.
    second = max(
        (w for w in scored[1:] if hidden(w) == least), key=lambda w: (w - first).length
    )
    return [first, second]


def shots(
    shapes: Sequence[Shape], out: Path, spots: Sequence[Vector] | None = None
) -> list[Path]:
    """Pictures of the shapes together, as <out>-<view>.png: from all round,
    or, with spots, close up at each from two sides, the rest cut away."""
    whole = Compound(list(shapes))
    box = whole.bounding_box()
    written = []
    if spots is None:
        for name, way in WHOLE.items():
            path = out.with_name(f"{out.name}-{name}.png")
            eye = box.center() + Vector(way).normalized() * 3 * box.diagonal
            picture(whole, eye, box.center(), path, False)
            written.append(path)
        return written
    for i, at in enumerate(spots, 1):
        near = Pos(at) * Box(2 * REACH, 2 * REACH, 2 * REACH, align=Align.CENTER)
        # A piece that doesn't reach the spot leaves an empty shape.
        cut = Compound([c for s in shapes if isinstance(c := s & near, Shape) and c])
        for name, way in zip("ab", ways(cut, at)):
            path = out.with_name(f"{out.name}-{i}{name}.png")
            picture(cut, at + way * 200, at, path, True)
            written.append(path)
    return written
