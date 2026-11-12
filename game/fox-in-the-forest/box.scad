// Upright card box for The Fox in the Forest Deluxe: the 61 standard-size
// cards in sleeves, standing on end, with the score tracker (score.scad)
// behind them, and a lift-off lid held on by magnets.
//
// x is across the cards, y is front (0) to back, z is up. The seam is level
// across the front and back walls and slopes up between them along the sides.
//
// The box is ten flat panels, mitred and glued: floor, top, and a body and a
// lid piece of each wall. Every panel prints with its outside face on the
// bed, and the mitres meet on the box's edges, so no joint shows on a face.
//
// Bar magnets stand on edge in the front and back walls, in pockets open to
// the inside and to the seam, each meeting its partner edge to edge across
// the seam. They're magnetized through their thickness, so glue one of each
// pair in flipped, to attract. A trapezoid key on each wall's seam locates
// the lid. Hidden tabs inside the mitres line the panels up for gluing.

// export: print
// Layers that the 0.6 mm inlays and the 0.8 mm magnet skins are whole numbers
// of, from the bed up.
// orca: layer_height=0.2 initial_layer_print_height=0.2

/* [Output] */
// "print" is every panel on the bed, outside down, one object per color.
part = "closed"; // [closed, open, exploded, print]

/* [Contents] */
// Dragon Shield Matte standard sleeve, outside, at its largest: width, length.
sleeve = [66.5, 92.5];
// 61 sleeved cards at ~0.61 mm each: a 0.30 mm card, 0.26 mm of sleeve, and
// ~0.05 mm of loose-stack air.
stack_h = 37.5;
// The score tracker, rupees and all (score.scad: top_h + rupee_lift +
// rupee_t).
score_t = 9;
card_clear = 0.5;
// Above the cards, under the lid.
top_clear = 0.5;

/* [Box] */
// Side walls, floor and top.
wall = 2;
// How far the seam drops from back to front.
seam_drop = 25;
// Height of the lid at the back, top plate included.
lid_back_h = 14;
// Chamfer on the outside edges, which also blunts the mitres' knife edges.
chamfer = 0.6;

/* [Magnets] */
// Bar magnets in the seam: length along the wall, height, thickness.
mag = [18.4, 9, 2.5];
// Pocket clearance on the thickness.
mag_c = 0.2;
// Gap for excess glue, past each end of a magnet and past its far edge from
// the seam. Crush ribs and stop pads cross it to hold the magnet in place.
mag_glue = 0.4;
// How far each end's crush ribs bite into the magnet's length.
mag_crush = 0.1;
// Width of a crush rib at its root.
mag_rib_w = 1;
// Plastic outside a pocket; with the magnet, the front and back walls'
// thickness.
mag_skin = 0.8;
// How far each magnet sits below its seam face, so the plastic bears.
mag_recess = 0.05;
// Magnets sit this far either side of center, on the front and the back.
mag_x = 20;

/* [Mitre tabs] */
// Hidden tabs along every mitre, alternating between the two panels: each
// reaches across the mitre's inner part into a notch in the other panel, so
// the panels register. Rough tab length.
tab_len = 12;
// Where along the mitre, outside to inside, the tabs start.
tab_start = 0.6;
// Least plastic left outside a notch.
tab_skin = 0.6;
// Clearance around a tab in its notch.
tab_c = 0.1;

/* [Seam keys] */
// Width at the base, height, and how far each flank leans in.
key_w = 14;
key_h = 2.5;
key_lean = 1.25;
// Clearance around a key in the lid.
key_c = 0.15;

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

/* [Forest] */
// Forest entrance inlaid flush in the body's back, stretched to fill it up
// to the seam.
forest_depth = 0.6;
// Left clear around the forest, to the back's edges and the seam; 0 is full
// bleed.
forest_margin = 2;

/* [View] */
// How far the panels pull apart in the exploded view.
explode = 12;

/* [Hidden] */
$fn = 48;
eps = 0.01;

