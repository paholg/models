"""Jenga box in two three-sided halves.

The stacker is the back and right walls plus an end cap, a little shorter than
the tower. Cap up, it squares the tower in its back-right corner and slides
off. Cap down, it holds the blocks, and the lid (front and left walls plus the
other end cap) slides down onto it. A lip on the lid's back and right edges
covers the rest of the tower. The right one is a strip of its own, glued in:
slide it up from below, its pointed ends in the lid's notches, until it meets
the cap, then run thin CA along it inside.

The halves slide on two dovetail seams, each a 180° turn of the other: a
groove in one half's wall, and a tongue on the edge of the other half's. A
store-bought draw latch will hold the lid down, across the seam under the lip;
its screw holes are still to come.

Storage orientation: x is right, y is toward the front, z is up. The tower
stands on the stacker's cap at z = 0.

Print the stacker on its right side and the lid on its left, each at 45° to
fit the bed diagonally. Both grooves are then in a wall on the bed and face
up, and both tongues are the top edge of a standing wall: nothing in the joint
overhangs. The lip strip, which would be a bridge at the top of the lid, is
printed on its own, outside face down.

"joint" is a test to print first: lengths of groove and of tongue at the
clearances in joint_clears, printed as their walls are in the box.

The view "assembly" shows the box closed; `lid_raise` lifts the lid.
"""

from math import cos, radians, sqrt, tan

from build123d import (
    Align,
    Box,
    Cylinder,
    Part,
    Polygon,
    Pos,
    Rot,
    Solid,
    Vector,
    Vertex,
    Wire,
    extrude,
)

from build.cad import Object, Piece, project

# Views

# Lid height above closed, in the assembly view.
lid_raise = 0

# Tower

# Measure your own tower; sets vary.
tower_w = 75
tower_h = 270
# Per side.
tower_clear = 0.5
# How much shorter the stacker's walls are than the tower. The lid's lip makes
# up the rest.
stacker_short = 5

# Walls

wall = 4
cap_t = 2
# Each tongue rides in a dovetail groove in the other half's wall.
tongue_t = 1.6
groove_depth = 2
# Undercut angle on the groove's inner side.
dovetail = 30

# Edges

# Outer edges, and the inner edges at each half's open end.
chamfer = 1
# V-groove along the outside seams between the halves.
reveal = 0.5

# Fit

slide_clear = 0.2
# Chamfer on the tongue tips and groove mouths.
lead_in = 0.6
# Gap under the lid's walls, so that it's the seam under the lip that closes.
seat_gap = 0.2

# Lip strip

# How far each pointed end reaches into its notch.
lip_key = 1.5
# Clearance at each end.
lip_c = 0.1
# How far the crush ribs on the ends' flanks bite.
lip_crush = 0.1

# Tests

joint_clears = [0.15, 0.2, 0.3]
joint_len = 40

eps = 0.01
c = slide_clear
tb = tongue_t
gd = groove_depth
li = lead_in
t_dv = tan(radians(dovetail))

iw = tower_w + 2 * tower_clear
ih = tower_h + tower_clear
h = iw / 2
o = h + wall
z_s = tower_h - stacker_short
# Underside of the lid's cap.
z_a = ih + c
z_top = z_a + cap_t
# Bottom of the lid's walls.
z_l = seat_gap
# Middle of the right wall, where the lip strip's pointed ends are.
x_key = (h - c + o) / 2

assert tb + c + li < wall and gd + li < wall, (
    "tongue_t, groove_depth or lead_in too big for wall"
)

Pt = tuple[float, float]


def block(x: Pt, y: Pt, z: Pt) -> Part:
    return Pos(x[0], y[0], z[0]) * Box(
        x[1] - x[0], y[1] - y[0], z[1] - z[0], align=Align.MIN
    )


def prism(pts: list[Pt], z0: float, z1: float) -> Part:
    """A polygon, drawn up from z0 to z1."""
    # Up whichever way the polygon winds, which would otherwise turn its face down.
    return Pos(0, 0, z0) * extrude(Polygon(*pts, align=None), z1 - z0, (0, 0, 1))


def grown(pts: list[Pt], d: float) -> list[Pt]:
    """A convex polygon's sides each moved out by d, its corners kept sharp, in
    the same order: to loft to from the polygon."""
    n = len(pts)
    area = sum(
        pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
        for i in range(n)
    )
    sign = 1 if area > 0 else -1

    def normal(a: Pt, b: Pt) -> Vector:
        return Vector(sign * (b[1] - a[1]), -sign * (b[0] - a[0])).normalized()

    out = []
    for i, p in enumerate(pts):
        n1 = normal(pts[i - 1], p)
        n2 = normal(p, pts[(i + 1) % n])
        v = (n1 + n2) * (d / (1 + n1.dot(n2)))
        out.append((p[0] + v.X, p[1] + v.Y))
    return out


