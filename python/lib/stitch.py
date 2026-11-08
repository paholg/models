"""Irregular lattice on a pyramid over any star-shaped outline, by stitching layers.

Each layer is the outline scaled toward the apex point and raised a row, with
points about `cell` apart along it (corners included while there's room). Each
pair of consecutive layers is stitched like a triangle strip: from the nearest
pair, repeatedly advance along whichever layer gives the shorter link. Every
link is printed once, as a strand. Where the zigzag's phase flips (at a
decrease or increase), the head retraces the last strand without extruding,
rather than bridging. Decreases become fans (several lower points to one upper
point) instead of needing alignment.

Layers never split (unlike insets), so there are no ridges to close; the cost
is that the slope varies around the shape, shallowest at the point farthest
from the apex.
"""

import math
from dataclasses import dataclass

import fullcontrol as fc

Point2 = tuple[float, float]
Step = fc.Point | fc.Extruder


@dataclass(frozen=True)
class StitchedPyramid:
    base: list[Point2]  # strand centerline outline at z=0, CCW
    apex: Point2  # ideally sees every edge (in the kernel); else faces lean out
    height: float  # apex height
    cell: float  # point spacing along each layer, mm
    row_height: float  # mm
    z_start: float  # first layer, resting on the floor
    node_layer: float = 0.3  # Z between a peak and the trough that sits on it
    min_angle: float = 0.0  # strands shallower than this are left out
    cap_perimeter: float = 3.0  # in cells; layers smaller than this get capped

    def layer_z(self, k: int) -> float:
        return self.z_start + k * self.row_height

    def _scaled(self, k: int) -> list[Point2]:
        s = 1 - self.layer_z(k) / self.height
        ax, ay = self.apex
        return [(ax + s * (x - ax), ay + s * (y - ay)) for x, y in self.base]

    def _perimeter(self, pts: list[Point2]) -> float:
        return sum(math.dist(p, q) for p, q in zip(pts, pts[1:] + pts[:1], strict=True))

    def layer_points(self, k: int) -> list[Point2]:
        """Points about a cell apart around layer k.

        Odd layers are shifted half a spacing, so each point sits between two
        below it (diamond-like links instead of alternating vertical/diagonal).
        Even layers include the corners.
        """
        shift = 0.5 if k % 2 else 0.0
        pts = self._scaled(k)
        edges = list(zip(pts, pts[1:] + pts[:1], strict=True))
        if self._perimeter(pts) >= len(pts) * self.cell:
            # Keep every corner; subdivide each edge.
            out = []
            for p, q in edges:
                n = max(1, round(math.dist(p, q) / self.cell))
                out += [
                    (
                        p[0] + (q[0] - p[0]) * (i + shift) / n,
                        p[1] + (q[1] - p[1]) * (i + shift) / n,
                    )
                    for i in range(n)
                ]
            return out
        # Too small for every corner: spread evenly around the perimeter.
        total = self._perimeter(pts)
        n = max(3, round(total / self.cell))
        out, walked, e = [], 0.0, 0
        for i in range(n):
            target = total * (i + shift) / n
            while walked + math.dist(*edges[e]) < target:
                walked += math.dist(*edges[e])
                e += 1
            p, q = edges[e]
            t = (target - walked) / (math.dist(p, q) or 1)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        return out

    def _layers(self) -> int:
        """Number of layers before capping."""
        k = 0
        while (
            self.layer_z(k + 1) < self.height
            and self._perimeter(self._scaled(k + 1)) >= self.cap_perimeter * self.cell
        ):
            k += 1
        return k + 1

    def _steep_enough(self, a: fc.Point, b: fc.Point) -> bool:
        horiz = math.dist((a.x or 0, a.y or 0), (b.x or 0, b.y or 0))
        rise = abs((b.z or 0) - (a.z or 0))
        return math.degrees(math.atan2(rise, horiz)) >= self.min_angle

    def _stitch(self, lower: list[fc.Point], upper: list[fc.Point]) -> list[list[Step]]:
        """Paths covering every link between two layers (each starts on `lower`)."""
        # Align: start the upper layer at the point nearest lower[0].
        j0 = min(range(len(upper)), key=lambda j: _d(upper[j], lower[0]))
        upper = upper[j0:] + upper[:j0]
        n, m = len(lower), len(upper)

        links = _best_strip(lower, upper)

        # Walk the links; pos is which end we're at (True = upper). Consecutive
        # links share a point; if we're at the other end, retrace the last link
        # without extruding to get there (a stitch repeat flips the zigzag's phase).
        paths: list[list[Step]] = []
        path: list[Step] = []
        pos_upper = False
        prev = None
        for i, j in links:
            lo, up = lower[i % n], upper[j % m]
            if not self._steep_enough(lo, up):
                if len(path) >= 2:
                    paths.append(path)
                path, prev = [], None
                continue
            if prev is None:
                path, pos_upper = list[Step]([lo, up]), True
            else:
                pi, pj = prev
                shared_upper = pj == j
                if pos_upper != shared_upper:
                    back = upper[pj % m] if shared_upper else lower[pi % n]
                    path += [
                        fc.Extruder(on=False),
                        back.model_copy(),
                        fc.Extruder(on=True),
                    ]
                path.append(lo if shared_upper else up)
                pos_upper = not shared_upper
            prev = (i, j)
        if len(path) >= 2:
            paths.append(path)
        return paths

    def _cap(self, top: list[fc.Point]) -> list[list[Step]]:
        """Strands from the top layer through the apex, in opposite pairs."""
        apex = fc.Point(x=self.apex[0], y=self.apex[1], z=self.height - self.node_layer)
        half = len(top) // 2
        return [
            list[Step]([top[i], apex.model_copy(), top[i + half]]) for i in range(half)
        ]

    def rows(self) -> list[list[list[Step]]]:
        """Per row: paths, each starting on a lower-layer point."""
        out = []
        layers = self._layers()
        for k in range(layers):
            z_lo, z_up = self.layer_z(k), self.layer_z(k + 1) - self.node_layer
            lower = [fc.Point(x=x, y=y, z=z_lo) for x, y in self.layer_points(k)]
            if k == layers - 1:
                out.append(self._cap(lower))
                break
            upper = [fc.Point(x=x, y=y, z=z_up) for x, y in self.layer_points(k + 1)]
            out.append(self._stitch(lower, upper))
        return out

    def steps(self, clearance: float = 1.0) -> list:
        """All rows as steps, with lifted travel to each path's start.

        The first travel (to the very first point) is left to the caller: see start().
        """
        steps = []
        for k, row in enumerate(self.rows()):
            for path in row:
                if steps:
                    z = self.layer_z(k + 1) + clearance
                    first = _ends(path)[0]
                    steps += [
                        fc.Extruder(on=False),
                        fc.Point(z=z),
                        fc.Point(x=first.x, y=first.y, z=z),
                        first.model_copy(),
                        fc.Extruder(on=True),
                    ]
                steps += [p.model_copy() for p in path[1:]]
        return steps

    def start(self) -> fc.Point:
        return _ends(self.rows()[0][0])[0]

    def end(self) -> fc.Point:
        return _ends(self.rows()[-1][-1])[1]

    def _segments(self):
        """Every extruded segment (start, end), following extruder on/off."""
        for row in self.rows():
            for path in row:
                last, on = None, True
                for step in path:
                    if isinstance(step, fc.Extruder):
                        on = bool(step.on)
                        continue
                    if last is not None and on:
                        yield last, step
                    last = step

    def strand_angles(self) -> list[float]:
        angles = []
        for p, q in self._segments():
            rise = abs((q.z or 0) - (p.z or 0))
            if rise > 1e-6:
                horiz = math.dist((p.x or 0, p.y or 0), (q.x or 0, q.y or 0))
                angles.append(math.degrees(math.atan2(rise, horiz)))
        return angles

    def bridges(self) -> int:
        return sum(
            1 for p, q in self._segments() if abs((q.z or 0) - (p.z or 0)) < 1e-6
        )