// Front and back wall thickness.
tf = mag.z + mag_c / 2 + mag_skin;
cav = [sleeve.x + card_clear, stack_h + score_t + card_clear, sleeve.y + top_clear];
bx = cav.x + 2 * wall;
by = cav.y + 2 * tf;
box_h = cav.z + 2 * wall;
xs = cav.x / 2;
xo = bx / 2;
y_back = by - tf;
z_top = box_h - wall;
// Seam height at the back and at the front.
z_sb = box_h - lid_back_h;
z_sf = z_sb - seam_drop;
seam_k = seam_drop / cav.y;
function seam_z(y) = max(z_sf, min(z_sf + seam_k * (y - tf), z_sb));
mag_d = mag.y + mag_recess;
assert(z_top - z_sb >= mag_d + mag_glue + 1, "lid too short at the back for its magnets");
assert(mag_x - mag.x / 2 - mag_glue - 1 >= key_w / 2 + key_c, "magnets crowd the key");
assert(mag_x + mag.x / 2 + mag_glue + 1 <= xs, "magnets run into the corners");

module box(x, y, z) {
  translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);
}

/* The shell, split at the seam */

module outer() {
  c = chamfer;
  hull() {
    box([-xo + c, xo - c], [c, by - c], [0, box_h]);
    box([-xo + c, xo - c], [0, by], [c, box_h - c]);
    box([-xo, xo], [c, by - c], [c, box_h - c]);
  }
}

module cavity() {
  box([-xs, xs], [tf, y_back], [wall, z_top]);
}

// Key outline, base on the seam at the origin, grown by g.
module key_2d(g = 0) {
  w = key_w / 2;
  offset(delta = g)
    polygon([[-w, -1], [-w, 0], [-w + key_lean, key_h], [w - key_lean, key_h], [w, 0], [w, -1]]);
}

module keys(g) {
  // Front and back.
  for (p = [[tf, z_sf], [by + 1, z_sb]])
    translate([0, p[0], p[1]]) rotate([90, 0, 0]) linear_extrude(tf + 1) key_2d(g);
  // Sides, leaning with the seam.
  y_mid = by / 2;
  translate([0, y_mid, seam_z(y_mid)]) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, seam_k, 1, 0]])
    rotate([90, 0, 90]) linear_extrude(bx + 2, center = true) key_2d(g);
}

// Everything the body keeps: below the seam, plus the keys grown by g.
module below_seam(g = 0) {
  big = [-bx, bx];
  intersection() {
    union() {
      box(big, [-1, by + 1], [-1, z_sf]);
      multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, seam_k, 1, z_sf - seam_k * tf]])
        box(big, [-1, by + 1], [-2 * box_h, 0]);
    }
    box(big, [-1, by + 1], [-1, z_sb]);
  }
  keys(g);
}

// Magnets as [x center, y of the cavity-side face, seam z, into the wall].
mag_at = [for (sx = [-1, 1], p = [[tf, z_sf, -1], [y_back, z_sb, 1]]) [sx * mag_x, p[0], p[1], p[2]]];

// Magnet m's frame, in the body (dir = -1) or the lid (1): x along the wall,
// y into it from its inside face, z away from the seam.
module at_mag(m, dir) {
  translate([m[0], m[1], m[2]]) scale([1, m[3], dir]) children();
}

// A pocket in that frame: oversize by mag_glue at both ends and at the far
// edge, with two crush ribs on each end, pointed, running the way the magnet
// drops in, and two pads at the far edge for it to seat against.
module mag_pocket() {
  l = mag.x / 2 + mag_glue;
  t = mag.z + mag_c / 2;
  difference() {
    box([-l, l], [-eps, t], [-eps, mag_d + mag_glue]);
    for (sx = [-1, 1], zc = [0.25, 0.75] * mag_d)
      translate([0, -2 * eps, 0]) rotate([-90, 0, 0]) linear_extrude(t + 4 * eps)
        polygon([for (q = [[l + eps, zc - mag_rib_w / 2], [l + eps, zc + mag_rib_w / 2],
                           [l - mag_glue - mag_crush, zc]]) [sx * q[0], -q[1]]]);
    for (sx = [-1, 1])
      box([sx * mag.x / 4 - 1, sx * mag.x / 4 + 1], [-2 * eps, t + eps], [mag_d, mag_d + mag_glue + eps]);
  }
}

module mag_pockets(dir) {
  for (m = mag_at) at_mag(m, dir) mag_pocket();
}

module magnets(dir) {
  for (m = mag_at) at_mag(m, dir) box([-mag.x / 2, mag.x / 2], [-eps, mag.z], [mag_recess, mag_d]);
}

// Reads from the front.
module fox(above = 0) {
  translate([0, 0, fox_z]) rotate([90, 0, 0])
    translate([0, 0, -fox_depth]) linear_extrude(fox_depth + above, convexity = 10)
      resize([0, fox_h], auto = true) import("fox.svg", center = true);
}

