"""Two parallel lattice hip roofs over the "hat" monotile.

Solid hat-shaped bottom (T0), then an inner lattice roof (T1), then the outer
one around it (T2). Every roof face rises at SLOPE, so the inner roof is the
outer one offset by GAP: the gap between them is constant at every height.
"""

from lib.hat import hat
from lib.preview import preview
from lib.pyramid import polygon_floor, strand_steps
from lib.roof import RoofLattice, row_height_for
from lib.settings import DEFAULT
from shapely.geometry import Polygon

from lib import u1

S = DEFAULT
LW, LH = S.line_width, S.layer_height

UNIT = 14.0  # mm per hex-grid unit; the hat is about 6 units wide
BOTTOM_LAYERS = 3
SLOPE = 45.0  # roof faces, degrees from horizontal
CELL = 3.0  # diamond width: node spacing along rows, mm
STRAND_ANGLE = 39.0  # typical strands, degrees from horizontal; < SLOPE
# Strands at corners and ridges come out shallower than typical; ones under
# this are left out.
MIN_ANGLE = STRAND_ANGLE - 4
GAP = 6.0  # horizontal gap between the roofs, mm

STRAND_DIAMETER = 0.6
STRAND_SPEED = 600  # mm/min
TRAVEL_CLEARANCE = 5.0

outline = Polygon(hat(UNIT))
z_start = BOTTOM_LAYERS * LH + STRAND_DIAMETER


def roof(inset: float) -> RoofLattice:
    return RoofLattice(
        outline=outline,
        inset=inset,
        slope=SLOPE,
        row_height=row_height_for(SLOPE, CELL, STRAND_ANGLE),
        cell=CELL,
        z_start=z_start,
        min_angle=MIN_ANGLE,
    )


outer = roof(LW / 2)
inner = roof(LW / 2 + GAP)

bottom = polygon_floor(outline, BOTTOM_LAYERS, LW, LH)
steps = [
    *bottom,
    *u1.tool_change(1, bottom[-1], S, to=inner.start()),
    *strand_steps(STRAND_DIAMETER, STRAND_SPEED),
    *inner.steps(),
    *u1.tool_change(
        2, inner.end(), S, to=outer.start(), travel_z=inner.height() + TRAVEL_CLEARANCE
    ),
    *outer.steps(),
]

if __name__ == "__main__":
    for lattice, name in [(inner, "inner"), (outer, "outer")]:
        angles = lattice.strand_angles()
        rows = lattice.rows()
        print(
            f"{name}: {len(rows)} rows of {lattice.row_height:.1f} mm, "
            f"{lattice.height():.1f} mm tall, "
            f"{sum(len(r) for r in rows)} paths, {len(angles)} strands "
            f"(min {min(angles):.0f}°), {lattice.bridges()} bridges"
        )
    print(u1.gcode(steps, "hat_roof", S))
    print(preview(steps, "hat_roof", S))
