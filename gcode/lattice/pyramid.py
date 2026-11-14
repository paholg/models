"""Square pyramid: solid bottom (T0), nonplanar diamond-lattice sides (T1)."""

from lib.preview import preview
from lib.pyramid import CENTER, Lattice, floor, square, strand_steps
from lib.settings import DEFAULT

from lib import u1

S = DEFAULT
LW, LH = S.line_width, S.layer_height

BASE = 60.0  # bottom side length, mm
HEIGHT = 50.0  # to the apex
BOTTOM_LAYERS = 3
DIAMONDS_PER_FACE = 10  # at the base; sets the diamond size
STRAND_DIAMETER = 0.6  # strands in air come out roughly round
STRAND_SPEED = 600  # mm/min

bottom = floor(BASE, BOTTOM_LAYERS, LW, LH)
lattice = Lattice(
    base=square(BASE - LW),
    apex=CENTER,
    height=HEIGHT,
    diamonds_per_face=DIAMONDS_PER_FACE,
    # Half a strand above the floor, so the first troughs are pressed into it.
    z_start=BOTTOM_LAYERS * LH + STRAND_DIAMETER / 2,
)

steps = [
    *bottom,
    *u1.tool_change(1, bottom[-1], S, to=lattice.start()),
    *strand_steps(STRAND_DIAMETER, STRAND_SPEED),
    *lattice.rows(),
    *lattice.cap(),
]

if __name__ == "__main__":
    print(u1.gcode(steps, "pyramid", S))
    print(preview(steps, "pyramid", S))
