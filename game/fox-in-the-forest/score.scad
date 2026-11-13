// Card-sized two-player score tracker for The Fox in the Forest Deluxe, to
// store in the card box with the deck.
//
// x is along the tracks, y is toward player 1's half, z is up, with the
// card's underside at z = 0. Everything reads from the -x long edge: player
// 1's sixes and ones, then player 0's, left to right, counting up away from
// the reader.
//
// Four pieces, all printed flat:
// - top: the face with the slots, numbers and channels, printed face down on
//   the bed so every slot and channel wall prints as a wall.
// - back: drops into a recess inside the top's rim and closes the channels,
//   with pins into holes in the top. Glue it on away from the channels;
//   two grooves around each channel catch squeeze-out.
// - sliders: a plate riding in the channel, with a stem up through the slot,
//   keyed long so the slider can't twist. Printed plate down. It clicks into
//   each position one of two ways (detent):
//   - magnets: a disc magnet glued into the plate's underside, over one
//     captured in the back at each position: the print pauses with the
//     back's pockets open, to drop the magnets in, then roofs them over. Put
//     every magnet in the back the same way up, and glue the sliders' to
//     attract them; wells around the sliders' pockets take the excess glue.
//   - arms: a spring arm down each side of the plate, fixed at both ends and
//     bent into a round hump in the middle that clicks into scallops in the
//     channel walls.
// - rupees: press onto the stems from above after the back is glued on, each
//   with a point over the end of its label. Printed flat, socket down.
// Assembly: drop the sliders into the top's channels, glue on the back, press
// on the rupees.

// export: print test
// orca: process="0.12 Fine" layer_height=0.1 elefant_foot_compensation=0.15

/* [Output] */
part = "assembled"; // [assembled, exploded, print, top, numbers, back, sliders, rupees, test]

/* [Card] */
// A sleeved card, a little under the box's cavity.
card = [66, 92];
card_r = 3;
// Roundovers on the card's outside edges: around the face, and around the
// rim's underside, which has to stay under rim_w.
face_round = 1.5;
rim_round = 0.6;

/* [Face] */
face_t = 1.6;
font = "TeX Gyre Bonum:style=Bold";
num_h = 4;
num_depth = 0.6;
pitch = 9;
// Half the band each track takes up across the card, and from there to its
// labels' ends. The rupee's point reaches past both, over the label.
band = 5.5;
num_gap = 1;

/* [Slider] */
detent = "magnets"; // [magnets, arms]
// Clearance at the slider plate's ends.
c = 0.3;
// Between the plate's sides and the channel walls; only the humps touch.
side_c = 0.2;
// Total up-and-down play of the plate in its channel.
z_play = 0.4;
// Thick enough for a floor under the magnets and a roof over them.
back_t = 1.7;
// The top's rim around the back, which drops into the recess it leaves.
rim_w = 1.2;
fit_c = 0.15;
// Locating pins on the back, into holes in the top.
pin_d = 3;
pin_h = 1.5;
// Grooves in the back around each channel catch glue before it reaches a
// slider.
moat_in = 0.5;
moat_w = 0.5;
moat_d = 0.7;
// A second groove this far outside the first, wherever there's room for it,
// gives glue on the wider lands somewhere nearer to go.
moat_gap = 1;
// The land left between any groove and the back's edge.
moat_edge = 0.3;
plate_t = 1.5;
// Plate size across and along the track.
plate_w = 11;
plate_l = 14;
plate_chamfer = 0.8;
stem = 3.2;
stem_chamfer = 0.4;
// A long key on the stem, in the slot, keeps the slider from twisting.
key_l = 8;
key_c = 0.25;
// Each side has a spring arm fixed at both ends, so whichever way the slider
// moves, the half of the arm behind the hump pulls it along in tension; an
// arm with a free end buckles when it's pushed hump first. The arm itself
// bends out into a round hump in the middle, one line wide throughout, which
// lets it flex by bending rather than stretching.
arm_t = 0.45;
arm_h = 1;
slit_w = 0.6;
arm_root = 1;
// How far each hump reaches past the channel wall, so how far the arms flex.
engage = 0.35;
// Outside radius of the hump; smaller is steeper, for a harder click.
hump_r = 3;
// Rounds the hump into the arm either side.
hump_fillet = 1;
notch_c = 0.15;
// Height of the slider plate's first layers, stepped in by half this against
// elephant's foot.
foot = 0.3;

