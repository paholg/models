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

function pb_names() = ["left", "right", "front", "back", "floor", "top"];
function pb_axis(name) = name == "left" || name == "right" ? 0 : name == "front" || name == "back" ? 1 : 2;
// Whether the panel is the far one of its pair, at `size` rather than 0.
function pb_far(name) = name == "right" || name == "back" || name == "top";
function pb_unit(i) = [for (k = [0 : 2]) k == i ? 1 : 0];
// Outward.
function pb_normal(name) = (pb_far(name) ? 1 : -1) * pb_unit(pb_axis(name));

// The box's outside, with chamfer c on every edge.
module pb_outer(size, c) {
  hull() for (i = [0 : 2])
    translate([for (k = [0 : 2]) k == i ? 0 : c]) cube([for (k = [0 : 2]) k == i ? size[k] : size[k] - 2 * c]);
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
