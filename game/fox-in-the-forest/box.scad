// Upright card box for The Fox in the Forest Deluxe: the 61 standard-size
// cards in sleeves, standing on end, with a lift-off lid and a two-player
// scoreboard on the back.
//
// x is across the cards, y is front (0) to back, z is up. The seam slopes
// down toward the front. Above the seam the body walls step in to an inner
// tongue, and the lid's walls cover the outer half, flush with the body.
//
// Print the body upright and the lid top down. Print the sliders separately,
// slide them into the back channels from the top, then press a plug into
// each channel above them (a drop of glue if loose).
//
// One player's tracks are upside down, so the box can lie on its front
// between the players and each reads their own score.

/* [Output] */
part = "closed"; // [closed, open, body, numbers, lid, sliders, plugs, test_block, test_slider]

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
font = "Liberation Sans:style=Bold";
num_h = 4.5;
num_depth = 0.6;
// Between a label and its slider's tip.
num_gap = 1;
pitch = 8;
// Between a sixes slider and the ones labels.
mid_gap = 1.5;
player_gap = 5;

/* [Slider] */
slot_w = 4;
// Stem length along the track, at the face.
stem_len = 4;
cap_w = 7;
cap_tip = 1.5;
cap_t = 1.2;
cap_chamfer = 0.4;
// The slider widens at 45° over this depth.
dove_h = 1.6;
plate_t = 1.0;
ceiling_gap = 0.3;
slide_clear = 0.15;
beam_t = 0.6;
slit_w = 0.5;
beam_root = 0.8;
bump_r = 0.8;
// How far the detent bump stands off the beam.
bump_h = 0.4;
// Bump position along the slider, from its center.
bump_v = 2.4;
// Plug above the top slider position, up to the seam.
plug_len = 5;
plug_clear = 0.05;

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

chan_d = dove_h + plate_t + ceiling_gap;
assert(chan_d + 0.8 <= back_t, "back wall too thin for the slider channel");
// Slider half-widths at the face and at the dovetail top.
sw0 = slot_w / 2 - slide_clear;
sw1 = sw0 + dove_h;
// Slider half-lengths at the face and at the dovetail top.
sl0 = stem_len / 2;
sl1 = sl0 + dove_h;
// Channel half-width at depth, and its reach into the beam-side wall.
ch_hw = slot_w / 2 + dove_h;
ch_hw_beam = ch_hw + bump_h;
bump_cu = sw1 - bump_r + bump_h;

// Each player has a sixes slider (0, 6, 12, 18) and a ones slider (0-5).
// Every track ends at the same top row, just under the plugs.
n_sixes = 4;
n_ones = 6;
v_top = z_sb - plug_len - sl1 - slide_clear;
v_ones = v_top - (n_ones - 1) * pitch;
// Bottom of the deepest channel, used by the test block.
v0 = 1.5 + slide_clear + sl1;
assert(v_ones - sl1 - slide_clear >= 1.5, "pitch too large for the back wall");
cap_len = pitch - 1;

