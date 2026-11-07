"""The "hat" aperiodic monotile (Smith, Myers, Kaplan & Goodman-Strauss, 2023)."""

import math

from shapely.geometry import Polygon

from .pyramid import CENTER, Center


def hat(unit: float, center: Center = CENTER) -> list[tuple[float, float]]:
    """The hat polykite, CCW, in mm, its bounding box centered on `center`.

    `unit` is mm per hex-grid unit; the hat is about 6 units wide.
    """
    s3 = math.sqrt(3)
    grid = [(0, 0), (-1, -1), (0, -2), (2, -2), (2, -1), (4, -2)]
    grid += [(5, -1), (4, 0), (3, 0), (2, 2), (0, 3), (0, 2), (-1, 2)]
    pts = [((x + y / 2) * unit, (s3 / 2 * y) * unit) for x, y in grid]
    if not Polygon(pts).exterior.is_ccw:
        pts.reverse()
    minx, miny, maxx, maxy = Polygon(pts).bounds
    dx, dy = center[0] - (minx + maxx) / 2, center[1] - (miny + maxy) / 2
    return [(x + dx, y + dy) for x, y in pts]
