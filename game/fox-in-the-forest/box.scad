// Upright card box for The Fox in the Forest Deluxe: the 61 standard-size
// cards in sleeves, standing on end, with a lift-off lid and a two-player
// scoreboard on the back.
//
// x is across the cards, y is front (0) to back, z is up. The seam slopes
// down toward the front. Above the seam the body walls step in to an inner
// tongue, and the lid's walls cover the outer half, flush with the body.
//
// Print the body upright and the lid top down. The sliders print in place in
// the body's back channels, captured, each at the bottom of its track, with a
// peg standing out of the face. The caps print flat and glue onto the pegs.
// Every downward face on the sliders and channels is 45° or steeper.
//
// The box lies on its front between the players, who sit at its ends. Each
// board reads upright from its player's end and sits toward it; one board is
// the other turned 180° about the center of the back.

// Each export imports into Orca as one object (answer yes when it asks), so
// the flat-printed caps get their own files.
// export: print caps test_block test_caps

/* [Output] */
// "print" is every printed piece in place on the bed, one object per color.
part = "closed"; // [closed, open, print, body, numbers, fox, sliders, lid, caps, test_block, test_caps]

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
back_t = 5;
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
// Half-width of a slider's lane, for placing labels; the caps overhang it.
track_w = 3.5;
// Between a label and its slider's lane.
num_gap = 1;
pitch = 8;
// Between a sixes slider and the ones labels.
mid_gap = 1.5;
player_gap = 5;

/* [Logo] */
// Title traced from the Deluxe box front, inlaid flush in the lid top.
logo_w = 58;
logo_depth = 0.6;

/* [Fox] */
// Fox silhouette inlaid flush in the body's front, below the seam.
fox_h = 50;
fox_depth = 0.6;
// Center height of the fox on the front.
fox_z = 31;

/* [Slider] */
// Print-in-place gap between slider and body, all around.
pip_clear = 0.3;
// Gap under each printed slider, between its lower 45° faces and the end of
// its channel. 0 rests it on the body, for a mechanism filament that doesn't
// bond to the body's (tried with PETG in PLA: the stems snapped first).
rest_gap = pip_clear;
// The cap is a flat rupee lying across the track, glued onto the stem's
// peg: cap_l to its points either way, cap_h to its flat push sides, its
// points cap_p long. A straight wall cap_wall tall, then facets inset by
// cap_bevel up to the flat top at cap_t.
cap_l = 5.5;
cap_h = 4;
cap_p = 2.5;
cap_t = 3;
cap_wall = 1.2;
cap_bevel = 1.5;
// Socket for the peg, and the glue gap around it.
socket_d = 2;
glue_gap = 0.15;
// Room for squeezed-out glue: grooves down the socket's sides and points,
// glue_groove wide and deep, and a 45° chamfer glue_chamfer deep round its
// mouth.
glue_groove = 0.6;
glue_chamfer = 0.6;
// Between the cap and the face, glued on.
cap_lift = 0.5;
// Stem through the slot, and the face lip it passes through. Its straight
// sides are stem_c either side of center, with 45° points.
stem_w = 3.4;
stem_c = 0.5;
slot_d = 1.2;
// Plate behind the lip. Its straight sides are plate_side long; its ends
// come to 45° points.
plate_w = 9.6;
plate_t = 1.2;
plate_side = 10;
// Detent: a spring beam down each side of the plate, rooted at its bottom,
// thinner than the plate so it can flex toward the lip. A 45° ridge on each
// beam's back drops into a groove in the channel floor at each position.
beam_w = 1.4;
beam_t = 0.8;
slit_w = 0.5;
beam_root = 1;
// How far the ridge stands off the beam. The beams must flex by
// bump_h - 2 * pip_clear to get between positions.
bump_h = 0.9;
// Ridge position along the slider, from its center.
bump_v = 3.5;

/* [Colors] */
// The in-place slider mechanism; the caps carry the player colors.
mech_color = "darkgreen";

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
// Slider half-length, and how far a channel reaches past its end positions.
sl = plate_side / 2 + hp;
assert(sl >= stem_c + hs, "plate shorter than the stem");
assert(cap_t - socket_d >= 0.8, "cap too thin over the socket");
chan_reach = sl + c * sqrt(2);
// Peg tip, out from the face.
w_peg = cap_lift + socket_d;
// Where the stem's sloped underside meets the peg, inside the socket's mouth
// chamfer: the slope reaches no further below the peg than the chamfer
// opens up, so the caps fit over it.
w_slope = cap_lift + glue_chamfer - glue_gap;
// Bottom of the stem at the plate, below center.
stem_low = stem_c + hs + w_slope + slot_d + c;
assert(stem_low <= sl, "stem's sloped underside runs off the plate");
// The plate's core, inside the slits, bears on the lip.
assert(hp - beam_w - slit_w >= hs + c + 0.5, "plate too narrow for the beams");
bump_u = hp - beam_w / 2;
assert(back_t - chan_d >= bump_h + 0.6, "channel floor too thin for the grooves");
assert(bump_h - 2 * c <= plate_t - beam_t + c, "beams can't flex far enough");

