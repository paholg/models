"""Smoke test: a 30 mm solid square, three layers in T0, then two more in T1.

Tests the start sequence and a tool change on something that sticks: solid
layers of concentric loops, like the lattice floors.
"""

from lib import u1
from lib.pyramid import floor
from lib.settings import DEFAULT

S = DEFAULT
LW, LH = S.line_width, S.layer_height

SIDE = 30.0
T0_LAYERS = 3
T1_LAYERS = 2

layers = floor(SIDE, T0_LAYERS + T1_LAYERS, LW, LH)


def layer(n: int) -> list:
    """Layer n's points, from 0."""
    return [p for p in layers if round(p.z / LH) == n + 1]


bottom = [p for n in range(T0_LAYERS) for p in layer(n)]
top = [p for n in range(T0_LAYERS, T0_LAYERS + T1_LAYERS) for p in layer(n)]

steps = [
    *bottom,
    *u1.tool_change(1, bottom[-1], S, to=top[0]),
    *top[1:],
]

if __name__ == "__main__":
    print(u1.gcode(steps, "tool_change", S))
