"""A card-sized score tracker for two players of The Fox in the Forest Deluxe,
to keep in the card box with the deck.

Each player has two tracks, sixes and ones, and a slider in each, with a rupee
on top whose point is over the score's label. The sliders ride in channels
under the face, their stems up through slots in it, keyed long so they can't
twist.

- The top: the face, with the slots, the numbers inlaid and the channels
  under it. It prints face down, so every slot and channel wall is a wall.
- The back: drops into a recess inside the top's rim and closes the channels,
  with pins into holes in the top. Glue it on away from the channels; two
  grooves around each channel catch the squeeze-out.
- The sliders: a plate riding in the channel, with a stem up through the slot.
  Printed plate down. Each clicks into place at every score one of two ways
  (`detent`):
  - magnets: a disc magnet glued into the plate's underside, over one sealed
    in the back at each score. The print pauses with the back's pockets open,
    to drop those in, then roofs them over. Put every magnet in the back the
    same way up, and glue the sliders' to attract them; wells around the
    sliders' pockets take the excess glue.
  - arms: a spring arm down each side of the plate, fixed at both ends and
    bent out into a round hump in the middle, which clicks into scallops in
    the channel walls.
- The rupees: press onto the stems after the back is glued on. Printed flat,
  socket down.

Put together: drop the sliders into the top's channels, glue on the back,
press on the rupees.

x is along the tracks, y is toward player 1's half, z is up, the card's
underside at z = 0. Everything reads from the -x long edge: player 1's sixes
and ones, then player 0's, left to right, each counting up away from the
reader. A slider and a rupee are drawn on their own about the z axis, the
slider's plate and the rupee's socket on z = 0, and the rupee's point toward
-y.

Each part is an object, and the four go on one plate, which pauses for the
back's magnets. "test" is three short tracks, at each of `test_bumps` for arms
or `test_lifts` for magnets, the dots on each counting from the first. The
views are the tracker put together, and pulled apart.
"""

from dataclasses import dataclass

from build123d import (
    Axis,
    Circle,
    Face,
    FontStyle,
    Kind,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    Sketch,
    Text,
    chamfer,
    extrude,
    fillet,
    loft,
    make_hull,
    mirror,
    offset,
)

from build.cad import Object, Piece, project

# Card

# A sleeved card, a little under the box's cavity.
card_x = 66
card_y = 92
card_r = 3
# Roundovers on the card's outside edges: around the face, and around the
# rim's underside, which has to stay under rim_w.
face_round = 1.5
rim_round = 0.6

# Face

face_t = 1.6
font = "TeX Gyre Bonum"
# The digits' height.
num_h = 4
num_depth = 0.6
pitch = 9
# Each track's places, 0 to 5 ones or sixes.
places = 6
# Half the band each track takes up across the card, and from there to its
# labels' ends. The rupee's point reaches past both, over the label.
band = 5.5
num_gap = 1

# Slider

detent = "magnets"  # or "arms"
# Clearance at the slider plate's ends.
c = 0.3
# Between the plate's sides and the channel walls; only the humps touch.
side_c = 0.2
# Total up-and-down play of the plate in its channel.
z_play = 0.4
# Thick enough for a floor under the magnets and a roof over them.
back_t = 1.7
# The top's rim around the back, which drops into the recess it leaves.
rim_w = 1.2
fit_c = 0.15
# Locating pins on the back, into holes in the top.
pin_d = 3
pin_h = 1.5
pin_chamfer = 0.4
# Grooves in the back around each channel catch glue before it reaches a
# slider.
moat_in = 0.5
moat_w = 0.5
moat_d = 0.7
# A second groove this far outside the first, wherever there's room for it,
# gives glue on the wider lands somewhere nearer to go.
moat_gap = 1
# The land left between any groove and the back's edge.
moat_edge = 0.3
# The back's edge on the bed, chamfered against elephant's foot.
back_foot = 0.3
plate_t = 1.5
# Plate size along and across the track.
plate_l = 14
plate_w = 11
plate_chamfer = 0.8
# The plate's edge on the bed, chamfered against elephant's foot, for magnets.
# With arms, the slits leave no room for it: see `arm_settings`.
plate_foot = 0.3
stem = 3.2
stem_chamfer = 0.4
# A long key on the stem, in the slot, keeps the slider from twisting. It
# stops this far under the face, short of the slot's chamfer.
key_l = 8
key_c = 0.25
key_short = 0.4
slot_chamfer = 0.4
# Each side has a spring arm fixed at both ends, so whichever way the slider
# moves, the half of the arm behind the hump pulls it along in tension; an
# arm with a free end buckles when it's pushed hump first. The arm itself
# bends out into a round hump in the middle, one line wide throughout, which
# lets it flex by bending rather than stretching: arm_t is one line only as
# `arm_settings` prints it.
arm_t = 0.45
arm_h = 1
slit_w = 0.6
arm_root = 1
# How far each hump reaches past the channel wall, so how far the arms flex.
engage = 0.35
# Outside radius of the hump; smaller is steeper, for a harder click.
hump_r = 3
# Rounds the hump into the arm either side.
hump_fillet = 1
notch_c = 0.15

