// A table sign: "Play Music", a QR code with a note in its middle, and its
// address, inlaid in black, flush in a white panel. It stands in two feet, which
// slot onto its bottom edge, and pack into pockets in its back, held there
// by magnets: three of 5 x 1 mm glued into each foot, and one over each of
// them in its pocket's floor, each in a hole with crush ribs.
// Or it hangs, feet packed, by a keyhole in its back, on a screw's head.
//
// The panel prints face down, its pockets and keyhole open to the top, the
// feet flat beside it, a left and a right.
//
// x is right and y is up, as it reads; z is out of the face, the back at z = 0.

// export: print

use <../../lib/piece.scad>

/* [Output] */
// "stand" is how it sits on a table; "stowed" has the feet in its back.
part = "print"; // [print, stand, stowed]

/* [Panel] */
w = 100;
// Panel thickness: the feet's pockets, the magnets over them, and a skin.
t = 6.2;
corner_r = 4;
edge_chamfer = 0.8;
// Panel edge to the text, at the top and bottom.
margin = 9;

/* [Face] */
// How deep the black goes into the white.
inlay = 0.6;
// One square of the code.
module_w = 2.4;
// Clear white around the code, in squares. Scanners want four.
quiet = 4;
// The squares cleared from the code's middle, and the note's size in them.
clear_n = 9;
note_n = 7;
font = "TeX Gyre Schola:style=Bold";
title = "Play Music";
title_size = 10.4;
url = "https://party.paholg.com";
url_size = 4.5;

/* [Feet] */
// Each foot's place on the bottom edge, from the panel's center, in "stand".
feet_x = 30;
foot_t = 3.2;
// How far back the sign leans.
lean = 15;
// The foot on the table, ahead of the panel's face and behind it.
foot_front = 12;
foot_back = 45;
// Under the panel's edge.
base_t = 3;
// How far up the panel's back the foot goes, and up its face: the address
// starts at `margin`.
back_h = 32;
jaw_h = 6.5;
// The front jaw's thickness, and the width of the bars the rest is made of.
jaw_w = 5;
bar = 5;
// The slot, over the panel's thickness, and how far the bumps on each of its
// walls stand in: twice that, less the first, is what holds the panel.
slot_clear = 0.3;
grip = 0.2;

/* [Magnets] */
magnet_d = 5;
magnet_h = 1;
// Room for glue: around the magnet, and under it.
magnet_gap = 0.15;
magnet_deep = 0.2;
// Crush ribs down each hole's wall, and how far into the magnet they reach.
magnet_ribs = 4;
magnet_rib_w = 0.8;
magnet_rib_press = 0.1;
// Foot around its magnet.
magnet_wall = 1.35;
// How much deeper the pockets' holes are: the magnets that far apart, for a
// foot to come out by a finger.
magnet_sink = 0.4;
// Their places along the foot's base, from the panel's face, and up its back,
// from the slot's floor.
magnet_base = [20, 34];
magnet_up = [18];

/* [Pockets] */
// Around a stowed foot, and how far under the panel's back it lies.
gap = 0.3;
top_gap = 0.2;
// The pockets' bottom, from the panel's, and the wall between the two.
stow_y = 24;
stow_wall = 6;
// The scoop for a finger, and how far past the feet's heels its middle is.
finger_r = 8;
finger_up = 2;
// How far short of the heels' ends the wall between the pockets stops, for a
// finger to reach both heels.
wall_back = 12;
// Off the feet's edges, top and bottom, and the mouths of what's cut in the
// panel's back.
bed_chamfer = 0.4;

/* [Keyhole] */
// The screw's head goes in at the bottom, and its shank slides up the slot.
hang_head_d = 9;
hang_shank_d = 4.4;
// What the head hangs on, and the room behind that for it: the lip prints as
// a ceiling, so the room narrows to the slot at 45 degrees, as a countersunk
// head does.
hang_lip = 1.4;
hang_head_h = 3;
// How far the screw slides.
hang_len = 8;
// The screw's place once hung, from the panel's top.
hang_top = 16;

