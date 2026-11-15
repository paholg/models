// A ghost for the end of a wand, with its one last vote in its mouth, in a slot,
// to take when it's spent.
//
// The wand is a hexagonal pencil, pressed into a socket in the ghost's hem
// and pulled out again to put away: three thin walls in the socket spring
// against three of its flats. The ghost prints standing, the vote face down.
//
// The vote has a magnet or steel sealed in its middle, and disc magnets
// above the slot hold it. The ghost and the vote are separate prints, and
// each pauses for what goes in it, then prints over.
//
// The ghost faces -y. In the vote's own frame its face is at z = 0, and the
// end that goes in the mouth is at -x.

// export: ghost vote fit

use <../../lib/piece.scad>

/* [Output] */
// `fit` is the socket alone, at each of `fit_press`, to try on a pencil: the
// dots on each count from the loosest.
part = "assembled"; // [assembled, empty, ghost, vote, fit]

/* [Ghost] */
// Across the shoulders, where the dome starts.
d = 28;
h = 40;
shoulder = 25;
// A bell: the body is this much wider each side at the hem, and the power
// sets how late it flares.
bell = 4.5;
bell_power = 1.8;
// The hem ripples below this height.
hem_h = 10;
hem_ripple = 1.2;
hem_lobes = 6;
// Folds in the sheet, from the crown to the hem: how deep, how many, and how
// far they wind round on the way down, in degrees. They fade out over the face.
fold = 0.9;
fold_n = 7;
fold_twist = 40;
foot_chamfer = 0.4;

/* [Eyes] */
eye_x = 5;
eye_z = 31;
eye_w = 3.6;
eye_h = 5.2;
eye_depth = 0.8;

/* [Wand] */
// The pencil, across its flats and across its corners.
pencil_flats = 7.0;
pencil_corners = 8.0;
wand_l = 180;
socket_depth = 11;
// Around the pencil's corners.
socket_c = 0.15;
// Each spring is a wall across the socket, held at its ends, with room behind
// to bend into. They stand the socket's whole depth: the pencil goes
// in by its plain end, its dipped end out.
spring_h = socket_depth;
spring_t = 0.5;
spring_span = 8;
spring_gap = 0.6;
// The socket's roof closes in steps this high.
roof_step = 0.2;
// How far the pencil pushes each spring back.
press = 0.15;
fit_press = [0, 0.1, 0.2, 0.3];

/* [Mouth] */
mouth_z = 18.8;
mouth_w = 25;
mouth_h = 12;
// How far the mouth is sunk into the face, and how thick its black back is.
mouth_depth = 2;
mouth_back = 2;
// Rounds the mouth's rim over.
mouth_round = 0.8;
// The slot leaves the face this far above the mouth's middle: the vote's
// corners leave it lower, where the face curves away.
slot_rise = 1.2;
// The vote sticks out of the mouth this far above level.
slot_angle = 30;
slot_depth = 10;
// The black around the slot, inside the ghost.
slot_wall = 0.6;
slot_c = 0.35;
// On the slot's edges, at the back of the mouth.
slot_chamfer = 0.5;
slot_round = 1.5;

/* [Vote] */
vote_w = 27.4;
vote_h = 14.7;
vote_t = 3.4;
vote_corner = 1.5;
vote_chamfer = 0.4;
// What's sealed in the vote: a bar magnet for now, and later two steel
// strike plates, 25.4 x 12.7 x 2 in all.
insert = [18.4, 9, 2.5];
// Around the insert's edges, and over it. The pocket is in the vote's
// middle, and with this its floor and its top fall between layers 0.1 high,
// whether the first is 0.2 or 0.25: on one, the slicer could take either side.
insert_c = 0.2;
insert_gap = 0.15;
label = "VOTE";
font = "Liberation Sans:style=Bold";
text_size = 5.5;
// Less than the skin over the insert.
inlay = 0.2;

/* [Magnets] */
// Discs in the ghost, stacked.
mag_d = 6;
mag_h = 2;
mag_n = 2;
mag_c = 0.1;
// From the vote's end to the ghost's magnets.
mag_inset = 1;
// Between the slot and the ghost's magnet.
mag_skin = 0.6;
// Open above the magnets' pocket, under what bridges it.
mag_over = 0.2;

/* [Colors] */
c_ghost = "White";
c_eyes = "Black";
c_vote = "FireBrick";
c_text = "White";

