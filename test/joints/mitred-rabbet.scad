// Coupon for a mitred rabbet: the corner joint for boxes glued up from flat
// panels, each printed with its outside face on the bed.
//
// The mitre runs only through the outer `mitre` of the wall. Inside it, panel
// A ends square and sits in a rabbet in panel B. Printed outside down, every
// mating face is a wall or faces up; nothing overhangs.
//
// The rabbet locates A, and squares it: A's end on its floor, A's inside face
// against its shoulder. The mitre only has to look closed, so B's half of it
// stands off by a gap. A printed 45° face is stepped, and proud of the model
// by some of a layer; with no gap the mitres meet first, and lever A off the
// rabbet and out of square.
//
// Four pairs, at the gaps in `mitre_gaps`; a pair's notches count its place
// in that list.
//
// Tried and dropped: printing A and B as one piece joined by a skin of one to
// three layers, to fold up warm. Every one folded well past 90°, and the
// skin creased white.

// The 0.08 High Quality process: fine steps on the mitre, slow outer walls.
// Seams at the back, on the coupons' far ends and off the joint.
// export: print
// orca: process="0.08 High Quality" layer_height=0.08 initial_layer_print_height=0.2 seam_position=back

/* [Output] */
part = "fit"; // [fit, print]

/* [Joint] */
// Panel thickness. Rough; see `t`.
thick = 2;
// Depth of the mitre below the outside faces; also the thickness of B's
// tongue under the rabbet. Rough; see `mitre`.
mitre_depth = 1;
// Gaps to try between the mitre's faces, measured along a panel's face.
mitre_gaps = [0, 0.05, 0.1, 0.15];
// Depth of the glue break: a trough under the mitre's inner end, cut from
// B. The joint goes together dry, and thin glue run along the
// inside corner wicks through the rabbet; it can't cross the trough, so it
// stops short of the mitre and the outside. Rough; see `brk`.
break_depth = 0.3;
// Chamfer on the box's outside edge.
chamfer = 0.6;
// Relief on A's inside end corner, to clear the rabbet's inside corner.
relief = 0.15;

/* [Layers] */
// As sliced. Heights in the joint snap to whole layers.
first_layer = 0.2;
layer = 0.08;

/* [Coupon] */
// Along the edge, and each panel's reach away from it.
len = 30;
width = 30;
bed_gap = 5;

/* [Hidden] */
$fn = 24;
c = chamfer;

// h to the nearest height the slicer ends a layer at.
function snap(h) = first_layer + round((h - first_layer) / layer) * layer;
t = snap(thick);
mitre = snap(mitre_depth);
brk = round(break_depth / layer) * layer;

// Profiles as printed: x away from the corner, y up from the outside face.
module a_2d() {
  polygon([[c, 0], [width, 0], [width, t], [mitre + relief, t], [mitre, t - relief],
           [mitre, mitre], [c / 2, c / 2]]);
}

module b_2d(k) {
  polygon([[c, 0], [width, 0], [width, t], [t, t], [t, mitre], [mitre + k, mitre],
           [mitre + k, mitre - brk], [mitre - brk + k, mitre - brk], [(c + k) / 2, (c - k) / 2]]);
}

// A profile stood up into a panel, len along y, with n notches in its far end.
module coupon(n) {
  difference() {
    translate([0, len, 0]) rotate([90, 0, 0]) linear_extrude(len) children();
    for (i = [0 : 1 : n - 1]) translate([width, 4 + 4 * i, -1]) cylinder(d = 2.5, h = 10);
  }
}

module pair(i) {
  translate([0, i * (len + bed_gap), 0]) children();
}

module piece(name) {
  echo(piece = name);
  children();
}

// One statement, so one object, for all the B panels and one for all the A.
piece("B") color("darkgreen")
  for (i = [0 : len(mitre_gaps) - 1]) pair(i) coupon(i + 1) b_2d(mitre_gaps[i]);
piece("A") color(part == "print" ? "darkgreen" : "forestgreen") for (i = [0 : len(mitre_gaps) - 1]) pair(i)
  if (part == "print") translate([width + bed_gap, 0, 0]) coupon(i + 1) a_2d();
  // Stood on B: A's depth runs along x, its length up.
  else multmatrix([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]]) coupon(i + 1) a_2d();