// Each player has a sixes slider (0-30) and a ones slider (0-5), for scores
// up to 35, the long game. The two tracks are the same length.
//
// This is the -u board, read from the bottom end. The other board is this one
// turned 180° about (0, v_c), so it can come no closer to the top than the
// seam allows; this one stops the same distance from the bottom.
n_sixes = 6;
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
u_sixes = w_two + num_gap + track_w;
u_ones = u_sixes + track_w + mid_gap + w_one + num_gap + track_w;
board_w = u_ones + track_w;
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

// Prism along u of a polygon in (v, w).
module prism_u(len, pts) {
  rotate([90, 0, 90]) linear_extrude(len, center = true) polygon(pts);
}

// 45° ridge d deep, pointing into the face (-w), its base at w = 0.
module wedge(len, d) {
  prism_u(len, [[-d, eps], [d, eps], [0, -d]]);
}

// The 2D children swept from position 0 to v = span.
module travel(span) {
  hull() {
    children();
    translate([0, span]) children();
  }
}

// A channel end around the plate: c clear at the sides, g clear off its 45°
// faces.
module chan_end(g) {
  hex(hp + c, plate_side / 2 - c + g * sqrt(2));
}

// One track's slot, channel and detent grooves, with position i at
// v = i * pitch, for the slider printed at position 0. With flip, mirrored
// end for end, for the slider printed at the top end of a board turned over.
module track_cut(n, bh = bump_h, flip = false) {
  span = (n - 1) * pitch;
  if (flip) translate([0, span, 0]) mirror([0, 1, 0]) track_cut(n, bh);
  else {
  translate([0, 0, -slot_d - eps]) linear_extrude(slot_d + 2 * eps)
    travel(span) offset(delta = c) hull() {
      hex(hs, stem_c);
      // Down to where the stem's sloped underside crosses the back of the
      // lip, and c more so the gap off the slope is c.
      translate([0, -(w_slope + slot_d + c)]) hex(hs, stem_c);
    }
  translate([0, 0, -chan_d]) linear_extrude(chan_d - slot_d + eps) hull() {
    chan_end(rest_gap);
    translate([0, span]) chan_end(c);
  }
  // The ridge grown by c, with its base c off the floor.
  d = bh - c + c * sqrt(2);
  for (i = [0 : n - 1], su = [-1, 1])
    translate([su * bump_u, i * pitch + bump_v, -chan_d]) wedge(beam_w + 2 * c, d);
  }
}

module label(s, u, v) {
  translate([u - track_w - num_gap, v])
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
  for (i = [0, 1]) player(i) for (t = tracks) at_track(t) track_cut(t[2], flip = i == 1);
  labels(eps);
}

module rupee_2d(inset = 0) {
  l = cap_l;
  h = cap_h;
  offset(delta = -inset)
    polygon([[-l, 0], [-l + cap_p, -h], [l - cap_p, -h], [l, 0], [l - cap_p, h], [-l + cap_p, h]]);
}

// Cap with its underside at w = 0, socket and all.
module cap() {
  difference() {
    union() {
      linear_extrude(cap_wall) rupee_2d();
      hull() {
        translate([0, 0, cap_wall - eps]) linear_extrude(eps) rupee_2d();
        translate([0, 0, cap_t - eps]) linear_extrude(eps) rupee_2d(cap_bevel);
      }
    }
    socket_2d() offset(delta = glue_gap) hex(hs, stem_c);
  }
}

// The socket for the peg outline given as the child, with glue relief.
module socket_2d() {
  translate([0, 0, -eps]) linear_extrude(socket_d + eps) {
    children();
    g = glue_groove;
    pv = stem_c + hs + glue_gap;
    pu = hs + glue_gap;
    for (s = [-1, 1]) {
      translate([s * pu, 0]) square([2 * g, g], center = true);
      translate([0, s * pv]) square([g, 2 * g], center = true);
    }
  }
  hull() {
    translate([0, 0, -eps]) linear_extrude(eps) offset(delta = glue_chamfer) children();
    translate([0, 0, glue_chamfer - eps]) linear_extrude(eps) children();
  }
}

// The slits and beams, as [inner, outer] u on each side, above the root.
module beam_zone(u0, u1) {
  for (su = [-1, 1]) translate([su > 0 ? u0 : -u1, -plate_side / 2 + beam_root])
    square([u1 - u0, 2 * sl]);
}

