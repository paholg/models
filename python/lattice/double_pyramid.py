"""Two nested lattice pyramids on one solid bottom.

Bottom (T0), then a shorter, inset inner lattice pyramid (T1), then the outer
lattice pyramid (T2) printed around it. The lattices are independent; they're
joined only through the bottom.

The outer lattice prints next to the finished inner one, so near the bottom the
hotend reaches down within about INNER_INSET of it. Increase the inset if it hits.
"""

from lib import u1
from lib.preview import preview
from lib.pyramid import Lattice, floor, strand_steps
from lib.settings import DEFAULT

S = DEFAULT
LW, LH = S.line_width, S.layer_height

BASE = 60.0  # bottom side length, mm
HEIGHT = 50.0  # outer apex
BOTTOM_LAYERS = 3
DIAMONDS_PER_FACE = 10  # outer, at the base

INNER_INSET = 10.0  # per side, mm
INNER_HEIGHT = 22.0  # inner apex: lower slope than the outer
INNER_DIAMONDS_PER_FACE = 7

STRAND_DIAMETER = 0.6  # strands in air come out roughly round
STRAND_SPEED = 600  # mm/min
TRAVEL_CLEARANCE = 5.0  # above the inner apex when moving to the outer lattice

z_start = BOTTOM_LAYERS * LH + STRAND_DIAMETER
bottom = floor(BASE, BOTTOM_LAYERS, LW, LH)
inner = Lattice(
    base=BASE - LW - 2 * INNER_INSET,
    height=INNER_HEIGHT,
    diamonds_per_face=INNER_DIAMONDS_PER_FACE,
    z_start=z_start,
)
outer = Lattice(
    base=BASE - LW,
    height=HEIGHT,
    diamonds_per_face=DIAMONDS_PER_FACE,
    z_start=z_start,
)

steps = [
    *bottom,
    *u1.tool_change(1, bottom[-1], S, to=inner.start()),
    *strand_steps(STRAND_DIAMETER, STRAND_SPEED),
    *inner.rows(),
    *inner.cap(),
    *u1.tool_change(
        2,
        inner.end(),
        S,
        to=outer.start(),
        travel_z=INNER_HEIGHT + TRAVEL_CLEARANCE,
    ),
    *outer.rows(),
    *outer.cap(),
]

if __name__ == "__main__":
    for lattice, name in [(inner, "inner"), (outer, "outer")]:
        print(
            f"{name}: {lattice.diamonds_per_face} diamonds/face, "
            f"{lattice.diamond_width:.1f} mm wide x {lattice.row_height:.1f} mm rows"
        )
    print(u1.gcode(steps, "double_pyramid", S))
    print(preview(steps, "double_pyramid", S))
