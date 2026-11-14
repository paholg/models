"""Pack the special tiles into a board and write special_layout.scad.

Run: just python game/feast-for-odin/pack_special.py [forge_w] [others_w]
(currently 86 209)

The forge section sits left of the others, side by side. The shapes are read
from manifest.md.

Greedy bottom-left packing on a 0.5 mm raster, into the shallowest block that
holds them. Each tile's footprint is its cells grown by the pocket clearance
plus half a wall, so neighbors never cut into each other. The block is
centered on its board, whose corners are rounded (for room to lift it out of
the box); the pockets keep clear of them. Tiles may rotate, not flip.
"""

import sys
from pathlib import Path

import numpy as np

UNIT = 11.0
CLEAR = 0.4  # pocket clearance around the tile
WALL = 2.0  # between pockets
NOTCH_R = 10.0
RES = 0.5  # mm per raster pixel
GAP = 4.0  # between the two sections
MARGIN = 2.0  # the board's edge past the pockets' block, across (special_margin)
BOARD_Y = 215.0  # the board's depth
CORNER_R = 45.0  # the board's corners' radius
CORNER_EDGE = 1.0  # more than half a wall between a pocket and a rounded corner


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
        shapes.append({(c, h - 1 - r) for r, line in enumerate(lines) for c, ch in enumerate(line) if ch == "x"})
    return shapes


def normalize(cells):
    mx = min(c for c, _ in cells)
    my = min(r for _, r in cells)
    return {(c - mx, r - my) for c, r in cells}


def rotate(cells):
    return normalize({(r, -c) for c, r in cells})


def notch(cells):
    """Finger notch on a bottom edge (no cell below), nearest the centroid's x.

    Returns (x, y) of its center in mm, on the tile's edge line.
    """
    cx = sum(c for c, _ in cells) / len(cells)
    edges = [(c, r) for c, r in cells if (c, r - 1) not in cells]
    c, r = min(edges, key=lambda e: (e[1], abs(e[0] + 0.5 - cx - 0.5)))
    return ((c + 0.5) * UNIT, r * UNIT - CLEAR)


def raster(cells, n):
    """Footprint raster in pixels: the cells grown by clearance plus half a
    wall."""
    m = CLEAR + WALL / 2
    w = (max(c for c, _ in cells) + 1) * UNIT
    h = (max(rr for _, rr in cells) + 1) * UNIT
    W = int(np.ceil((w + 2 * m) / RES))
    H = int(np.ceil((h + 2 * m) / RES))
    img = np.zeros((H, W), bool)
    cell = int(np.ceil((UNIT + 2 * m) / RES))
    for c, rr in cells:
        x0 = int(round(c * UNIT / RES))
        y0 = int(round(rr * UNIT / RES))
        img[y0 : y0 + cell, x0 : x0 + cell] = True
    # Offset from raster origin to the tile's cell origin, in mm.
    return img, (m, m)


def corners(width, height):
    """What the board's rounded corners take from a width x height block of
    pockets, centered on it: True where no footprint may go."""
    Wp, Hp = int(width / RES), int(height / RES)
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    x, y = xx * RES, yy * RES
    # The board's edges, in the block's coordinates.
    x0, x1 = -MARGIN, width + MARGIN
    y0, y1 = -(BOARD_Y - height) / 2, height + (BOARD_Y - height) / 2
    r = CORNER_R
    dx = np.maximum(np.maximum(x0 + r - x, x - (x1 - r)), 0)
    dy = np.maximum(np.maximum(y0 + r - y, y - (y1 - r)), 0)
    return np.hypot(dx, dy) > r - CORNER_EDGE


def pack(shapes, width, height):
    """Place every shape in a width x height block clear of the board's
    corners, or return None."""
    Wp = int(width / RES)
    grid = corners(width, height)
    placed = []
    order = sorted(range(len(shapes)), key=lambda i: -len(shapes[i]))
    for i in order:
        best = None
        cells = normalize(shapes[i])
        for rot in range(4):
            img, off = raster(cells, i)
            h, w = img.shape
            if w > Wp:
                cells = rotate(cells)
                continue
            for y in range(0, grid.shape[0] - h + 1):
                if best and y + h >= best[0]:
                    break
                found = None
                for x in range(0, Wp - w + 1):
                    if not (grid[y : y + h, x : x + w] & img).any():
                        found = x
                        break
                if found is not None:
                    best = (y + h, y, found, set(cells), img, off)
                    break
            cells = rotate(cells)
        if best is None:
            return None
        top, y, x, cells, img, off = best
        grid[y : y + img.shape[0], x : x + img.shape[1]] |= img
        placed.append((cells, x * RES + off[0], y * RES + off[1]))
    return placed


def pack_min(shapes, width):
    """Pack into the shallowest block that works, in steps."""
    for height in np.arange(60, BOARD_Y - 2 * MARGIN + 0.1, 2.5):
        placed = pack(shapes, width, height)
        if placed:
            return placed, float(height)
    sys.exit(f"nothing fits a width of {width}")


def main():
    forge_w = float(sys.argv[1]) if len(sys.argv) > 1 else 70
    others_w = float(sys.argv[2]) if len(sys.argv) > 2 else 225
    forge_text, others_text = shapes_text()
    forge, f_h = pack_min(parse(forge_text), forge_w)
    others, o_h = pack_min(parse(others_text), others_w)
    # Each block is centered on its board; in the file both are as deep as the
    # deeper, so center the shallower one in that.
    depth = max(f_h, o_h)
    forge = [(c, x, y + (depth - f_h) / 2) for c, x, y in forge]
    others = [(c, x, y + (depth - o_h) / 2) for c, x, y in others]
    out = [
        "// Generated by pack_special.py; do not edit.",
        f"special_size = [{forge_w + GAP + others_w}, {max(f_h, o_h):.2f}];",
        f"special_forge_w = {forge_w};",
        f"special_gap = {GAP};",
        f"special_notch_r = {NOTCH_R};",
        f"special_corner_r = {CORNER_R};",
        "// [section, [cells as [col, row]], [x, y] of cell origin, notch [x, y]]",
        "special_tiles = [",
    ]
    for sec, placed, dx in (("forge", forge, 0), ("others", others, forge_w + GAP)):
        for cells, x, y in placed:
            nx, ny = notch(cells)
            cs = ", ".join(f"[{c}, {r}]" for c, r in sorted(cells))
            out.append(f'    ["{sec}", [{cs}], [{x + dx:.2f}, {y:.2f}], [{x + dx + nx:.2f}, {y + ny:.2f}]],')
    out.append("];")
    path = Path(__file__).with_name("special_layout.scad")
    path.write_text("\n".join(out) + "\n")
    print(f"{forge_w} + {others_w}: forge {f_h:.1f}, others {o_h:.1f}", file=sys.stderr)


if __name__ == "__main__":
    main()
