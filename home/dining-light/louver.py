"""Honeycomb louver for the down-facing side of the dining table light.

x is along the light, y is across it, z is up (into the light). Printed as
modeled. The honeycomb sits up inside the light; flat tabs at the bottom
reach out under the wood sides and take a screw each, driven up from below.
"""

from math import atan, ceil, copysign, cos, degrees, radians, sin, sqrt

from build123d import (
    BuildSketch,
    Circle,
    Face,
    Kind,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    Wire,
    extrude,
    make_hull,
    mirror,
    offset,
)

from project.cad import main

# Light

# Interior width of the prism: 4 15/16 in.
interior_w = 125.4
# Total side-to-side slop.
fit_clearance = 0.6
length = 265

# Honeycomb

# Cell opening, across flats. Flats face across the light, so this is the
# tighter direction; along the light the cutoff is about 4 degrees wider.
cell = 10
# Louver depth. Cutoff from straight down is atan(cell / depth). The light is
# 50 in above a 37 in wide table: the table edge is 20 degrees out, a seated
# eye roughly 31, so aim for about 30.
depth = 17
wall = 0.8
# Cells in the middle of the louver are stretched this much along the light,
# to let more light through. Shielding across the table is unchanged; only
# people sitting in line with the light lose some. 1 = regular hexagons.
stretch = 2
# Regular cells are kept for this far in from each end. 0 for this test piece;
# the full-length light will want regular cells at its two ends.
end_len = 0
# Length over which the stretch eases in.
ramp_len = 0

# Frame

rail_t = 3
end_t = 1.2

# Tabs

# Flat tabs stick out under the bottom edge of the wood sides; screws go up
# through them into the wood.
tabs_per_side = 3
tab_w = 16
tab_t = 3
# Thickness of the wood sides: 3/4 in. The screw is centered in it.
side_t = 19
# Clearance for a #6 / 3.5 mm wood screw.
screw_d = 4
# Tab center to the end of the louver, for the outermost tabs.
tab_inset = 25

width = interior_w - fit_clearance
pitch = cell + wall

# The hex grid is laid out unstretched along u, then mapped to x: stretched
# in the middle, eased over the ramp, unstretched at the ends.
mid_x = max(0, length / 2 - end_len - ramp_len)
mid_u = mid_x / stretch
ramp_u = ramp_len * 2 / (stretch + 1)


def warp(u: float) -> float:
    a = abs(u)
    t = a - mid_u
    if a <= mid_u:
        x = stretch * a
    elif t <= ramp_u:
        x = mid_x + stretch * t - (stretch - 1) * t * t / (2 * ramp_u)
    else:
        x = mid_x + ramp_len + t - ramp_u
    return copysign(x, u)


def cells() -> list[Wire]:
    """The outline of every cell's opening, cut off where the frame begins."""
    # Flats face +-y, columns step along u.
    r = pitch / sqrt(3)
    du = pitch * sqrt(3) / 2
    nu = ceil((mid_u + ramp_u + end_len) / du) + 1
    ny = ceil(width / 2 / pitch) + 1
    inside = Rectangle(length - 2 * end_t, width - 2 * rail_t)
    box = inside.bounding_box()
    wires = []
    for i in range(-nu, nu + 1):
        for j in range(-ny, ny + 1):
            cu = i * du
            cy = (j + (0 if i % 2 == 0 else 0.5)) * pitch
            corners = [
                (warp(cu + r * cos(radians(60 * k))), cy + r * sin(radians(60 * k)))
                for k in range(6)
            ]
            if not any(
                box.min.X < x < box.max.X and box.min.Y < y < box.max.Y
                for x, y in corners
            ):
                continue
            opening = offset(
                Polygon(*corners, align=None), -wall / 2, kind=Kind.INTERSECTION
            )
            # Only the cells at the frame want cutting.
            if not all(
                box.min.X <= x <= box.max.X and box.min.Y <= y <= box.max.Y
                for x, y in corners
            ):
                opening = opening & inside
            wires += [face.outer_wire() for face in opening.faces()]
    return wires


def honeycomb() -> Part:
    # One face, with a hole for each cell, drawn up: no cell is cut from a solid.
    return extrude(Face(Rectangle(length, width).wire(), cells()), depth)


def tab() -> Part:
    """Centered on x, reaching out in -y from the wall's inside face at y = 0."""
    screw_y = -side_t / 2
    # As far as the honeycomb's side, which stands this far in from the wall.
    root = fit_clearance / 2
    with BuildSketch() as outline:
        with Locations((0, root / 2)):
            Rectangle(tab_w, root)
        with Locations((0, screw_y)):
            Circle(tab_w / 2)
        make_hull()
        with Locations((0, screw_y)):
            Circle(screw_d / 2, mode=Mode.SUBTRACT)
    return extrude(outline.sketch, tab_t)


def tabs() -> list[Part]:
    span = length - 2 * tab_inset
    near = [
        Pos(-span / 2 + k * span / max(1, tabs_per_side - 1), -interior_w / 2) * tab()
        for k in range(tabs_per_side)
    ]
    return near + [mirror(t, Plane.XZ) for t in near]


def louver() -> Part:
    print(
        f"  cutoff across flats: {degrees(atan(cell / depth)):.4f} deg from straight down"
    )
    print(
        f"  cutoff across corners: {degrees(atan(cell * 2 / sqrt(3) / depth)):.4f} deg"
    )
    return honeycomb() + tabs()


main(__file__, parts={"print": louver})
