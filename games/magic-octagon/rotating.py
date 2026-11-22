"""The reeded coin of coin.py, with halves that turn against each other and lock
every 45 degrees. Locked, it looks and handles like the glued coin; a strong
magnet frees the lock.

The halves are held together by a hub: a flanged post, trapped in the gold
half's cavity by a ring glued over it, and glued into a socket in the black
half. Both glue joints are inside, so the edge shows only the one seam. A
steel wave washer (6 x 12 x 0.3) between ring and flange draws the halves
together, face on face, so that nothing rattles; the ring stands into the
black half to make room for it.

The lock comes two ways, to try both:

- radial: a printed wedge with a 2x6 steel dowel pin pressed into it lies
  across the seam, in a channel of the gold half that narrows toward the
  centre. A 2x2 magnet inboard of it, glued in a slot of the ring, draws it
  in, into one of eight notches in the black half. Channel and notch are one
  taper across the seam, so the wedge jams in both halves at once and leaves
  no play. A magnet held to the rim at the wedge draws it out, into the wide
  of the channel and a groove that runs all the way round.
- axial: a printed plunger, a cone with a 3x1 magnet in it, in a sleeve glued
  into the gold half. The sleeve's bore and each of the black half's eight
  seats are one cone across the seam, so the plunger, drawn into a seat by the
  3x1 magnet beyond it (all eight the same way up), wedges in both halves at
  once and leaves no play. The plunger's roof is the plastic between the
  magnets. Laying the coin gold face down on a magnet draws the plunger back,
  into the wide end of the sleeve; the magnet has to be the right way up.

Assembly: hub into the gold half's cavity, flange down, washer on its stem;
glue the ring over them, sparingly and at its outer edge, held down against
the washer until it sets, and see that the hub still turns. Radial: glue the
magnet into the ring's slot; pin into the wedge, and the wedge in, pin down.
Axial: glue the black half's magnets in, and one to the top of the plunger's
pocket; plunger into the sleeve from its wide end, and glue the sleeve into
the gold half. Then a little gel glue in the black half's socket, and press it
on.

In a half's own frame the face is at z = 0 and the seam side is up.

"radial" and "axial" are the prints, each the coin with its lock, and each
has a view of it put together, to cut through or take apart in FreeCAD.
"""

from math import atan, degrees, hypot, radians, tan

from build123d import (
    Axis,
    Circle,
    Location,
    Part,
    Polygon,
    Pos,
    Rectangle,
    Rot,
    Sketch,
    chamfer,
    extrude,
)

from build.cad import Object, Piece, View, part, project, sketch
from designs.coin import (
    ARROW_COLORS,
    FILAMENTS,
    HALF_COLORS,
    HALVES,
    INLAY,
    Coin,
    D,
    arrow_settings,
    half_settings,
    up,
)

LOCKS = ("radial", "axial")

# Coin

# Thicker than coin.py's 2.5, for the washer's height.
half_t = 3

# Hub

stem_d = 5.6
flange_d = 12.4
flange_t = 0.6
ring_d = 18
ring_t = 0.6
# How much of the ring is in the gold half; the rest stands into the black.
ring_down = 0.2
# The wave washer, and the height it is squeezed to, between ring and flange:
# lower presses the halves together harder. As measured, and squeezed about
# half of the way to flat.
washer_id = 6.1
washer_od = 11.82
washer_t = 0.3
washer_free = 1.8
spring_h = 1
# What is glued into the gold half sits this far under the seam, clear of the
# other half.
ring_sink = 0.05
# Under the flange, and around the stem and the ring.
play = 0.1
# How far the stem goes into the black half, from the seam.
socket_depth = 2
socket_c = 0.15
# A wider mouth on the socket, to stop glue creeping up the stem.
trap = 0.5
trap_depth = 0.3
ribs = 3
rib_w = 0.8
rib_press = 0.1
stem_chamfer = 0.3

# Lock

