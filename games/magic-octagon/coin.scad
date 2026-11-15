// An octagonal coin with an arrow inlaid in each face, pointing at a vertex;
// the two arrows are a quarter turn apart.
//
// It comes in three shapes: the octagon; a round coin; and a round one with a
// reeded edge, like a quarter's, which has a bump where each of the octagon's
// vertices would be.
//
// Two halves, split through the coin's thickness and printed face down, so
// both faces come off the bed. Each half has a pin and a crush-ribbed hole on
// its glue side, placed so the halves only go together one way: with the
// arrows a quarter turn apart.
//
// In a half's own frame the face is at z = 0 and the glue side is up.

// export: print

use <../../lib/orca.scad>
use <../../lib/piece.scad>

/* [Output] */
// `print` is one of each shape; the others show `shape`.
part = "assembled"; // [assembled, exploded, print]
shape = "octagon"; // [octagon, round, knurled]

/* [Coin] */
// Across the vertices, or the knurls.
d = 40;
half_t = 2.5;
// Rounds the vertices.
corner_r = 1;
face_chamfer = 0.6;
// A small chamfer either side of the seam hides a little misalignment.
seam_chamfer = 0.2;

/* [Knurling] */
// Reeds around the edge, as on a quarter: flat-topped, with a groove between
// each two. A multiple of 8, for one at each vertex.
knurls = 96;
// The grooves, at the edge and at their floors.
groove_w = 0.65;
groove_floor = 0.2;
groove_d = 0.4;
// The bumps at the vertices: reeds that are wider, and stand this far out of
// the edge.
bump_w = 2;
bump_top = 1.2;
bump_h = 0.5;
bump_r = 0.2;

/* [Arrow] */
// Where each face's arrow points, in the half's own frame. The top half is
// flipped over the x axis.
angles = [0, 90];
inlay = 0.6;
arrow_tail = -12;
arrow_tip = 15;
shaft_w = 4;
head_w = 12;
head_l = 9;
arrow_r = 0.5;

/* [Joint] */
pin_d = 4;
pin_h = 1.2;
// From the centre, on the diagonals between the arrows.
pin_r = 11;
pin_c = 0.15;
pin_chamfer = 0.4;
// The hole is this much deeper than the pin, for glue.
hole_extra = 0.3;
ribs = 3;
rib_w = 0.8;
rib_press = 0.1;

/* [Colors] */
c_half = ["Gold", "Black"];
c_arrow = ["Black", "Gold"];

/* [Hidden] */
$fn = 64;
eps = 0.01;

shapes = ["octagon", "round", "knurled"];
// What is drawn is of $shape.
$shape = shape;
assert(knurls % 8 == 0, "knurls must be a multiple of 8");

module outline(inset = 0) {
  if ($shape == "octagon")
    offset(r = corner_r) offset(delta = -corner_r - inset) circle(d = d, $fn = 8);
  else
    circle(r = d / 2 - inset, $fn = 192);
}

// A convex outline, chamfered at the face and the seam: its children, which
// draw themselves $inset smaller.
module chamfered() {
  hull() {
    linear_extrude(eps) { $inset = face_chamfer; children(); }
    translate([0, 0, face_chamfer])
      linear_extrude(half_t - face_chamfer - seam_chamfer) { $inset = 0; children(); }
    translate([0, 0, half_t - eps]) linear_extrude(eps) { $inset = seam_chamfer; children(); }
  }
}

// A groove between two reeds, into the edge at +x. The faces' chamfers are
// deeper than it, so it runs out before the face and leaves a rim.
module groove() {
  translate([d / 2, 0, -eps]) linear_extrude(half_t + 2 * eps) polygon([
    [1, groove_w / 2 + 1], [0, groove_w / 2], [-groove_d, groove_floor / 2],
    [-groove_d, -groove_floor / 2], [0, -groove_w / 2], [1, -groove_w / 2 - 1],
  ]);
}

