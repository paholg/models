"""Smoke test: a 30mm spiral-vase cylinder, 10mm tall, T0 bottom half, T1 top half."""

import fullcontrol as fc

from lib import u1
from lib.settings import Settings

S = Settings()
LAYER = S.layer_height
HEIGHT = 10
RADIUS = 15
SEGMENTS_PER_TURN = 64
CENTER_X, CENTER_Y = 135, 135


def helix(z0: float, height: float) -> list:
    turns = height / LAYER
    return fc.helixZ(
        fc.Point(x=CENTER_X, y=CENTER_Y, z=z0),
        RADIUS,
        RADIUS,
        start_angle=0,
        n_turns=turns,
        pitch_z=LAYER,
        segments=round(SEGMENTS_PER_TURN * turns),
    )


bottom = helix(LAYER, HEIGHT / 2)
top = helix(bottom[-1].z, HEIGHT / 2)

steps = [*bottom, *u1.tool_change(1, bottom[-1], S), *top[1:]]

print(u1.gcode(steps, "cylinder", S))