/* [Hidden] */
eps = 0.01;
$fn = 48;

// The code for `url`, version 3-H, top row first. From segno:
//   segno.make("https://party.paholg.com", error="h", micro=False, boost_error=False)
// H mends 30% of it, which is what lets the note take its middle.
qr = [
  "11111110101010011011001111111",
  "10000010001100010001101000001",
  "10111010001110011011001011101",
  "10111010111011101010101011101",
  "10111010000011001101001011101",
  "10000010001010011111101000001",
  "11111110101010101010101111111",
  "00000000011011001111000000000",
  "00101110101010100010110001001",
  "11010100111100111100111000101",
  "01101111010001110000000100011",
  "01111000101100001010011010010",
  "11010011101100101100101101000",
  "01111100111100001110111100011",
  "01101110000100101010110100101",
  "00110001011101001011010100000",
  "01001111111110111100111001000",
  "01001001110101001010111001011",
  "10110011100011010010110010111",
  "01010101111110000110101110010",
  "10100111011110111111111110000",
  "00000000100010111000100010001",
  "11111110011000111011101010111",
  "10000010111001000100100010010",
  "10111010110111100100111111011",
  "10111010010111101100110011000",
  "10111010111011011011000111101",
  "10000010010110111001100100010",
  "11111110001001001000110010011",
];

qr_n = len(qr);
qr_w = qr_n * module_w;
quiet_w = quiet * module_w;

// Bottom up: the address, the code, the title.
url_y = margin;
qr_y = url_y + url_size + quiet_w;
title_y = qr_y + qr_w + quiet_w;
// The title's "y" hangs below its line, into the quiet zone's spare room.
h = title_y + title_size + margin;

slot_w = t + slot_clear;
pocket_d = foot_t + top_gap;
heel_h = 4;
round_r = 1.2;
bump_r = 0.6;

hole_d = magnet_d + 2 * magnet_gap;
hole_h = magnet_h + magnet_deep;
boss_r = hole_d / 2 + magnet_wall;
// A magnet's center, in from its bar's outer edge: the boss stands into the
// foot's middle, not out of it.
magnet_in = max(boss_r, bar / 2);
// Each magnet's place in the foot's side, and the turn from the foot's y to
// the way across the bar it is in.
magnets = [
  for (x = magnet_base) [[x, magnet_in], 0],
  for (u = magnet_up) [slot_xy(slot_w + magnet_in, u), 90 - lean],
];
// The steps that chamfers are made of, and the mouth of a magnet's hole.
layer = 0.2;
// The keyhole's room, from the head's width to the shank's.
hang_taper = (hang_head_d - hang_shank_d) / 2;

assert(t - pocket_d - magnet_sink - hole_h - inlay >= 0.5, "the white under the magnets is too thin");
assert(foot_t - hole_h >= 0.8, "the foot under its magnet is too thin");
assert(t - hang_lip - hang_head_h - inlay >= 0.6, "the white under the keyhole is too thin");
assert(hang_taper <= hang_head_h, "the keyhole's room is too shallow to narrow to its slot");
assert(h - hang_top - hang_len - hang_head_d / 2 > stow_y + foot_front + foot_back + finger_up + finger_r + 2,
       "the keyhole runs into the pockets");
assert(jaw_h < margin - url_size * 0.4, "the front jaw would cover the address");
assert(qr_w + 2 * quiet_w <= w, "the code's quiet zone is wider than the panel");
echo(str("Sign is ", w, " x ", h, " x ", t, " mm, and leans back ", lean, " degrees"));

// A plate with rounded corners, chamfered top and bottom, from the origin.
module plate(size, r, k) {
  module outline(inset) translate([r, r])
    offset(r = r - inset) square([size.x - 2 * r, size.y - 2 * r]);
  hull() {
    linear_extrude(eps) outline(k);
    translate([0, 0, k]) linear_extrude(size.z - 2 * k) outline(0);
    translate([0, 0, size.z - eps]) linear_extrude(eps) outline(k);
  }
}

