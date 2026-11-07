"""Square pyramids: solid floors and nonplanar diamond lattices on the faces.

Each face gets a flat diamond grid, as if drawn on the unrolled triangle: with
n diamonds per face at the start, diamond width = face width / n and row height
= (height - z_start) / n, so each row up has one diamond fewer per face and the
corners are shared nodes. Every diamond is the same size.

Each row is a zigzag loop: troughs on this row's nodes, peaks on the next row's
nodes, which are offset by half a diamond. Rows start/end at corner 0, stepping
up along that edge. The apex is closed with an X of edge strands.
"""

from dataclasses import dataclass

import fullcontrol as fc

Center = tuple[float, float]
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


@dataclass(frozen=True)
class Lattice:
    base: float  # strand centerline side length at z=0
    height: float  # apex
    diamonds_per_face: int  # at z_start; sets the diamond size
    z_start: float  # first row's troughs
    node_layer: float = 0.3  # Z between a peak and the trough that sits on it
    center: Center = CENTER

    @property
    def row_height(self) -> float:
        return (self.height - self.z_start) / self.diamonds_per_face

    @property
    def diamond_width(self) -> float:
        return 2 * self.half_start / self.diamonds_per_face

    @property
    def half_start(self) -> float:
        return self.base / 2 * (1 - self.z_start / self.height)

    def node(self, level: int, face: int, j: int, peak: bool = False) -> fc.Point:
        """Node j (0 = face's starting corner) on `face` at `level`.

        Level m has n - m diamonds per face. A peak sits node_layer below the
        level, so the next row's trough lands on top of it.
        """
        n = self.diamonds_per_face
        q = n - level
        half = self.half_start * q / n
        z = self.z_start + level * self.row_height - (self.node_layer if peak else 0)
        u = (face + (j / q if q else 0)) / 4
        return square_point(half, u, z, self.center)

    def row(self, m: int) -> list:
        """Zigzag loop between level m (troughs) and m+1 (peaks), from corner 0.

        Per face: corner peak, then alternating troughs/peaks. At corners 1-3,
        after arriving at the corner peak, travel down the edge and print it
        upward. Corner 0's edge is printed by the step up between rows.
        """
        q = self.diamonds_per_face - m
        points = []
        for face in range(4):
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

    def cap(self) -> list:
        """X of edge strands from the top corners to the apex.

        Starts where the last row ends (corner 0); travels between the two halves.
        """
        top = self.diamonds_per_face - 1
        apex = self.node(self.diamonds_per_face, 0, 0, peak=True)
        c = [self.node(top, f, 0, peak=True) for f in range(4)]
        assert c[1].z is not None
        return [
            apex,
            c[2],
            fc.Extruder(on=False),
            fc.Point(z=c[1].z + 2),
            fc.Point(x=c[1].x, y=c[1].y),
            c[1],
            fc.Extruder(on=True),
            apex.model_copy(),
            c[3],
        ]

    def end(self) -> fc.Point:
        """Where cap() finishes."""
        return self.node(self.diamonds_per_face - 1, 3, 0, peak=True)