# How the sides of the wedge and of the plunger lean. Steeper is less fussy
# about the print's size, but lets a twist push them out.
taper = 12

# Radial lock

pin_d = 2
pin_l = 6
# How far the wedge moves, and how far it reaches into a notch.
travel = 1.2
# From the magnet to the wedge and its pin, seated: sets how hard it is held.
hold_gap = 0.6
hold_d = 2
hold_l = 2
# The wedge: beside the pin at its narrow end, beyond the pin at its wide
# one, and how far it stands into each half. The pin lies under a roof, in
# the gold half's side.
wedge_wall = 0.6
wedge_end = 0.6
wedge_up = 1
wedge_down = 1.6
# Added to the width of the channel and the notches. A tenth here moves where
# the wedge stops by a quarter of a millimetre: wider seats it further in.
wedge_fit = 0
# Each side of the magnet.
lock_c = 0.1
# More room where the other half only has to clear what turns past.
sweep_c = 0.2
# Where the wedge is, from the gold arrow: behind its tail.
pin_a = 180

# Axial lock

# The magnets: the plunger's, and the eight that hold it.
apin_d = 3
apin_t = 1
ahold_d = 3
ahold_t = 1
# How wide the cone is at the seam.
cone_d0 = 4.3
# Added to the width of the sleeve's bore and of the seats. A tenth here moves
# where the plunger stops by a quarter of a millimetre: wider seats it deeper.
cone_fit = 0
# How far the plunger reaches across the seam, and how much further it could.
engage = 0.7
seat_extra = 0.25
# Over the plunger's magnet: the plastic between it and the one that holds it.
roof = 0.4
sleeve_wall = 0.8
# What the gold half keeps under the sleeve, over the arrow's inlay.
floor_a = 0.45
apin_r = 13
# Behind the gold arrow's tail, as the wedge is.
apin_a = 180

# Every 45 degrees the halves' bumps line up again.
coin = Coin("knurled", half_t=half_t)
steps = 8

seat_r = ring_d / 2 + play
# The black half's room for the ring.
recess_b = ring_t - ring_down + play
cav_r = flange_d / 2 + 3 * play
cav_depth = ring_down + spring_h + flange_t + play
stem_l = ring_down + spring_h + socket_depth
assert washer_id > stem_d and flange_d >= washer_od, "the washer doesn't fit the hub"
assert washer_t < spring_h < washer_free, "the washer isn't squeezed, or is crushed"

lock_r = seat_r + hold_gap
hold_in = seat_r - hold_l - 2 * lock_c
free_r = lock_r + travel
wedge_l = pin_l + wedge_end
wedge_h = wedge_up + wedge_down
slope = tan(radians(taper))


def wedge_w(r: float) -> float:
    """The wedge's width, seated, this far from the centre."""
    return pin_d + 2 * wedge_wall + 2 * (r - lock_r) * slope


# What its outer corners sweep, drawn out.
sweep_r = hypot(free_r + wedge_l, wedge_w(lock_r + wedge_l) / 2) + sweep_c


def cone_d(s: float) -> float:
    """The cone's width, this far from the seam into the gold half."""
    return cone_d0 + 2 * s * slope


pocket_depth = half_t - INLAY - floor_a
sleeve_h = pocket_depth - ring_sink
sleeve_d = cone_d(pocket_depth) + cone_fit + 2 * sleeve_wall
# Drawn back, the plunger stands on the pocket's floor, clear of the seam.
plunger_h = pocket_depth - 0.15
# Where its base is when it is seated.
seated = plunger_h - engage
seat_depth_b = engage + seat_extra