# Magnets

# Disc magnets: diameter, thickness.
mag_d = 5
mag_t = 1
# Pocket clearance on the diameter.
mag_c = 0.2
# The channel floor over the back's magnets, printed after the pause. The back
# is set to 0.1 mm layers over a 0.2 mm first one (see `fine`), so every layer
# ends on a multiple of 0.1 and is sliced at its middle, 0.05 off one. With
# back_t one too, this puts the pockets' top and floor on layer ends, midway
# between slicing planes: on a plane, the slicer could take either side, and
# the pocket could lose a layer of its slack.
mag_roof = 0.3
# Height of the back's pockets over the magnets, so the nozzle clears them.
mag_slack = 0.1
# How far the slider's magnet sits above the plate's underside. With the
# roof, and the slack if the magnet stays down, the gap between the magnets:
# more is a softer click.
mag_lift = 0.2
# Wells around the slider's magnet pocket, for excess glue.
mag_well_d = 1.6
mag_wells = 4

# Rupee

# From the stem to its point, and the radius of its round end.
rupee_l = 7.5
rupee_h = 4.5
rupee_t = 3.5
rupee_wall = 1.2
rupee_bevel = 1.5
# Rounds the point, at every inset.
rupee_r = 1
rupee_lift = 0.5
socket_d = 2.5
# Socket clearance around the stem; the ribs then take up rib_press.
socket_c = 0.1
rib_press = 0.1
rib_w = 0.8
socket_chamfer = 0.4
# Glue wells down the socket's corners, past the stem's chamfered corners and
# below its tip, so glue has somewhere to go without holding the rupee up.
well_d = 1.2
well_extra = 0.4

# Test

test_bumps = [0.25, 0.35, 0.45]
# The sliders' mag_lift on each track, for magnets.
test_lifts = [0.2, 0.2, 0.2]
test_n = 3

arms = detent == "arms"
chan_d = plate_t + z_play
z_face = back_t + chan_d
top_h = z_face + face_t
# Stem from the plate's top to its tip in the socket.
stem_len = z_play + face_t + rupee_lift + socket_d
hs = stem / 2
hw = plate_w / 2
# Channel half-width, and the slits' inner edge, out from the middle.
cw = hw + side_c
y_core = hw - arm_t - slit_w
mag_hole = mag_d + mag_c
# The print pauses here, for the back's magnets: the top of their pockets.
pause = back_t - mag_roof

assert rim_round < rim_w, "rim rounded away"
assert face_round < face_t, "face roundover reaches the channels"
assert arm_h <= plate_t, "arms taller than the plate"
assert round(pause - mag_t - mag_slack, 6) >= 0.3, "back too thin under the magnets"
assert round(plate_t - mag_t - max(test_lifts), 6) >= 0.2, (
    "plate too thin over the magnet"
)
assert mag_hole + mag_well_d + 2 <= min(pitch, plate_w), (
    "magnets crowd each other or the plate's sides"
)
assert slit_w >= max(test_bumps) + 0.15, "slits too narrow for the arms to flex"
assert y_core >= hs + key_c + 1.2, "plate core too narrow to bear on the face"
assert rupee_t - socket_d >= 0.8, "rupee too thin over the socket"
assert rupee_t - socket_d - well_extra >= 0.5, "rupee too thin over the glue wells"


