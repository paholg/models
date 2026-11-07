"""Body-centered cubic strut lattice, stretched vertically, clipped to a volume.

Level k nodes form a square grid with pitch `cell`; odd levels are offset by
half a cell in x and y. Each node rests on the (up to) four nodes diagonally
below it. Stretching (level_height vs cell) sets the strut angle.

Each layer (level k -> k+1) prints as zigzags: for each row of upper nodes, one
zigzag along x to the lower row on each side, together covering every strut.
Zigzags are split where nodes fall outside the volume, and every segment
starts on a lower (supported) node.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

import fullcontrol as fc

Point2 = tuple[float, float]
Inside = Callable[[float, float, float], bool]
# A zigzag vertex: (is_lower, point).
Vertex = tuple[bool, fc.Point]


@dataclass(frozen=True)
class BCC:
    inside: Inside  # (x, y, z) -> whether a node there is part of the lattice
    origin: Point2  # a level-0 node position
    extent: float  # half-width of the region to search for nodes, mm
    cell: float  # horizontal node pitch, mm
    level_height: float  # mm
    z_start: float  # level 0, resting on the floor
    levels: int  # number of layers (level k -> k+1)
    node_layer: float = 0.3  # Z between a peak and the trough that sits on it

    def strut_angle(self) -> float:
        """Degrees from horizontal."""
        rise = self.level_height - self.node_layer
        return math.degrees(math.atan2(rise, self.cell / math.sqrt(2)))

    def level_z(self, k: int) -> float:
        return self.z_start + k * self.level_height

    def _half_steps(self) -> range:
        """Half-cell indices covering the search region."""
        n = 2 * (math.ceil(self.extent / self.cell) + 1)
        return range(-n, n + 1)

    def _zigzag(self, k: int, y_upper: float, y_lower: float) -> list[list[Vertex]]:
        """Vertices alternating lower/upper along x, split where outside the volume.

        Half-cell index t is a lower node when t has the parity of k (odd levels
        are offset by half a cell).
        """
        z_low, z_up = self.level_z(k), self.level_z(k + 1)
        segments: list[list[Vertex]] = [[]]
        for t in self._half_steps():
            x = self.origin[0] + t * self.cell / 2
            lower = (t - k) % 2 == 0
            y, z = (y_lower, z_low) if lower else (y_upper, z_up)
            if self.inside(x, y, z):
                z_print = z if lower else z - self.node_layer
                segments[-1].append((lower, fc.Point(x=x, y=y, z=z_print)))
            elif segments[-1]:
                segments.append([])
        return [s for s in (_supported(s) for s in segments) if len(s) >= 2]

    def layer(self, k: int) -> list[list[fc.Point]]:
        """Segments for level k -> k+1, alternating direction where possible."""
        n = math.ceil(self.extent / self.cell) + 1
        upper_off = self.cell / 2 if (k + 1) % 2 else 0.0
        segments = []
        for j in range(-n, n + 1):
            y_up = self.origin[1] + upper_off + j * self.cell
            for y_low in (y_up - self.cell / 2, y_up + self.cell / 2):
                for seg in self._zigzag(k, y_up, y_low):
                    # Reverse every other one, if it still starts on a lower node.
                    if len(segments) % 2 and seg[-1][0]:
                        seg = seg[::-1]
                    segments.append([p for _, p in seg])
        return segments

    def layer_steps(self, k: int, clearance: float = 1.0) -> list:
        """Layer k as steps, travelling above the layer between segments.

        Assumes the head is already at first_point(k) with the extruder on.
        """
        steps = []
        travel_z = self.level_z(k + 1) + clearance
        for i, seg in enumerate(self.layer(k)):
            if i:
                steps += [
                    fc.Extruder(on=False),
                    fc.Point(z=travel_z),
                    fc.Point(x=seg[0].x, y=seg[0].y, z=travel_z),
                    seg[0],
                    fc.Extruder(on=True),
                ]
            steps += seg[1:]
        return steps

    def first_point(self, k: int) -> fc.Point:
        return self.layer(k)[0][0]

    def last_point(self, k: int) -> fc.Point:
        return self.layer(k)[-1][-1]


def _supported(seg: list[Vertex]) -> list[Vertex]:
    """Make a segment start on a lower node: reverse it, or drop a leading upper."""
    if seg and not seg[0][0]:
        return seg[::-1] if seg[-1][0] else seg[1:]
    return seg