/* [Magnets] */
// Disc magnets: diameter, thickness.
mag = [5, 1];
// Pocket clearance on the diameter.
mag_c = 0.2;
// The channel floor over the back's magnets, printed after the pause. Whole
// layers, so the pause falls on a layer's top.
mag_roof = 0.3;
// Height of the back's pockets over the magnets, so the nozzle clears them.
mag_slack = 0.1;
// How far the slider's magnet sits above the plate's underside. With the
// roof, and the slack if the magnet stays down, the gap between the magnets:
// more is a softer click.
mag_lift = 0.2;
// Wells around the slider's magnet pocket, for excess glue.
mag_well_d = 1.6;
mag_wells = 4;

/* [Rupee] */
// From the stem to its point, and the radius of its round end.
rupee_l = 7.5;
rupee_h = 4.5;
rupee_t = 3.5;
rupee_wall = 1.2;
rupee_bevel = 1.5;
// Rounds the outline's corners.
rupee_r = 1;
rupee_lift = 0.5;
socket_d = 2.5;
// Socket clearance around the stem; the ribs then take up rib_press.
socket_c = 0.1;
rib_press = 0.1;
rib_w = 0.8;
socket_chamfer = 0.4;
// Glue wells down the socket's corners, past the stem's chamfered corners and
// below its tip, so glue has somewhere to go without holding the rupee up.
well_d = 1.2;
well_extra = 0.4;

/* [Test] */
test_bumps = [0.25, 0.35, 0.45];
// The sliders' mag_lift on each track, for magnets.
test_lifts = [0.2, 0.2, 0.2];
test_n = 3;

/* [Hidden] */
$fn = 48;
eps = 0.01;

chan_d = plate_t + z_play;
z_face = back_t + chan_d;
top_h = z_face + face_t;
// Stem from the plate's top to its tip in the socket.
stem_len = z_play + face_t + rupee_lift + socket_d;
hs = stem / 2;
hw = plate_w / 2;
hl = plate_l / 2;
// Channel half-width, and the slits' inner edge, out from center.
cw = hw + side_c;
y_core = hw - arm_t - slit_w;
// Hump height off the plate side, for engagement e.
function bump_hh(e) = side_c + e;
arms = detent == "arms";
assert(rim_round < rim_w, "rim rounded away");
assert(face_round < face_t, "face roundover reaches the channels");
assert(arm_h <= plate_t, "arms taller than the plate");
assert(back_t - mag_roof - mag.y - mag_slack >= 0.3 - eps, "back too thin under the magnets");
assert(plate_t - mag.y - max(test_lifts) >= 0.2 - eps, "plate too thin over the magnet");
assert(mag.x + mag_c + mag_well_d + 2 <= min(pitch, plate_w), "magnets crowd each other or the plate's sides");
assert(slit_w >= max(test_bumps) + 0.15, "slits too narrow for the arms to flex");
assert(y_core >= hs + key_c + 1.2, "plate core too narrow to bear on the face");
assert(rupee_t - socket_d >= 0.8, "rupee too thin over the socket");
assert(rupee_t - socket_d - well_extra >= 0.5, "rupee too thin over the glue wells");

num_size = num_h / 0.97;
// Labels turn 90° to read from the card's long edge, so their rows are as
// deep as the widest label ("30") is long.
num_len = 1.8 * num_size;
n_sixes = 6;
n_ones = 6;
// Track rows in player 0's half, from its edge: [y, positions, step].
// Reading from the long edge, the sixes come first, nearer the card's end,
// then the ones. Each row is its labels, then its track's band. The gaps at
// the end, between the rows, and between the players (shared) are all equal.
row_gap = (card.y / 2 - 2 * (num_len + num_gap + 2 * band)) / 2.5;
assert(row_gap >= 1.5, "rows too crowded");
y_sixes = -card.y / 2 + row_gap + num_len + num_gap + band;
y_ones = y_sixes + band + row_gap + num_len + num_gap + band;
tracks = [[y_ones, n_ones, 1], [y_sixes, n_sixes, 6]];

function x0(n) = -(n - 1) * pitch / 2;

module rrect(size, r) {
  offset(r = r) square([size.x - 2 * r, size.y - 2 * r], center = true);
}

// The half is laid out for -y; both players get it turned 180°, so they read
// the same way, and player 0's copy shifts down into the -y half, keeping the
// gaps at the ends and between the players equal.
player_dy = [-card.y / 2 + row_gap / 2, 0];
module player(i) {
  translate([0, player_dy[i]]) rotate([0, 0, 180]) children();
}
function player_xy(i, p) = [-p.x, -p.y + player_dy[i]];