def digits(s: str, em: float = 1) -> Text:
    return Text(s, em, font, font_style=FontStyle.BOLD)


# The labels' size, for digits num_h high.
num_em = num_h / digits("0").bounding_box().size.Y
# Labels turn 90° to read from the card's long edge, so their rows are as
# deep as the widest label, the sixes' last, is long.
num_len = digits(str((places - 1) * 6), num_em).bounding_box().size.X
# Player 1's half, from the card's +y edge in: the sixes' row, then the
# ones', each its labels and then its track's band. The gaps at the edge,
# between the rows, and between the players (shared) are all equal. Player
# 0's half is the same, `half` lower.
row_gap = (card_y / 2 - 2 * (num_len + num_gap + 2 * band)) / 2.5
half = card_y / 2 - row_gap / 2
y_sixes = card_y / 2 - row_gap - num_len - num_gap - band
y_ones = y_sixes - band - row_gap - num_len - num_gap - band
assert row_gap >= 1.5, "rows too crowded"


@dataclass
class Track:
    """A slot and its channel: its score 0 at (x, y), counting up toward +x."""

    x: float
    y: float
    n: int
    step: int = 0  # what each place counts, for its labels; none for 0
    engage: float = engage
    lift: float = mag_lift

    def at(self, i: int) -> float:
        """Place i's x."""
        return self.x + i * pitch

    @property
    def span(self) -> float:
        return (self.n - 1) * pitch


def track(y: float, step: int) -> Track:
    """A track of the card, centered on it."""
    return Track(-(places - 1) * pitch / 2, y, places, step)


# Each player's ones and sixes.
tracks = [
    [track(y_ones - half, 1), track(y_sixes - half, 6)],
    [track(y_ones, 1), track(y_sixes, 6)],
]
card_tracks = [t for player in tracks for t in player]
# Pins, in each half: under the label rows between the tracks, at the ends,
# and in the strip between the sixes and the edge.
pins = [
    (sx * (card_x / 2 - 7), (y_ones + y_sixes) / 2 - dy)
    for dy in (half, 0)
    for sx in (-1, 1)
] + [(0, (card_y / 2 - rim_w + y_sixes + cw) / 2 - dy) for dy in (half, 0)]
assert pins[-1][1] - pin_d / 2 - fit_c - 1 > y_sixes + cw + moat_in + moat_w, (
    "pin crowds the sixes track"
)
# The two players' middle channels, with a moat each and some glue land.
assert row_gap - 2 * (cw - band) >= 2 * (moat_in + moat_w) + 0.4, (
    "middle channels too close"
)

# The test's tracks, spaced to fit a locating pin between each pair, clear of
# the moats.
test_dy = 2 * cw + 2 * (moat_in + moat_w) + pin_d + 2 * fit_c + 2
test_x = (test_n - 1) * pitch + plate_l + 8
test_y = 3 * test_dy + 2
test_tracks = [
    Track(-(test_n - 1) * pitch / 2, (k - 1) * test_dy, test_n, 0, bump, lift)
    for k, (bump, lift) in enumerate(zip(test_bumps, test_lifts))
]
test_pins = [(0, -test_dy / 2), (0, test_dy / 2)]


# Shapes


def up(face: Face | Sketch, z0: float, height: float) -> Part:
    """A face, drawn up from z0."""
    return Pos(0, 0, z0) * extrude(face, height, (0, 0, 1))


def grown(face: Face | Sketch, d: float, kind: Kind = Kind.INTERSECTION) -> Sketch:
    """Grown by d, or shrunk for a d below 0: its corners kept sharp, or with
    Kind.ARC the convex ones rounded."""
    return Sketch() + offset(face, d, kind=kind)


def bevelled(x: float, y: float, k: float) -> Polygon:
    """A rectangle about the origin, its corners cut off at 45°, k along each
    side."""
    a, b = x / 2, y / 2
    return Polygon(
        (a - k, -b),
        (a, -b + k),
        (a, b - k),
        (a - k, b),
        (-a + k, b),
        (-a, b - k),
        (-a, -b + k),
        (-a + k, -b),
    )


