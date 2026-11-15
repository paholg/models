"""Strand settings side by side: a row of small zigzag fences, one per variant.

The fences share one raft, and each is two rows of the pyramid's diamonds, in
a vertical plane. Fence 1 is nearest the front of the bed; the
rest follow toward the back, in the order of VARIANTS. All in T0.
"""

from dataclasses import dataclass

import fullcontrol as fc
from lib.preview import preview
from lib.pyramid import CENTER, polygon_floor
from lib.settings import DEFAULT
from shapely.geometry import box

from lib import u1

S = DEFAULT
LW, LH = S.line_width, S.layer_height


@dataclass(frozen=True)
class Variant:
    diameter: float  # strand, mm; the nozzle is 0.4
    speed: int  # mm/min
    dwell: float = 0.0  # s at each peak, for it to set
    temp: int = 210  # nozzle


VARIANTS = [
    Variant(0.6, 600),  # what the pyramid used
    Variant(0.6, 180),
    Variant(0.45, 600),
    Variant(0.45, 180),
    Variant(0.45, 180, dwell=1.0),
    Variant(0.45, 90, dwell=1.0),
    Variant(0.45, 180, dwell=1.0, temp=190),
    Variant(0.6, 180, dwell=1.0, temp=190),
]

TEETH = 4
PITCH = 5.8  # diamond width, mm
ROW = 4.9  # row height, mm
NODE_LAYER = 0.3  # Z between a peak and the trough that sits on it
SPACING = 12.0  # between fences, mm
MARGIN = 4.0  # of raft around the fences, mm
FLOOR_LAYERS = 2
RETRACT = 1.5  # mm, on travels
CLEARANCE = 3.0  # above the fence when travelling

LENGTH = TEETH * PITCH
x0 = CENTER[0] - LENGTH / 2
floor_top = FLOOR_LAYERS * LH


def fence_y(i: int) -> float:
    return CENTER[1] + (i - (len(VARIANTS) - 1) / 2) * SPACING


def travel(to: fc.Point, z: float) -> list:
    return [
        fc.ManualGcode(text=f"G1 E-{RETRACT} F1800 ; retract"),
        *u1.travel(to, z)[:-1],
        fc.ManualGcode(text=f"G1 E{RETRACT} F1800 ; unretract"),
        fc.Extruder(on=True),
    ]


def fence(i: int, v: Variant) -> list:
    y = fence_y(i)
    z0 = floor_top + v.diameter / 2  # pressed half a strand into the floor
    top = z0 + 2 * ROW + CLEARANCE
    dwell = [fc.ManualGcode(text=f"G4 P{v.dwell * 1000:.0f}")] if v.dwell else []

    def at(k: float, z: float) -> fc.Point:
        return fc.Point(x=x0 + k * PITCH, y=y, z=z)

    # Row 1, left to right: troughs on the floor, peaks half a diamond along.
    row1: list = [at(0, z0)]
    for j in range(TEETH):
        row1 += [at(j + 0.5, z0 + ROW - NODE_LAYER), *dwell, at(j + 1, z0)]
    # Row 2, right to left: troughs on row 1's peaks.
    row2: list = [at(TEETH - 0.5, z0 + ROW)]
    for j in range(TEETH - 1, 0, -1):
        row2 += [at(j, z0 + 2 * ROW - NODE_LAYER), *dwell, at(j - 0.5, z0 + ROW)]

    return [
        fc.Extruder(on=False),
        fc.Point(z=top),
        fc.ManualGcode(text=f"; fence {i + 1}: {v}\nM109 S{v.temp}"),
        fc.ExtrusionGeometry(
            area_model="circle",
            diameter=v.diameter,
            width=v.diameter,
            height=v.diameter,
        ),
        fc.Printer(print_speed=v.speed),
        *travel(row1[0], top),
        *row1[1:],
        *travel(row2[0], top),
        *row2[1:],
    ]


raft = box(
    x0 - MARGIN,
    fence_y(0) - MARGIN,
    x0 + LENGTH + MARGIN,
    fence_y(len(VARIANTS) - 1) + MARGIN,
)

steps = [
    *polygon_floor(raft, FLOOR_LAYERS, LW, LH),
    *[step for i, v in enumerate(VARIANTS) for step in fence(i, v)],
]

if __name__ == "__main__":
    for i, v in enumerate(VARIANTS):
        print(f"fence {i + 1} (y {fence_y(i):.0f}): {v}")
    print(u1.gcode(steps, "strands", S))
    print(preview(steps, "strands", S))