// What's drawn in 2D, h thick from z = 0, in steps a layer high: grown by k_bed
// at the bed and by k_top at its top, or shrunk, for less than nothing.
module stepped(h, k_bed, k_top = 0) {
  n_bed = round(abs(k_bed) / layer);
  n_top = round(abs(k_top) / layer);
  for (i = [0:1:n_bed - 1]) translate([0, 0, i * layer]) linear_extrude(layer + eps)
    offset(delta = k_bed * (n_bed - i - 0.5) / n_bed) children();
  translate([0, 0, n_bed * layer]) linear_extrude(h - (n_bed + n_top) * layer) children();
  for (i = [0:1:n_top - 1]) translate([0, 0, h - (i + 1) * layer - eps]) linear_extrude(layer + eps)
    offset(delta = k_top * (n_top - i - 0.5) / n_top) children();
}

// A foot's side is drawn standing: x back along the table, y up from it.
// The slot leans in it, and has a frame of its own: v from the wall at the
// panel's face to the one at its back, u up the panel from the slot's floor.
function slot_xy(v, u) = [
  v * cos(lean) + u * sin(lean),
  base_t + slot_w * sin(lean) - v * sin(lean) + u * cos(lean),
];

module foot_2d() {
  // A triangle of bars behind the panel, and a jaw ahead of it.
  difference() {
    offset(r = round_r) offset(delta = -round_r) polygon([
      [-foot_front, 0],
      [foot_back, 0],
      [foot_back, heel_h],
      slot_xy(slot_w + bar, back_h),
      slot_xy(slot_w, back_h),
      slot_xy(slot_w, 0),
      slot_xy(0, 0),
      slot_xy(0, jaw_h),
      slot_xy(-jaw_w, jaw_h),
      [-foot_front, base_t],
    ]);
    offset(r = 2) offset(delta = -bar - 2) polygon([
      [slot_xy(slot_w, 0).x, 0],
      slot_xy(slot_w, back_h),
      slot_xy(slot_w + bar, back_h),
      [foot_back, heel_h],
      [foot_back, 0],
    ]);
  }
  // Bumps to hold the panel: a pair near the floor, and one up the back for
  // the panel to lean on.
  for (u = [3.5, back_h - 4]) translate(slot_xy(slot_w + bump_r - grip, u)) circle(bump_r);
  translate(slot_xy(grip - bump_r, 3.5)) circle(bump_r);
  // Around each magnet, should the bars be narrower than it wants.
  for (m = magnets) translate(m[0]) circle(boss_r);
}

// A foot, as it prints: its magnets go in from the top, which is the side
// that faces into its pocket. So the two are a left and a right.
module foot() {
  difference() {
    stepped(foot_t, -bed_chamfer, -bed_chamfer) foot_2d();
    for (m = magnets) translate([m[0].x, m[0].y, foot_t - hole_h]) rotate(m[1]) {
      // The ribs stop a layer short of the mouth, for the magnet to start in.
      linear_extrude(hole_h - layer + eps) magnet_hole_2d();
      translate([0, 0, hole_h - layer]) cylinder(d = hole_d, h = layer + eps);
    }
  }
}

// A magnet's hole, less its crush ribs.
module magnet_hole_2d() difference() {
  circle(d = hole_d);
  for (i = [0:magnet_ribs - 1]) rotate(i * 360 / magnet_ribs)
    translate([magnet_d / 2 - magnet_rib_press, -magnet_rib_w / 2]) square([1, magnet_rib_w]);
}

// The holes in a pocket's floor for its magnets. As in the feet, the ribs stop
// a layer short of the mouth.
module magnet_holes() for (m = magnets) translate([m[0].x, m[0].y, pocket_d]) rotate(m[1]) {
  translate([0, 0, -eps]) cylinder(d = hole_d, h = layer + eps);
  translate([0, 0, layer - eps]) linear_extrude(magnet_sink + hole_h - layer + eps) magnet_hole_2d();
}