# The thinnest floors, all over an arrow's inlay: under the cavity, and under
# the axial lock's magnets. The sleeve's is floor_a.
floor_hub = min(half_t - INLAY - cav_depth, half_t - INLAY - socket_depth)
floor_hold = half_t - INLAY - seat_depth_b - ahold_t - 0.05
eps = 0.01
assert floor_hub >= 0.4 - eps, "the cavity leaves too little under the arrow"
assert floor_hold >= 0.4 - eps, "the magnets leave too little under them"
assert apin_r - sleeve_d / 2 >= seat_r + 0.4, "the sleeve is too near the ring"
assert cone_d(seated - plunger_h + roof) >= apin_d + 1, "the plunger's wall is too thin"
assert hold_in >= cav_r + 0.4 - eps, "the magnet's slot breaks into the cavity"
assert sweep_r + 1.5 <= D / 2, "the wedge's groove is too near the rim"


# Cut from the seam side of a half


def bore(r: float, depth: float) -> Part:
    return up(Sketch() + Circle(r), half_t - depth, depth + 1)


def groove_2d(r0: float, r1: float) -> Sketch:
    return sketch(Sketch() + Circle(r1) - Circle(r0))


def box_2d(x0: float, x1: float, w: float) -> Sketch:
    """From x0 to x1 along +x, w wide."""
    return Pos((x0 + x1) / 2) * Rectangle(x1 - x0, w)


def cone(d0: float, d1: float, h: float, below: float = 0) -> Part:
    """From d0 wide at z = 0 to d1 at h, to cut: drawn on a millimetre past h,
    and `below` past 0, at the same slope."""
    k = (d1 - d0) / h / 2
    return Pos(0, 0, -below) * extrude(
        Circle(d0 / 2 - below * k), h + below + 1, (0, 0, 1), taper=-degrees(atan(k))
    )


def taper_2d(r0: float, r1: float, fit: float = 0) -> Sketch:
    """The wedge's outline along +x, seated, from r0 to r1; `fit` wider."""

    def w(r: float) -> float:
        return (wedge_w(r) + fit) / 2

    return sketch(
        Sketch() + Polygon((r0, w(r0)), (r1, w(r1)), (r1, -w(r1)), (r0, -w(r0)))
    )


# The halves


def half_a(lock: str) -> Part:
    """The gold half: the hub's cavity and the ring's seat, and the lock's
    moving part."""
    cuts = [up(coin.arrow_2d(0), -1, 1 + INLAY), bore(cav_r, cav_depth)]
    cuts.append(bore(seat_r, ring_down))
    if lock == "radial":
        channel = up(
            taper_2d(seat_r - eps, free_r + wedge_l + lock_c, wedge_fit),
            half_t - wedge_down - 0.05,
            wedge_down + 1,
        )
        slot = up(
            box_2d(hold_in, seat_r, hold_d + 2 * lock_c),
            half_t - hold_d / 2 - lock_c,
            hold_d,
        )
        cuts.append(Rot(0, 0, pin_a) * (channel + slot))
    else:
        at = Rot(0, 0, apin_a) * Pos(apin_r, 0)
        cuts.append(at * bore(sleeve_d / 2 + 0.05, pocket_depth))
    return part(coin.blank() - cuts)


def socket() -> Part:
    """The stem's socket, crush ribs below a glue trap, under the ring's room."""
    r = stem_d / 2 + socket_c
    rib_h = socket_depth - recess_b - trap_depth
    ribbed = (
        Sketch()
        + Circle(r)
        - [
            Rot(0, 0, k * 360 / ribs)
            * Pos(stem_d / 2 - rib_press + 0.5)
            * Rectangle(1, rib_w)
            for k in range(ribs)
        ]
    )
    return part(
        up(ribbed, half_t - socket_depth, rib_h)
        + bore(r, socket_depth - rib_h)
        + bore(r + trap, recess_b + trap_depth)
        + bore(seat_r + sweep_c, recess_b)
    )


def at_detent(i: int) -> Location:
    """At the axial lock's seat i, in the black half's frame."""
    return Rot(0, 0, -apin_a + i * 360 / steps) * Pos(apin_r, 0)