/* [Hidden] */
$fn = 64;
eps = 0.01;
// Out of the print, each color's hole is this much smaller than what fills
// it: walls that meet exactly flicker in OpenSCAD's view.
fit = part == "ghost" || part == "vote" ? 0 : 0.02;
r = d / 2;
slot_t = vote_t + 2 * slot_c;
slot_h = vote_h + 2 * slot_c;
mag_depth = mag_n * mag_h + 2 * mag_c;
// What's left hollow in the vote, in its middle: its size, and the skin
// under it, which is the same as over it.
hollow = [insert[0] + 2 * insert_c, insert[1] + 2 * insert_c, insert[2] + insert_gap];
hollow_z = (vote_t - hollow[2]) / 2;
// Each goes in once the print is past its top.
vote_pause = hollow_z + hollow[2];
ghost_pause = mouth_z + slot_rise - slot_depth * sin(slot_angle) - slot_t / 2 * cos(slot_angle)
  + (mag_inset + mag_d + mag_c) * sin(slot_angle)
  + (slot_t + mag_skin + mag_depth) * cos(slot_angle) + mag_over;

// The ghost's skin, as rings of points.
steps = 96;
zs = concat(
  [0, foot_chamfer],
  [for (z = [1:0.5:shoulder]) z],
  [for (a = [3:3:87]) shoulder + (h - shoulder) * sin(a)]
);
function hem(z) = pow(max(0, 1 - z / hem_h), 2);
// The body's radius, without the ripples.
function body_r(z) = r + bell * pow(max(0, 1 - z / shoulder), bell_power);
// Two sets of folds, out of step, so that no two are alike.
function folds(z, a) =
  let (
    turn = fold_twist * (1 - z / h),
    off_face = min(abs(a - 270), 360 - abs(a - 270)),
    face = 1 - exp(-pow(off_face / 55, 2))
  )
    fold * pow(1 - z / h, 0.6) * face
      * (0.6 * cos(fold_n * (a + turn)) + 0.4 * cos((fold_n + 4) * (a - 0.6 * turn) + 40));
function radius(z, a) =
  folds(z, a) + (
    z < shoulder
      ? body_r(z) + hem_ripple * cos(hem_lobes * a) * hem(z)
        - (z == 0 ? foot_chamfer : 0)
      : r * sqrt(1 - pow((z - shoulder) / (h - shoulder), 2))
  );

module skin() {
  n = len(zs);
  points = concat(
    [for (z = zs, j = [0:steps - 1])
      let (a = j * 360 / steps, q = radius(z, a)) [q * cos(a), q * sin(a), z]],
    [[0, 0, h]]
  );
  faces = concat(
    [[for (j = [0:steps - 1]) j]],
    [for (i = [0:n - 2], j = [0:steps - 1])
      let (k = (j + 1) % steps)
        [i * steps + j, (i + 1) * steps + j, (i + 1) * steps + k, i * steps + k]],
    [for (j = [0:steps - 1])
      [n * steps, (n - 1) * steps + (j + 1) % steps, (n - 1) * steps + j]]
  );
  polyhedron(points, faces, convexity = 4);
}

// The socket's outline: a triangle of springs around the pencil, its corners
// rounded off, and the room behind each spring. Without the springs, it's all
// of that, as above them.
module socket_2d(press, springs = true) {
  g = pencil_flats / 2 - press;
  rc = sqrt(g * g + spring_span * spring_span / 4);
  assert(rc >= pencil_corners / 2 + socket_c, "the springs are too short to clear the pencil's corners");
  for (i = [0:2]) rotate(i * 120 + 90) {
    intersection() {
      circle(r = rc);
      rotate(-30) translate([0, -rc]) square([2 * rc, 2 * rc]);
      rotate(30) translate([0, -rc]) square([2 * rc, 2 * rc]);
      translate([-rc, -rc]) square([rc + g, 2 * rc]);
    }
    translate([g + spring_t, -spring_span / 2]) square([spring_gap, spring_span]);
    if (!springs) translate([g - eps, -spring_span / 2]) square([spring_t + 2 * eps, spring_span]);
  }
}

// The pencil's socket, under a roof that closes in at 45 degrees, to print
// without support.
module socket(press = press) {
  top = pencil_flats / 2 - press + spring_t + spring_gap;
  translate([0, 0, -eps]) linear_extrude(spring_h + eps) socket_2d(press);
  translate([0, 0, spring_h]) linear_extrude(socket_depth - spring_h + eps)
    socket_2d(press, false);
  for (k = [0:roof_step:top])
    translate([0, 0, socket_depth + k]) linear_extrude(roof_step + eps)
      offset(delta = -k) socket_2d(press, false);
}