// A foot's place in the panel's back: side s, heel up, its base to the middle.
module stow(s) translate([s * stow_wall / 2, stow_y + foot_front, 0])
  scale([-s, 1, 1]) rotate(90) children();

// A foot's pocket, which it drops into: the magnets are what hold it.
module pocket_2d() offset(delta = gap) foot_2d();

// The keyhole, where the screw ends up: at the origin, in the panel's back.
module keyhole() {
  module run(d) hull() for (y = [0, -hang_len]) translate([0, y]) circle(d = d);
  stepped(hang_lip + eps, bed_chamfer) {
    run(hang_shank_d);
    translate([0, -hang_len]) circle(d = hang_head_d);
  }
  translate([0, 0, hang_lip]) {
    hull() {
      linear_extrude(eps) run(hang_shank_d);
      translate([0, 0, hang_taper]) linear_extrude(hang_head_h - hang_taper) run(hang_head_d);
    }
    translate([0, -hang_len]) cylinder(d = hang_head_d, h = hang_head_h);
  }
}

module body() {
  difference() {
    translate([-w / 2, 0, 0]) plate([w, h, t], corner_r, edge_chamfer);
    translate([0, 0, -eps]) {
      for (s = [-1, 1]) stow(s) {
        stepped(pocket_d + eps, bed_chamfer) pocket_2d();
        magnet_holes();
      }
      translate([0, stow_y + foot_front + foot_back, 0])
        stepped(pocket_d + eps, bed_chamfer) {
          translate([0, finger_up]) circle(finger_r);
          // The wall's end, round.
          a = stow_wall / 2 - gap;
          difference() {
            translate([-a - eps, -wall_back - a]) square([2 * a + 2 * eps, wall_back + a]);
            translate([0, -wall_back - a]) circle(a);
          }
        }
      translate([0, h - hang_top, 0]) keyhole();
    }
    face(eps);
  }
}

module code() {
  // The middle squares, left out for the note.
  lo = (qr_n - clear_n) / 2;
  function cleared(i) = i >= lo && i < lo + clear_n;
  // A hair over, so that neighbors are one solid.
  translate([-qr_w / 2, qr_y]) for (row = [0:qr_n - 1], col = [0:qr_n - 1])
    if (qr[row][col] == "1" && !(cleared(row) && cleared(col)))
      translate([col * module_w, (qr_n - 1 - row) * module_w]) square(module_w + eps);
}

// The note, s tall, about the origin. It is Nicu Buculei's, from Open Clip
// Art, in the public domain:
// https://commons.wikimedia.org/wiki/File:Music_note.svg
module note(s) {
  resize([0, s], auto = true) import("note.svg", center = true);
}

// The black, in the face: `more` further out of it, to cut its place.
module face(more = 0) {
  translate([0, 0, t - inlay]) linear_extrude(inlay + more) {
    translate([0, title_y]) text(title, size = title_size, font = font, halign = "center");
    code();
    translate([0, qr_y + qr_w / 2]) note(note_n * module_w);
    translate([0, url_y]) text(url, size = url_size, font = font, halign = "center");
  }
}

// Each color a statement of its own, here at the top, to be a part of its own.
// The sign, where its feet hold it: its back's bottom edge in their slots.
module placed() {
  if (part == "stand") {
    at = slot_xy(slot_clear / 2 + t, 0);
    translate([0, at.x, at.y]) rotate([90 - lean, 0, 0]) children();
  } else if (part == "print") {
    translate([0, 0, t]) rotate([0, 180, 0]) children();
  } else {
    children();
  }
}

module feet() {
  for (i = [0, 1]) {
    s = 2 * i - 1;
    if (part == "stand")
      translate([s * feet_x, 0, 0]) rotate([90, 0, 90]) translate([0, 0, -foot_t / 2]) foot();
    else if (part == "stowed") stow(s) foot();
    else translate([w / 2 + 50, 10 - stow_y, 0]) stow(s) foot();
  }
}

piece("sign") color("white") placed() body();
piece("feet") color("white") feet();
piece("text") color("black") placed() face();
