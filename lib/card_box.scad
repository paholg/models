// An upright box for a deck of cards standing on end, with a lift-off lid
// held on by magnets.
//
//   use <../../lib/card_box.scad>
//   card_box(part, sleeve = [66.5, 92.5], stack = 40, front_art = "crest")
//     translate([0, 30]) import("crest.svg", center = true);
//
// x is across the cards, centered; y is front (0) to back; z is up. The seam
// is level across the front and back walls and slopes up between them along
// the sides.
//
// The box is ten flat panels, glued, for faces off the bed all round and
// inlays that print flat: floor, top, and a body and a lid piece of each
// wall. Every panel prints with its outside face on the bed. They
// join in mitred rabbets (panel_box.scad), whose seams fall on the box's
// edges, so no joint shows on a face. The front and back drop between the
// sides, and the floor and top into all four walls. To glue the body, or the
// lid: tape its panels up dry, outside, then run thin CA along the inside
// corners.
//
// Bar magnets stand on edge in the front and back walls, in pockets open to
// the inside, each facing its partner edge to edge across the seam. A cover
// of plastic stands between each magnet and the seam, so that magnets never
// touch and the seam bears on plastic: a wall one line wide, as a panel
// prints, stopping `ease` short of the wall's inside face. They're magnetized through their thickness, so glue one of each
// pair in flipped, to attract. A trapezoid key on each wall's seam locates
// the lid.
//
// A panel's last layers, its inside face, flare a little past its edges, and
// at the seam that holds the lid off. So the seam's inside edges are
// chamfered, keys and all, as panel_box.scad's are in the joints.
//
// Art is inlaid flush in the front, the back and the top: a second color, in
// pieces of its own. It is the box's children, in that order, each drawn in
// 2D as it reads from outside, and had by naming it:
//   front  x across, y up from the floor, 0 at the front's bottom center
//   back   the same on the back, seen from behind
//   top    x across, y to the back, 0 at the top's center
// $cb_size, the box's outside, and $cb_seam, the seam's height at the front
// and at the back, are there to fit it by. It is trimmed to its face.
//
// A face's art can be of several colors: layers, each with a name and a
// color, and a piece of its own. The face's child is then drawn once for
// each, with its name in $cb_art, and draws that layer alone. They go on
// like paint, a later layer covering the ones before it:
//   card_box(part, front_art = [["card", "white"], ["pips", "red"]]) {
//     if ($cb_art == "card") square([20, 30], center = true);
//     else circle(4);
//   }
//
// Printing. The joints fit as drawn at 0.08 mm layers: the 0.6 mm inlays, the
// 0.84 mm magnet skins, the 2.04 mm walls and the 3.4 mm front and back all
// end on whole layers, from the bed up. So the box asks for those layers
// itself. For python/generate.py, the file that draws the box wants only:
//   // export: panels seam magnets
//
// With more colors than the printer has heads, the body and the lid can
// print apart, each with its own: `// export: body lid` in place of panels.
//
// More than one box in a file: give each a `name`, which goes before its
// pieces' names, and move them apart.

use <orca.scad>
use <panel_box.scad>
use <piece.scad>

