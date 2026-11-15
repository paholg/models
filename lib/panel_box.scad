// Boxes glued up from six flat panels, each printed with its outside face on
// the bed, and joined along every edge by a mitred rabbet.
//
//   use <../../lib/panel_box.scad>
//   pb_panel("front", size = [80, 60, 100], t = [2.04, 2.04, 2.04]);
//
// The box runs from the origin to `size`. Its panels are "left" and "right"
// (the faces across x), "front" and "back" (y), "floor" and "top" (z); t is
// their thickness by axis. A panel here is its whole face of the box, as a
// region: intersect it with the box you want, chamfers, cavity, inlays and
// all, to cut that box into panels.
//
// The joint. A mitre runs through the outer `mitre` of the wall, so the seam
// falls on the box's edge. Inside it, one panel ends square and sits in a
// rabbet in the other. Printed outside down, every mating face is a wall or
// faces up: nothing overhangs, so nothing droops and binds.
//
// Which panel sits in which is by `rank`, by axis: along an edge, the higher
// panel ends square and the lower has the rabbet. By default the front and
// back drop between the sides, and the floor and top drop into all four
// walls. So every panel goes on from outside, along its own normal; none is
// trapped, and squeezing the box closes every joint at once. Where three
// panels meet, the cuts along the three edges share the corner out between
// them with nothing left over.
//
// Fit, as found with test/joints at 0.08 mm layers: the rabbet locates the
// panels and the mitre closes with no gap. At 0.2 mm layers the mitre's
// steps stand proud and lever the joint out of square; mitre_gap is for
// that. Keep `mitre`, `brk` and every t on whole layers.
//
// Gluing: tape the panels up dry, outside, then run thin CA along the inside
// corners. It wicks through the rabbet and stops at the glue break, a trough
// under the mitre's inner end, short of the outside.
//
// The same box prints whole as well, with no joints: the box itself, not cut
// into panels, opening up. A lid prints top down: pb_top_down turns it over.

function pb_names() = ["left", "right", "front", "back", "floor", "top"];
function pb_axis(name) = name == "left" || name == "right" ? 0 : name == "front" || name == "back" ? 1 : 2;
// Whether the panel is the far one of its pair, at `size` rather than 0.
function pb_far(name) = name == "right" || name == "back" || name == "top";
function pb_unit(i) = [for (k = [0 : 2]) k == i ? 1 : 0];
// Outward.
function pb_normal(name) = (pb_far(name) ? 1 : -1) * pb_unit(pb_axis(name));

// Magnets, to hold a lid: bars standing on edge in a wall, each in a pocket
// open to the inside, facing its partner edge to edge across the seam between
// body and lid. pb_magnet_pocket is one pocket, to cut from a wall.
//
// In panels a `cover` of plastic stands between each magnet and the seam, so
// that magnets never touch and the seam bears on plastic: a wall one line
// wide, as the panel prints. Printed whole, that cover is a roof over the
// pocket, and would sag: `whole` leaves it off, and the magnet sits as far
// below the seam, bare.

// The box's outside, with chamfer c on every edge.
module pb_outer(size, c) {
  hull() for (i = [0 : 2])
    translate([for (k = [0 : 2]) k == i ? 0 : c]) cube([for (k = [0 : 2]) k == i ? size[k] : size[k] - 2 * c]);
}

// Children turned over onto the bed, top face down, as a one-piece lid
// prints.
module pb_top_down(size) {
  translate([0, size.y, size.z]) rotate([180, 0, 0]) children();
}

// Children drawn in (depth below panel a, depth below panel b), extruded the
// length of the edge those two share. A panel is given as [axis, far].
module pb_edge(size, a, b) {
  c = 3 - a[0] - b[0];
  ea = (a[1] ? -1 : 1) * pb_unit(a[0]);
  eb = (b[1] ? -1 : 1) * pb_unit(b[0]);
  o = [for (k = [0 : 2]) k == a[0] ? (a[1] ? size[k] : 0) : k == b[0] ? (b[1] ? size[k] : 0) : -1];
  multmatrix([for (k = [0 : 2]) [ea[k], eb[k], pb_unit(c)[k], o[k]]]) linear_extrude(size[c] + 2)
    children();
}

