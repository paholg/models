"""Lay the special tiles out on their two boards and write special_layout.json,
which insert.py reads, rather than packing the tiles each time it draws.

Run: just python games/feast-for-odin/pack_special.py

The forge board sits left of the others, side by side; both boards' sizes are
fixed. The shapes are read from manifest.md.

The tiles are spread over each board with the widest gap that fits: the same
gap between pockets, from a pocket to the board's edge (whose corners are
rounded, for room to lift it out of the box) and to the forge board's icon.
For a given gap, greedy bottom-left packing on a 0.5 mm raster, each tile's
footprint its cells grown by the pocket clearance plus half the gap; the gap
is the widest for which some order of the tiles packs. The pack is then
centered as far as it can be. Tiles may rotate, not flip.

What it writes, for each board: its size as packed, which insert.py centers
on the board it draws, the gap, and each tile's cells, as [col, row], and
where its cell origin is on the board, in mm.
"""

import json
import random
from pathlib import Path

import numpy as np

UNIT = 11.0
CLEAR = 0.4  # pocket clearance around the tile
RES = 0.5  # mm per raster pixel
MARGIN = 2.0  # a board is its section and this each side: 2, so the two fit
FORGE_W = 86.0  # the sections' widths
OTHERS_W = 209.0
BOARD_Y = 215.0  # the boards' depth
CORNER_R = 45.0  # the boards' corners' radius
# The forge board's icon, [x0, y0, x1, y1] on the board: forge_icon_at and
# forge_icon_w in insert.py.
ICON = [29.0, 14.3, 61.0, 41.7]
GAPS = np.arange(2.0, 30.01, 0.25)  # the gaps to try
ORDERS = 24  # tile orders to try per gap


def shapes_text():
    """The two sections' ASCII shapes, from the manifest's "Special tiles"."""
    text = Path(__file__).with_name("manifest.md").read_text()
    text = text[text.index("### Special tiles") : text.index("## Misc")]
    forge, others = text.split("The others:")
    return forge[forge.index("icon):") + len("icon):") :], others


def parse(text):
    """ASCII blocks -> list of cell sets, (col, row) with row 0 at the bottom."""
    shapes = []
    for block in text.strip("\n").split("\n\n"):
        lines = [line.rstrip() for line in block.split("\n")]
        h = len(lines)
        shapes.append(
            {
                (c, h - 1 - r)
                for r, line in enumerate(lines)
                for c, ch in enumerate(line)
                if ch == "x"
            }
        )
    return shapes


def normalize(cells):
    mx = min(c for c, _ in cells)
    my = min(r for _, r in cells)
    return {(c - mx, r - my) for c, r in cells}


def rotate(cells):
    return normalize({(r, -c) for c, r in cells})


def raster(cells, gap):
    """Footprint raster in pixels: the cells grown by clearance plus half the
    gap. Also the offset from its origin to the tile's cell origin, in mm."""
    m = CLEAR + gap / 2
    w = (max(c for c, _ in cells) + 1) * UNIT
    h = (max(rr for _, rr in cells) + 1) * UNIT
    img = np.zeros(
        (int(np.ceil((h + 2 * m) / RES)), int(np.ceil((w + 2 * m) / RES))), bool
    )
    cell = int(np.ceil((UNIT + 2 * m) / RES))
    for c, rr in cells:
        x0 = int(c * UNIT / RES)
        y0 = int(rr * UNIT / RES)
        img[y0 : y0 + cell, x0 : x0 + cell] = True
    return img, m


def board(width, gap, keep_out):
    """A width x BOARD_Y board's raster: True where no footprint may go, which
    is within half a gap of its edge or of keep_out, a box or None."""
    yy, xx = np.mgrid[0 : int(BOARD_Y / RES), 0 : int(width / RES)]
    x, y = (xx + 0.5) * RES, (yy + 0.5) * RES
    r = CORNER_R
    dx = np.maximum(np.maximum(r - x, x - (width - r)), 0)
    dy = np.maximum(np.maximum(r - y, y - (BOARD_Y - r)), 0)
    grid = np.hypot(dx, dy) > r - gap / 2 - RES
    if keep_out:
        x0, y0, x1, y1 = keep_out
        g = gap / 2 + RES
        grid |= (x > x0 - g) & (x < x1 + g) & (y > y0 - g) & (y < y1 + g)
    return grid


def collisions(grid_f, shape, img):
    """Where img's origin can't go on the grid whose rfft2 is grid_f."""
    f = np.fft.irfft2(grid_f * np.conj(np.fft.rfft2(img, shape)), shape)
    return f[: shape[0] - img.shape[0] + 1, : shape[1] - img.shape[1] + 1] > 0.5


