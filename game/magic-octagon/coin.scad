// An octagonal coin with an arrow inlaid in each face, pointing at a vertex;
// the two arrows are a quarter turn apart.
//
// Two halves, split through the coin's thickness and printed face down, so
// both faces come off the bed. Each half has a pin and a crush-ribbed hole on
// its glue side, placed so the halves only go together one way: with the
// arrows a quarter turn apart.
//
// In a half's own frame the face is at z = 0 and the glue side is up.

// export: print

/* [Output] */
part = "assembled"; // [assembled, exploded, print]

/* [Coin] */
// Across the vertices.
d = 40;
half_t = 2.5;
// Rounds the vertices.
corner_r = 1;
face_chamfer = 0.6;
// A small chamfer either side of the seam hides a little misalignment.
seam_chamfer = 0.2;

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
// One for each half. Each distinct color is a filament; halves or arrows that
// share a color share a filament.
c_half = ["DimGray", "FireBrick"];
c_arrow = ["Gold", "Gold"];

/* [Hidden] */
$fn = 64;
eps = 0.01;

module outline(inset = 0) {
  offset(r = corner_r) offset(delta = -corner_r - inset) circle(d = d, $fn = 8);
}

module blank() {
  hull() {
    linear_extrude(eps) outline(face_chamfer);
    translate([0, 0, face_chamfer])
      linear_extrude(half_t - face_chamfer - seam_chamfer) outline();
    translate([0, 0, half_t - eps]) linear_extrude(eps) outline(seam_chamfer);
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

module bed(i) { translate([i * (d + 5), 0, 0]) children(); }

// Each top-level statement of a layout is a piece: a part in Orca.
module piece(name, orca = "") {
  echo(piece = name, orca = orca);
  children();
}

// On the faces, which print on the bed: rings around the octagons, and lines
// along each arrow. Angles follow the model, so that turning it in Orca turns
// the lines too.
orca_half = "bottom_surface_pattern=concentric";
function orca_arrow(angle) = str(
  "bottom_surface_pattern=monotonic bottom_layer_direction=", angle,
  " align_infill_direction_to_model=1"
);

if (part == "print") {
  piece("half 0", orca_half) color(c_half[0]) bed(0) half(angles[0]);
  piece("half 1", orca_half) color(c_half[1]) bed(1) half(angles[1]);
  piece("arrow 0", orca_arrow(angles[0])) color(c_arrow[0]) bed(0) arrow(angles[0]);
  piece("arrow 1", orca_arrow(angles[1])) color(c_arrow[1]) bed(1) arrow(angles[1]);
} else {
  e = part == "exploded" ? 6 : 0;
  for (i = [0, 1]) {
    color(c_half[i]) place(i, e) half(angles[i]);
    color(c_arrow[i]) place(i, e) arrow(angles[i]);
  }
}