def half_b(lock: str) -> Part:
    """The black half, in its own frame. What locks is the same every 45
    degrees, so its being flipped over is no matter."""
    cuts = [up(coin.arrow_2d(1), -1, 1 + INLAY), socket()]
    if lock == "radial":
        # Round the magnet, which stands half out of the ring.
        hold = groove_2d(hold_in - sweep_c, seat_r + sweep_c)
        cuts.append(up(hold, half_t - hold_d / 2 - sweep_c, hold_d))
        # Round the wedge, drawn out, and the notches it's drawn into.
        notch = taper_2d(seat_r, free_r, wedge_fit)
        sweep = groove_2d(free_r - eps, sweep_r) + [
            Rot(0, 0, pin_a + i * 360 / steps) * notch for i in range(steps)
        ]
        cuts.append(up(sweep, half_t - wedge_up - sweep_c, wedge_up + 1))
    else:
        seat = Pos(0, 0, half_t - seat_depth_b) * cone(
            cone_d(-seat_depth_b) + cone_fit, cone_d(0) + cone_fit, seat_depth_b
        )
        hold = bore(ahold_d / 2 + 0.05, seat_depth_b + ahold_t + 0.05)
        cuts += [at_detent(i) * part(seat + hold) for i in range(steps)]
    return part(coin.blank() - cuts)


# The hardware, each as printed


def wedge() -> Part:
    """Roof down, the pin's slot open above, and open at the narrow end, where
    the pin's end faces the magnet."""
    body = up(taper_2d(lock_r, lock_r + wedge_l), 0, wedge_h)
    slot = box_2d(lock_r - 1, lock_r + pin_l + 0.1, pin_d)
    return part(body - up(slot, wedge_h - pin_d - 0.05, pin_d + 1))


def sleeve() -> Part:
    """As it sits in the gold half: wide end down."""
    bore = cone(
        cone_d(pocket_depth) + cone_fit, cone_d(ring_sink) + cone_fit, sleeve_h, 1
    )
    return part(extrude(Circle(sleeve_d / 2), sleeve_h) - bore)


def plunger() -> Part:
    """Wide end down. Its magnet goes to the top of its pocket."""
    body = extrude(Circle(cone_d(seated) / 2), plunger_h, (0, 0, 1), taper=taper)
    return part(
        body - up(Sketch() + Circle(apin_d / 2 + 0.05), -1, plunger_h - roof + 1)
    )


def ring(lock: str) -> Part:
    """One flat side down. The radial lock's magnet goes through it."""
    shape = Sketch() + Circle(ring_d / 2) - Circle(stem_d / 2 + play)
    if lock == "radial":
        shape -= Rot(0, 0, pin_a) * box_2d(
            hold_in, hold_in + ring_d, hold_d + 2 * lock_c
        )
    return extrude(sketch(shape), ring_t)


def hub() -> Part:
    """Flange down."""
    stem = extrude(Circle(stem_d / 2), flange_t + stem_l)
    stem = chamfer(stem.faces().sort_by(Axis.Z).last.edges(), stem_chamfer)
    return part(extrude(Circle(flange_d / 2), flange_t) + stem)


def washer() -> Part:
    """Squeezed to spring_h."""
    return extrude(
        sketch(Sketch() + Circle(washer_od / 2) - Circle(washer_id / 2)), spring_h
    )


def cylinder(d: float, h: float) -> Part:
    return extrude(Circle(d / 2), h)


# Put together, each half's face at z = 0, the gold's down and the black's up.
top = Pos(0, 0, 2 * half_t) * Rot(180, 0, 0)


def bed(x: float, y: float = 0) -> Pos:
    return Pos(x * (D + 5), -y * (D + 5))