num_size = num_h / 0.97;
w_two = 1.12 * num_size;
w_one = 0.56 * num_size;
cap_reach = cap_w / 2 + cap_tip;
// Slot centers in one player's board, from its left edge.
u_sixes = w_two + num_gap + cap_reach;
u_ones = u_sixes + cap_w / 2 + mid_gap + w_one + num_gap + cap_reach;
board_w = u_ones + cap_w / 2;
board_l = -(2 * board_w + player_gap) / 2;
// Tracks as [u, v of position 0, positions, step, flipped]. The left player
// reads upright; the right player's board is turned 180°, so its zeros are
// at the top.
tracks = [
  [board_l + u_sixes, v_top - (n_sixes - 1) * pitch, n_sixes, 6, false],
  [board_l + u_ones, v_ones, n_ones, 1, false],
  [-board_l - u_sixes, v_top, n_sixes, 6, true],
  [-board_l - u_ones, v_top, n_ones, 1, true],
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

module channel_2d() {
  hw = slot_w / 2;
  polygon([[-hw, 1], [-hw, 0], [-ch_hw, -dove_h], [-ch_hw, -chan_d],
           [ch_hw, -chan_d], [ch_hw, -dove_h], [hw, 0], [hw, 1]]);
}

// Channel in face coordinates from v0 up to v1.
module chan(v0, v1) {
  translate([0, v0, 0]) rotate([-90, 0, 0]) mirror([0, 1, 0])
    linear_extrude(v1 - v0) channel_2d();
}

// One track's travel and detent notches, with position i at v = i * pitch.
module track_cut(n) {
  chan(-sl1 - slide_clear, (n - 1) * pitch + sl1 + slide_clear);
  // Detent notches, reaching above the plate for the slider's play.
  for (i = [0 : n - 1])
    translate([bump_cu, i * pitch + bump_v, -chan_d])
      cylinder(r = bump_r + slide_clear, h = chan_d - dove_h + 0.4);
}

module label(s, u, v) {
  translate([u - cap_reach - num_gap, v])
    text(s, size = num_size, font = font, halign = "right", valign = "center");
}

module track_labels(n, step, above = 0) {
  translate([0, 0, -num_depth]) linear_extrude(num_depth + above)
    for (i = [0 : n - 1]) label(str(step * i), 0, i * pitch);
}

module at_track(t) {
  translate([t[0], t[1], 0]) rotate([0, 0, t[4] ? 180 : 0]) children();
}

module labels(above = 0) {
  for (t = tracks) at_track(t) track_labels(t[2], t[3], above);
}

module board_cuts() {
  for (t = tracks) {
    at_track(t) track_cut(t[2]);
    // Entry for the slider, from the top row up through the tongue.
    translate([t[0], 0, 0]) chan(v_top, box_h + 1);
  }
  labels(eps);
}

module plug_2d() {
  offset(delta = -plug_clear) intersection() {
    channel_2d();
    translate([-ch_hw - 1, -chan_d - 1]) square([2 * ch_hw + 2, chan_d + 1]);
  }
}

module cap_2d() {
  polygon([[-cap_reach, 0], [-cap_w / 2, -cap_len / 2], [cap_w / 2, -cap_len / 2],
           [cap_w / 2, cap_len / 2], [-cap_w / 2, cap_len / 2]]);
}

module slider() {
  d1 = dove_h + plate_t;
  hull() {
    linear_extrude(eps) cap_2d();
    translate([0, 0, cap_t - eps]) linear_extrude(eps) offset(delta = -cap_chamfer) cap_2d();
  }
  difference() {
    union() {
      hull() {
        slab([-sw0, sw0], [-sl0, sl0], 0, eps);
        slab([-sw1, sw1], [-sl1, sl1], dove_h - eps, dove_h);
      }
      slab([-sw1, sw1], [-sl1, sl1], dove_h - eps, d1);
    }
    // Frees the detent beam along the +u edge.
    slab([sw1 - beam_t - slit_w, sw1 - beam_t], [-sl1 + beam_root, sl1 + 1], 0, d1 + 1);
  }
  intersection() {
    translate([bump_cu, bump_v, -d1]) cylinder(r = bump_r, h = plate_t);
    slab([sw1 - beam_t, sw1 + 1], [-sl1, sl1], dove_h, d1);
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

module lid() {
  difference() {
    outer();
    below_seam();
    tongue_box(lip_clear, [0, box_h - top_t]);
    snaps(snap_r + snap_clear, snap_len + 2 * snap_clear);
  }
}

module sliders_in_place() {
  on_back() for (t = tracks) at_track(t) slider();
}

module chan_plug(u, v0, v1) {
  translate([u, v0, 0]) rotate([-90, 0, 0]) mirror([0, 1, 0])
    linear_extrude(v1 - v0) plug_2d();
}

module plugs_in_place() {
  on_back() for (t = tracks) chan_plug(t[0], v_top + sl1 + slide_clear, z_sb);
}

// Flat on the bed, cap down.
module print_slider() {
  translate([0, 0, cap_t]) rotate([180, 0, 0]) slider();
}

module assembly(lift) {
  color("darkgreen") body();
  color("white") numbers();
  color("orange") sliders_in_place();
  color("darkgreen") plugs_in_place();
  color("forestgreen") translate([0, 0, lift]) lid();
}

// A short track and plug for checking the fit, printed upright like the body.
module test_block() {
  n = 3;
  v_t = v0 + (n - 1) * pitch;
  h = v_t + sl1 + slide_clear + plug_len;
  rotate([90, 0, 0]) difference() {
    slab([-cap_reach - num_gap - w_one - 2, ch_hw_beam + 2], [0, h], 0, back_t);
    translate([0, v0, 0]) track_cut(n);
    chan(v_t, h + 1);
    translate([0, v0, 0]) track_labels(n, 1, eps);
  }
}

if (part == "body") {
  body();
} else if (part == "numbers") {
  numbers();
} else if (part == "lid") {
  translate([0, by, box_h]) rotate([180, 0, 0]) lid();
} else if (part == "sliders") {
  for (i = [0 : 3]) translate([i * (cap_w + cap_tip + 3), 0, 0]) print_slider();
} else if (part == "plugs") {
  for (i = [0 : 3]) translate([i * (2 * ch_hw + 3), 0, 0]) linear_extrude(plug_len) plug_2d();
} else if (part == "test_block") {
  test_block();
} else if (part == "test_slider") {
  print_slider();
} else if (part == "open") {
  assembly(40);
} else if (part == "closed") {
  assembly(0);
}