module both() {
  player(0) children();
  player(1) children();
}

// Children at each track's position 0, for player 0's half.
// Tracks count up away from the reader at the +x edge, so position 0 is at
// +x and the children are mirrored to run toward -x.
module at_tracks(ts = tracks) {
  for (t = ts) translate([-x0(t[1]), t[0], 0]) mirror([1, 0, 0]) let($n = t[1], $step = t[2]) children();
}

// The hump's outside, on the +y side of a plate edge at y = 0, for
// engagement e, grown by g.
module hump_2d(e, g = 0) {
  intersection() {
    translate([0, bump_hh(e) - hump_r]) circle(r = hump_r + g, $fn = 128);
    translate([-hump_r - 1, -eps]) square([2 * hump_r + 2, hump_r]);
  }
}

// Everything inside an arm's outer face, for a plate edge at y = 0: straight,
// with the hump filleted in.
module arm_outer_2d(e) {
  offset(r = -hump_fillet) offset(r = hump_fillet) {
    translate([-hl - 5, -5]) square([plate_l + 10, 5]);
    hump_2d(e);
  }
}

// Where an arm and the slit behind it go, on the +y side.
module arm_zone_2d(g = 0) {
  translate([-hl + arm_root - g, y_core]) square([plate_l - 2 * arm_root + 2 * g, hw - y_core + 2]);
}

// The slider plate outline and arms, centered.
module plate_2d(e) {
  if (arms) for (sy = [-1, 1]) mirror([0, sy > 0 ? 0 : 1]) {
    intersection() {
      arm_zone_2d(eps);
      translate([0, hw]) difference() {
        arm_outer_2d(e);
        offset(r = -arm_t) arm_outer_2d(e);
      }
    }
  }
  difference() {
    offset(delta = plate_chamfer, chamfer = true)
      square([plate_l - 2 * plate_chamfer, plate_w - 2 * plate_chamfer], center = true);
    if (arms) for (sy = [-1, 1]) mirror([0, sy > 0 ? 0 : 1]) arm_zone_2d();
  }
}

// Above the arms, between their roots, on both sides.
module over_arms() {
  for (sy = [-1, 1]) mirror([0, sy > 0 ? 0 : 1])
    translate([-hl + arm_root, hw - arm_t - eps, arm_h]) cube([plate_l - 2 * arm_root, 2, plate_t]);
}

module stem_2d(g = 0) {
  offset(delta = g) offset(delta = stem_chamfer, chamfer = true) square(stem - 2 * stem_chamfer, center = true);
}

module key_2d(g = 0) {
  offset(delta = g) offset(delta = stem_chamfer, chamfer = true)
    square([key_l - 2 * stem_chamfer, stem - 2 * stem_chamfer], center = true);
}

// A magnet pocket, opening downward at z = 0, depth deep.
module mag_pocket(depth) {
  translate([0, 0, -eps]) cylinder(d = mag.x + mag_c, h = depth + eps);
}

// Wells around a magnet pocket's edge, as deep: glue pushed out from under
// the magnet ends up here, not on the plate's underside.
module mag_wells(depth) {
  for (i = [0 : mag_wells - 1]) rotate(45 + i * 360 / mag_wells)
    translate([(mag.x + mag_c) / 2, 0, -eps]) cylinder(d = mag_well_d, h = depth + eps, $fn = 16);
}

// Slider at its rest height, plate on the back. marks dimples go in the
// plate's top beside the key, clear of the arms and magnet, to tell test
// sliders apart.
module slider(e = engage, marks = 0, lift = mag_lift) {
  y_mark = arms ? (hs + y_core) / 2 : hw - 1.3;
  translate([0, 0, back_t]) {
    // The plate, slits through, the arms cut down to arm_h. (Too thin to
    // step in against elephant's foot; use the slicer's compensation.)
    difference() {
      linear_extrude(plate_t) plate_2d(e);
      if (arms) over_arms();
      else { mag_pocket(mag.y + lift); mag_wells(mag.y + lift); }
      for (j = [0 : 1 : marks - 1]) translate([(j - (marks - 1) / 2) * 2, y_mark, plate_t - 0.4])
        cylinder(d = 1, h = 1);
    }
    // The key, up the slot to just under the face's softened edge.
    translate([0, 0, plate_t - eps]) linear_extrude(z_play + face_t - 0.4 + eps) key_2d();
    translate([0, 0, plate_t - eps]) linear_extrude(stem_len + eps) stem_2d();
  }
}

