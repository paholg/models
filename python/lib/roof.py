"""Diamond lattice on a hip roof over any outline.

The roof is a height field: height grows with distance from the outline, at
`slope`. So every face rises at the same slope, each level's cross-section is
the outline inset by a constant amount, and two roofs offset horizontally are
parallel (constant gap at every height). Ridges are where the distance to the
outline stops growing.

Every level gets its own nodes, evenly spaced around each of its loops and
offset to sit between the level below's nodes. Row m weaves level m's nodes
(troughs) with level m+1's (peaks) in order around each loop:
- trough/peak neighbors are strands;
- two peaks in a row (an increase) are joined by a bridge;
- two troughs in a row (a decrease) are joined by a bridge between nodes that
  are already printed;
- anything shallower than `min_angle` or too long is cut, and each chain is
  arranged to start on a trough (supported).
Only peaks a chain actually prints become the next row's troughs, but since the
next level is repopulated anyway, gaps stay local instead of growing upward.

Troughs under a ridge (no full row above them) are walked along the ridge
instead, zigzagging across it via peaks on the ridge line, which closes it.
"""

import functools
import itertools
import math
from dataclasses import dataclass

import fullcontrol as fc
from shapely.geometry import LinearRing, Point, Polygon

CLIMB_STEP = 0.2  # mm, steepest-ascent step
# A step gaining less than this fraction of its length means a ridge. Hips
# still gain sin(half the corner angle): 0.71 for 90°, 0.5 for 60°.
STALL = 0.25
BEND = 0.9  # a step gaining less than this has left a plain face
# A full row must be gained within this many rows of climbing: hips need
# 1/sin(half the corner angle) (1.41 for 90°).
HIP_REACH = 1.6
MIN_SPACING = 0.6  # cells; level nodes closer than this merge
MAX_SPACING = 1.5  # cells; wider gaps get extra level nodes
MAX_BRIDGE = 1.6  # cells


@dataclass(eq=False)
class Node:
    x: float
    y: float
    z: float
    loop: int | None  # index into its level's loops; None for ridge points


def row_height_for(
    slope: float, cell: float, strand_angle: float, node_layer: float = 0.3
) -> float:
    """Row height giving strands of `strand_angle` for diamonds `cell` wide.

    A strand goes half a cell along the row and one row's inset inward while
    rising a row (less the node overlap); solve that for the row height.
    Strands on a face can't be steeper than it, so strand_angle < slope.
    """
    if strand_angle >= slope:
        raise ValueError(
            f"strand_angle ({strand_angle:g}°) must be less than slope ({slope:g}°): "
            f"a strand on a face can't be steeper than the face"
        )
    t2 = math.tan(math.radians(strand_angle)) ** 2
    a = 1 - t2 / math.tan(math.radians(slope)) ** 2
    c = node_layer**2 - t2 * cell**2 / 4
    return (node_layer + math.sqrt(node_layer**2 - a * c)) / a


def _point(n: Node) -> fc.Point:
    return fc.Point(x=n.x, y=n.y, z=n.z)