// One panel's region of the box.
//   rank       by axis; along an edge the higher panel sits in the lower's rabbet
//   mitre      depth of the mitre below the outside faces, and so the
//              thickness of the tongue under a rabbet
//   mitre_gap  between the mitre's faces, taken from the lower panel
//   brk        depth of the glue break
//   relief     chamfer on a higher panel's inside end corner, to clear the
//              rabbet's inside corner
//   gap        between a higher panel's end and the rabbet's floor
module pb_panel(name, size, t, rank = [0, 1, 2], mitre = 1, mitre_gap = 0, brk = 0.32, relief = 0.15,
                gap = 0) {
  i = pb_axis(name);
  far = pb_far(name);
  big = max(size) + 2;
  e = mitre + gap;
  difference() {
    translate([for (k = [0 : 2]) k == i && far ? size[k] - t[k] : 0])
      cube([for (k = [0 : 2]) k == i ? t[k] : size[k]]);
    for (j = [0 : 2], fj = [false, true]) if (j != i) {
      // The higher panel gives up what is outside the mitre, and then below
      // its square end.
      if (rank[i] > rank[j])
        pb_edge(size, [i, far], [j, fj])
          polygon([[-1, -1], [mitre, mitre], [mitre, e], [t[i] - relief, e], [t[i], e + relief],
                   [big, e + relief], [big, -1]]);
      // The lower gives up what is outside the mitre, the glue break, and
      // then the rabbet, as wide as the higher is thick.
      else
        pb_edge(size, [j, fj], [i, far])
          polygon([[mitre_gap - 1, -1], [mitre - brk + mitre_gap, mitre - brk],
                   [mitre + mitre_gap, mitre - brk], [mitre + mitre_gap, mitre], [t[j], mitre],
                   [t[j], big], [-1, big], [-1, -1]]);
    }
  }
}

// From the seam to the pads a magnet's far edge seats against.
function pb_magnet_far(mag, cover, c = 0.12) = cover + mag.y + c;

// A magnet's pocket: x along the wall, y into it from its inside face, z away
// from the seam, which is at 0. Oversize by `glue` at both ends and at the far
// edge, with two crush ribs on each end, flat-tipped, running the way the
// magnet drops in, and two pads at the far edge for it to seat against.
//   mag      length along the wall, height, thickness
//   cover    plastic between the magnet and the seam
//   whole    for a box printed whole: no cover, the magnet set back by it
//   c        clearance on the thickness, and between the cover and the pads
//   glue     gap for excess glue
//   crush    how far each end's ribs bite into the magnet's length
//   rib_w    width of a rib at its root
//   rib_tip  width of its tip: flat, and wide enough to print at its full
//            height. A pointed rib came out about 0.1 mm short, rounded off by
//            the nozzle, and a 0.15 mm crush gripped nothing.
module pb_magnet_pocket(mag, cover, whole = false, c = 0.12, glue = 0.4, crush = 0.1, rib_w = 1.2,
                        rib_tip = 0.4) {
  eps = 0.01;
  l = mag.x / 2 + glue;
  t = mag.z + c / 2;
  far = pb_magnet_far(mag, cover, c);
  z0 = whole ? -eps : cover;
  difference() {
    translate([-l, -eps, z0]) cube([2 * l, t + eps, far + glue - z0]);
    for (sx = [-1, 1], zc = [for (f = [0.25, 0.75]) cover + f * mag.y])
      translate([0, -2 * eps, 0]) rotate([-90, 0, 0]) linear_extrude(t + 4 * eps)
        polygon([for (q = [[l + eps, zc - rib_w / 2], [l + eps, zc + rib_w / 2],
                           [l - glue - crush, zc + rib_tip / 2], [l - glue - crush, zc - rib_tip / 2]])
                   [sx * q[0], -q[1]]]);
    for (sx = [-1, 1]) translate([sx * mag.x / 4 - 1, -2 * eps, far]) cube([2, t + 3 * eps, glue + eps]);
  }
}