// One track's slot and channel, with notches for every position, at
// position 0.
module track_cut(n, e = engage) {
  span = (n - 1) * pitch;
  translate([0, 0, back_t - eps]) linear_extrude(chan_d + eps) {
    chan_2d(n);
    // The hump seats with notch_c all around it.
    if (arms) for (i = [0 : n - 1], a = [0, 180]) translate([i * pitch, 0]) mirror([0, a > 0 ? 1 : 0])
      translate([0, hw]) hump_2d(e, notch_c);
  }
  translate([0, 0, z_face - eps]) linear_extrude(face_t + 2 * eps)
    hull() { key_2d(key_c); translate([span, 0]) key_2d(key_c); }
  // Soften the slot's edge in the face, which prints on the bed.
  translate([0, 0, top_h - 0.4]) hull() {
    linear_extrude(eps) hull() { key_2d(key_c); translate([span, 0]) key_2d(key_c); }
    translate([0, 0, 0.4 + eps]) linear_extrude(eps)
      hull() { key_2d(key_c + 0.4); translate([span, 0]) key_2d(key_c + 0.4); }
  }
}

module labels_2d() {
  both() at_tracks() for (i = [0 : $n - 1])
    translate([i * pitch, -band - num_gap]) mirror([1, 0, 0]) rotate(90)
      text(str(i * $step), size = num_size, font = font, halign = "right", valign = "center");
}

module numbers(above = 0) {
  translate([0, 0, top_h - num_depth]) linear_extrude(num_depth + above, convexity = 10) labels_2d();
}

// Pins, for player 0's half: under the label row between the tracks, and in
// the strip between the ones track and the edge.
pins = [
  [card.x / 2 - 7, (y_ones + y_sixes) / 2],
  [-card.x / 2 + 7, (y_ones + y_sixes) / 2],
  [0, (-card.y / 2 + rim_w + y_sixes - cw) / 2],
];
assert(pins[2].y + pin_d / 2 + fit_c + 1 < y_sixes - cw - moat_in - moat_w, "pin crowds the sixes track");
// The two players' middle channels, with a moat each and some glue land.
assert(row_gap - 2 * (cw - band) >= 2 * (moat_in + moat_w) + 0.4, "middle channels too close");
function both_pins() = [for (i = [0, 1], p = pins) player_xy(i, p)];

// A channel's outline, for position 0.
module chan_2d(n) {
  translate([-hl - c, -cw]) square([(n - 1) * pitch + plate_l + 2 * c, 2 * cw]);
}

// Grooves around the children, all a back's channels: one around each, and
// a second further out, around them all, which drops out where channels are
// too close for it.
module moat_2d() {
  for (d = [moat_in, moat_in + moat_w + moat_gap])
    difference() { offset(delta = d + moat_w) children(); offset(delta = d) children(); }
}

// A slab of the size outline, h tall, its bottom edge rounded over by r_bot
// and its top edge by r_top.
module round_slab(size, r, h, r_bot, r_top) {
  n = 12;
  hull() for (i = [0 : n]) {
    a = 90 * i / n;
    in_b = r_bot * (1 - cos(a));
    in_t = r_top * (1 - cos(a));
    translate([0, 0, r_bot * (1 - sin(a))]) linear_extrude(eps) rrect(size - 2 * [in_b, in_b], r - in_b);
    translate([0, 0, h - r_top * (1 - sin(a)) - eps]) linear_extrude(eps) rrect(size - 2 * [in_t, in_t], r - in_t);
  }
}

// The top's body, size outline, with the recess for its back, pin holes, and
// the children cut out.
module top_body(size, r, pin_xy = []) {
  difference() {
    round_slab(size, r, top_h, rim_round, face_round);
    translate([0, 0, -eps]) linear_extrude(back_t + eps) rrect(size - 2 * [rim_w, rim_w], r - rim_w);
    for (p = pin_xy) translate([p.x, p.y, back_t - eps]) cylinder(d = pin_d + 2 * fit_c, h = pin_h + 0.3);
    children();
  }
}