// Reads from the back. Kept to the back panel, inside its mitres.
module forest(above = 0) {
  intersection() {
    region("back");
    translate([0, by, z_sb / 2]) rotate([90, 0, 180])
      translate([0, 0, -forest_depth]) linear_extrude(forest_depth + above, convexity = 10)
        resize([bx - 2 * forest_margin, z_sb - 2 * forest_margin])
          import("forest.svg", center = true);
  }
}

// The inlay itself, trimmed to the box's chamfers. Rendered, as the preview
// otherwise paints it over the whole box.
module forest_inlay() {
  render(convexity = 10) intersection() { forest(); outer(); }
}

// Reads from the front, looking down on the lid.
module logo(above = 0) {
  translate([0, by / 2, box_h - logo_depth])
    linear_extrude(logo_depth + above, convexity = 10)
      resize([logo_w, 0], auto = true) import("logo.svg", center = true);
}

module body_shell() {
  difference() {
    intersection() {
      outer();
      below_seam();
    }
    cavity();
    mag_pockets(-1);
    fox(eps);
    forest(eps);
  }
}

module lid_shell() {
  difference() {
    outer();
    below_seam(key_c);
    cavity();
    mag_pockets(1);
    logo(eps);
  }
}

/* Panels: each is the part of a shell inside its region, which runs from
   its outside face of the box in to its face of the cavity. The regions meet
   in mitres along every edge. */

walls = ["front", "back", "left", "right"];

module region(name) {
  X = [-xo, xo]; Y = [0, by]; Z = [0, box_h];
  x = [-xs, xs]; y = [tf, y_back]; z = [wall, z_top];
  hull() {
    if (name == "front") { box(X, [-eps, 0], Z); box(x, [tf, tf + eps], z); }
    else if (name == "back") { box(X, [by, by + eps], Z); box(x, [y_back - eps, y_back], z); }
    else if (name == "left") { box([-xo - eps, -xo], Y, Z); box([-xs, -xs + eps], y, z); }
    else if (name == "right") { box([xo, xo + eps], Y, Z); box([xs - eps, xs], y, z); }
    else if (name == "floor") { box(X, Y, [-eps, 0]); box(x, y, [wall, wall + eps]); }
    else { box(X, Y, [box_h, box_h + eps]); box(x, y, [z_top - eps, z_top]); }
  }
}

function thk(name) = name == "front" || name == "back" ? tf : wall;

// Mitres as [panel A, panel B, a point on the outside edge, direction along
// it, ranges along it to fill with tabs]. The upright ones are cut up
// separately either side of the seam.
mitres = concat(
  [for (a = ["front", "back"], b = ["left", "right"]) let (zc = a == "front" ? z_sf : z_sb)
    [a, b, [b == "left" ? -xo : xo, a == "front" ? 0 : by, 0], [0, 0, 1], [[wall, zc], [zc, z_top]]]],
  [for (p = ["floor", "top"], w = walls) let (z = p == "floor" ? 0 : box_h)
    w == "front" || w == "back"
      ? [p, w, [0, w == "front" ? 0 : by, z], [1, 0, 0], [[-xs, xs]]]
      : [p, w, [w == "left" ? -xo : xo, 0, z], [0, 1, 0], [[tf, y_back]]]]);

// A tab's outline, in depth below its own panel's outside face (t thick) and
// below the other's (to thick). From tab_start along the mitre its underside
// climbs toward the other panel's face at 45° as printed, or steeper to
// leave tab_skin, and it ends level with its own panel's inside face.
module tab_2d(t, to, g) {
  k = tab_start;
  offset(delta = g)
    polygon([[k * t, k * to], [t, to], [t, max(k * to - (1 - k) * t, tab_skin)]]);
}

// The tabs panel name owns, grown by g.
module tabs(name, g = 0) {
  for (m = mitres) if (m[0] == name || m[1] == name) {
    a = m[0]; b = m[1]; c = m[2]; e = m[3];
    na = normal(a); nb = normal(b);
    mine = name == a ? 0 : 1;
    // (depth below a, depth below b, along the edge) to box coordinates.
    multmatrix([for (i = [0 : 2]) [-na[i], -nb[i], e[i], c[i]]])
      for (r = m[4]) let (n = max(2, round((r[1] - r[0]) / tab_len)), l = (r[1] - r[0]) / n)
        for (i = [mine : 2 : n - 1]) translate([0, 0, r[0] + i * l - g]) linear_extrude(l + 2 * g)
          if (mine == 0) tab_2d(thk(a), thk(b), g);
          else mirror([1, -1]) tab_2d(thk(b), thk(a), g);
  }
}