def printed(lock: str) -> list[Piece]:
    """What's printed, each where it sits and where it's printed: both halves
    face down, their arrows, and the lock's parts beside them."""
    gold = HALF_COLORS[0]
    pieces = [
        Piece(
            half,
            f"half {i}",
            HALF_COLORS[i],
            FILAMENTS[i],
            half_settings(coin.shape),
            parent=HALVES[i],
            at=at,
            place=bed(i),
        )
        for i, (half, at) in enumerate(
            [(half_a(lock), Location()), (half_b(lock), top)]
        )
    ]
    pieces += [
        Piece(
            coin.arrow(i),
            f"arrow {i}",
            ARROW_COLORS[i],
            FILAMENTS[1 - i],
            arrow_settings(coin.angles[i]),
            parent=HALVES[i],
            at=at,
            place=bed(i),
        )
        for i, at in enumerate([Location(), top])
    ]
    pieces += [
        Piece(
            ring(lock),
            "ring",
            gold,
            parent="lock",
            at=Pos(0, 0, half_t - ring_down),
            place=bed(0, 0.75),
        ),
        Piece(
            hub(),
            "hub",
            gold,
            parent="lock",
            at=Pos(0, 0, half_t - cav_depth + play),
            place=bed(1, 0.75),
        ),
    ]
    if lock == "radial":
        on = Rot(0, 0, pin_a) * Pos(0, 0, half_t)
        at = on * Pos(0, 0, wedge_up) * Rot(180, 0, 0)
        place = bed(0.5, 0.75) * Rot(0, 0, 90) * Pos(-lock_r)
        pieces.append(Piece(wedge(), "wedge", gold, at=at, place=place, parent="lock"))
    else:
        on = Rot(0, 0, apin_a) * Pos(apin_r, 0)
        pieces += [
            Piece(
                sleeve(),
                "sleeve",
                gold,
                parent="lock",
                at=on * Pos(0, 0, half_t - pocket_depth),
                place=bed(0.3, 0.75),
            ),
            Piece(
                plunger(),
                "plunger",
                gold,
                parent="lock",
                at=on * Pos(0, 0, half_t - seated),
                place=bed(0.6, 0.75),
            ),
        ]
    return pieces


def bought(lock: str) -> list[Piece]:
    """What's bought, where it sits, to show: the washer, and the lock's pin
    and magnets."""
    steel, magnet = "silver", "dimgray"
    washer_at = Pos(0, 0, half_t - ring_down - spring_h)
    pieces = [Piece(washer(), "washer", steel, at=washer_at, parent="lock")]
    if lock == "radial":
        on = Rot(0, 0, pin_a) * Pos(0, 0, half_t)
        along_x = Rot(0, 90, 0)
        pin_z = pin_d / 2 + 0.05 - wedge_down
        pin = on * Pos(lock_r, 0, pin_z) * along_x * cylinder(pin_d, pin_l)
        hold = on * Pos(seat_r - hold_l) * along_x * cylinder(hold_d, hold_l)
        pieces += [
            Piece(pin, "pin", steel, parent="lock"),
            Piece(hold, "magnets", magnet, parent="lock"),
        ]
    else:
        on = Rot(0, 0, apin_a) * Pos(apin_r, 0)
        pin = Pos(0, 0, half_t + engage - roof - apin_t) * cylinder(apin_d, apin_t)
        # The black half's, one at each of its seats.
        hold = Pos(apin_r, 0, half_t + seat_depth_b) * cylinder(ahold_d, ahold_t)
        holds = [Rot(0, 0, apin_a + i * 360 / steps) * hold for i in range(steps)]
        pieces.append(Piece(part(on * pin + holds), "magnets", magnet, parent="lock"))
    return [p.sitting() for p in pieces]


# Views


views = {
    f"{lock}-assembly": View(
        lambda coins, lock=lock: coins[lock] + bought(lock),
        "Locked, with what's bought",
        [lock],
    )
    for lock in LOCKS
}

project(
    __file__,
    objects={
        lock: Object(
            lambda lock=lock: printed(lock), f"The {lock} lock's coin, face down"
        )
        for lock in LOCKS
    },
    views=views,
    plates=[["radial"], ["axial"]],
)
