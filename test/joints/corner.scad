// Coupon for a box corner in mitred rabbets (see mitred-rabbet.scad): the
// three panels that meet there, each printed with its outside face on the bed.
//
// The corner is at the origin and the box's inside is +x, +y, +z. Panel i's
// outside face is the plane where axis i is 0: 0 is a side, 1 the front, 2
// the floor. That is also their rank: along each edge, the higher panel ends
// square and sits in a rabbet in the lower one. So the front drops between
// the sides, and the floor drops into all the walls.
//
// Each panel is its slab, less what the joint along each of its two edges
// gives to the other panel there. Those cuts run on through the corner, and
// between them share it out with nothing left over and nothing overhanging.

// export: print
// orca: process="0.08 High Quality" layer_height=0.08 initial_layer_print_height=0.2 seam_position=back

/* [Output] */
part = "fit"; // [fit, exploded, print]

/* [Joint] */
// Panel thickness: side, front, floor. Rough; see `t`.
thick = [2, 3.4, 2];
// Depth of the mitre below the outside faces; also the thickness of the
// tongue under a rabbet. Rough; see `mitre`.
mitre_depth = 1;
// Gap between the mitre's faces, taken from the lower panel and measured
// along its face. At 0.2 mm layers a printed 45° face is proud of the model,
// and levers the panels acute; at 0.08 mm, mitred-rabbet.scad's pairs were
// squarest and tightest with none, and leant further open with each 0.05 mm.
mitre_gap = 0;
// Gap between a panel's end and the floor of the rabbet it sits in.
gap = 0;
// Depth of the glue break: a trough under the mitre's inner end, cut from
// the lower panel. The joint goes together dry, and thin glue run along the
// inside corner wicks through the rabbet; it can't cross the trough, so it
// stops short of the mitre and the outside. Rough; see `brk`.
break_depth = 0.3;
// Chamfer on the box's outside edges.
chamfer = 0.6;
// Relief on a panel's inside end corner, to clear the rabbet's inside corner.
relief = 0.15;

/* [Layers] */
// As sliced. Heights in the joint snap to whole layers.
first_layer = 0.2;
layer = 0.08;

/* [Coupon] */
// Length of each edge.
len = 30;
bed_gap = 5;
explode = 8;

/* [Hidden] */
big = 2 * len;

// h to the nearest height the slicer ends a layer at.
function snap(h) = first_layer + round((h - first_layer) / layer) * layer;
t = [for (h = thick) snap(h)];
mitre = snap(mitre_depth);
brk = round(break_depth / layer) * layer;
names = ["side", "front", "floor"];

function unit(i) = [for (k = [0 : 2]) k == i ? 1 : 0];

// Children drawn in (depth below a, depth below b, along their edge) land in
// box coordinates.
module edge_frame(a, b) {
  ea = unit(a); eb = unit(b); ec = unit(3 - a - b);
  multmatrix([for (k = [0 : 2]) [ea[k], eb[k], ec[k], 0]]) translate([0, 0, -1]) linear_extrude(big)
    children();
}

// What panel a, the higher, gives up along its edge with b: outside the
// mitre, and then below its square end.
module cut_higher(a, b) {
  e = mitre + gap;
  edge_frame(a, b)
    polygon([[-1, -1], [mitre, mitre], [mitre, e], [t[a] - relief, e], [t[a], e + relief],
             [big, e + relief], [big, -1]]);
}

// What panel b, the lower, gives up along its edge with a: outside the
// mitre, the glue break, and then the rabbet, as wide as a is thick.
module cut_lower(a, b) {
  edge_frame(a, b)
    polygon([[mitre_gap - 1, -1], [mitre - brk + mitre_gap, mitre - brk], [mitre + mitre_gap, mitre - brk],
             [mitre + mitre_gap, mitre], [t[a], mitre], [t[a], big], [-1, big], [-1, -1]]);
}

module outer() {
  c = chamfer;
  hull() {
    translate([c, c, 0]) cube(big);
    translate([c, 0, c]) cube(big);
    translate([0, c, c]) cube(big);
  }
}

module panel(i) {
  intersection() {
    difference() {
      cube([for (k = [0 : 2]) k == i ? t[i] : len]);
      for (j = [0 : 2]) if (j != i) {
        if (i > j) cut_higher(i, j);
        else cut_lower(j, i);
      }
    }
    outer();
  }
}

// On the bed, outside face down.
module flat(i) {
  translate([i * (len + bed_gap), 0, 0])
    if (i == 0) multmatrix([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]]) children();
    else if (i == 1) multmatrix([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]]) children();
    else children();
}

module piece(name) {
  echo(piece = name);
  children();
}

colors = ["darkgreen", "forestgreen", "seagreen"];
if (part == "print") {
  piece(names[0]) color(colors[0]) flat(0) panel(0);
  piece(names[1]) color(colors[0]) flat(1) panel(1);
  piece(names[2]) color(colors[0]) flat(2) panel(2);
} else {
  e = part == "exploded" ? explode : 0;
  for (i = [0 : 2]) color(colors[i]) translate(-e * unit(i)) panel(i);
}
