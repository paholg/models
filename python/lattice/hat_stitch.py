"""Two nested stitched-lattice pyramids over the "hat" monotile.

Solid hat-shaped bottom (T0), an inner lattice pyramid over a smaller hat (T1),
then the outer one around it (T2). Layers are the hat scaled toward the apex;
consecutive layers are stitched point-to-nearest-point (see lib/stitch.py), so
the lattice is irregular but has no holes or alignment constraints.
"""

import math

from shapely.geometry import Polygon

from lib import u1
from lib.hat import hat
from lib.preview import preview
from lib.pyramid import best_view, kernel_center, polygon_floor, strand_steps
from lib.roof import row_height_for
from lib.settings import DEFAULT
from lib.stitch import StitchedPyramid

S = DEFAULT
LW, LH = S.line_width, S.layer_height

UNIT = 14.0  # mm per hex-grid unit; the hat is about 6 units wide
BOTTOM_LAYERS = 3
# Slope at the hat's farthest point from the apex (the shallowest spot); sets
# the apex height. Elsewhere the surface is steeper.
SLOPE = 35.0
CELL = 6.0  # point spacing along layers, mm
# Typical strands at the shallowest spot run this much below the slope (they
# cross the face diagonally); sets the row height.
STRAND_BELOW_SLOPE = 5.0
MIN_ANGLE = 15.0  # shallower strands are left out (leaving holes)

INNER_GAP = 8.0  # mm between each outer edge and its parallel inner edge, at the base
INNER_SLOPE = 30.0  # lower than the outer

STRAND_DIAMETER = 0.6
STRAND_SPEED = 600  # mm/min
TRAVEL_CLEARANCE = 5.0

outline = hat(UNIT)
# Strand centerlines: outer sits half a line in from the floor's edge.


def inset(pts: list[tuple[float, float]], distance: float) -> list[tuple[float, float]]:
    """Outline with every edge moved in by `distance` (parallel), CCW."""
    shape = Polygon(pts).buffer(-distance, join_style="mitre")
    assert isinstance(shape, Polygon), "inset split the outline"
    out = list(shape.exterior.coords)[:-1]
    return out if shape.exterior.is_ccw else out[::-1]


outer_base = inset(outline, LW / 2)
inner_base = inset(outer_base, INNER_GAP)
z_start = BOTTOM_LAYERS * LH + STRAND_DIAMETER


def pyramid(base, apex, slope: float) -> StitchedPyramid:
    far = max(math.dist(p, apex) for p in base)
    return StitchedPyramid(
        base=base,
        apex=apex,
        height=far * math.tan(math.radians(slope)),
        cell=CELL,
        row_height=row_height_for(slope, CELL, slope - STRAND_BELOW_SLOPE),
        z_start=z_start,
        min_angle=MIN_ANGLE,
    )


outer = pyramid(outer_base, kernel_center(outer_base), SLOPE)
# The inset may have no point that sees every edge (past ~4 mm it doesn't); then
# a face or two leans slightly outward.
inner = pyramid(inner_base, best_view(inner_base), INNER_SLOPE)

bottom = polygon_floor(Polygon(outline), BOTTOM_LAYERS, LW, LH)
steps = [
    *bottom,
    *u1.tool_change(1, bottom[-1], S, to=inner.start()),
    *strand_steps(STRAND_DIAMETER, STRAND_SPEED),
    *inner.steps(),
    *u1.tool_change(
        2, inner.end(), S, to=outer.start(), travel_z=inner.height + TRAVEL_CLEARANCE
    ),
    *outer.steps(),
]

if __name__ == "__main__":
    for lattice, name in [(inner, "inner"), (outer, "outer")]:
        angles = lattice.strand_angles()
        rows = lattice.rows()
        print(
            f"{name}: {len(rows)} rows of {lattice.row_height:.1f} mm, "
            f"{lattice.height:.1f} mm tall, {sum(len(r) for r in rows)} paths, "
            f"{len(angles)} strands (min {min(angles):.0f}°), {lattice.bridges()} bridges"
        )
    print(u1.gcode(steps, "hat_stitch", S))
    print(preview(steps, "hat_stitch", S))
