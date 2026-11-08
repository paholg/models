// Upright card box for The Fox in the Forest Deluxe: the 61 standard-size
// cards in sleeves, standing on end, with a lift-off lid and a two-player
// scoreboard on the back.
//
// x is across the cards, y is front (0) to back, z is up. The seam slopes
// down toward the front. Above the seam the body walls step in to an inner
// tongue, and the lid's walls cover the outer half, flush with the body.
//
// Print the body upright and the lid top down. The sliders print in place in
// the body's back channels, captured, each at the bottom of its track.
// Every downward face on the sliders and channels is 45° or steeper.
//
// The box lies on its front between the players, who sit at its ends. Each
// board reads upright from its player's end and sits toward it; one board is
// the other turned 180° about the center of the back.

// export: print test_block

/* [Output] */
// "print" is every printed piece in place on the bed, one object per color.
part = "closed"; // [closed, open, print, body, numbers, sliders, lid, test_block]

/* [Cards] */
// Dragon Shield Matte standard sleeve, outside, at its largest: width, length.
sleeve = [66.5, 92.5];
// 61 sleeved cards at ~0.61 mm each: a 0.30 mm card, 0.26 mm of sleeve, and
// ~0.05 mm of loose-stack air.
stack_h = 37.5;
card_clear = 0.5;
// Above the cards, under the lid.
top_clear = 0.5;

/* [Box] */
wall = 1.6;
// Holds the score channels.
back_t = 4;
floor_t = 1.2;
top_t = 1.6;
corner_r = 1;
// How far the seam drops from back to front.
seam_drop = 25;
// Tongue thickness on the sides and front; the back tongue is half back_t.
lip_t = 0.7;
// How far the lid overlaps the tongue.
lip_h = 5;
lip_clear = 0.1;
// Between the tongue top and the lid's top plate.
lip_top_gap = 0.5;

/* [Snap] */
snap_r = 0.8;
// How far the bumps stand off the lips.
snap_h = 0.35;
snap_len = 6;
// Back bumps sit this far either side of center, clear of the channels.
snap_x_back = 28;
snap_clear = 0.1;

/* [Scoreboard] */
font = "TeX Gyre Bonum:style=Bold";
num_h = 4.5;
num_depth = 0.6;
// Between a label and its slider's tip.
num_gap = 1;
pitch = 8;
// Between a sixes slider and the ones labels.
mid_gap = 1.5;
player_gap = 5;

/* [Logo] */
// Title traced from the Deluxe box front, inlaid flush in the lid top.
logo_w = 58;
logo_depth = 0.6;

/* [Slider] */
// Print-in-place gap between slider and body, all around.
pip_clear = 0.3;
// The cap points at its label: tip reach to the left, flat back edge to the
// right. Its bottom and top run at 45° from the tip and back corners.
cap_tip = 4;
cap_back = 3;
cap_t = 1.2;
cap_chamfer = 0.4;
// Stem through the slot, and the face lip it passes through.
stem_w = 3.4;
slot_d = 1.2;
// Plate behind the lip. Its straight sides are plate_side long; its ends
// come to 45° points.
plate_w = 6.8;
plate_t = 1.2;
plate_side = 10;
// Detent beam along the plate's +u edge, rooted at its bottom.
beam_t = 0.8;
slit_w = 0.5;
beam_root = 1;
bump_r = 1.5;
// How far the bump stands off the beam. More than twice pip_clear, so it
// still catches with the slider pushed fully away.
bump_h = 0.9;
// Bump position along the slider, from its center.
bump_v = 3.5;

/* [Hidden] */
$fn = 48;
eps = 0.01;

cav = [sleeve.x + card_clear, stack_h + card_clear, sleeve.y + top_clear];
back_lip_t = back_t / 2;
bx = cav.x + 2 * wall;
by = wall + cav.y + back_t;
box_h = floor_t + cav.z + top_t;
y_back = by - back_t;
// Seam height at the back and at the front.
z_sb = box_h - top_t - lip_top_gap - lip_h;
z_sf = z_sb - seam_drop;
seam_k = seam_drop / y_back;
function seam_z(y) = min(z_sf + seam_k * y, z_sb);

c = pip_clear;
chan_d = slot_d + 2 * c + plate_t;
assert(chan_d + 0.8 <= back_t, "back wall too thin for the slider channel");
hs = stem_w / 2;
hp = plate_w / 2;
stem_c = cap_tip - hs - 0.5;
assert(stem_c >= 0, "stem too wide for the cap");
assert(cap_back < cap_tip, "cap back must be inside its 45° sides");
assert(hp - beam_t - slit_w >= hs, "plate too narrow for the detent beam");
// Slider half-length, and how far a channel reaches past its end positions.
sl = plate_side / 2 + hp;
chan_reach = sl + c * sqrt(2);
bump_u = hp - bump_r + bump_h;