module panel(name, lid = false) {
  intersection() {
    if (lid) lid_shell();
    else body_shell();
    difference() {
      union() {
        region(name);
        tabs(name);
      }
      for (o = concat(walls, ["floor", "top"])) if (o != name) tabs(o, tab_c);
    }
  }
}

/* Placement */

function normal(name) =
  name == "front" ? [0, -1, 0] : name == "back" ? [0, 1, 0] :
  name == "left" ? [-1, 0, 0] : name == "right" ? [1, 0, 0] :
  name == "floor" ? [0, 0, -1] : [0, 0, 1];

// Pulled e out along the panel's normal, the lid's panels lifted as well.
module exploded(name, e, lift = 0) {
  translate(e * normal(name) + [0, 0, lift]) children();
}

// On the bed, outside face down. Each wall's lid piece lies beyond its body
// piece, the seam between them opened by lid_gap.
lid_gap = 5;
bed_gap = 5;
module flat(name, lid = false) {
  h = box_h + lid_gap;
  g = lid ? lid_gap : 0;
  y1 = h + bed_gap;
  y2 = y1 + by + bed_gap;
  x1 = bx + bed_gap;
  if (name == "front")
    translate([xo, h, 0]) rotate([90, 0, 0]) translate([0, 0, g]) children();
  else if (name == "back")
    translate([x1 + xo, 0, by]) rotate([-90, 0, 0]) translate([0, 0, g]) children();
  else if (name == "left")
    translate([h, y1, xo]) rotate([0, -90, 0]) translate([0, 0, g]) children();
  else if (name == "right")
    translate([h + bed_gap, y1, xo]) rotate([0, 90, 0]) translate([0, 0, g]) children();
  else if (name == "floor")
    translate([xo, y2, 0]) children();
  else
    translate([x1 + xo, y2 + by, box_h]) rotate([180, 0, 0]) children();
}

// Each top-level statement exports as its own object, named for the slicer
// and with slicer settings of its own (see python/generate.py), so one per
// panel and per inlay.
module piece(name, orca = "") {
  echo(piece = name, orca = orca);
  children();
}

// The pattern each piece's outside face prints in, on the bed.
function bottom(pattern) = str("bottom_surface_pattern=", pattern);
// Monotonic lines at angle a on the bed, from +x.
function lines(a) = str(bottom("monotonic"), " solid_infill_direction=", a);
// Front, back and top: lines up the box, or across it. Sides: along the
// seam, which leans the other way on each as they lie on the bed.
function face(name) =
  name == "front" || name == "back" ? lines(90) :
  name == "left" ? lines(atan2(1, -seam_k)) :
  name == "right" ? lines(atan2(1, seam_k)) :
  name == "floor" ? bottom("concentric") : lines(0);

if (part == "print") {
  for (w = walls) piece(w, face(w)) color("darkgreen") flat(w) panel(w);
  piece("floor", face("floor")) color("darkgreen") flat("floor") panel("floor");
  for (w = walls) piece(str("lid ", w), face(w)) color("darkgreen") flat(w, true) panel(w, true);
  piece("top", face("top")) color("darkgreen") flat("top") panel("top", true);
  piece("fox", bottom("octagramspiral")) color("yellow") flat("front") fox();
  piece("forest", bottom("archimedeanchords")) color("yellow") flat("back") forest_inlay();
  piece("logo", face("top")) color("yellow") flat("top") logo();
} else {
  e = part == "exploded" ? explode : 0;
  lift = part == "closed" ? 0 : part == "open" ? 40 : 3 * explode;
  color("darkgreen") {
    for (w = walls) exploded(w, e) panel(w);
    exploded("floor", e) panel("floor");
  }
  color("forestgreen") {
    for (w = walls) exploded(w, e, lift) panel(w, true);
    exploded("top", e, lift) panel("top", true);
  }
  color("orange") exploded("front", e) fox();
  color("white") exploded("back", e) forest_inlay();
  color("white") exploded("top", e, lift) logo();
  color("silver") {
    for (w = ["front", "back"]) exploded(w, e) intersection() { magnets(-1); region(w); }
    for (w = ["front", "back"]) exploded(w, e, lift) intersection() { magnets(1); region(w); }
  }
}