@dataclass(frozen=True)
class RoofLattice:
    outline: Polygon
    inset: float  # horizontal inset of the first row from the outline, mm
    slope: float  # roof face angle from horizontal, degrees
    row_height: float  # mm
    cell: float  # target node spacing along each level, mm
    z_start: float  # first row's troughs
    node_layer: float = 0.3  # Z between a peak and the trough that sits on it
    min_angle: float = 45.0  # degrees; shallower strands are left out

    def __post_init__(self):
        typical = self.typical_strand_angle()
        if typical < self.min_angle:
            raise ValueError(
                f"strands on a {self.slope:g}° roof with {self.cell:g} mm cells would be "
                f"about {typical:.0f}°, under min_angle {self.min_angle:g}° (a strand on "
                f"a face can't be steeper than the face). Steepen the slope, narrow the "
                f"cells, or lower min_angle."
            )

    def typical_strand_angle(self) -> float:
        """Degrees, for a diamond of width `cell` on a plain face."""
        rise = self.row_height - self.node_layer
        return math.degrees(math.atan2(rise, math.hypot(self.cell / 2, self.row_inset)))

    @property
    def row_inset(self) -> float:
        """Horizontal inset per row."""
        return self.row_height / math.tan(math.radians(self.slope))

    def level_z(self, m: int) -> float:
        return self.z_start + m * self.row_height

    def height_at(self, x: float, y: float) -> float:
        """Roof surface height above (x, y)."""
        d = self.outline.exterior.distance(Point(x, y))
        return self.z_start + (d - self.inset) * math.tan(math.radians(self.slope))

    def loops(self, m: int) -> list[LinearRing]:
        """Level m's cross-section: one ring per piece (pieces split at necks)."""
        shape = self.outline.buffer(-(self.inset + m * self.row_inset))
        if shape.is_empty:
            return []
        return [LinearRing(p.exterior.coords) for p in getattr(shape, "geoms", [shape])]

    # Level nodes

    def _nearest_ring(self, rings: list[LinearRing], x: float, y: float) -> int:
        return min(range(len(rings)), key=lambda i: rings[i].distance(Point(x, y)))

    def _level_nodes(self, m: int, below: list[Node]) -> list[Node]:
        """Level m's nodes: midway between the level below's, about a cell apart."""
        rings = self.loops(m)
        z = self.level_z(m)
        nodes = []
        for i, ring in enumerate(rings):
            length = ring.length
            params = sorted(
                ring.project(Point(n.x, n.y))
                for n in below
                if self._nearest_ring(rings, n.x, n.y) == i
                and ring.distance(Point(n.x, n.y)) < 2 * self.row_inset
            )
            if len(params) >= 2:
                cyclic = [*params, params[0] + length]
                candidates = [
                    (a + b) / 2 % length for a, b in itertools.pairwise(cyclic)
                ]
            else:
                n = max(3, round(length / self.cell))
                candidates = [length * k / n for k in range(n)]
            for s in _resample(sorted(candidates), length, self.cell):
                p = ring.interpolate(s)
                nodes.append(Node(p.x, p.y, z, i))
        return nodes

    # Climbing (ridge detection)

    def _climb(self, start: Node) -> Node | None:
        """The ridge point above a trough, or None if a full row fits above it.

        Steepest ascent on the distance-to-outline field: runs straight up
        faces, follows hips, and stalls at ridges. A full row only counts if
        it's gained within HIP_REACH rows of path (what a hip needs); a climb
        that has to wander further (e.g. along a rising ridge) means the trough
        is under a ridge. The ridge point is where the climb first bent: where
        the straight run up the face met the ridge.
        """
        boundary = self.outline.exterior

        def dist(px: float, py: float) -> float:
            return boundary.distance(Point(px, py))

        x, y = start.x, start.y
        d = dist(x, y)
        target = d + self.row_inset
        h = CLIMB_STEP / 2
        bend = None
        travelled = 0.0
        for _ in range(int(4 * self.row_inset / CLIMB_STEP) + 1):
            # Finite differences: on a hip this averages the two faces' slopes,
            # pointing up the hip; on a ridge they cancel.
            gx = dist(x + h, y) - dist(x - h, y)
            gy = dist(x, y + h) - dist(x, y - h)
            norm = math.hypot(gx, gy) or 1.0
            nx, ny = x + CLIMB_STEP * gx / norm, y + CLIMB_STEP * gy / norm
            nd = dist(nx, ny)
            travelled += CLIMB_STEP
            if nd >= target and travelled <= HIP_REACH * self.row_inset:
                return None
            gain = (nd - d) / CLIMB_STEP
            if bend is None and gain < BEND:
                bend = (x, y)
            if gain < STALL or not self.outline.contains(Point(nx, ny)):
                break
            if travelled > HIP_REACH * self.row_inset:
                break
            x, y, d = nx, ny, nd
        bx, by = bend or (x, y)
        return Node(bx, by, self.height_at(bx, by) - self.node_layer, None)

    # Rows

    def _steep_enough(self, a: Node, b: Node) -> bool:
        horiz = math.dist((a.x, a.y), (b.x, b.y))
        return math.degrees(math.atan2(abs(b.z - a.z), horiz)) >= self.min_angle

    def _edge_ok(
        self, u: Node, v: Node, kind_u: str, kind_v: str, strip: set[int]
    ) -> bool:
        if id(u) in strip or id(v) in strip:
            return False
        if kind_u == kind_v:  # bridge
            return math.dist((u.x, u.y), (v.x, v.y)) <= MAX_BRIDGE * self.cell
        return self._steep_enough(u, v)

    def _row(
        self, m: int, troughs: list[Node], peaks: list[Node]
    ) -> tuple[list[list[Node]], list[tuple[Node, Node]]]:
        """Chains for row m, and (trough, ridge point) for troughs under a ridge."""
        rings = self.loops(m)
        strip = []
        for t in troughs:
            ridge = self._climb(t)
            if ridge is not None:
                strip.append((t, ridge))
        strip_ids = {id(t) for t, _ in strip}

        chains = []
        for i, ring in enumerate(rings):
            items = [("t", t) for t in troughs if t.loop == i]
            for p in peaks:
                j = self._nearest_ring(rings, p.x, p.y)
                if j == i and ring.distance(Point(p.x, p.y)) < 2 * self.row_inset:
                    items.append(("p", p))
            if len(items) < 2:
                continue
            items.sort(key=lambda kn: ring.project(Point(kn[1].x, kn[1].y)))
            ok = [
                self._edge_ok(u, v, ku, kv, strip_ids)
                for (ku, u), (kv, v) in zip(items, items[1:] + items[:1], strict=True)
            ]
            chains += _chains(items, ok)
        return chains, strip

    @functools.cached_property
    def _rows(self) -> list[list[list[fc.Point]]]:
        out = []
        troughs = self._level_nodes(0, [])
        m = 0
        while troughs and self.loops(m):
            peaks = self._level_nodes(m + 1, troughs) if self.loops(m + 1) else []
            for p in peaks:
                p.z -= self.node_layer
            chains, strip = self._row(m, troughs, peaks)
            row = [[_point(n) for n in c] for c in chains]
            row += self._ridge_paths(strip)
            if row:
                out.append(row)
            printed = {id(n) for c in chains for n in c}
            troughs = [
                Node(p.x, p.y, self.level_z(m + 1), p.loop)
                for p in peaks
                if id(p) in printed
            ]
            m += 1
        return out

    def rows(self) -> list[list[list[fc.Point]]]:
        """Per row: paths, each starting on a trough (cached)."""
        return self._rows

    def _ridge_paths(self, strip: list[tuple[Node, Node]]) -> list[list[fc.Point]]:
        """Close the last strip under each ridge.

        `strip` is (trough, ridge point) for troughs under a ridge. They're
        chained along each ridge by how close their ridge points are, then
        walked in order: troughs on opposite sides get a peak on the ridge
        between them (or, if that's too shallow, a bridge straight across);
        troughs on the same side get a bridge. Lone troughs get a strand up.
        """
        ridge_of = {id(t): r for t, r in strip}
        remaining = list(strip)
        paths: list[list[fc.Point]] = []
        while remaining:
            # Start at an end: the ridge point farthest from the rest's centroid.
            cx = sum(r.x for _, r in remaining) / len(remaining)
            cy = sum(r.y for _, r in remaining) / len(remaining)
            seq = [
                max(remaining, key=lambda tr: math.dist((tr[1].x, tr[1].y), (cx, cy)))
            ]
            remaining.remove(seq[0])
            while remaining:
                last = seq[-1][1]
                nxt = min(
                    remaining,
                    key=lambda tr: math.dist((tr[1].x, tr[1].y), (last.x, last.y)),
                )
                if (
                    math.dist((nxt[1].x, nxt[1].y), (last.x, last.y))
                    > MAX_BRIDGE * self.cell
                ):
                    break
                seq.append(nxt)
                remaining.remove(nxt)
            for chain in self._walk_ridge(seq):
                if len(chain) == 1:
                    t = chain[0]
                    r = ridge_of[id(t)]
                    if self._steep_enough(t, r):
                        paths.append([_point(t), _point(r)])
                else:
                    paths.append([_point(n) for n in chain])
        return paths

    def _walk_ridge(self, seq: list[tuple[Node, Node]]) -> list[list[Node]]:
        """Chains along one ridge; each starts (and ends) on a trough."""
        chains, chain = [], [seq[0][0]]
        for (u, ru), (v, rv) in itertools.pairwise(seq):
            close = math.dist((u.x, u.y), (v.x, v.y)) <= MAX_BRIDGE * self.cell
            opposite = (u.x - ru.x) * (v.x - rv.x) + (u.y - ru.y) * (v.y - rv.y) < 0
            link = None
            if opposite:
                px, py = (ru.x + rv.x) / 2, (ru.y + rv.y) / 2
                peak = Node(px, py, self.height_at(px, py) - self.node_layer, None)
                if self._steep_enough(u, peak) and self._steep_enough(peak, v):
                    link = [peak, v]
            if link is None and close:
                link = [v]  # bridge between printed troughs
            if link:
                chain += link
            else:
                chains.append(chain)
                chain = [v]
        chains.append(chain)
        return chains

    # Output

    def steps(self, clearance: float = 1.0) -> list:
        """All rows as steps, with lifted travel to each path's start.

        The first travel (to the very first trough) is left to the caller: see start().
        """
        steps = []
        for m, row in enumerate(self.rows()):
            for path in row:
                if steps:
                    z = self.level_z(m + 1) + clearance
                    steps += [
                        fc.Extruder(on=False),
                        fc.Point(z=z),
                        fc.Point(x=path[0].x, y=path[0].y, z=z),
                        path[0],
                        fc.Extruder(on=True),
                    ]
                steps += path[1:]
        return steps

    def start(self) -> fc.Point:
        return self.rows()[0][0][0]

    def end(self) -> fc.Point:
        return self.rows()[-1][-1][-1]

    def height(self) -> float:
        return max(
            p.z for row in self.rows() for path in row for p in path if p.z is not None
        )

    def _segments(self):
        """(start, end, is_strand): strands join a trough and a peak; the rest are bridges."""
        for m, row in enumerate(self.rows()):
            z_trough = self.level_z(m)
            for path in row:
                for p, q in itertools.pairwise(path):
                    on_trough = [abs((n.z or 0) - z_trough) < 1e-6 for n in (p, q)]
                    yield p, q, on_trough[0] != on_trough[1]

    def strand_angles(self) -> list[float]:
        """Degrees from horizontal of every trough-to-peak strand."""
        angles = []
        for p, q, is_strand in self._segments():
            if is_strand:
                horiz = math.dist((p.x or 0, p.y or 0), (q.x or 0, q.y or 0))
                angles.append(
                    math.degrees(math.atan2(abs((q.z or 0) - (p.z or 0)), horiz))
                )
        return angles

    def bridges(self) -> int:
        return sum(1 for _, _, is_strand in self._segments() if not is_strand)