def stem_2d(g: float = 0) -> Sketch:
    return grown(bevelled(stem, stem, stem_chamfer), g)


def key_2d(g: float = 0) -> Sketch:
    return grown(bevelled(key_l, stem, stem_chamfer), g)


def rings(shapes: Sketch, gaps: list[float], w: float) -> Sketch:
    """A groove w wide around the shapes, at each of `gaps` out from them. One
    goes round them all, so it drops out where they're too close for it."""
    return Sketch() + [grown(shapes, g + w) - grown(shapes, g) for g in gaps]


# The detent arms and their scallops


def hump_2d(e: float, g: float = 0) -> Sketch:
    """The hump's outside, on the +y side of a plate edge at y = 0, for
    engagement e, grown by g."""
    circle = Pos(0, side_c + e - hump_r) * Circle(hump_r + g)
    return Sketch() + (circle & Pos(0, hump_r / 2) * Rectangle(2 * hump_r, hump_r))


def arm_2d(e: float) -> Sketch:
    """An arm, on the +y side of a plate edge at y = 0: one line wide, out of
    the edge into the hump, which is filleted into it either side."""
    outer = Sketch() + Pos(0, -2.5) * Rectangle(plate_l + 10, 5) + hump_2d(e)
    corners = [
        v for v in outer.vertices() if abs(v.Y) < 1e-6 and abs(v.X) < hump_r + 0.5
    ]
    outer = fillet(corners, hump_fillet)
    band = outer - grown(outer, -arm_t, Kind.ARC)
    zone = Pos(0, -arm_t / 2) * Rectangle(plate_l - 2 * arm_root + 0.02, arm_t + 2)
    return Sketch() + (band & zone)


def arm_zone(side: int) -> Sketch:
    """Where an arm and the slit behind it go, on side ±1."""
    zone = Pos(0, (y_core + hw + 2) / 2) * Rectangle(
        plate_l - 2 * arm_root, hw + 2 - y_core
    )
    return zone if side > 0 else mirror(zone, Plane.XZ)


def on_side(side: int, shape: Sketch) -> Sketch:
    """Something drawn on the +y side of a plate edge at y = 0, moved to the
    plate's side ±1."""
    moved = Pos(0, hw) * shape
    return moved if side > 0 else mirror(moved, Plane.XZ)


# The slider


def plate_2d() -> Sketch:
    """The slider plate's outline, less the arms' room."""
    shape = Sketch() + bevelled(plate_l, plate_w, plate_chamfer)
    if arms:
        shape -= [arm_zone(s) for s in (-1, 1)]
    return shape


def slider(e: float = engage, lift: float = mag_lift, marks: int = 0) -> Part:
    """Plate down, on z = 0, along x. `marks` dimples go in the plate's top
    beside the key, clear of the arms and the magnet, to tell test sliders
    apart."""
    body = extrude(plate_2d(), plate_t)
    if not arms:
        body = chamfer(body.faces().sort_by(Axis.Z).first.edges(), plate_foot)
    if arms:
        body += extrude(Sketch() + [on_side(s, arm_2d(e)) for s in (-1, 1)], arm_h)
    else:
        # The magnet's pocket, and wells around its edge, as deep: glue pushed
        # out from under the magnet ends up there, not on the plate's
        # underside.
        wells = [
            Rot(0, 0, 45 + i * 360 / mag_wells)
            * Pos(mag_hole / 2, 0)
            * Circle(mag_well_d / 2)
            for i in range(mag_wells)
        ]
        body -= up(Sketch() + Circle(mag_hole / 2) + wells, -1, 1 + mag_t + lift)
    y_mark = (hs + y_core) / 2 if arms else hw - 1.3
    body -= Part() + [
        Pos((j - (marks - 1) / 2) * 2, y_mark, plate_t - 0.4) * extrude(Circle(0.5), 1)
        for j in range(marks)
    ]
    key = up(key_2d(), plate_t, z_play + face_t - key_short)
    return body + key + up(stem_2d(), plate_t, stem_len)


# The top