def pack(shapes, grid, gap, order):
    """Place every shape on the grid, bottom-left, or return None. Returns
    (cells, footprint, [x, y] of the footprint in pixels) each."""
    grid = grid.copy()
    placed = []
    for i in order:
        best = None
        cells = normalize(shapes[i])
        grid_f = np.fft.rfft2(grid)
        for _ in range(4):
            img, _m = raster(cells, gap)
            if img.shape[0] <= grid.shape[0] and img.shape[1] <= grid.shape[1]:
                free = ~collisions(grid_f, grid.shape, img)
                rows = np.flatnonzero(free.any(axis=1))
                if len(rows):
                    y = int(rows[0])
                    x = int(np.argmax(free[y]))
                    key = (y + img.shape[0], x)
                    if best is None or key < best[0]:
                        best = (key, set(cells), img, x, y)
            cells = rotate(cells)
        if best is None:
            return None
        _key, cells, img, x, y = best
        grid[y : y + img.shape[0], x : x + img.shape[1]] |= img
        placed.append((cells, img, [x, y]))
    return placed


def center(placed, grid):
    """Shift the whole pack toward the middle of the free part of the grid,
    as far as it stays clear."""
    free = np.argwhere(~grid)
    lo = np.array([min(p[2][k] for p in placed) for k in (0, 1)])
    hi = np.array([max(p[2][k] + p[1].shape[1 - k] for p in placed) for k in (0, 1)])
    want = (free.min(axis=0)[::-1] + free.max(axis=0)[::-1] + 1 - lo - hi) / 2
    for f in (1, 0.75, 0.5, 0.25):
        dx, dy = (int(np.round(v * f)) for v in want)
        ok = all(
            0 <= y + dy
            and 0 <= x + dx
            and y + dy + img.shape[0] <= grid.shape[0]
            and x + dx + img.shape[1] <= grid.shape[1]
            and not (
                grid[y + dy : y + dy + img.shape[0], x + dx : x + dx + img.shape[1]]
                & img
            ).any()
            for _c, img, (x, y) in placed
        )
        if ok:
            return [(c, img, [x + dx, y + dy]) for c, img, (x, y) in placed]
    return placed


def spread(shapes, width, keep_out=None):
    """Pack with the widest gap that works. Returns the gap and each tile's
    (cells, x, y), the cell origin in mm on the board."""
    rng = random.Random(0)
    by_size = sorted(range(len(shapes)), key=lambda i: -len(shapes[i]))
    orders = [by_size] + [rng.sample(by_size, len(by_size)) for _ in range(ORDERS - 1)]

    def attempt(gap):
        grid = board(width, gap, keep_out)
        for order in orders:
            placed = pack(shapes, grid, gap, order)
            if placed:
                return center(placed, grid)
        return None

    lo, hi, best = 0, len(GAPS) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        placed = attempt(GAPS[mid])
        if placed:
            best, lo = (float(GAPS[mid]), placed), mid + 1
        else:
            hi = mid - 1
    if best is None:
        raise SystemExit(f"nothing fits a width of {width}")
    gap, placed = best
    m = CLEAR + gap / 2
    return gap, [(c, x * RES + m, y * RES + m) for c, _img, (x, y) in placed]


def dump(boards):
    """The layout as JSON, a tile to a line."""
    out = ["{", f' "corner_r": {CORNER_R},', ' "boards": {']
    for i, (name, b) in enumerate(boards.items()):
        out.append(f'  "{name}": {{"size": {b["size"]}, "gap": {b["gap"]}, "tiles": [')
        out.append(",\n".join(f"   {json.dumps(t)}" for t in b["tiles"]))
        out.append("  ]}" + ("," if i < len(boards) - 1 else ""))
    return "\n".join([*out, " }", "}", ""])


def main():
    forge_text, others_text = shapes_text()
    boards = {}
    for name, width, text, keep_out in (
        ("forge", FORGE_W, forge_text, ICON),
        ("others", OTHERS_W, others_text, None),
    ):
        size = [width + 2 * MARGIN, BOARD_Y]
        gap, placed = spread(parse(text), size[0], keep_out)
        tiles = [
            {"cells": sorted(map(list, cells)), "at": [round(x, 2), round(y, 2)]}
            for cells, x, y in placed
        ]
        boards[name] = {"size": size, "gap": gap, "tiles": tiles}
    path = Path(__file__).with_name("special_layout.json")
    path.write_text(dump(boards))
    print(f"gaps: forge {boards['forge']['gap']}, others {boards['others']['gap']}")


if __name__ == "__main__":
    main()
