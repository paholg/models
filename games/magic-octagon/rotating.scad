// The reeded coin of coin.scad, with halves that turn against each other and
// lock every 45 degrees. Locked, it looks and handles like the glued coin; a
// strong magnet frees the lock.
//
// The halves are held together by a hub: a flanged post, trapped in the gold
// half's cavity by a ring glued over it, and glued into a socket in the black
// half. Both glue joints are inside, so the edge shows only the one seam.
// A steel wave washer (6 x 12 x 0.3) between ring and flange draws the halves
// together, face on face, so that nothing rattles; the ring stands into the
// black half to make room for it.
//
// The lock comes two ways, to try both:
//
// * radial: a printed wedge with a 2x6 steel dowel pin pressed into it lies
//   across the seam, in a channel of the gold half that narrows toward the
//   centre. A 2x2 magnet inboard of it, glued in a slot of the ring, draws it
//   in, into one of eight notches in the black half. Channel and notch are
//   one taper across the seam, so the wedge jams in both halves at once and
//   leaves no play. A magnet held to the rim at the wedge draws it out, into
//   the wide of the channel and a groove that runs all the way round.
// * axial: a printed plunger, a cone with a 3x1 magnet in it, in a sleeve
//   glued into the gold half. The sleeve's bore and each of the black half's
//   eight seats are one cone across the seam, so the plunger, drawn into a
//   seat by the 3x1 magnet beyond it (all eight the same way up), wedges in
//   both halves at once and leaves no play. The plunger's roof is the plastic
//   between the magnets. Laying the coin gold face down on a magnet draws the
//   plunger back, into the wide end of the sleeve; the magnet has to be the
//   right way up.
//
// Assembly: hub into the gold half's cavity, flange down; glue the ring over
// it, washer on its stem; glue the ring over them, sparingly and at its outer
// edge, held down against the washer until it sets, and see that the hub
// still turns.
// Radial: glue the magnet into the ring's slot; pin into the wedge, and the
// wedge in, pin down. Axial: glue the black half's magnets in, and one
// to the top of the plunger's pocket; plunger into the sleeve from its wide
// end, and glue the sleeve into the gold half. Then a little gel glue in the
// black half's socket, and press it on.
//
// In a half's own frame the face is at z = 0 and the seam side is up.

// export: radial axial

use <../../lib/orca.scad>
use <../../lib/piece.scad>
use <coin.scad>

/* [Output] */
// `radial` and `axial` are the prints; the others show `lock`.
part = "assembled"; // [assembled, exploded, section, inside, radial, axial]
lock = "radial"; // [radial, axial]

/* [Coin] */
// Thicker than coin.scad's 2.5, for the washer's height.
half_t = 3;

/* [Hub] */
stem_d = 5.6;
flange_d = 12.4;
flange_t = 0.6;
ring_d = 18;
ring_t = 0.6;
// How much of the ring is in the gold half; the rest stands into the black.
ring_down = 0.2;
// The wave washer, and the height it is squeezed to, between ring and flange:
// lower presses the halves together harder. As measured, and squeezed about
// half of the way to flat.
washer_id = 6.1;
washer_od = 11.82;
washer_t = 0.3;
washer_free = 1.8;
spring_h = 1;
// What is glued into the gold half sits this far under the seam, clear of the
// other half.
ring_sink = 0.05;
// Under the flange, and around the stem and the ring.
play = 0.1;
// How far the stem goes into the black half, from the seam.
socket_depth = 2;
socket_c = 0.15;
// A wider mouth on the socket, to stop glue creeping up the stem.
trap = 0.5;
trap_depth = 0.3;
ribs = 3;
rib_w = 0.8;
rib_press = 0.1;
chamfer = 0.3;

/* [Lock] */
// How the sides of the wedge and of the plunger lean. Steeper is less fussy
// about the print's size, but lets a twist push them out.
taper = 12;

/* [Radial lock] */
pin_d = 2;
pin_l = 6;
// How far the wedge moves, and how far it reaches into a notch.
travel = 1.2;
// From the magnet to the wedge and its pin, seated: sets how hard it is held.
hold_gap = 0.6;
hold_d = 2;
hold_l = 2;
// The wedge: beside the pin at its narrow end, beyond the pin at its wide
// one, and how far it stands into each half. The pin lies under a roof, in
// the gold half's side.
wedge_wall = 0.6;
wedge_end = 0.6;
wedge_up = 1;
wedge_down = 1.6;
// Added to the width of the channel and the notches. A tenth here moves where
// the wedge stops by a quarter of a millimetre: wider seats it further in.
wedge_fit = 0;
// Each side of the magnet.
lock_c = 0.1;
// More room where the other half only has to clear what turns past.
sweep_c = 0.2;
// Where the wedge is, from the gold arrow: behind its tail.
pin_a = 180;