def _resample(params: list[float], length: float, cell: float) -> list[float]:
    """Positions along a loop, merging ones closer than MIN_SPACING cells and
    filling gaps wider than MAX_SPACING cells."""
    if not params:
        return []
    kept: list[float] = []
    for s in params:
        if kept and s - kept[-1] < MIN_SPACING * cell:
            continue
        if kept and s - kept[-1] > MAX_SPACING * cell:
            extra = round((s - kept[-1]) / cell) - 1
            kept += [
                kept[-1] + (s - kept[-1]) * k / (extra + 1) for k in range(1, extra + 1)
            ]
        kept.append(s)
    # Wrap-around gap.
    wrap = kept[0] + length - kept[-1]
    if len(kept) > 1 and wrap < MIN_SPACING * cell:
        kept.pop()
    elif wrap > MAX_SPACING * cell:
        extra = round(wrap / cell) - 1
        kept += [
            (kept[-1] + wrap * k / (extra + 1)) % length for k in range(1, extra + 1)
        ]
    return sorted(kept)


def _chains(items: list[tuple[str, Node]], ok: list[bool]) -> list[list[Node]]:
    """Maximal runs of a cyclic sequence joined by ok edges, each starting on a
    trough and containing at least one peak.

    ok[i] says whether items[i] -> items[i + 1] (cyclically) may be printed.
    """
    n = len(items)
    if all(ok):
        runs = [[*items, items[0]]]  # the whole loop
    else:
        start = (ok.index(False) + 1) % n  # just after a cut
        runs, run = [], [items[start]]
        for k in range(n):
            i = (start + k) % n
            if ok[i]:
                run.append(items[(i + 1) % n])
            else:
                runs.append(run)
                run = [items[(i + 1) % n]]
    chains = []
    for run in runs:
        if run and run[0][0] == "p":
            # Must start supported: reverse if it ends on a trough, else drop the peak.
            run = run[::-1] if run[-1][0] == "t" else run[1:]
        if len(run) >= 2 and any(k == "p" for k, _ in run):
            chains.append([node for _, node in run])
    return chains