// The back, dropping into the top's recess, with its pins, and the 2D
// children grooved into it as glue moats, short of its edge and its pins.
module back_plate(size, r, pin_xy = []) {
  in = rim_w + fit_c;
  difference() {
    hull() {
      linear_extrude(eps) rrect(size - 2 * [in + foot, in + foot], r - rim_w);
      translate([0, 0, foot]) linear_extrude(back_t - foot) rrect(size - 2 * [in, in], r - rim_w);
    }
    translate([0, 0, back_t - moat_d]) linear_extrude(moat_d + eps) difference() {
      intersection() {
        children();
        rrect(size - 2 * [in + moat_edge, in + moat_edge], r - rim_w);
      }
      for (p = pin_xy) translate(p) circle(d = pin_d + 2 * moat_in);
    }
  }
  for (p = pin_xy) translate([p.x, p.y, back_t - eps]) {
    cylinder(d = pin_d, h = pin_h - 0.4 + eps);
    translate([0, 0, pin_h - 0.4]) cylinder(d1 = pin_d, d2 = pin_d - 0.8, h = 0.4);
  }
}

module top() {
  top_body(card, card_r, both_pins()) {
    both() at_tracks() track_cut($n);
    numbers(eps);
  }
}

// Where the print pauses for the back's magnets: the top of their pockets.
z_pause = back_t - mag_roof;

// Magnet pockets closed inside the back, under each of a track's n
// positions, from position 0.
module back_pockets(n) {
  if (!arms) for (i = [0 : n - 1]) translate([i * pitch, 0, z_pause]) mirror([0, 0, 1])
    cylinder(d = mag.x + mag_c, h = mag.y + mag_slack);
}

module back() {
  difference() {
    back_plate(card, card_r, both_pins()) moat_2d() both() at_tracks() chan_2d($n);
    both() at_tracks() back_pockets($n);
  }
}

// An arrow across the track: a circle around the stem, wide enough to cover
// the socket's glue wells under the bevel, drawn out to a point at -y, which
// sits over the end of its label. The point is rounded at every inset.
module rupee_2d(inset = 0) {
  l = rupee_l;
  h = rupee_h;
  // How far out the sharp point is, for its rounded tip to land at -l.
  d = (l - rupee_r) / (1 - rupee_r / h);
  offset(r = rupee_r) offset(delta = -inset - rupee_r) hull() {
    circle(r = h, $fn = 96);
    translate([0, -d]) square(eps, center = true);
  }
}

// Long axis across the track (y), underside at z = 0.
module rupee() {
  difference() {
    union() {
      linear_extrude(rupee_wall) rupee_2d();
      hull() {
        translate([0, 0, rupee_wall - eps]) linear_extrude(eps) rupee_2d();
        translate([0, 0, rupee_t - eps]) linear_extrude(eps) rupee_2d(rupee_bevel);
      }
    }
    translate([0, 0, -eps]) linear_extrude(socket_d + eps) difference() {
      stem_2d(socket_c);
      // Crush ribs down the middle of each socket wall.
      for (a = [0 : 90 : 270]) rotate(a)
        translate([hs + socket_c - rib_press - socket_c, -rib_w / 2]) square([1, rib_w]);
    }
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * hs, sy * hs, -eps])
      cylinder(d = well_d, h = socket_d + well_extra + eps, $fn = 16);
    hull() {
      translate([0, 0, -eps]) linear_extrude(eps) stem_2d(socket_c + socket_chamfer);
      translate([0, 0, socket_chamfer]) linear_extrude(eps) stem_2d(socket_c);
    }
  }
}

module sliders_in_place(players = [0, 1]) {
  for (p = players) player(p) at_tracks() children();
}

module rupees_in_place(p) {
  sliders_in_place([p]) translate([0, 0, top_h + rupee_lift]) rupee();
}

/* Print layout */

// Each top-level statement of a layout is a piece: a part in Orca, with a
// name and slicer settings of its own (see python/generate.py).
module piece(name, orca = "") {
  echo(piece = name, orca = orca);
  children();
}

// The layouts are drawn with the tracks along x and the back toward +x, then
// turned onto the bed: tracks front to back, and the back at the front of the
// printer, to reach its magnet pockets at the pause.
module bed() {
  rotate(-90) children();
}

// Lines along the tracks, so along y on the bed: on the top's face, which
// prints on the bed, and on the back's channel floor, its top. Angles follow
// the model, so that turning it in Orca turns the lines too.
turned = " align_infill_direction_to_model=1";
orca_top = str("bottom_surface_pattern=monotonic bottom_layer_direction=90", turned);
orca_back = str("bottom_surface_pattern=concentric top_surface_pattern=monotonic top_layer_direction=90", turned);
orca_rupee = "top_surface_pattern=concentric";