// Slider at position 0, in face coordinates. With flip, mirrored end for
// end, for a board turned over; $flip sets it from sliders_in_place.
module slider(bh = bump_h, flip = undef) {
  f = is_undef(flip) ? (is_undef($flip) ? false : $flip) : flip;
  if (f) mirror([0, 1, 0]) slider(bh, false);
  else {
  w_front = -slot_d - c;
  w_back = w_front - plate_t;
  // Stem and peg, the peg's tip seating on the socket's bottom. The stem's
  // underside slopes down at 45° from the peg to the plate, so it doesn't
  // print as a long level ledge sticking out of the plate.
  translate([0, 0, w_slope - eps]) linear_extrude(w_peg - w_slope + eps) hex(hs, stem_c);
  hull() {
    translate([0, 0, w_slope - eps]) linear_extrude(eps) hex(hs, stem_c);
    translate([0, 0, w_front - eps]) linear_extrude(eps) hull() {
      hex(hs, stem_c);
      translate([0, -(w_slope - w_front)]) hex(hs, stem_c);
    }
  }
  translate([0, 0, w_back]) {
    linear_extrude(plate_t) difference() {
      hex(hp, plate_side / 2);
      beam_zone(hp - beam_w - slit_w, hp + 1);
    }
    linear_extrude(beam_t) intersection() {
      hex(hp, plate_side / 2);
      beam_zone(hp - beam_w, hp + 1);
    }
    for (su = [-1, 1]) translate([su * bump_u, bump_v, 0]) wedge(beam_w, bh);
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
    fox(eps);
  }
}

// Reads from the front.
module fox(above = 0) {
  translate([0, 0, fox_z]) rotate([90, 0, 0])
    translate([0, 0, -fox_depth]) linear_extrude(fox_depth + above, convexity = 10)
      resize([0, fox_h], auto = true) import("fox.svg", center = true);
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
    translate([0, i == 0 ? 0 : (t[2] - 1) * pitch, 0]) let($flip = i == 1) children();
}

module cap_on() {
  translate([0, 0, cap_lift]) cap();
}

// Flat on the bed in a row, starting at the origin.
module caps_flat(n) {
  for (k = [0 : n - 1]) translate([k * (2 * cap_l + 4), 0, 0]) cap();
}

module assembly(lift) {
  color("darkgreen") body();
  color("white") numbers();
  color("orange") fox();
  color(mech_color) sliders_in_place() slider();
  color("orange") sliders_in_place([0]) cap_on();
  color("royalblue") sliders_in_place([1]) cap_on();
  color("forestgreen") translate([0, 0, lift]) lid();
  color("white") translate([0, 0, lift]) logo();
}

// Short tracks side by side, one per bump height, with their sliders and
// labels, printed upright like the body.
test_n = 3;
test_bumps = [0.75, 0.9, 1.05];
test_dx = 15;
test_v0 = 1.5 + chan_reach;

// Face coordinates to the bed, with position 0 of the first track at the
// origin.
module on_test() {
  rotate([90, 0, 0]) translate([0, test_v0, 0]) children();
}

module test_tracks() {
  for (k = [0 : len(test_bumps) - 1]) translate([k * test_dx, 0, 0]) children(0);
}

module test_block() {
  h = test_v0 + (test_n - 1) * pitch + chan_reach + 1.5;
  on_test() difference() {
    slab([-track_w - num_gap - w_one - 2, (len(test_bumps) - 1) * test_dx + hp + c + 2],
         [-test_v0, h - test_v0], 0, back_t);
    for (k = [0 : len(test_bumps) - 1]) translate([k * test_dx, 0, 0]) {
      track_cut(test_n, test_bumps[k]);
      track_labels(test_n, 1, eps);
    }
  }
}

// Top down, beside the body.
module print_lid() {
  translate([bx + 10, by, box_h]) rotate([180, 0, 0]) children();
}

if (part == "print") {
  color("darkgreen") body();
  color("white") numbers();
  color(mech_color) sliders_in_place([0]) slider();
  color("forestgreen") print_lid() lid();
  // New pieces go last, so a saved Orca project's parts keep their order.
  color("white") print_lid() logo();
  color(mech_color) sliders_in_place([1]) slider();
  color("orange") fox();
} else if (part == "body") {
  body();
} else if (part == "fox") {
  fox();
} else if (part == "numbers") {
  numbers();
} else if (part == "lid") {
  print_lid() lid();
} else if (part == "sliders") {
  sliders_in_place() slider();
} else if (part == "caps") {
  color("orange") caps_flat(2);
  color("royalblue") translate([0, 2 * cap_h + 30, 0]) caps_flat(2);
} else if (part == "test_caps") {
  color("orange") caps_flat(len(test_bumps));
} else if (part == "test_block") {
  color("darkgreen") test_block();
  color("white") on_test() test_tracks() track_labels(test_n, 1);
  color(mech_color) on_test() for (k = [0 : len(test_bumps) - 1])
    translate([k * test_dx, 0, 0]) slider(test_bumps[k]);
} else if (part == "open") {
  assembly(40);
} else if (part == "closed") {
  assembly(0);
}