def _best_strip(lower: list[fc.Point], upper: list[fc.Point]) -> list[tuple[int, int]]:
    """Links (i, j) stitching two closed layers, from (0, 0) around to the end.

    Dynamic programming over the strip (each step advances one layer) for the
    least total squared link length, which strongly avoids long, shallow links.
    The final link back to (0, 0) is implied, not included.
    """
    n, m = len(lower), len(upper)
    inf = float("inf")
    cost = [[inf] * (m + 1) for _ in range(n + 1)]
    came: list[list[tuple[int, int] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = _d(lower[0], upper[0]) ** 2
    for i in range(n + 1):
        for j in range(m + 1):
            if i == j == 0:
                continue
            link = _d(lower[i % n], upper[j % m]) ** 2
            for pi, pj in ((i - 1, j), (i, j - 1)):
                if pi >= 0 and pj >= 0 and cost[pi][pj] + link < cost[i][j]:
                    cost[i][j] = cost[pi][pj] + link
                    came[i][j] = (pi, pj)
    links = []
    at: tuple[int, int] | None = came[n][m]  # (n, m) is (0, 0) again
    while at is not None:
        links.append(at)
        at = came[at[0]][at[1]]
    return links[::-1]


def _ends(path: list[Step]) -> tuple[fc.Point, fc.Point]:
    """A path's first and last points (paths always start and end on points)."""
    first, last = path[0], path[-1]
    assert isinstance(first, fc.Point) and isinstance(last, fc.Point)
    return first, last


def _d(a: fc.Point, b: fc.Point) -> float:
    return math.dist((a.x or 0, a.y or 0), (b.x or 0, b.y or 0))
