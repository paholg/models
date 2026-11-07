"""Square pyramid: solid bottom (T0), nonplanar diamond-lattice sides (T1).

Each face gets a flat diamond grid, as if drawn on the unrolled triangle: with
n diamonds per face at the base, diamond width = face width / n and row height
= (height - floor) / n, so each row up has one diamond fewer per face and the
corners are shared nodes. Every diamond is the same size.

Each row is a zigzag loop: troughs on this row's nodes, peaks on the next row's
nodes, which are offset by half a diamond. Rows start/end at corner 0, stepping
up along that edge. The apex is closed with an X of edge strands.
"""

import fullcontrol as fc

from lib import u1
from lib.preview import preview
from lib.settings import DEFAULT

S = DEFAULT
LW, LH = S.line_width, S.layer_height

# Shape
BASE = 60.0  # bottom side length, mm
HEIGHT = 50.0  # to the apex
CX, CY = 135.0, 135.0

# Bottom
BOTTOM_LAYERS = 3

# Lattice
DIAMONDS_PER_FACE = 10  # at the base; sets the diamond size
NODE_LAYER = 0.3  # Z between a peak and the trough that sits on it, mm
STRAND_DIAMETER = 0.6  # strands in air come out roughly round
STRAND_SPEED = 600  # mm/min


def square_point(half: float, u: float, z: float) -> fc.Point:
    """Point at fraction u around a square of half-width `half`, CCW from (-half, -half)."""
    side = (u % 1) * 4
    i = int(side)
    a = -half + 2 * half * (side - i)
    x, y = [(a, -half), (half, a), (-a, half), (-half, -a)][i]
    return fc.Point(x=CX + x, y=CY + y, z=z)


def bottom() -> list:
    steps = []
    for layer in range(BOTTOM_LAYERS):
        z = LH * (layer + 1)
        loops = []
        half = BASE / 2 - LW / 2
        while half > LW / 2:
            loops.append([square_point(half, q / 4, z) for q in range(5)])
            half -= LW
        # Alternate outside-in / inside-out so layers connect without travel.
        if layer % 2:
            loops.reverse()
        steps += [p for loop in loops for p in loop]
    return steps


class Grid:
    """Node positions on the four faces."""

    def __init__(self, z_start: float):
        self.n = DIAMONDS_PER_FACE
        self.z_start = z_start
        self.row_height = (HEIGHT - z_start) / self.n
        half0 = BASE / 2 - LW / 2
        self.half_start = half0 * (1 - z_start / HEIGHT)

    def node(self, level: int, face: int, j: int, peak: bool = False) -> fc.Point:
        """Node j (0 = face's starting corner) on `face` at `level`.

        Level m has n - m diamonds per face. A peak sits NODE_LAYER below the
        level, so the next row's trough lands on top of it.
        """
        q = self.n - level
        half = self.half_start * q / self.n
        z = self.z_start + level * self.row_height - (NODE_LAYER if peak else 0)
        u = (face + (j / q if q else 0)) / 4
        return square_point(half, u, z)

    def row(self, m: int) -> list:
        """Zigzag loop between level m (troughs) and m+1 (peaks), from corner 0.

        Per face: corner peak, then alternating troughs/peaks. At corners 1-3,
        after arriving at the corner peak, travel down the edge and print it
        upward. Corner 0's edge is printed by the step up between rows.
        """
        q = self.n - m
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

    def lattice(self) -> list:
        # Start at corner 0 on the floor, step up the edge into row 0.
        points = [self.node(0, 0, 0)]
        for m in range(self.n - 1):
            points += self.row(m)
        return points

    def cap(self) -> list:
        """X of edge strands from the top corners to the apex.

        Starts where the last row ends (corner 0); travels between the two halves.
        """
        top = self.n - 1
        apex = self.node(self.n, 0, 0, peak=True)
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


floor = bottom()
z_floor = BOTTOM_LAYERS * LH
grid = Grid(z_floor + STRAND_DIAMETER)
sides = grid.lattice()

steps = [
    *floor,
    *u1.tool_change(1, floor[-1], S, to=sides[0]),
    # width/height only affect the preview; G-code uses the circle's area.
    fc.ExtrusionGeometry(
        area_model="circle",
        diameter=STRAND_DIAMETER,
        width=STRAND_DIAMETER,
        height=STRAND_DIAMETER,
    ),
    fc.Printer(print_speed=STRAND_SPEED),
    fc.ManualGcode(
        text=f"; LINE_WIDTH: {STRAND_DIAMETER}\n; LAYER_HEIGHT: {STRAND_DIAMETER}"
    ),
    *sides[1:],
    *grid.cap(),
]

if __name__ == "__main__":
    print(u1.gcode(steps, "lattice_pyramid", S))
    print(preview(steps, "lattice_pyramid", S))