// A vertex's bump, chamfered by leaning in, as the edge under it does.
module bump_2d() {
  translate([d / 2 - $inset, 0]) offset(r = bump_r) offset(delta = -bump_r) polygon([
    [-1, bump_w / 2], [0, bump_w / 2], [bump_h, bump_top / 2],
    [bump_h, -bump_top / 2], [0, -bump_w / 2], [-1, -bump_w / 2],
  ]);
}

module blank() {
  if ($shape == "knurled") {
    difference() {
      chamfered() outline($inset);
      for (i = [0:knurls - 1]) rotate((i + 0.5) * 360 / knurls) groove();
    }
    for (i = [0:7]) rotate(i * 45) chamfered() bump_2d();
  } else {
    chamfered() outline($inset);
  }
}

module arrow_2d() {
  offset(r = arrow_r) offset(delta = -arrow_r) {
    translate([arrow_tail, -shaft_w / 2])
      square([arrow_tip - head_l - arrow_tail + 1, shaft_w]);
    polygon([
      [arrow_tip, 0],
      [arrow_tip - head_l, head_w / 2],
      [arrow_tip - head_l, -head_w / 2],
    ]);
  }
}

module arrow(angle) {
  rotate(angle) linear_extrude(inlay) arrow_2d();
}

// The pin is at +45 degrees and the hole at -45, so that flipping a half over
// the x axis puts each over the other.
module at_pin() { rotate(45) translate([pin_r, 0, half_t]) children(); }
module at_hole() { rotate(-45) translate([pin_r, 0, half_t]) children(); }

module pin() {
  cylinder(d = pin_d, h = pin_h - pin_chamfer);
  translate([0, 0, pin_h - pin_chamfer])
    cylinder(d1 = pin_d, d2 = pin_d - 2 * pin_chamfer, h = pin_chamfer);
}

module hole() {
  hole_d = pin_d + 2 * pin_c;
  depth = pin_h + hole_extra;
  difference() {
    union() {
      translate([0, 0, -depth]) cylinder(d = hole_d, h = depth + eps);
      translate([0, 0, -pin_chamfer])
        cylinder(d1 = hole_d, d2 = hole_d + 2 * pin_chamfer, h = pin_chamfer + eps);
    }
    // Crush ribs, stopping short of the mouth's chamfer.
    for (i = [0:ribs - 1]) rotate(i * 360 / ribs)
      translate([pin_d / 2 - rib_press, -rib_w / 2, -depth - eps])
        cube([1, rib_w, depth - pin_chamfer]);
  }
}

module half(angle) {
  difference() {
    blank();
    translate([0, 0, -eps]) scale([1, 1, 1 + eps]) arrow(angle);
    at_hole() hole();
  }
  at_pin() pin();
}

// Into place on the coin: the second half goes on upside down.
module place(i, e = 0) {
  if (i == 0) translate([0, 0, -e]) children();
  else translate([0, 0, 2 * half_t + e]) rotate([180, 0, 0]) children();
}

// Each shape's two halves are a row on the bed.
module bed(i, row = 0) {
  pitch = d + 2 * bump_h + 5;
  translate([i * pitch, -row * pitch, 0]) children();
}

// On the faces, which print on the bed: rings around the octagons or chords
// around the round ones, and lines along each arrow. Angles follow the model,
// so that turning it in Orca turns the lines too.
function half_settings(shape) =
  [orca_bottom_pattern(shape == "octagon" ? "octagramspiral" : "archimedeanchords")];
function arrow_settings(angle) =
  [orca_bottom_pattern("monotonic"), orca_bottom_direction(angle), orca_align_infill_to_model()];

if (part == "print") {
  for (row = [0:len(shapes) - 1]) {
    $shape = shapes[row];
    $piece_prefix = $shape;
    for (i = [0, 1]) {
      piece(str("half ", i), half_settings($shape))
        color(c_half[i]) bed(i, row) half(angles[i]);
      piece(str("arrow ", i), arrow_settings(angles[i]))
        color(c_arrow[i]) bed(i, row) arrow(angles[i]);
    }
  }
} else {
  e = part == "exploded" ? 6 : 0;
  for (i = [0, 1]) {
    color(c_half[i]) place(i, e) half(angles[i]);
    color(c_arrow[i]) place(i, e) arrow(angles[i]);
  }
}