def slab(x: float, y: float, r: float) -> Part:
    """The top's outside, its face rounded over, and lightly its rim."""
    body = extrude(RectangleRounded(x, y, r), top_h)
    body = fillet(body.faces().sort_by(Axis.Z).last.edges(), face_round)
    return fillet(body.faces().sort_by(Axis.Z).first.edges(), rim_round)


def channel_2d(t: Track) -> Sketch:
    """A track's channel, and for arms, a scallop for the hump at every place,
    for it to seat in with notch_c all round."""
    shape = Sketch() + Pos(t.x + t.span / 2, t.y) * Rectangle(
        t.span + plate_l + 2 * c, 2 * cw
    )
    if arms:
        scallop = [on_side(s, hump_2d(t.engage, notch_c)) for s in (-1, 1)]
        shape += [Pos(t.at(i), t.y) * f for i in range(t.n) for f in scallop]
    return shape


def slot_2d(t: Track) -> Sketch:
    """The slot the stem and its key run in."""
    return Pos(t.x + t.span / 2, t.y) * grown(
        bevelled(t.span + key_l, stem, stem_chamfer), key_c
    )


def label(s: str) -> Sketch:
    """Its end at the origin, centered on it, reading from -x toward -y."""
    text = digits(s, num_em)
    box = text.bounding_box()
    return Rot(0, 0, -90) * Pos(-box.max.X, -box.center().Y) * text


def labels_2d() -> Sketch:
    """Each place's score, on the +y side of its track."""
    return Sketch() + [
        Pos(t.at(i), t.y + band + num_gap) * label(str(i * t.step))
        for t in card_tracks
        for i in range(t.n)
    ]


def numbers() -> Part:
    """Inlaid in the face, flush."""
    return up(labels_2d(), top_h - num_depth, num_depth)


def top_body(x: float, y: float, r: float, ts: list[Track], at: list) -> Part:
    """The top, x by y, its corners r: with the recess for its back, the
    holes for its pins, and the tracks' channels and slots."""
    body = slab(x, y, r)
    cuts = [
        up(RectangleRounded(x - 2 * rim_w, y - 2 * rim_w, r - rim_w), -1, back_t + 1),
        *[Pos(*p) * up(Circle(pin_d / 2 + fit_c), 0, back_t + pin_h + 0.3) for p in at],
    ]
    for t in ts:
        cuts.append(up(channel_2d(t), 0, z_face))
        cuts.append(up(slot_2d(t), z_face - 1, face_t + 2))
        # The slot's edge softened in the face, which prints on the bed.
        mouth = Pos(0, 0, top_h - slot_chamfer) * extrude(
            slot_2d(t), slot_chamfer, (0, 0, 1), taper=-45
        )
        cuts.append(mouth)
    return body - cuts


def top() -> Part:
    return top_body(card_x, card_y, card_r, card_tracks, pins) - numbers()


# The back


def back_plate(x: float, y: float, r: float, ts: list[Track], at: list) -> Part:
    """The back, for a top x by y with corners r: it drops into the top's
    recess, with its pins up into the top, its magnets' pockets sealed in it,
    and glue moats round the channels, short of its edge and its pins."""
    inset = rim_w + fit_c
    outline = RectangleRounded(x - 2 * inset, y - 2 * inset, r - rim_w)
    body = extrude(outline, back_t)
    body = chamfer(body.faces().sort_by(Axis.Z).first.edges(), back_foot)
    channels = Sketch() + [channel_2d(t) for t in ts]
    moats = rings(channels, [moat_in, moat_in + moat_w + moat_gap], moat_w)
    moats &= RectangleRounded(
        x - 2 * (inset + moat_edge), y - 2 * (inset + moat_edge), r - rim_w
    )
    moats -= [Pos(*p) * Circle(pin_d / 2 + moat_in) for p in at]
    body -= up(moats, back_t - moat_d, moat_d + 1)
    if not arms:
        pocket = up(Circle(mag_hole / 2), pause - mag_t - mag_slack, mag_t + mag_slack)
        body -= Part() + [Pos(t.at(i), t.y) * pocket for t in ts for i in range(t.n)]
    pin = up(Circle(pin_d / 2), back_t, pin_h)
    pin = chamfer(pin.faces().sort_by(Axis.Z).last.edges(), pin_chamfer)
    return body + [Pos(*p) * pin for p in at]


