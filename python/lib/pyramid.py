"""Pyramids: solid floors and nonplanar diamond lattices on the faces.

Each face gets a flat diamond grid, as if drawn on the unrolled triangle: with
n diamonds per face at the start, diamond width = face width / n and row height
= (height - z_start) / n, so each row up has one diamond fewer per face and the
corners are shared nodes. Every diamond is the same size.

Each row is a zigzag loop: troughs on this row's nodes, peaks on the next row's
nodes, which are offset by half a diamond. Rows start/end at corner 0, stepping
up along that edge. The apex is closed with an X of edge strands.
"""

import math
from dataclasses import dataclass

import fullcontrol as fc
from shapely.geometry import Polygon

Point2 = tuple[float, float]
Center = Point2
CENTER: Center = (135.0, 135.0)


def square_point(half: float, u: float, z: float, center: Center = CENTER) -> fc.Point:
    """Point at fraction u around a square of half-width `half`, CCW from (-half, -half)."""
    side = (u % 1) * 4
    i = int(side)
    a = -half + 2 * half * (side - i)
    x, y = [(a, -half), (half, a), (-a, half), (-half, -a)][i]
    return fc.Point(x=center[0] + x, y=center[1] + y, z=z)


def floor(
    side: float,
    layers: int,
    line_width: float,
    layer_height: float,
    center: Center = CENTER,
) -> list:
    """Solid square floor of concentric loops; `side` is the outer edge."""
    steps = []
    for layer in range(layers):
        z = layer_height * (layer + 1)
        loops = []
        half = side / 2 - line_width / 2
        while half > line_width / 2:
            loops.append([square_point(half, q / 4, z, center) for q in range(5)])
            half -= line_width
        # Alternate outside-in / inside-out so layers connect without travel.
        if layer % 2:
            loops.reverse()
        steps += [p for loop in loops for p in loop]
    return steps


def strand_steps(diameter: float, speed: int) -> list:
    """Switch to round strands printed in air."""
    return [
        # width/height only affect the preview; G-code uses the circle's area.
        fc.ExtrusionGeometry(
            area_model="circle", diameter=diameter, width=diameter, height=diameter
        ),
        fc.Printer(print_speed=speed),
        fc.ManualGcode(text=f"; LINE_WIDTH: {diameter}\n; LAYER_HEIGHT: {diameter}"),
    ]


def square(side: float, center: Center = CENTER) -> list[Point2]:
    """Square vertices, CCW from (-half, -half), matching square_point's order."""
    h = side / 2
    cx, cy = center
    return [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]


def polygon_floor(
    outline: Polygon, layers: int, line_width: float, layer_height: float
) -> list:
    """Solid floor of concentric inward offsets of `outline`, travelling between loops."""
    steps = []
    for layer in range(layers):
        z = layer_height * (layer + 1)
        k = 0
        while True:
            inset = outline.buffer(
                -(line_width / 2 + k * line_width), join_style="mitre"
            )
            if inset.is_empty:
                break
            for poly in getattr(inset, "geoms", [inset]):
                ring = list(poly.exterior.coords)
                steps.append(fc.Extruder(on=False))
                steps += [fc.Point(x=x, y=y, z=z) for x, y in ring[:1]]
                steps.append(fc.Extruder(on=True))
                steps += [fc.Point(x=x, y=y, z=z) for x, y in ring[1:]]
            k += 1
    return steps