// The socket alone, in a collar, with dots to tell it by.
module fit_piece(i) {
  od = 2 * (pencil_flats / 2 + spring_t + spring_gap) + 6;
  c = 0.5;
  difference() {
    hull() {
      cylinder(d = od - 2 * c, h = socket_depth);
      translate([0, 0, c]) cylinder(d = od, h = socket_depth - 2 * c);
    }
    socket(fit_press[i]);
    translate([0, 0, socket_depth - eps]) linear_extrude(10) socket_2d(fit_press[i], false);
    for (j = [0:i]) rotate(j * 25 - 90) translate([od / 2 - 1.5, 0, socket_depth - 0.4])
      cylinder(d = 1.2, h = 1, $fn = 16);
  }
}

// The slot's own frame: x runs out of the mouth from the slot's end, y across
// the vote, and z up through it.
module in_slot() {
  c = cos(slot_angle);
  n = sin(slot_angle);
  z = mouth_z + slot_rise;
  o = [0, -body_r(z), z] + slot_depth * [0, c, -n] - slot_t / 2 * [0, n, c];
  multmatrix([
    [0, 1, 0, o[0]],
    [-c, 0, n, o[1]],
    [n, 0, c, o[2]],
    [0, 0, 0, 1],
  ]) children();
}

module slot(grow = 0, side = 0) {
  in_slot() translate([0, -slot_h / 2 - grow - side, -grow])
    cube([slot_depth + d, slot_h + 2 * (grow + side), slot_t + 2 * grow]);
}

// What chamfering the slot's edges takes off the back of the mouth: steps, each
// a little narrower and a little deeper than the last.
module slot_edge() {
  n = 5;
  for (k = [0:n - 1])
    difference() {
      slot(slot_chamfer * (1 - (k + 0.5) / n));
      inner(mouth_depth + slot_chamfer * (k + 1) / n);
    }
  // And its two ends rounded over, further, to lead the vote in from either
  // side. Only within the mouth: the slot's corners come near its rim.
  for (t = [0:15:75])
    difference() {
      intersection() {
        slot(side = slot_round * (1 - cos(t)));
        mouth_hole();
      }
      inner(mouth_depth + slot_round * (1 - sin(t)));
    }
}

// The ghost's magnet lies along the slot, above it. Its pocket is open
// straight up as far as the pause, to drop the magnet in.
module pocket() {
  intersection() {
    hull() for (lift = [0, h])
      translate([0, 0, lift]) in_slot()
        translate([mag_inset + mag_d / 2, 0, slot_t + mag_skin])
          cylinder(d = mag_d + 2 * mag_c, h = mag_depth);
    translate([-d, -d, 0]) cube([2 * d, 2 * d, ghost_pause]);
  }
}

// The skin, this far in.
module inner(depth) {
  translate([0, 0, shoulder]) scale(1 - depth / r) translate([0, 0, -shoulder]) skin();
}

module mouth_hole(grow = 0) {
  translate([0, 0, mouth_z]) rotate([90, 0, 0])
    scale([mouth_w / 2 + grow, mouth_h / 2 + grow, 1]) cylinder(r = 1, h = d);
}

// The cuts for what's black reach out past the skin, and each black piece is
// what's left of its cut inside the skin: a cut that ended on the skin itself
// would leave slivers there.

// The mouth's back, and a sheath around the slot, so that no white shows
// down it. The mouth's sides are the ghost's own.
module mouth_cut(grow = 0) {
  w = slot_wall + grow;
  difference() {
    mouth_hole(grow);
    inner(mouth_depth + mouth_back + grow);
  }
  // Out to the face: the vote's corners pass the mouth's rim.
  mouth_sheath(w);
  // And all that's between the sheath and the mouth's back, which would be an
  // island of white in each layer.
  intersection() {
    mouth_hole(grow);
    hull() for (y = [0, -d]) translate([0, y, 0]) mouth_sheath(w);
  }
}

module mouth_sheath(w) {
  in_slot() translate([-w, -slot_h / 2 - w, -w])
    cube([slot_depth + w + 1, slot_h + 2 * w, slot_t + 2 * w]);
}

// What rounding the rim takes off: steps around a quarter circle, each a
// little wider and a little shallower than the last.
module mouth_rim() {
  for (t = [0:15:75])
    difference() {
      mouth_hole(mouth_round * (1 - cos(t)));
      inner(mouth_round * (1 - sin(t)));
    }
}