def back() -> Part:
    return back_plate(card_x, card_y, card_r, card_tracks, pins)


# The rupee


def rupee_2d(inset: float = 0) -> Sketch:
    """An arrow across the track: a circle around the stem, wide enough to
    cover the socket's glue wells under the bevel, drawn out to a point at
    -y, which sits over the end of its label. Inset, the point stays round."""
    # How far out the sharp point is, for its round end to land at -rupee_l.
    d = (rupee_l - rupee_r) / (1 - rupee_r / rupee_h)
    # The point's round end, for a sharp point drawn in by inset + rupee_r.
    tip = d - (inset + rupee_r) * d / rupee_h
    ends = [Circle(rupee_h - inset), Pos(0, -tip) * Circle(rupee_r)]
    return make_hull([e for f in ends for e in f.edges()])


def socket() -> Part:
    """The stem's socket, with crush ribs down the middle of each wall, glue
    wells down its corners, and its mouth chamfered."""
    ribs = [
        Rot(0, 0, a) * Pos(hs - rib_press + 0.5, 0) * Rectangle(1, rib_w)
        for a in (0, 90, 180, 270)
    ]
    walls = up(stem_2d(socket_c) - ribs, -1, socket_d + 1)
    wells = up(
        Sketch()
        + [
            Pos(sx * hs, sy * hs) * Circle(well_d / 2)
            for sx in (-1, 1)
            for sy in (-1, 1)
        ],
        -1,
        socket_d + well_extra + 1,
    )
    mouth = Pos(0, 0, socket_chamfer) * extrude(
        stem_2d(socket_c), socket_chamfer, (0, 0, -1), taper=-45
    )
    return walls + wells + mouth


def rupee() -> Part:
    """Socket down, on z = 0: straight walls, then a bevel up to its top."""
    wall = extrude(rupee_2d(), rupee_wall)
    bevel = loft(
        [
            Pos(0, 0, rupee_wall) * rupee_2d(),
            Pos(0, 0, rupee_t) * rupee_2d(rupee_bevel),
        ],
        ruled=True,
    )
    return wall + bevel - socket()


# Settings

# The back's magnet pockets and their roof are laid out for 0.1 mm layers over
# a 0.2 mm first one (see mag_roof). The slack over a magnet has to be a layer,
# for the pause, and the roof under half a millimeter, for the click: thicker
# layers would round both too coarsely. The first layer's height is the whole print's, in Orca, so it's set
# for the project.
fine = {} if arms else {"layer_height": 0.1}
first_layer = {} if arms else {"initial_layer_print_height": 0.2}
# Lines along the tracks, so along x: on the top's face, which prints on the
# bed, and on the back's channel floor, its top. Angles follow the model, so
# that turning it on the plate turns the lines too.
top_settings = {
    "bottom_surface_pattern": "monotonic",
    "bottom_layer_direction": 0,
    "align_infill_direction_to_model": True,
}
back_settings = {
    "bottom_surface_pattern": "concentric",
    "top_surface_pattern": "monotonic",
    "top_layer_direction": 0,
    "align_infill_direction_to_model": True,
}
rupee_settings = {"top_surface_pattern": "concentric"}
pauses = [] if arms else [pause]
# Each arm one line, arm_t wide: classic walls leave out a wall too thin for a
# loop, and the arm can't be thicker and still flex. And the slicer takes in
# the plate's first layer, which elephant's foot would otherwise spread into
# the slits, too narrow for a chamfer.
arm_settings = (
    {
        "wall_generator": "arachne",
        "outer_wall_line_width": arm_t,
        "elefant_foot_compensation": 0.15,
    }
    if arms
    else {}
)

body_color = "darkgreen"
number_color = "yellow"
rupee_colors = ["magenta", "cyan"]


# Put together


def on_track(t: Track, i: int, z: float) -> Location:
    """At place i of a track, z high, turned for its labels: a rupee's point
    toward them."""
    return Pos(t.at(i), t.y, z) * Rot(0, 0, 180)