// Each player has a sixes slider (0, 6, 12, 18) and a ones slider (0-5).
// The sixes track shares the ones track's top.
//
// This is the -u board, read from the bottom end. The other board is this one
// turned 180° about (0, v_c), so it can come no closer to the top than the
// seam allows; this one stops the same distance from the bottom.
n_sixes = 4;
n_ones = 6;
v_c = box_h / 2;
end_gap = box_h - z_sb + 1.5;
v_ones = end_gap + chan_reach;
v_sixes = v_ones + (n_ones - n_sixes) * pitch;

num_size = num_h / 0.97;
// Widest two- and one-digit labels ("18", "4") in the font, measured.
w_two = 1.8 * num_size;
w_one = 0.9 * num_size;
// Slot centers in one board, from its left edge.
u_sixes = w_two + num_gap + cap_tip;
u_ones = u_sixes + cap_back + mid_gap + w_one + num_gap + cap_tip;
board_w = u_ones + cap_back;
board_l = -(2 * board_w + player_gap) / 2;
// Tracks as [u, v of position 0, positions, step].
tracks = [
  [board_l + u_sixes, v_sixes, n_sixes, 6],
  [board_l + u_ones, v_ones, n_ones, 1],
];

module rrect(size, r) {
  offset(r = r) square([size.x - 2 * r, size.y - 2 * r], center = true);
}

module box(x, y, z) {
  translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);
}

module outer() {
  translate([0, by / 2, 0]) linear_extrude(box_h) rrect([bx, by], corner_r);
}

// Everything at or below the seam, raised by dz.
module below_seam(dz = 0) {
  intersection() {
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, seam_k, 1, z_sf + dz]])
      box([-bx, bx], [-1, by + 1], [-box_h, 0]);
    box([-bx, bx], [-1, by + 1], [-1, z_sb + dz]);
  }
}

// Scoreboard parts are built facing the viewer: u right, v up, w out of the
// back face with the face at w = 0.
module on_back() {
  multmatrix([[-1, 0, 0, 0], [0, 0, 1, by], [0, 1, 0, 0]]) children();
}

// Box in face coordinates between depths d0 < d1 below the face.
module slab(u, v, d0, d1) {
  translate([u[0], v[0], -d1]) cube([u[1] - u[0], v[1] - v[0], d1 - d0]);
}

// Player 0 sits at the bottom end and gets the -u board as given; player 1
// sits at the lid end and gets its copy turned 180° onto the +u side.
module player(i) {
  if (i == 0) children();
  else translate([0, 2 * v_c, 0]) rotate([0, 0, 180]) children();
}

module both_players() {
  player(0) children();
  player(1) children();
}

module at_track(t) {
  translate([t[0], t[1], 0]) children();
}

// Straight sides at ±s from -c to c, with 45° points beyond.
module hex(s, c) {
  polygon([[-s, -c], [0, -c - s], [s, -c], [s, c], [0, c + s], [-s, c]]);
}

// The 2D children swept from position 0 to v = span.
module travel(span) {
  hull() {
    children();
    translate([0, span]) children();
  }
}

// One track's slot, channel and detent notches, with position i at
// v = i * pitch.
module track_cut(n) {
  span = (n - 1) * pitch;
  translate([0, 0, -slot_d - eps]) linear_extrude(slot_d + 2 * eps)
    travel(span) offset(delta = c) hex(hs, stem_c);
  translate([0, 0, -chan_d]) linear_extrude(chan_d - slot_d + eps)
    travel(span) offset(delta = c) hex(hp, plate_side / 2);
  for (i = [0 : n - 1])
    translate([bump_u, i * pitch + bump_v, -chan_d])
      cylinder(r = bump_r + c, h = chan_d - slot_d);
}

module label(s, u, v) {
  translate([u - cap_tip - num_gap, v])
    text(s, size = num_size, font = font, halign = "right", valign = "center");
}

module track_labels(n, step, above = 0) {
  translate([0, 0, -num_depth]) linear_extrude(num_depth + above, convexity = 10)
    for (i = [0 : n - 1]) label(str(step * i), 0, i * pitch);
}

module labels(above = 0) {
  both_players() for (t = tracks) at_track(t) track_labels(t[2], t[3], above);
}

module board_cuts() {
  both_players() for (t = tracks) at_track(t) track_cut(t[2]);
  labels(eps);
}

module cap_2d() {
  k = cap_tip - cap_back;
  polygon([[-cap_tip, 0], [0, -cap_tip], [cap_back, -k], [cap_back, k], [0, cap_tip]]);
}