def taper(a: list[Pt], za: float, b: list[Pt], zb: float) -> Part:
    """From polygon a at za to polygon b at zb, corner to corner."""
    return Solid.make_loft(
        [Wire.make_polygon([(x, y, z) for x, y in p]) for p, z in ((a, za), (b, zb))],
        ruled=True,
    )


# Seam profiles: u (x) runs into the groove from its wall's inner face, s (y)
# across it, with the dovetail side negative. The tongue's dovetail side runs
# from its wall's corner at u = -c; the groove's is c from it.


def tongue_s(u: float, c: float) -> float:
    return -(u + c) * t_dv


def groove_s(u: float, c: float) -> float:
    return tongue_s(u, c) - c / cos(radians(dovetail))


def groove_pts(c: float) -> list[Pt]:
    return [
        (-eps, groove_s(-eps, c)),
        (gd, groove_s(gd, c)),
        (gd, tb + c),
        (-eps, tb + c),
    ]


def tongue_pts(c: float) -> list[Pt]:
    """Buried in its wall behind u = -c."""
    return [
        (-c - 1, tongue_s(-c - 1, c)),
        (gd - c, tongue_s(gd - c, c)),
        (gd - c, tb),
        (-c - 1, tb),
    ]


def at_seam(i: int):
    """Seam 0 is front-right: the groove in the stacker's right wall, the tongue
    on the lid's front wall. Seam 1 is back-left: the groove in the lid's left
    wall, the tongue on the stacker's back wall."""
    return Rot(0, 0, 180 * i) * Pos(h, h, 0)


def groove(z0: float, z1: float, mouth_up: bool, c: float = c) -> Part:
    """From z0 to z1, flared to a lead-in at its mouth: the top, or the bottom."""
    pts = groove_pts(c)
    wide = grown(pts, li)
    m, d = (z1, 1) if mouth_up else (z0, -1)
    return (
        prism(pts, z0, z1)
        + taper(pts, m - d * li, wide, m)
        + prism(wide, min(m, m + d), max(m, m + d))
    )


def tongue(z0: float, z1: float, lead_up: bool, c: float = c) -> Part:
    """From z0 to z1, narrowed to a lead-in at its leading end: the top, or the
    bottom."""
    pts = tongue_pts(c)
    tip = grown(pts, -li / 2)
    if lead_up:
        return prism(pts, z0, z1 - li) + taper(pts, z1 - li, tip, z1)
    return taper(tip, z0, pts, z0 + li) + prism(pts, z0 + li, z1)


def envelope() -> Part:
    """The closed box's outside, chamfered on every edge."""
    b = block((-o, o), (-o, o), (-cap_t, z_top))
    return b.chamfer(chamfer, None, b.edges())


def edge_cut(
    a: tuple[float, float, float], b: tuple[float, float, float], r: float
) -> Part:
    """Cuts a 45° chamfer of size r into the edges along a -> b, which runs
    along an axis, with pyramid ends so that cuts meeting at a corner join
    cleanly."""
    k = max(range(3), key=lambda i: abs(b[i] - a[i]))
    if b[k] < a[k]:
        a, b = b, a
    va, vb = Vector(*a), Vector(*b)
    axes = [Vector(*(1 if j == i else 0 for j in range(3))) for i in range(3)]
    along, p, q = axes[k], axes[(k + 1) % 3], axes[(k + 2) % 3]

    def diamond(v: Vector) -> Wire:
        return Wire.make_polygon([v + p * r, v + q * r, v - p * r, v - q * r])

    return Solid.make_loft(
        [Vertex(va - along * r), diamond(va), diamond(vb), Vertex(vb + along * r)],
        ruled=True,
    )


def reveals() -> Part:
    """Along every outside seam."""
    f = h - c / 2
    edges = [
        # Front: up the right wall's end, over it, and under the front wall.
        ((f, o, 0), (f, o, z_s)),
        ((f, o, z_s), (o, o, z_s)),
        ((-o, o, 0), (f, o, 0)),
        # Right: under the lip.
        ((o, -o, z_s), (o, o, z_s)),
        # Back: up the left wall's end, under the lip, and under the left wall.
        ((-f, -o, 0), (-f, -o, z_s)),
        ((-f, -o, z_s), (o, -o, z_s)),
        ((-o, -o, 0), (-f, -o, 0)),
        # Left: under the left wall.
        ((-o, -o, 0), (-o, o, 0)),
    ]
    return Part() + [edge_cut(a, b, reveal) for a, b in edges]


def stacker() -> Part:
    body = (
        block((-o, o), (-o, o), (-cap_t, 0))
        + block((-h + c, o), (-o, -h), (-cap_t, z_s))
        + block((h, o), (-o, o), (-cap_t, z_s))
        + at_seam(1) * tongue(-eps, z_s, True)
    )
    body -= at_seam(0) * groove(0, z_s, True)
    body -= reveals()
    # Inner top edges of the right and back walls.
    body -= edge_cut((h, -h, z_s), (h, h, z_s), chamfer)
    body -= edge_cut((-h - gd, -h, z_s), (h, -h, z_s), chamfer)
    return body & envelope()