/* [Axial lock] */
// The magnets: the plunger's, and the eight that hold it.
apin_d = 3;
apin_t = 1;
ahold_d = 3;
ahold_t = 1;
// How wide the cone is at the seam.
cone_d0 = 4.3;
// Added to the width of the sleeve's bore and of the seats. A tenth here moves
// where the plunger stops by a quarter of a millimetre: wider seats it deeper.
cone_fit = 0;
// How far the plunger reaches across the seam, and how much further it could.
engage = 0.7;
seat_extra = 0.25;
// Over the plunger's magnet: the plastic between it and the one that holds it.
roof = 0.4;
sleeve_wall = 0.8;
// What the gold half keeps under the sleeve, over the arrow's inlay.
floor_a = 0.45;
apin_r = 13;
// Behind the gold arrow's tail, as the wedge is.
apin_a = 180;

/* [Hidden] */
$fn = 96;
eps = 0.01;
// Every 45 degrees the halves' bumps line up again.
$shape = "knurled";

d = coin_d();
$half_t = half_t;
inlay = coin_inlay();
angles = coin_angles();
c_half = coin_colors()[0];
c_arrow = coin_colors()[1];
steps = 8;

seat_r = ring_d / 2 + play;
// The black half's room for the ring.
recess_b = ring_t - ring_down + play;
cav_r = flange_d / 2 + 3 * play;
cav_depth = ring_down + spring_h + flange_t + play;
stem_l = ring_down + spring_h + socket_depth;
assert(washer_id > stem_d && flange_d >= washer_od, "the washer doesn't fit the hub");
assert(spring_h > washer_t && spring_h < washer_free, "the washer isn't squeezed, or is crushed");

lock_r = seat_r + hold_gap;
hold_in = seat_r - hold_l - 2 * lock_c;
free_r = lock_r + travel;
wedge_l = pin_l + wedge_end;
wedge_h = wedge_up + wedge_down;
// The wedge's width, seated, this far from the centre.
function wedge_w(r) = pin_d + 2 * wedge_wall + 2 * (r - lock_r) * tan(taper);
// What its outer corners sweep, drawn out.
sweep_r = norm([free_r + wedge_l, wedge_w(lock_r + wedge_l) / 2]) + sweep_c;

// The cone's width, this far from the seam into the gold half.
function cone_d(s) = cone_d0 + 2 * s * tan(taper);
pocket_depth = half_t - inlay - floor_a;
sleeve_h = pocket_depth - ring_sink;
sleeve_d = cone_d(pocket_depth) + cone_fit + 2 * sleeve_wall;
// Drawn back, the plunger stands on the pocket's floor, clear of the seam.
plunger_h = pocket_depth - 0.15;
// Where its base is when it is seated.
seated = plunger_h - engage;
seat_depth_b = engage + seat_extra;

// The thinnest floors, all over an arrow's inlay: under the cavity, and under
// the axial lock's sleeve and magnets.
floor_hub = min(half_t - inlay - cav_depth, half_t - inlay - socket_depth);
floor_pin = floor_a;
floor_hold = half_t - inlay - seat_depth_b - ahold_t - 0.05;
echo(floor_hub = floor_hub, floor_pin = floor_pin, floor_hold = floor_hold);
assert(floor_hub >= 0.4 - eps, "the cavity leaves too little under the arrow");
assert(floor_hold >= 0.4 - eps, "the magnets leave too little under them");
assert(apin_r - sleeve_d / 2 >= seat_r + 0.4, "the sleeve is too near the ring");
assert(cone_d(seated - plunger_h + roof) >= apin_d + 1, "the plunger's wall is too thin");
assert(hold_in >= cav_r + 0.4 - eps, "the magnet's slot breaks into the cavity");
assert(sweep_r + 1.5 <= d / 2, "the wedge's groove is too near the rim");

// Cut from the seam side of a half: a bore, a ring, and a slot along +x.
module bore(r, depth) {
  translate([0, 0, half_t - depth]) cylinder(r = r, h = depth + eps);
}

module groove(r0, r1, depth) {
  translate([0, 0, half_t - depth]) linear_extrude(depth + eps)
    difference() { circle(r = r1); circle(r = r0); }
}

