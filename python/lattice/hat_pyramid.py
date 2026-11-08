"""Two nested lattice pyramids over the "hat" aperiodic monotile.

Like double_pyramid: solid hat-shaped bottom (T0), an inner lattice pyramid
over a smaller hat (T1), then the outer one around it (T2). The apex sits above
the hat's kernel (the region that sees every edge), so every face leans inward.

Heights are derived from a minimum strand angle, since the far edges of the hat
are much further from the apex than the near ones.
"""

import math

from shapely.geometry import Polygon

from lib import u1
from lib.hat import hat
from lib.preview import preview
from lib.pyramid import Lattice, kernel_center, polygon_floor, strand_steps
from lib.settings import DEFAULT

S = DEFAULT
LW, LH = S.line_width, S.layer_height

UNIT = 14.0  # mm per hex-grid unit; the hat is about 6 units wide
BOTTOM_LAYERS = 3
DIAMONDS_PER_FACE = 5  # every face, at the bottom
MIN_STRAND_ANGLE = 50.0  # degrees from horizontal, outer lattice
# Split edges longer than this (in hex units) into equal faces. 1.8 splits only
# the length-2 edge (diamond widths vary by sqrt(3)); 1.0 also splits the
# sqrt(3) edges, for near-uniform diamonds but an extra rib up those faces.
MAX_FACE_LENGTH = 1.8

INNER_SCALE = (
    0.55  # inner hat, scaled toward the apex (see hat_roof for a constant gap)
)
INNER_DIAMONDS_PER_FACE = 4
INNER_MIN_STRAND_ANGLE = 45.0  # lower slope than the outer

STRAND_DIAMETER = 0.6
STRAND_SPEED = 600  # mm/min
TRAVEL_CLEARANCE = 5.0


def split_long_edges(pts: list[tuple[float, float]], max_len: float) -> list:
    """Split each edge longer than max_len into equal parts.

    Has 10% slack, since offsetting the outline stretches some edges slightly.
    """
    out = []
    for p0, p1 in zip(pts, pts[1:] + pts[:1], strict=True):
        parts = max(1, math.ceil(math.dist(p0, p1) / max_len - 0.1))
        out += [
            (p0[0] + (p1[0] - p0[0]) * k / parts, p0[1] + (p1[1] - p0[1]) * k / parts)
            for k in range(parts)
        ]
    return out


def height_for(base, apex, min_angle: float) -> float:
    """Height at which the worst face's strands are at min_angle."""
    worst = 0.0
    for p0, p1 in zip(base, base[1:] + base[:1], strict=True):
        length = math.dist(p0, p1)
        cross = (p1[0] - p0[0]) * (apex[1] - p0[1]) - (p1[1] - p0[1]) * (
            apex[0] - p0[0]
        )
        worst = max(worst, math.hypot(length / 2, abs(cross) / length))
    return worst * math.tan(math.radians(min_angle))


def inset(outline: list[tuple[float, float]], distance: float) -> list:
    """Outline offset inward by `distance`, CCW, starting near outline[0], long edges split."""
    pts = list(Polygon(outline).buffer(-distance, join_style="mitre").exterior.coords)
    pts = pts[:-1]
    if not Polygon(pts).exterior.is_ccw:
        pts.reverse()
    # buffer() may rotate the vertex order.
    first = min(range(len(pts)), key=lambda i: math.dist(pts[i], outline[0]))
    pts = pts[first:] + pts[:first]
    return split_long_edges(pts, MAX_FACE_LENGTH * UNIT)


outline = hat(UNIT)

# Strand centerlines: outer sits half a line in from the floor's edge.
outer_base = inset(outline, LW / 2)
apex = kernel_center(outer_base)
inner_base = [
    (apex[0] + INNER_SCALE * (x - apex[0]), apex[1] + INNER_SCALE * (y - apex[1]))
    for x, y in outer_base
]

z_start = BOTTOM_LAYERS * LH + STRAND_DIAMETER
outer_apex = inner_apex = apex
outer = Lattice(
    base=outer_base,
    apex=outer_apex,
    height=height_for(outer_base, outer_apex, MIN_STRAND_ANGLE),
    diamonds_per_face=DIAMONDS_PER_FACE,
    z_start=z_start,
)
inner = Lattice(
    base=inner_base,
    apex=inner_apex,
    height=height_for(inner_base, inner_apex, INNER_MIN_STRAND_ANGLE),
    diamonds_per_face=INNER_DIAMONDS_PER_FACE,
    z_start=z_start,
)

bottom = polygon_floor(Polygon(outline), BOTTOM_LAYERS, LW, LH)
last_floor_point = bottom[-1]

steps = [
    *bottom,
    *u1.tool_change(1, last_floor_point, S, to=inner.start()),
    *strand_steps(STRAND_DIAMETER, STRAND_SPEED),
    *inner.rows(),
    *inner.cap(),
    *u1.tool_change(
        2, inner.end(), S, to=outer.start(), travel_z=inner.height + TRAVEL_CLEARANCE
    ),
    *outer.rows(),
    *outer.cap(),
]

if __name__ == "__main__":
    for lattice, name in [(inner, "inner"), (outer, "outer")]:
        widths = lattice.diamond_widths()
        print(
            f"{name}: {lattice.faces} faces, {lattice.height:.1f} mm tall, "
            f"diamonds {min(widths):.1f}-{max(widths):.1f} mm wide x "
            f"{lattice.row_height:.1f} mm rows, strands >= {min(lattice.strand_angles()):.0f}°"
        )
    print(u1.gcode(steps, "hat_pyramid", S))
    print(preview(steps, "hat_pyramid", S))