def assembly(apart: float = 0) -> list[Piece]:
    """At 0, as each player's sliders start. `apart` pulls the layers apart."""
    lift = Pos(0, 0, apart)
    sliders = Part() + [on_track(t, 0, back_t) * slider() for t in card_tracks]
    return [
        Piece(Pos(0, 0, -apart) * back(), "back", body_color),
        Piece(sliders, "sliders", body_color),
        Piece(lift * top(), "top plate", body_color, parent="top"),
        Piece(lift * numbers(), "numbers", number_color, parent="top"),
    ] + [
        Piece(
            Pos(0, 0, 2 * apart)
            * (Part() + [on_track(t, 0, top_h + rupee_lift) * rupee() for t in player]),
            f"rupees {p}",
            color,
        )
        for p, (player, color) in enumerate(zip(tracks, rupee_colors))
    ]


# Prints, with the tracks along x.

# Turned over, not mirrored, which would print the numbers backwards.
face_down = Pos(0, 0, top_h) * Rot(180, 0, 0)


def grid(part: Part, n: int, dx: float, dy: float) -> Part:
    """n of a part, two to a row, dx and dy apart."""
    return Part() + [Pos(k % 2 * dx, k // 2 * dy) * part for k in range(n)]


def top_print() -> list[Piece]:
    return [
        Piece(face_down * top(), "top plate", body_color, parent="top"),
        Piece(face_down * numbers(), "numbers", number_color, parent="top"),
    ]


def back_print() -> list[Piece]:
    return [Piece(back(), "back", body_color)]


def sliders_print() -> list[Piece]:
    sliders = grid(slider(), len(card_tracks), plate_l + 5, plate_w + 5)
    return [Piece(sliders, "sliders", body_color)]


def rupees_print() -> list[Piece]:
    """A player's two in a row, a row each."""
    return [
        Piece(
            Pos(0, p * (rupee_l + rupee_h + 4)) * grid(rupee(), 2, 2 * rupee_h + 4, 0),
            f"rupees {p}",
            color,
        )
        for p, color in enumerate(rupee_colors)
    ]


def test() -> list[Piece]:
    """Three short tracks: the top face down, with 1 to 3 dots by each, and
    its back, sliders, and a rupee each."""
    dots = Part() + [
        Pos(-test_x / 2 + 2.5, t.y - 2 + 2 * j, top_h - 0.4) * extrude(Circle(0.5), 1)
        for k, t in enumerate(test_tracks)
        for j in range(k + 1)
    ]
    top_part = top_body(test_x, test_y, 2, test_tracks, test_pins) - dots
    back_part = back_plate(test_x, test_y, 2, test_tracks, test_pins)
    sliders = Part() + [
        Pos(-test_x / 2 - 12, t.y) * slider(t.engage, t.lift, k + 1)
        for k, t in enumerate(test_tracks)
    ]
    rupees = Part() + [Pos(-test_x / 2 - 26, t.y * 0.7) * rupee() for t in test_tracks]
    return [
        Piece(face_down * top_part, "top plate", body_color, settings=top_settings),
        Piece(
            Pos(test_x + 4, 0) * back_part,
            "back",
            body_color,
            settings=back_settings,
        ),
        Piece(sliders, "sliders", body_color),
        Piece(rupees, "rupees", rupee_colors[0], settings=rupee_settings),
    ]


project(
    __file__,
    objects={
        "top": Object(top_print, "Face down", settings=top_settings),
        "back": Object(
            back_print,
            "Pausing for its magnets" if pauses else "Its pins up",
            settings=back_settings | fine,
            pauses=pauses,
        ),
        "sliders": Object(sliders_print, "All four, plate down", settings=arm_settings),
        "rupees": Object(
            rupees_print, "All four, socket down", settings=rupee_settings
        ),
        "test": Object(
            test,
            "Three short tracks, a detent strength each",
            settings=fine | arm_settings,
            pauses=pauses,
        ),
    },
    views={
        "assembly": Object(assembly, "Put together"),
        "exploded": Object(lambda: assembly(8), "Pulled apart"),
    },
    # Together: the plate pauses for the back's magnets.
    plates=["top back sliders rupees"],
    orca=first_layer,
)