module slot(r0, r1, w, depth) {
  translate([r0, -w / 2, half_t - depth]) cube([r1 - r0, w, depth + eps]);
}

// The wedge's outline along +x, seated, from r0 to r1; `fit` wider.
module taper_2d(r0, r1, fit = 0) {
  polygon([for (e = [[r0, 1], [r1, 1], [r1, -1], [r0, -1]])
    [e[0], e[1] * (wedge_w(e[0]) + fit) / 2]]);
}

// As printed: roof down, the pin's slot open above, and open at the narrow
// end, where the pin's end faces the magnet.
module wedge() {
  difference() {
    linear_extrude(wedge_h) taper_2d(lock_r, lock_r + wedge_l);
    translate([lock_r - eps, -pin_d / 2, wedge_h - pin_d - 0.05])
      cube([pin_l + 0.1, pin_d, pin_d + 1]);
  }
}

module face(i) {
  translate([0, 0, -eps]) scale([1, 1, 1 + eps]) arrow(angles[i]);
}

// The gold half: the hub's cavity and the ring's seat, and the lock's moving
// part.
module half_a() {
  difference() {
    blank();
    face(0);
    bore(cav_r, cav_depth);
    bore(seat_r, ring_down);
    if ($lock == "radial") rotate(pin_a) {
      translate([0, 0, half_t - wedge_down - 0.05]) linear_extrude(wedge_down + 0.05 + eps)
        taper_2d(seat_r - eps, free_r + wedge_l + lock_c, wedge_fit);
      slot(hold_in, seat_r, hold_d + 2 * lock_c, hold_d / 2 + lock_c);
    } else rotate(apin_a) translate([apin_r, 0, 0]) {
      bore(sleeve_d / 2 + 0.05, pocket_depth);
    }
  }
}

// The stem's socket, crush ribs below a glue trap, under the ring's room.
module socket() {
  r = stem_d / 2 + socket_c;
  difference() {
    bore(r, socket_depth);
    for (i = [0:ribs - 1]) rotate(i * 360 / ribs)
      translate([stem_d / 2 - rib_press, -rib_w / 2, half_t - socket_depth - eps])
        cube([1, rib_w, socket_depth - recess_b - trap_depth]);
  }
  bore(r + trap, recess_b + trap_depth);
  bore(seat_r + sweep_c, recess_b);
}

// The black half, in its own frame. What locks is the same every 45 degrees,
// so its being flipped over is no matter.
module half_b() {
  difference() {
    blank();
    face(1);
    socket();
    if ($lock == "radial") {
      // Round the magnet, which stands half out of the ring.
      groove(hold_in - sweep_c, seat_r + sweep_c, hold_d / 2 + sweep_c);
      // Round the wedge, drawn out.
      groove(free_r - eps, sweep_r, wedge_up + sweep_c);
      for (i = [0:steps - 1]) rotate(pin_a + i * 360 / steps)
        translate([0, 0, half_t - wedge_up - sweep_c]) linear_extrude(wedge_up + sweep_c + eps)
          taper_2d(seat_r, free_r, wedge_fit);
    } else {
      for (i = [0:steps - 1]) at_detent(i) {
        translate([0, 0, half_t - seat_depth_b])
          cylinder(d1 = cone_d(-seat_depth_b) + cone_fit, d2 = cone_d(0) + cone_fit,
                   h = seat_depth_b + eps);
        bore(ahold_d / 2 + 0.05, seat_depth_b + ahold_t + 0.05);
      }
    }
  }
}

// The axial lock's seats, in the black half's frame.
module at_detent(i) {
  rotate(-apin_a + i * 360 / steps) translate([apin_r, 0, 0]) children();
}

// As printed, and as it sits in the gold half: wide end down.
module sleeve() {
  difference() {
    cylinder(d = sleeve_d, h = sleeve_h);
    translate([0, 0, -eps])
      cylinder(d1 = cone_d(pocket_depth) + cone_fit, d2 = cone_d(ring_sink) + cone_fit,
               h = sleeve_h + 2 * eps);
  }
}

// As printed: wide end down. Its magnet goes to the top of its pocket.
module plunger() {
  difference() {
    cylinder(d1 = cone_d(seated), d2 = cone_d(-engage), h = plunger_h);
    translate([0, 0, -eps]) cylinder(d = apin_d + 0.1, h = plunger_h - roof + eps);
  }
}