//   part       closed, open, exploded: views.
//              panels: every panel on the bed, outside down.
//              body, lid: the panels of one of them, where they lie in panels.
//              seam: a test, three short lengths of the front wall across the
//              seam, each with the key and one magnet pocket, at the fits in
//              seam_fits.
//              magnets: a smaller one, a strip of wall with a magnet pocket at
//              each crush in mag_crushes.
//   explode    how far the panels pull apart in the exploded view
//   name       goes before the names of its pieces
//
//   sleeve     a card in its sleeve, outside, at its largest: width, length
//   stack      what stands in the box, front to back: the deck, and whatever
//              goes in beside it
//   clear      room round that: across the cards, front to back, and above
//              them, under the lid. 2.5 across is what a bought deck box has.
//
//   wall        side walls, floor and top
//   seam_drop   how far the seam drops from back to front
//   lid_back_h  height of the lid at the back, top plate included
//   chamfer     on the outside edges, which also blunts the mitres' knife edges
//   ease        chamfer on the inside edges that meet another piece: the
//               seam's, and the joints'. Whole layers.
//
//   box_color, lid_color, art_color  the body's, the lid's ("" for the
//              body's), and that of art given by name alone
//
//   front_art, back_art, top_art  each face's art: its name, as a piece for
//              the slicer, in art_color; or its layers, a list of [name,
//              color]; or "" for none
//   *_pattern  the pattern its face prints in, on the bed, as a panel, or ""
//              for the panel's own
//   art_depth  how deep art is inlaid
//
//   mag        bar magnets in the seam: length along the wall, height, thickness
//   mag_c      pocket clearance on the thickness, where the pocket is open to
//              the inside
//   mag_slack  room for the magnet's height, between the cover and the pads.
//              Loose: a magnet that's tight there bows the cover out at the
//              seam, and its partner's pull seats it against the cover anyway.
//   mag_glue   gap for excess glue, past each end of a magnet and past its far
//              edge from the seam. Crush ribs and stop pads cross it to hold
//              the magnet in place.
//   mag_crush  how far each end's crush ribs bite into the magnet's length
//   mag_rib_w  width of a crush rib at its root
//   mag_rib_tip  width of its tip: flat, and wide enough to print at its full
//              height. A pointed rib came out about 0.1 mm short, rounded off
//              by the nozzle, and a 0.15 mm crush gripped nothing.
//   mag_skin   plastic outside a pocket; with the magnet, the front and back
//              walls' thickness
//   mag_cover  plastic between a magnet and its seam face
//   mag_x      magnets sit this far either side of center, on the front and
//              the back
//
//   key_w, key_h, key_lean  seam keys: width at the base, height, and how far
//              each flank leans in
//   key_c      clearance around a key in the lid
//
//   seam_fits  the seam test: each coupon's [key clearance, magnet crush]; its
//              notches count its place here
//   seam_test_x, seam_test_h  a coupon's reach along the wall, and either side
//              of the seam
//   mag_crushes  the magnet test: each pocket's crush; its notches count its
//              place here
//   mag_test_rim  plastic around each pocket, along the wall and away from the
//              seam
//
//   lid_gap, bed_gap  on the bed: between a wall's body piece and its lid
//              piece, and between panels
module card_box(part = "closed", explode = 12, name = "",
                sleeve = [66.5, 92.5], stack = 40, clear = [2.5, 0.5, 0.5],
                wall = 2.04, seam_drop = 25, lid_back_h = 14, chamfer = 0.6, ease = 0.24,
                box_color = "forestgreen", lid_color = "", art_color = "yellow",
                front_art = "", front_art_pattern = "", back_art = "", back_art_pattern = "",
                top_art = "", top_art_pattern = "", art_depth = 0.6,
                mag = [18.4, 9, 2.5], mag_c = 0.12, mag_slack = 0.3, mag_glue = 0.4, mag_crush = 0.1, mag_rib_w = 1.2,
                mag_rib_tip = 0.4, mag_skin = 0.84, mag_cover = 0.4, mag_x = 20,
                key_w = 14, key_h = 2.5, key_lean = 1.25, key_c = 0.05,
                seam_fits = [[0.05, 0.05], [0.05, 0.1], [0.05, 0.2]], seam_test_x = [-9, 31], seam_test_h = 14,
                mag_crushes = [0.05, 0.1, 0.2], mag_test_rim = 3,
                lid_gap = 5, bed_gap = 5) {
  $fn = 48;
  $piece_prefix = name;
  lid_c = lid_color == "" ? box_color : lid_color;
  eps = 0.01;

  // The seam test's coupons set these two for themselves.
  function cb_key_c() = is_undef($key_c) ? key_c : $key_c;
  function cb_mag_crush() = is_undef($mag_crush) ? mag_crush : $mag_crush;

  // Front and back wall thickness.
  tf = mag.z + mag_c / 2 + mag_skin;
  cav = [sleeve.x + clear.x, stack + clear.y, sleeve.y + clear.z];
  bx = cav.x + 2 * wall;
  by = cav.y + 2 * tf;
  box_h = cav.z + 2 * wall;
  // The box, outside. The $ ones are for the art to fit itself by.
  cb_size = [bx, by, box_h];
  $cb_size = cb_size;
  xs = cav.x / 2;
  xo = bx / 2;
  y_back = by - tf;
  z_top = box_h - wall;
  // Seam height at the back and at the front.
  z_sb = box_h - lid_back_h;
  z_sf = z_sb - seam_drop;
  // The seam's height: at the front, at the back.
  $cb_seam = [z_sf, z_sb];
  seam_k = seam_drop / cav.y;
  function cb_seam_z(y) = max(z_sf, min(z_sf + seam_k * (y - tf), z_sb));
  // From the seam face to the pads at a magnet's far edge.
  mag_d = mag_cover + mag.y + mag_slack;
  assert(z_top - z_sb >= mag_d + mag_glue + 1, "lid too short at the back for its magnets");
  assert(mag_x - mag.x / 2 - mag_glue - 1 >= key_w / 2 + key_c, "magnets crowd the key");
  assert(ease <= 0.5, "ease reaches under the keys");
  assert(mag_x + mag.x / 2 + mag_glue + 1 <= xs, "magnets run into the corners");

  module cb_box(x, y, z) {
    translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);
  }

  /* The shell, split at the seam */

  module cb_outer() {
    translate([-xo, 0, 0]) pb_outer(cb_size, chamfer);
  }

  module cb_cavity() {
    cb_box([-xs, xs], [tf, y_back], [wall, z_top]);
  }

  // Key outline, base on the seam at the origin, grown by g.
  module cb_key_2d(g = 0) {
    w = key_w / 2;
    offset(delta = g)
      polygon([[-w, -1], [-w, 0], [-w + key_lean, key_h], [w - key_lean, key_h], [w, 0], [w, -1]]);
  }

  module cb_keys(g) {
    // Front and back.
    for (p = [[tf, z_sf], [by + 1, z_sb]])
      translate([0, p[0], p[1]]) rotate([90, 0, 0]) linear_extrude(tf + 1) cb_key_2d(g);
    // Sides, leaning with the seam.
    y_mid = by / 2;
    translate([0, y_mid, cb_seam_z(y_mid)]) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, seam_k, 1, 0]])
      rotate([90, 0, 90]) linear_extrude(bx + 2, center = true) cb_key_2d(g);
  }

  // Everything the body keeps: below the seam, plus the keys grown by g. With
  // the seam between the keys raised by lift.
  module cb_below_seam(g = 0, lift = 0) {
    big = [-bx, bx];
    translate([0, 0, lift]) intersection() {
      union() {
        cb_box(big, [-1, by + 1], [-1, z_sf]);
        multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, seam_k, 1, z_sf - seam_k * tf]])
          cb_box(big, [-1, by + 1], [-2 * box_h, 0]);
      }
      cb_box(big, [-1, by + 1], [-1, z_sb]);
    }
    cb_keys(g);
  }

  /* Magnets */

  // A magnet's pocket: x along the wall, y into it from its inside face, z away
  // from the seam, which is at 0. Its cover stops `ease` short of the inside
  // face, flat, where the seam's chamfer would leave it a feather. Oversize by mag_glue at both ends and at the
  // far edge, with two crush ribs on each end, flat-tipped, running the way the
  // magnet drops in, and two pads at the far edge for it to seat against.
  module cb_mag_pocket() {
    l = mag.x / 2 + mag_glue;
    t = mag.z + mag_c / 2;
    crush = cb_mag_crush();
    translate([-l, -eps, -eps]) cube([2 * l, ease + eps, mag_cover + 2 * eps]);
    difference() {
      translate([-l, -eps, mag_cover]) cube([2 * l, t + eps, mag_d + mag_glue - mag_cover]);
      for (sx = [-1, 1], zc = [for (f = [0.25, 0.75]) mag_cover + f * mag.y])
        translate([0, -2 * eps, 0]) rotate([-90, 0, 0]) linear_extrude(t + 4 * eps)
          polygon([for (q = [[l + eps, zc - mag_rib_w / 2], [l + eps, zc + mag_rib_w / 2],
                             [l - mag_glue - crush, zc + mag_rib_tip / 2],
                             [l - mag_glue - crush, zc - mag_rib_tip / 2]]) [sx * q[0], -q[1]]]);
      for (sx = [-1, 1]) translate([sx * mag.x / 4 - 1, -2 * eps, mag_d]) cube([2, t + 3 * eps, mag_glue + eps]);
    }
  }

  // Magnets as [x center, y of the cavity-side face, seam z, into the wall].
  mag_at = [for (sx = [-1, 1], p = [[tf, z_sf, -1], [y_back, z_sb, 1]]) [sx * mag_x, p[0], p[1], p[2]]];

  // Magnet m's frame, in the body (dir = -1) or the lid (1): x along the wall,
  // y into it from its inside face, z away from the seam.
  module cb_at_mag(m, dir) {
    translate([m[0], m[1], m[2]]) scale([1, m[3], dir]) children();
  }

  module cb_mag_pockets(dir) {
    for (m = mag_at) cb_at_mag(m, dir) cb_mag_pocket();
  }

  // The magnets themselves, for the views.
  module cb_magnets(dir) {
    for (m = mag_at) cb_at_mag(m, dir)
      cb_box([-mag.x / 2, mag.x / 2], [-eps, mag.z], [mag_cover, mag_cover + mag.y]);
  }

  /* Art */

  cb_art_faces = ["front", "back", "top"];
  // A face's layers, each [name, color].
  function cb_layers(art) = art == "" || art == [] ? [] : is_string(art) ? [[art, art_color]] : art;
  function cb_art_layers(face) = cb_layers(face == "front" ? front_art : face == "back" ? back_art : top_art);
  function cb_art_pattern(face) =
    face == "front" ? front_art_pattern : face == "back" ? back_art_pattern : top_art_pattern;

  // One layer of a face's art as drawn, sunk art_depth into the face, and
  // going on `over` past that, both ways.
  module cb_art_drawn(face, layer, over = 0) {
    $cb_art = layer;
    h = art_depth + 2 * over;
    if (face == "front")
      rotate([90, 0, 0]) translate([0, 0, -art_depth - over]) linear_extrude(h, convexity = 10) children(0);
    else if (face == "back")
      translate([0, by, 0]) rotate([90, 0, 180]) translate([0, 0, -art_depth - over])
        linear_extrude(h, convexity = 10) children(1);
    else
      translate([0, by / 2, box_h - art_depth - over]) linear_extrude(h, convexity = 10) children(2);
  }

  // What it takes out of its face, every layer of it: kept to its panel,
  // inside the mitres, and no deeper than the art.
  module cb_art_cut(face) {
    layers = cb_art_layers(face);
    if (layers != []) intersection() {
      cb_region(face);
      union() for (l = layers) cb_art_drawn(face, l[0]) { children(0); children(1); children(2); }
      cb_art_slab(face);
    }
  }

  // The outside of a face, to just past the art's depth and well out of it.
  module cb_art_slab(face) {
    d = art_depth;
    if (face == "front") cb_box([-bx, bx], [-1, d], [-1, box_h + 1]);
    else if (face == "back") cb_box([-bx, bx], [by - d, by + 1], [-1, box_h + 1]);
    else cb_box([-bx, bx], [-1, by + 1], [box_h - d, box_h + 1]);
  }

  // Layer i of the inlay itself, less the layers over it, and trimmed to the
  // box's chamfers as well. Rendered, as the preview otherwise paints it over
  // the whole box.
  module cb_art(face, i) {
    layers = cb_art_layers(face);
    render(convexity = 10) difference() {
      intersection() {
        cb_region(face);
        cb_art_drawn(face, layers[i][0]) { children(0); children(1); children(2); }
        cb_outer();
      }
      for (j = [i + 1 : 1 : len(layers) - 1])
        cb_art_drawn(face, layers[j][0], eps) { children(0); children(1); children(2); }
    }
  }

  /* The seam's inside edges */

  // What the chamfer takes from the body, or from the lid: in each wall, next
  // to its inside face, whatever is within reach across the seam, the reach
  // falling from `ease` at the face to nothing `ease` into the wall. In steps
  // finer than a layer, as the seam is no shape to taper whole. Each wall's
  // is kept to its own panel.
  module cb_seam_ease(lid) {
    n = 6;
    for (w = walls, k = [0 : n - 1]) {
      // Into the wall, from and to.
      a = k == 0 ? -eps : k * ease / n;
      b = (k + 1) * ease / n;
      s = ease * (1 - (k + 0.5) / n);
      intersection() {
        cb_region(w);
        if (w == "front") cb_box([-xo, xo], [tf - b, tf - a], [0, box_h]);
        else if (w == "back") cb_box([-xo, xo], [y_back + a, y_back + b], [0, box_h]);
        else if (w == "left") cb_box([-xs - b, -xs - a], [0, by], [0, box_h]);
        else cb_box([xs + a, xs + b], [0, by], [0, box_h]);
        if (lid) cb_below_seam(cb_key_c() + s, s);
        else difference() {
          cb_box([-bx, bx], [-1, by + 1], [-1, box_h + 1]);
          cb_below_seam(-s, -s);
        }
      }
    }
  }

  /* Shells */

  // Before their art is cut.
  module cb_body_blank() {
    difference() {
      intersection() {
        cb_outer();
        cb_below_seam();
      }
      cb_cavity();
      cb_mag_pockets(-1);
      cb_seam_ease(false);
    }
  }

  module cb_lid_blank() {
    difference() {
      cb_outer();
      cb_below_seam(cb_key_c());
      cb_cavity();
      cb_mag_pockets(1);
      cb_seam_ease(true);
    }
  }

  module cb_body() {
    difference() {
      cb_body_blank();
      cb_art_cut("front") { children(0); children(1); children(2); }
      cb_art_cut("back") { children(0); children(1); children(2); }
    }
  }

  module cb_lid() {
    difference() {
      cb_lid_blank();
      cb_art_cut("top") { children(0); children(1); children(2); }
    }
  }

  /* The seam test: the front wall across the seam, cut short, body and lid.
     Each lies outside down with its seam face to the front of the bed, so
     that Orca's seams, at the back, keep off it. */

  module cb_seam_coupon(i, lid) {
    $key_c = seam_fits[i][0];
    $mag_crush = seam_fits[i][1];
    x = seam_test_x;
    z = lid ? [z_sf - key_h - 1, z_sf + seam_test_h] : [z_sf - seam_test_h, z_sf + key_h + 1];
    difference() {
      intersection() {
        if (lid) cb_lid_blank();
        else cb_body_blank();
        cb_box(x, [-1, tf], z);
      }
      // Notches in the end away from the magnet.
      for (n = [0 : i]) translate([x[0], -1, z_sf + (lid ? 1 : -1) * (4 + 3.5 * n)])
        rotate([-90, 0, 0]) cylinder(d = 2, h = tf + 2);
    }
  }

  module cb_seam_test() {
    w = seam_test_x[1] - seam_test_x[0];
    for (i = [0 : len(seam_fits) - 1]) translate([i * (w + bed_gap), 0, 0]) {
      // The body's seam face is its top, so stood down toward the front.
      translate([-seam_test_x[0], z_sf + key_h + 1, 0]) rotate([90, 0, 0]) cb_seam_coupon(i, false);
      // The lid's is its bottom, so turned about as well.
      translate([seam_test_x[1], 2 * (key_h + 1) + seam_test_h + bed_gap - z_sf, 0])
        rotate([0, 0, 180]) rotate([90, 0, 0]) cb_seam_coupon(i, true);
    }
  }

  /* The magnet test: a strip of the front wall's thickness with a row of
     pockets, open to the inside as in the box. It lies outside down, seam face
     to the front of the bed. */

  module cb_mag_test() {
    r = mag_test_rim;
    pitch = mag.x + 2 * mag_glue + r;
    d = mag_d + mag_glue + r;
    n = len(mag_crushes);
    translate([r + mag.x / 2 + mag_glue, 0, tf]) rotate([-90, 0, 0]) difference() {
      cb_box([-pitch / 2 - r / 2, (n - 0.5) * pitch + r / 2], [0, tf], [0, d]);
      for (i = [0 : n - 1]) translate([i * pitch, 0, 0]) {
        $mag_crush = mag_crushes[i];
        cb_mag_pocket();
        // Notches in the edge away from the seam.
        for (k = [0 : i]) translate([(k - i / 2) * 3.5, -1, d]) rotate([-90, 0, 0]) cylinder(d = 2, h = tf + 2);
      }
    }
  }

  /* Panels: each is the part of a shell inside its region, its whole face of
     the box. The regions meet in mitred rabbets along every edge. */

  walls = ["front", "back", "left", "right"];

  module cb_region(name) {
    translate([-xo, 0, 0]) pb_panel(name, cb_size, [wall, tf, wall], relief = ease, ease = ease);
  }

  module cb_panel(name, lid = false) {
    intersection() {
      if (lid) cb_lid() { children(0); children(1); children(2); }
      else cb_body() { children(0); children(1); children(2); }
      cb_region(name);
    }
  }

  /* Placement */

  // Pulled e out along the panel's normal, the lid's panels lifted as well.
  module cb_exploded(name, e, lift = 0) {
    translate([0, 0, lift]) pb_exploded(name, e) children();
  }

  // On the bed, outside face down. Each wall's lid piece lies beyond its body
  // piece, the seam between them opened by lid_gap.
  module cb_flat(name, lid = false) {
    pb_flat(name, cb_size, bed_gap, lid_gap) translate([xo, 0, lid ? lid_gap : 0]) children();
  }

  // The pattern each panel's outside face prints in, on the bed. Front, back
  // and top: lines up the box, or across it. Sides: along the seam, which leans
  // the other way on each as they lie on the bed.
  // Monotonic lines at angle a on the bed, from +x.
  function cb_lines(a) = [orca_bottom_pattern("monotonic"), orca_solid_infill_direction(a)];
  function cb_face(name) =
    name == "front" || name == "back" ? cb_lines(90) :
    name == "left" ? cb_lines(atan2(1, -seam_k)) :
    name == "right" ? cb_lines(atan2(1, seam_k)) :
    name == "floor" ? [orca_bottom_pattern("concentric")] : cb_lines(0);

  // A face's art, as a panel: its own pattern, or its panel's.
  function cb_art_face(face) = cb_art_pattern(face) == "" ? cb_face(face) : [orca_bottom_pattern(cb_art_pattern(face))];

  /* The box: its pieces, or a view of it. Children are the art. */

  module cb_draw() {
    // The layers the joints fit at, and walls that print the magnets' covers:
    // one line wide, which classic walls would leave out.
    orca([orca_process("0.08 High Quality"), orca_layer_height(0.08), orca_first_layer_height(0.2),
          orca_wall_generator("arachne")]);
    if (part == "seam") {
      piece("seam test") color(box_color) cb_seam_test();
    } else if (part == "magnets") {
      piece("magnet test") color(box_color) cb_mag_test();
    } else if (part == "panels" || part == "body" || part == "lid") {
      if (part != "lid") {
        for (w = walls) piece(w, cb_face(w)) color(box_color) cb_flat(w) cb_panel(w) { children(0); children(1); children(2); }
        piece("floor", cb_face("floor")) color(box_color) cb_flat("floor") cb_panel("floor") { children(0); children(1); children(2); }
      }
      if (part != "body") {
        for (w = walls) piece(str("lid ", w), cb_face(w)) color(lid_c) cb_flat(w, true) cb_panel(w, true) { children(0); children(1); children(2); }
        piece("top", cb_face("top")) color(lid_c) cb_flat("top") cb_panel("top", true) { children(0); children(1); children(2); }
      }
      // The top's art is the lid's, the rest the body's.
      for (f = cb_art_faces) if (part == "panels" || (part == "lid") == (f == "top")) {
        layers = cb_art_layers(f);
        for (i = [0 : 1 : len(layers) - 1])
          piece(layers[i][0], cb_art_face(f)) color(layers[i][1]) cb_flat(f) cb_art(f, i) { children(0); children(1); children(2); }
      }
    } else {
      // Exploded pulls the panels apart, and the art out of its faces.
      e = part == "exploded" ? explode : 0;
      lift = part == "closed" ? 0 : part == "open" ? 40 : 3 * explode;
      color(box_color) {
        for (w = walls) cb_exploded(w, e) cb_panel(w) { children(0); children(1); children(2); }
        cb_exploded("floor", e) cb_panel("floor") { children(0); children(1); children(2); }
      }
      color(lid_c) {
        for (w = walls) cb_exploded(w, e, lift) cb_panel(w, true) { children(0); children(1); children(2); }
        cb_exploded("top", e, lift) cb_panel("top", true) { children(0); children(1); children(2); }
      }
      color("silver") for (w = ["front", "back"]) {
        cb_exploded(w, e) render() intersection() { cb_magnets(-1); cb_region(w); }
        cb_exploded(w, e, lift) render() intersection() { cb_magnets(1); cb_region(w); }
      }
      for (f = cb_art_faces) {
        layers = cb_art_layers(f);
        for (i = [0 : 1 : len(layers) - 1]) color(layers[i][1])
          cb_exploded(f, e, f == "top" ? lift : 0) cb_art(f, i) { children(0); children(1); children(2); }
      }
    }
  }

  // Art that isn't given draws nothing.
  cb_draw() {
    if ($children > 0) children(0);
    if ($children > 1) children(1);
    if ($children > 2) children(2);
  }
}