// Slider at position 0, in face coordinates.
module slider() {
  w_plate = -slot_d - c;
  hull() {
    translate([0, 0, c]) linear_extrude(eps) cap_2d();
    translate([0, 0, c + cap_t - eps]) linear_extrude(eps)
      offset(delta = -cap_chamfer) cap_2d();
  }
  translate([0, 0, w_plate - eps]) linear_extrude(c - w_plate + 2 * eps) hex(hs, stem_c);
  translate([0, 0, w_plate - plate_t]) linear_extrude(plate_t) {
    difference() {
      hex(hp, plate_side / 2);
      // Frees the detent beam.
      translate([hp - beam_t - slit_w, -plate_side / 2 + beam_root])
        square([slit_w, 2 * sl]);
    }
    intersection() {
      translate([bump_u, bump_v]) circle(bump_r);
      translate([hp - beam_t, -sl]) square([beam_t + bump_h + 1, 2 * sl]);
    }
  }
}

// Tongue footprint, grown by c.
module tongue_box(c, z) {
  box([-cav.x / 2 - lip_t - c, cav.x / 2 + lip_t + c],
      [wall - lip_t - c, y_back + back_lip_t + c], z);
}

module lips() {
  intersection() {
    difference() {
      tongue_box(0, [0, box_h]);
      box([-cav.x / 2, cav.x / 2], [wall, y_back], [0, box_h + 1]);
    }
    below_seam(lip_h);
  }
}

// Bumps on the front lip (one, centered) and the back lip (two).
module snaps(r, len) {
  inset = snap_r - snap_h;
  y_f = wall - lip_t + inset;
  y_b = y_back + back_lip_t - inset;
  for (p = [[0, y_f], [-snap_x_back, y_b], [snap_x_back, y_b]])
    translate([p.x, p.y, seam_z(p.y) + lip_h / 2])
      rotate([0, 90, 0]) cylinder(r = r, h = len, center = true);
}

module body() {
  difference() {
    union() {
      intersection() {
        outer();
        below_seam();
      }
      lips();
      intersection() {
        snaps(snap_r, snap_len);
        below_seam(lip_h);
      }
    }
    box([-cav.x / 2, cav.x / 2], [wall, y_back], [floor_t, box_h + 1]);
    on_back() board_cuts();
  }
}

module numbers() {
  on_back() labels();
}

// Reads from the front, looking down on the lid.
module logo(above = 0) {
  translate([0, by / 2, box_h - logo_depth])
    linear_extrude(logo_depth + above, convexity = 10)
      resize([logo_w, 0], auto = true) import("logo.svg", center = true);
}

module lid() {
  difference() {
    outer();
    below_seam();
    tongue_box(lip_clear, [0, box_h - top_t]);
    snaps(snap_r + snap_clear, snap_len + 2 * snap_clear);
    logo(eps);
  }
}

// Each at the bottom of its track, like the test block: position 0 for
// player 0, the last position for player 1, whose board is upside down.
module sliders_in_place(players = [0, 1]) {
  on_back() for (i = players) player(i) for (t = tracks) at_track(t)
    translate([0, i == 0 ? 0 : (t[2] - 1) * pitch, 0]) slider();
}

module assembly(lift) {
  color("darkgreen") body();
  color("white") numbers();
  color("orange") sliders_in_place([0]);
  color("royalblue") sliders_in_place([1]);
  color("forestgreen") translate([0, 0, lift]) lid();
  color("white") translate([0, 0, lift]) logo();
}

// A short track with its slider and labels, printed upright like the body.
test_n = 3;
test_v0 = 1.5 + chan_reach;

// Face coordinates to the bed, with position 0 at the origin.
module on_test() {
  rotate([90, 0, 0]) translate([0, test_v0, 0]) children();
}

module test_block() {
  h = test_v0 + (test_n - 1) * pitch + chan_reach + 1.5;
  on_test() difference() {
    slab([-cap_tip - num_gap - w_one - 2, bump_u + bump_r + c + 2],
         [-test_v0, h - test_v0], 0, back_t);
    track_cut(test_n);
    track_labels(test_n, 1, eps);
  }
}

// Top down, beside the body.
module print_lid() {
  translate([bx + 10, by, box_h]) rotate([180, 0, 0]) children();
}

if (part == "print") {
  color("darkgreen") body();
  color("white") numbers();
  color("orange") sliders_in_place([0]);
  color("forestgreen") print_lid() lid();
  // New pieces go last, so a saved Orca project's parts keep their order.
  color("white") print_lid() logo();
  color("royalblue") sliders_in_place([1]);
} else if (part == "body") {
  body();
} else if (part == "numbers") {
  numbers();
} else if (part == "lid") {
  print_lid() lid();
} else if (part == "sliders") {
  sliders_in_place();
} else if (part == "test_block") {
  color("darkgreen") test_block();
  color("white") on_test() track_labels(test_n, 1);
  color("orange") on_test() slider();
} else if (part == "open") {
  assembly(40);
} else if (part == "closed") {
  assembly(0);
}