// As printed: one flat side down. The radial lock's magnet goes through it.
module ring() {
  difference() {
    cylinder(r = ring_d / 2, h = ring_t);
    translate([0, 0, -eps]) cylinder(r = stem_d / 2 + play, h = ring_t + 2 * eps);
    if ($lock == "radial") rotate(pin_a)
      translate([hold_in, -hold_d / 2 - lock_c, -eps])
        cube([ring_d, hold_d + 2 * lock_c, ring_t + 2 * eps]);
  }
}

// As printed: flange down.
module hub() {
  cylinder(d = flange_d, h = flange_t);
  cylinder(d = stem_d, h = flange_t + stem_l - chamfer);
  translate([0, 0, flange_t + stem_l - chamfer])
    cylinder(d1 = stem_d, d2 = stem_d - 2 * chamfer, h = chamfer);
}

// The hardware, where it rests when locked.
module hardware() {
  if ($lock == "radial") rotate(pin_a) translate([0, 0, half_t]) {
    color("Peru") translate([0, 0, wedge_up]) rotate([180, 0, 0]) wedge();
    color("Silver") translate([lock_r, 0, pin_d / 2 + 0.05 - wedge_down]) rotate([0, 90, 0])
      cylinder(d = pin_d, h = pin_l);
    color("DimGray") translate([seat_r - hold_l, 0, 0]) rotate([0, 90, 0])
      cylinder(d = hold_d, h = hold_l);
  } else {
    rotate(apin_a) translate([apin_r, 0, 0]) {
      color("Khaki") translate([0, 0, half_t - pocket_depth]) sleeve();
      color("Peru") translate([0, 0, half_t - seated]) plunger();
      color("Silver") translate([0, 0, half_t + engage - roof - apin_t])
        cylinder(d = apin_d, h = apin_t);
    }
    color("DimGray") for (i = [0:steps - 1]) rotate(apin_a + i * 360 / steps)
      translate([apin_r, 0, half_t + seat_depth_b]) cylinder(d = ahold_d, h = ahold_t);
  }
}

// The black half goes on upside down.
module flipped(e = 0) {
  translate([0, 0, 2 * half_t + e]) rotate([180, 0, 0]) children();
}

module assembly(e = 0, top = true) {
  color(c_half[0]) half_a();
  color(c_arrow[0]) arrow(angles[0]);
  color("Peru") translate([0, 0, half_t - cav_depth + play + e / 3]) hub();
  color("Silver") translate([0, 0, half_t - ring_down - spring_h + e / 2]) difference() {
    cylinder(d = washer_od, h = spring_h);
    translate([0, 0, -eps]) cylinder(d = washer_id, h = spring_h + 2 * eps);
  }
  color("Khaki") translate([0, 0, half_t - ring_down + 2 * e / 3]) ring();
  translate([0, 0, e]) hardware();
  if (top) {
    color(c_half[1]) flipped(2 * e) half_b();
    color(c_arrow[1]) flipped(2 * e) arrow(angles[1]);
  }
}

module bed(x, y = 0) {
  translate([x * (d + 5), -y * (d + 5), 0]) children();
}

if (part == "radial" || part == "axial") {
  $lock = part;
  piece("half 0", half_settings($shape)) color(c_half[0]) bed(0) half_a();
  piece("arrow 0", arrow_settings(angles[0])) color(c_arrow[0]) bed(0) arrow(angles[0]);
  piece("half 1", half_settings($shape)) color(c_half[1]) bed(1) half_b();
  piece("arrow 1", arrow_settings(angles[1])) color(c_arrow[1]) bed(1) arrow(angles[1]);
  piece("ring") color(c_half[0]) bed(0, 0.75) ring();
  piece("hub") color(c_half[0]) bed(1, 0.75) hub();
  if (part == "radial")
    piece("wedge") color(c_half[0]) bed(0.5, 0.75) rotate(90) translate([-lock_r, 0, 0]) wedge();
  if (part == "axial") {
    piece("sleeve") color(c_half[0]) bed(0.3, 0.75) sleeve();
    piece("plunger") color(c_half[0]) bed(0.6, 0.75) plunger();
  }
} else {
  $lock = lock;
  if (part == "section") difference() {
    assembly();
    rotate($lock == "radial" ? pin_a : apin_a) translate([-d, -d, -1]) cube([2 * d, d, 10]);
  } else if (part == "inside") {
    assembly(top = false);
    translate([d + 5, 0, 0]) color(c_half[1]) half_b();
  } else {
    assembly(part == "exploded" ? 6 : 0);
  }
}
