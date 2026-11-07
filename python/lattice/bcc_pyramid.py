"""Square pyramid filled with a stretched BCC strut lattice, one tool per layer.

Solid bottom (T0), then the lattice clipped to the pyramid, cycling through
LAYER_TOOLS. No skin: the strut ends define the outline.

Level height is how far the nozzle reaches down past just-printed struts a cell
away, so it's limited by the hotend's clearance below the heater block/duct.
"""

from lib import u1
from lib.bcc import BCC
from lib.preview import preview
from lib.pyramid import CENTER, floor, strand_steps
from lib.settings import DEFAULT

S = DEFAULT
LW, LH = S.line_width, S.layer_height

BASE = 60.0  # bottom side length, mm
HEIGHT = 50.0  # to the apex
BOTTOM_LAYERS = 3

CELL = 6.0  # horizontal node pitch, mm
LEVEL_HEIGHT = 6.0  # mm; with CELL sets the strut angle
LAYER_TOOLS = [1, 2, 3]  # cycled per layer

STRAND_DIAMETER = 0.6
STRAND_SPEED = 600  # mm/min
TRAVEL_CLEARANCE = 2.0  # above the current layer when travelling or changing tools

half0 = BASE / 2 - STRAND_DIAMETER  # node centers stay a strand in from the edge


def inside(x: float, y: float, z: float) -> bool:
    half = half0 * (1 - z / HEIGHT)
    return abs(x - CENTER[0]) <= half + 1e-6 and abs(y - CENTER[1]) <= half + 1e-6


z_start = BOTTOM_LAYERS * LH + STRAND_DIAMETER
lattice = BCC(
    inside=inside,
    origin=CENTER,
    extent=BASE / 2,
    cell=CELL,
    level_height=LEVEL_HEIGHT,
    z_start=z_start,
    levels=int((HEIGHT - z_start) / LEVEL_HEIGHT),
)
layers = [k for k in range(lattice.levels) if lattice.layer(k)]

bottom = floor(BASE, BOTTOM_LAYERS, LW, LH)
tools = u1.ToolState(S)
steps = list(bottom)
at = bottom[-1]
for i, k in enumerate(layers):
    steps += tools.change(
        LAYER_TOOLS[i % len(LAYER_TOOLS)],
        at,
        lattice.first_point(k),
        travel_z=lattice.level_z(k) + TRAVEL_CLEARANCE,
    )
    if i == 0:
        steps += strand_steps(STRAND_DIAMETER, STRAND_SPEED)
    steps += lattice.layer_steps(k, clearance=TRAVEL_CLEARANCE)
    at = lattice.last_point(k)

if __name__ == "__main__":
    struts = sum(len(seg) - 1 for k in layers for seg in lattice.layer(k))
    print(
        f"{len(layers)} layers, {struts} struts, "
        f"strut angle {lattice.strut_angle():.0f}°, "
        f"nozzle reaches {LEVEL_HEIGHT:.1f} mm below the top of each layer"
    )
    print(u1.gcode(steps, "bcc_pyramid", S))
    print(preview(steps, "bcc_pyramid", S))