module mouth() {
  render(convexity = 6) difference() {
    intersection() {
      inner(mouth_depth);
      mouth_cut();
    }
    slot();
    slot_edge();
    pocket();
  }
}

module eye_holes(grow = 0) {
  for (s = [-1, 1]) translate([s * eye_x, 0, eye_z]) rotate([90, 0, 0])
    scale([eye_w / 2 + grow, eye_h / 2 + grow, 1]) cylinder(r = 1, h = d);
}

module eye_cut(grow = 0) {
  difference() {
    eye_holes(grow);
    inner(eye_depth + grow);
  }
}

module eyes() {
  render(convexity = 4) intersection() {
    skin();
    eye_cut();
  }
}

module ghost() {
  render(convexity = 6) difference() {
    skin();
    eye_cut(-fit);
    mouth_cut(-fit);
    mouth_rim();
    socket();
    slot();
    pocket();
  }
}

module vote_2d() {
  offset(r = vote_corner) offset(delta = -vote_corner)
    square([vote_w, vote_h], center = true);
}

module label_2d() {
  text(label, size = text_size, font = font, halign = "center", valign = "center");
}

// On both sides, in the middle. The face's is flipped, to read from below.
// `over` is how far it stands out of each side, to cut its place with.
module vote_text(grow = 0, over = 0) {
  {
    translate([0, 0, -over]) mirror([0, 1, 0])
      linear_extrude(inlay + grow + over) offset(delta = grow) label_2d();
    translate([0, 0, vote_t - inlay - grow])
      linear_extrude(inlay + grow + over) offset(delta = grow) label_2d();
  }
}

module vote() {
  c = vote_chamfer;
  n = 4;
  render(convexity = 6) difference() {
    union() {
      for (i = [0:n - 1]) {
        inset = c * (1 - i / n);
        translate([0, 0, i * c / n])
          linear_extrude(c / n + eps) offset(delta = -inset) vote_2d();
        translate([0, 0, vote_t - (i + 1) * c / n])
          linear_extrude(c / n) offset(delta = -inset) vote_2d();
      }
      translate([0, 0, c]) linear_extrude(vote_t - 2 * c) vote_2d();
    }
    vote_text(-fit, 1);
    translate([0, 0, hollow_z + hollow[2] / 2]) cube(hollow, center = true);
  }
}

// Into the ghost's mouth, face up.
module held() {
  in_slot() translate([vote_w / 2, 0, slot_t - slot_c]) rotate([180, 0, 0]) children();
}

// The ghost's seams are scattered, not in a line. Orca keeps a seam's place
// for a whole object, so the ghost is one of its own: its pieces share a name
// for that, and each carries the setting.
orca_seam = "seam_position=random";
// The sheet's texture: soft bumps on the outside of the white alone, which
// leaves the socket's springs, and the black, smooth.
orca_ghost = str(
  orca_seam,
  " fuzzy_skin=external fuzzy_skin_noise_type=perlin fuzzy_skin_scale=2.5",
  " fuzzy_skin_thickness=0.2 fuzzy_skin_point_distance=0.3",
  " fuzzy_skin_octaves=2 fuzzy_skin_persistence=0.4"
);

// The vote's layers are thin, for its edges. Orca keeps a layer height for a
// whole object, so, as with the ghost, its pieces share a name and the setting.
orca_vote = "layer_height=0.1 top_surface_pattern=hilbertcurve bottom_surface_pattern=hilbertcurve";

if (part == "fit") {
  od = 2 * (pencil_flats / 2 + spring_t + spring_gap) + 6;
  piece("fit") color(c_ghost) render(convexity = 6)
    for (i = [0:len(fit_press) - 1]) translate([i * (od + 3), 0, 0]) fit_piece(i);
} else if (part == "ghost") {
  echo(pause = ghost_pause);
  piece("ghost", orca_ghost) color(c_ghost) ghost();
  piece("ghost", orca_seam) color(c_eyes) eyes();
  piece("ghost", orca_seam) color(c_eyes) mouth();
} else if (part == "vote") {
  echo(pause = vote_pause);
  piece("vote", orca_vote) color(c_vote) vote();
  piece("vote", orca_vote) color(c_text) vote_text();
} else if (part == "assembled" || part == "empty") {
  color(c_ghost) ghost();
  color(c_eyes) eyes();
  color(c_eyes) mouth();
  if (part == "assembled") {
    color(c_vote) held() vote();
    color(c_text) held() vote_text();
  }
  color("#222") translate([0, 0, socket_depth - wand_l])
    cylinder(d = pencil_corners, h = wand_l, $fn = 6);
}