@dataclass(frozen=True)
class Lattice:
    """Diamond lattice on a pyramid over a star-shaped polygon.

    `base` is the strand centerline outline at z=0 (CCW), and the apex is above
    `apex`, which must see every edge (be in the polygon's kernel). Each face
    starts with `diamonds_per_face` diamonds, so diamond width scales with edge
    length; row height is shared.
    """

    base: list[Point2]
    apex: Point2
    height: float
    diamonds_per_face: int  # at z_start, on every face
    z_start: float  # first row's troughs
    node_layer: float = 0.3  # Z between a peak and the trough that sits on it

    @property
    def faces(self) -> int:
        return len(self.base)

    @property
    def row_height(self) -> float:
        return (self.height - self.z_start) / self.diamonds_per_face

    def diamond_widths(self) -> list[float]:
        """Per face, at z_start."""
        s = 1 - self.z_start / self.height
        n = self.diamonds_per_face
        b = self.base
        return [s * math.dist(b[f], b[(f + 1) % len(b)]) / n for f in range(len(b))]

    def strand_angles(self) -> list[float]:
        """Per face: degrees from horizontal of the strands (lower is less supported)."""
        angles = []
        for f in range(self.faces):
            p0, p1 = self.base[f], self.base[(f + 1) % self.faces]
            length = math.dist(p0, p1)
            # Perpendicular distance from the apex to the edge line.
            cross = (p1[0] - p0[0]) * (self.apex[1] - p0[1]) - (p1[1] - p0[1]) * (
                self.apex[0] - p0[0]
            )
            r = abs(cross) / length
            angles.append(
                math.degrees(math.atan2(self.height, math.hypot(length / 2, r)))
            )
        return angles

    def node(self, level: int, face: int, j: int, peak: bool = False) -> fc.Point:
        """Node j (0 = face's starting corner) on `face` at `level`.

        Level m has n - m diamonds per face, on the base scaled toward the apex.
        A peak sits node_layer below the level, so the next row's trough lands
        on top of it.
        """
        n = self.diamonds_per_face
        q = n - level
        z = self.z_start + level * self.row_height
        scale = (1 - self.z_start / self.height) * q / n
        p0 = self.base[face % self.faces]
        p1 = self.base[(face + 1) % self.faces]
        t = j / q if q else 0
        ax, ay = self.apex
        x = ax + scale * (p0[0] + t * (p1[0] - p0[0]) - ax)
        y = ay + scale * (p0[1] + t * (p1[1] - p0[1]) - ay)
        return fc.Point(x=x, y=y, z=z - (self.node_layer if peak else 0))

    def row(self, m: int) -> list:
        """Zigzag loop between level m (troughs) and m+1 (peaks), from corner 0.

        Per face: corner peak, then alternating troughs/peaks. At corners other
        than 0, after arriving at the corner peak, travel down the edge and
        print it upward. Corner 0's edge is printed by the step up between rows.
        """
        q = self.diamonds_per_face - m
        points = []
        for face in range(self.faces):
            corner_peak = self.node(m + 1, face, 0, peak=True)
            points.append(corner_peak)
            if face:
                points += [
                    fc.Extruder(on=False),
                    self.node(m, face, 0),
                    fc.Extruder(on=True),
                    corner_peak.model_copy(),
                ]
            for j in range(1, q):
                points.append(self.node(m, face, j))
                if j < q - 1:
                    points.append(self.node(m + 1, face, j, peak=True))
        points.append(self.node(m + 1, 0, 0, peak=True))  # close the loop
        return points

    def start(self) -> fc.Point:
        """Corner 0 on the floor, where the lattice begins."""
        return self.node(0, 0, 0)

    def rows(self) -> list:
        """All rows, from start() (exclusive) up to the top corners."""
        points = []
        for m in range(self.diamonds_per_face - 1):
            points += self.row(m)
        return points

    def _cap_pairs(self) -> list[tuple[int, int]]:
        half = self.faces // 2
        return [(i, i + half) for i in range(half)]

    def cap(self) -> list:
        """Edge strands from the top corners to the apex, in opposite pairs.

        Starts where the last row ends (corner 0); travels between pairs.
        """
        top = self.diamonds_per_face - 1
        apex = self.node(self.diamonds_per_face, 0, 0, peak=True)
        c = [self.node(top, f, 0, peak=True) for f in range(self.faces)]
        steps = []
        for i, (a, b) in enumerate(self._cap_pairs()):
            if i:
                z = c[a].z
                assert z is not None
                steps += [
                    fc.Extruder(on=False),
                    fc.Point(z=z + 2),
                    fc.Point(x=c[a].x, y=c[a].y),
                    c[a],
                    fc.Extruder(on=True),
                ]
            steps += [apex.model_copy(), c[b]]
        return steps

    def end(self) -> fc.Point:
        """Where cap() finishes."""
        b = self._cap_pairs()[-1][1]
        return self.node(self.diamonds_per_face - 1, b, 0, peak=True)
