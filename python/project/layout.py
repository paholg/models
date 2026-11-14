"""Lay parts out on plates, and share the tool heads out among their colors."""

import random
import sys

# The U1's tool heads.
FILAMENTS = 4
# The U1's bed, and how Orca spaces its plates: a fifth of the bed apart.
BED = (270.0, 270.0)
PLATE_STRIDE = 1.2
# Around a plate's parts, and between them.
PLATE_MARGIN = 3.0
PLATE_GAP = 5.0
# Orders to try packing a group's parts in.
PACK_TRIES = 300


def pack(group: list[str], sizes: dict[str, tuple[float, float]]) -> list[list[tuple]]:
    """Lay a group's parts out on as few plates as it can.

    Returns each plate's (part, x, y, turned): where the part's box goes on the bed,
    and whether it's turned a quarter. The best of many orders: biggest first, then
    shuffled ones.
    """
    rng = random.Random(0)
    orders = [
        sorted(group, key=lambda p: -max(sizes[p])),
        sorted(group, key=lambda p: -sizes[p][0] * sizes[p][1]),
    ]
    orders += [rng.sample(group, len(group)) for _ in range(PACK_TRIES)]
    return min((pack_in_order(o, sizes) for o in orders), key=len)


def pack_in_order(
    group: list[str], sizes: dict[str, tuple[float, float]]
) -> list[list[tuple]]:
    """Lay parts out in the order given, each on the first plate with room, where it
    leaves the least of the free rectangle it best fits (MaxRects)."""
    room = [BED[k] - 2 * PLATE_MARGIN + PLATE_GAP for k in (0, 1)]
    plates: list[tuple[list, list]] = []  # each one's free rectangles, and its parts
    for part in group:
        w, h = (v + PLATE_GAP for v in sizes[part])
        if not any(a <= room[0] and b <= room[1] for a, b in ((w, h), (h, w))):
            sys.exit(f"{part} is too big for the bed: {sizes[part]}")
        for n in range(len(plates) + 1):
            if n == len(plates):
                plates.append(([(0.0, 0.0, *room)], []))
            free, placed = plates[n]
            fits = [
                (min(fw - a, fh - b), fx, fy, a, b, turned)
                for fx, fy, fw, fh in free
                for a, b, turned in ((w, h, False), (h, w, True))
                if a <= fw + 1e-6 and b <= fh + 1e-6
            ]
            if fits:
                break
        _, x, y, a, b, turned = min(fits)
        placed.append((part, x, y, turned))
        # Cut what it covers out of every free rectangle, and drop those inside others.
        cut = []
        for fx, fy, fw, fh in free:
            if x >= fx + fw or x + a <= fx or y >= fy + fh or y + b <= fy:
                cut.append((fx, fy, fw, fh))
                continue
            if x > fx:
                cut.append((fx, fy, x - fx, fh))
            if x + a < fx + fw:
                cut.append((x + a, fy, fx + fw - x - a, fh))
            if y > fy:
                cut.append((fx, fy, fw, y - fy))
            if y + b < fy + fh:
                cut.append((fx, y + b, fw, fy + fh - y - b))
        free[:] = [
            r
            for i, r in enumerate(cut)
            if not any(
                j != i
                and (
                    o[0] <= r[0]
                    and o[1] <= r[1]
                    and o[0] + o[2] >= r[0] + r[2]
                    and o[1] + o[3] >= r[1] + r[3]
                )
                and (o != r or j < i)
                for j, o in enumerate(cut)
            )
        ]
    out = []
    for _free, placed in plates:
        # Centered on the bed.
        spans = [
            (x, y, x + sizes[p][turned], y + sizes[p][not turned])
            for p, x, y, turned in placed
        ]
        dx = (BED[0] - max(s[2] for s in spans) - min(s[0] for s in spans)) / 2
        dy = (BED[1] - max(s[3] for s in spans) - min(s[1] for s in spans)) / 2
        out.append([(p, x + dx, y + dy, turned) for p, x, y, turned in placed])
    return out


def loadouts(plates: list[list[str]]) -> list[dict[str, int]]:
    """Which tool head each plate's colors go on, changing as few as can be.

    A color stays where it is while it's loaded; a new one takes an empty head, or
    else the place of the color that's needed again last.
    """
    heads: list[str | None] = [None] * FILAMENTS
    out = []
    for i, colors in enumerate(plates):
        if len(colors) > FILAMENTS:
            print(
                f"  warning: plate {i + 1} has {len(colors)} colors for {FILAMENTS} filaments; extras go on filament 1"
            )
        colors = colors[:FILAMENTS]

        def next_use(c: str | None, i: int = i) -> int:
            return next(
                (j for j in range(i + 1, len(plates)) if c in plates[j]), len(plates)
            )

        for c in colors:
            if c not in heads:
                spare = [k for k, h in enumerate(heads) if h not in colors]
                k = max(spare, key=lambda k: (heads[k] is None, next_use(heads[k]), -k))
                heads[k] = c
        out.append({c: heads.index(c) + 1 for c in colors})
    return out