// Turned over, not mirrored, which would print the numbers backwards.
module print_top() {
  translate([0, 0, top_h]) rotate([180, 0, 0]) children();
}

// The layouts are spelled out at the top level, at the end of the file, one
// statement per color: each top-level statement exports as its own object,
// where a module would export as one solid with only its faces colored.
module print_sliders() {
  for (k = [0 : 3]) translate([-card.x / 2 - 12, -card.y / 2 + 8 + k * (plate_w + 6), -back_t]) slider();
}

// Rupees ks of the four.
module print_rupees(ks) {
  for (k = ks) translate([-card.x / 2 - 28, -card.y / 2 + 8 + k * (rupee_l + rupee_h + 4), 0]) rupee();
}

/* Test: three short tracks, with different hump engagements (test_bumps) for
   arms, or magnet gaps (test_lifts) for magnets. */

// Tracks spaced to fit a locating pin between each pair, clear of the moats.
test_dy = 2 * cw + 2 * (moat_in + moat_w) + pin_d + 2 * fit_c + 2;
test_w = 3 * test_dy + 2;
test_l = (test_n - 1) * pitch + plate_l + 8;
function test_y(k) = (k - 1) * test_dy;
test_pins = [[0, -test_dy / 2], [0, test_dy / 2]];

module test_top() {
  top_body([test_l, test_w], 2, test_pins) {
    for (k = [0 : 2]) translate([x0(test_n), test_y(k), 0]) track_cut(test_n, test_bumps[k]);
    // Engagement marks: 1 to 3 dots by the track, smallest first.
    for (k = [0 : 2], j = [0 : k]) translate([-test_l / 2 + 2.5, test_y(k) - 2 + 2 * j, top_h - 0.4])
      cylinder(d = 1, h = 1);
  }
}

module test_back() {
  translate([test_l + 4, 0, 0]) difference() {
    back_plate([test_l, test_w], 2, test_pins)
      moat_2d() for (k = [0 : 2]) translate([x0(test_n), test_y(k)]) chan_2d(test_n);
    for (k = [0 : 2]) translate([x0(test_n), test_y(k)]) back_pockets(test_n);
  }
}

module test_sliders() {
  for (k = [0 : 2]) translate([-test_l / 2 - 12, test_y(k), -back_t])
    slider(test_bumps[k], k + 1, test_lifts[k]);
}

module test_rupees() {
  for (k = [0 : 2]) translate([-test_l / 2 - 26, test_y(k) * 0.7, 0]) rupee();
}

// One color per filament, shared by every view and layout: generate.py gives
// each color a filament, in the order a layout first uses them.
c_body = "darkgreen";
c_slider = "darkgreen";
c_number = "yellow";
c_rupee = ["magenta", "cyan"];

if (part == "assembled" || part == "exploded") {
  e = part == "exploded" ? 8 : 0;
  color(c_body) translate([0, 0, -e]) back();
  color(c_slider) sliders_in_place() slider();
  color(c_body, part == "exploded" ? 0.4 : 1) translate([0, 0, e]) top();
  color(c_number) translate([0, 0, e]) numbers();
  color(c_rupee[0]) translate([0, 0, 2 * e]) rupees_in_place(0);
  color(c_rupee[1]) translate([0, 0, 2 * e]) rupees_in_place(1);
} else if (part == "print") {
  if (!arms) echo(pause = z_pause);
  piece("top", orca_top) color(c_body) bed() print_top() top();
  piece("numbers", orca_top) color(c_number) bed() print_top() numbers();
  piece("back", orca_back) color(c_body) bed() translate([card.x + 5, 0, 0]) back();
  piece("sliders") color(c_slider) bed() print_sliders();
  piece("rupees 0", orca_rupee) color(c_rupee[0]) bed() print_rupees([0, 1]);
  piece("rupees 1", orca_rupee) color(c_rupee[1]) bed() print_rupees([2, 3]);
} else if (part == "test") {
  if (!arms) echo(pause = z_pause);
  piece("top", orca_top) color(c_body) bed() print_top() test_top();
  piece("back", orca_back) color(c_body) bed() test_back();
  piece("sliders") color(c_slider) bed() test_sliders();
  piece("rupees", orca_rupee) color(c_rupee[0]) bed() test_rupees();
}
else if (part == "top") top();
else if (part == "numbers") numbers();
else if (part == "back") back();
else if (part == "sliders") sliders_in_place() slider();
else if (part == "rupees") rupee();
