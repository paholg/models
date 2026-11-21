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
    and whether it's turned a quarter, which it is only where it fits on a plate
    no other way. The best of many orders: biggest first, then shuffled ones.
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
    leaves the least of the free rectangle it best fits (MaxRects): as it is, if
    it fits that way, and turned only if not."""
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
            for a, b, turned in ((w, h, False), (h, w, True)):
                fits = [
                    (min(fw - a, fh - b), fx, fy, a, b, turned)
                    for fx, fy, fw, fh in free
                    if a <= fw + 1e-6 and b <= fh + 1e-6
                ]
                if fits:
                    break
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


def heads(sets: list[list[str]]) -> dict[str, int]:
    """A tool head for each color, the same one wherever it's used.

    `sets` are the colors that print together: each part's, and each plate's.
    Colors that do take different heads. The most used pick first, and each
    takes the head with the fewest colors on it, so that as few as can be share
    one, and the filament on it changes between plates as little as can be.
    """
    order = sorted(
        dict.fromkeys(c for s in sets for c in s),
        key=lambda c: -sum(c in s for s in sets),
    )
    out: dict[str, int] = {}
    for c in order:
        taken = {out[d] for s in sets if c in s for d in s if d in out}
        load = [sum(h == k for h in out.values()) for k in range(1, FILAMENTS + 1)]
        free = [k for k in range(1, FILAMENTS + 1) if k not in taken]
        if not free:
            print(
                f"  warning: no filament free for {c}, of {len(order)} colors for {FILAMENTS}; it goes on filament 1"
            )
        out[c] = min(free, key=lambda k: load[k - 1]) if free else 1
    return out