def lip_point(sy: int, z0: float) -> Part:
    """A pointed end of the lip strip, at the back (sy = -1) or the front (1),
    from z0 up to the cap: a 45° point, so it prints in the strip and its notch
    in the lid."""
    pts = [(-lip_key - eps, -sy * eps), (0, sy * lip_key), (lip_key + eps, -sy * eps)]
    return Pos(x_key, sy * h) * prism(pts, z0, z_a)


def lid() -> Part:
    body = (
        block((-o, o), (-o, o), (z_a, z_top))
        # Lip over the stacker's back and right walls.
        + block((-o, o), (-o, -h), (z_s, z_top))
        + block((h - c, o), (h, o), (z_s, z_top))
        # Front and left walls.
        + block((-o, h - c), (h, o), (z_l, z_top))
        + block((-o, -h), (-o, o), (z_l, z_top))
        + at_seam(0) * tongue(z_l, z_top, False)
    )
    body -= at_seam(1) * groove(z_l, z_s + c, False)
    body -= lip_point(-1, z_s - eps) + lip_point(1, z_s - eps)
    body -= reveals()
    # Inner bottom edges of the front wall and its tongue, and of the left wall.
    body -= edge_cut((-h, h, z_l), (h + gd - c, h, z_l), chamfer)
    body -= edge_cut((-h, -h, z_l), (-h, h, z_l), chamfer)
    return body & envelope()


def lip_strip() -> Part:
    """The lip over the stacker's right wall. Ribs along each end's flanks crush
    into the notches and center it; they stop short of the top, to start it."""
    r = 0.4
    # A flank's gap to its notch, square to it.
    gap = lip_c / sqrt(2)
    bite = (gap + lip_crush - r) / sqrt(2)
    rib = Cylinder(r, z_a - z_s - 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = block((h - c, o), (-h + lip_c, h - lip_c), (z_s, z_a))
    for sy in (-1, 1):
        shift = Pos(0, -sy * lip_c)
        body += shift * lip_point(sy, z_s)
        for sx in (-1, 1):
            at = (x_key + sx * lip_key / 2 + sx * bite, sy * (h + lip_key / 2 + bite))
            body += shift * Pos(*at, z_s) * rib
    body -= reveals()
    return body & envelope()


def tower() -> Part:
    return block((-tower_w / 2, tower_w / 2), (-tower_w / 2, tower_w / 2), (0, tower_h))


# Prints


def stacker_print() -> Part:
    return Rot(0, 0, 45) * Pos(0, 0, o) * Rot(0, 90, 0) * stacker()


def lid_print() -> Part:
    return Rot(0, 0, 45) * Pos(0, 0, o) * Rot(0, -90, 0) * lid()


def strip_print() -> Part:
    """Outside face down: on the lid, it would be a bridge."""
    return Rot(0, 90, 0) * lip_strip()


def notches(i: int, length: float) -> Part:
    """A row of d = 2 notches, i + 1 of them, to tell the coupons apart."""
    return Part() + [
        Pos(0, 0, 5 + 3.5 * n) * Rot(-90, 0, 0) * Cylinder(1, length)
        for n in range(i + 1)
    ]


def joint_test() -> list[Piece]:
    """Coupon i's length of grooved wall, outside face on the bed, and beside it
    its length of tongued wall, standing."""
    back = 12
    pieces = []
    for i, jc in enumerate(joint_clears):
        at = Pos(0, i * (back + wall + 5), 0)
        grooved = (
            block((0, wall), (-back, wall), (0, joint_len))
            - groove(-1, joint_len, True, jc)
            - Pos(wall, -back, 0) * notches(i, 2 * wall)
        )
        tongued = (
            block((-jc - back, -jc), (0, wall), (0, joint_len))
            + tongue(0, joint_len, False, jc)
        ) - Pos(-jc - back, 0, 0) * notches(i, 3 * wall)
        pieces += [
            Piece(at * Pos(0, 0, wall) * Rot(0, 90, 0) * grooved, f"groove {jc}"),
            Piece(
                at * Pos(-5, 0, back) * Rot(0, -90, 0) * Pos(jc, 0, 0) * tongued,
                f"tongue {jc}",
            ),
        ]
    return pieces


# Views


def assembly() -> list[Piece]:
    up = Pos(0, 0, lid_raise)
    return [
        Piece(stacker(), "stacker", "white"),
        Piece(up * lid(), "lid", "lightgray"),
        Piece(up * lip_strip(), "lip strip", "gainsboro"),
        Piece(tower(), "tower", "burlywood"),
    ]


project(
    __file__,
    objects={
        "stacker": Object(stacker_print, "Back and right walls and an end cap"),
        "lid": Object(lid_print, "Front and left walls, the other end cap and a lip"),
        "strip": Object(strip_print, "The lid's right lip, glued in"),
        "joint": Object(joint_test, "Dovetail test pieces, one per clearance"),
    },
    views={"assembly": Object(assembly, "The box closed, around the tower")},
    plates=["stacker lid strip"],
)
