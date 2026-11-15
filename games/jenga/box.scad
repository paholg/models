// Jenga box in two three-sided halves. The stacker is the back and right walls
// plus an end cap, a little shorter than the tower. Cap up, it squares the
// tower in its back-right corner and slides off. Cap down, it holds the blocks,
// and the lid (front and left walls plus the other end cap) slides down onto
// it. A lip on the lid's back and right edges covers the rest of the tower.
// The right one is a strip of its own, glued in: slide it up from below, its
// pointed ends in the lid's notches, until it meets the cap, then run thin CA
// along it inside.
//
// The halves slide on two dovetail seams, each a 180° turn of the other: a
// groove in one half's wall, and a tongue on the edge of the other half's.
// A store-bought draw latch will hold the lid down, across the seam under the
// lip; its screw holes are still to come.
//
// Storage orientation: x is right, y is toward the front, z is up. The tower
// stands on the stacker's cap at z = 0.
//
// Print the stacker on its right side and the lid on its left, each at 45° to
// fit the bed diagonally. Both grooves are then in a wall on the bed and face
// up, and both tongues are the top edge of a standing wall: nothing in the
// joint overhangs. The lip strip, which would be a bridge at the top of the
// lid, lies beside it, outside face down.
//
// "joint" is a test to print first: lengths of groove and of tongue at the
// clearances in joint_clears, printed as their walls are in the box.

// export: stacker lid joint
// orca: brim_type=outer_only brim_width=5

/* [Output] */
part = "assembly"; // [assembly, stack, stacker, lid, joint]
// Lid height above closed, in the assembly view.
lid_raise = 0;

/* [Tower] */
// Measure your own tower; sets vary.
tower_w = 75;
tower_h = 270;
// Per side.
tower_clear = 0.5;
// How much shorter the stacker's walls are than the tower. The lid's lip
// makes up the rest.
stacker_short = 5;

/* [Walls] */
wall = 4;
cap_t = 2;
// Each tongue rides in a dovetail groove in the other half's wall.
tongue_t = 1.6;
groove_depth = 2;
// Undercut angle on the groove's inner side.
dovetail = 30;

/* [Edges] */
// Outer edges, and the inner edges at each half's open end.
chamfer = 1;
// V-groove along the outside seams between the halves.
reveal = 0.5;

/* [Fit] */
slide_clear = 0.2;
// Chamfer on the tongue tips and groove mouths.
lead_in = 0.6;
// Gap under the lid's walls, so that it's the seam under the lip that closes.
seat_gap = 0.2;

/* [Lip strip] */
// How far each pointed end reaches into its notch.
lip_key = 1.5;
// Clearance at each end.
lip_c = 0.1;
// How far the crush ribs on the ends' flanks bite.
lip_crush = 0.1;

/* [Tests] */
joint_clears = [0.15, 0.2, 0.3];
joint_len = 40;

/* [Hidden] */
$fn = 48;

eps = 0.01;
c = slide_clear;
tb = tongue_t;
gd = groove_depth;
li = lead_in;
t_dv = tan(dovetail);

iw = tower_w + 2 * tower_clear;
ih = tower_h + tower_clear;
h = iw / 2;
o = h + wall;
z_s = tower_h - stacker_short;
// Underside of the lid's cap.
z_a = ih + c;
z_top = z_a + cap_t;
// Bottom of the lid's walls.
z_l = seat_gap;

assert(tb + c + li < wall && gd + li < wall, "tongue_t, groove_depth or lead_in too big for wall");

module box(x, y, z) {
  translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);
}

// Seam profiles: u runs into the groove from its wall's inner face, s across
// it, with the dovetail side negative. The tongue's dovetail side runs from
// its wall's corner at u = -c; the groove's is c from it.
function tongue_s(u, c) = -(u + c) * t_dv;
function groove_s(u, c) = tongue_s(u, c) - c / cos(dovetail);
function groove_pts(c) = [[-eps, groove_s(-eps, c)], [gd, groove_s(gd, c)], [gd, tb + c], [-eps, tb + c]];
// Buried in its wall behind u = -c.
function tongue_pts(c) = [[-c - 1, tongue_s(-c - 1, c)], [gd - c, tongue_s(gd - c, c)], [gd - c, tb], [-c - 1, tb]];

// Seam 0 is front-right: the groove in the stacker's right wall, the tongue on
// the lid's front wall. Seam 1 is back-left: the groove in the lid's left
// wall, the tongue on the stacker's back wall.
module at_seam(i) {
  rotate(180 * i) translate([h, h, 0]) children();
}

// From z0 to z1, flared to a lead-in at its mouth: the top, or the bottom.
module groove(z0, z1, mouth_up, c = c) {
  m = mouth_up ? z1 : z0;
  d = mouth_up ? 1 : -1;
  translate([0, 0, z0]) linear_extrude(z1 - z0) polygon(groove_pts(c));
  hull() {
    translate([0, 0, m - d * li]) linear_extrude(eps, center = true) polygon(groove_pts(c));
    translate([0, 0, m + d / 2]) linear_extrude(1, center = true) offset(delta = li) polygon(groove_pts(c));
  }
}

// From z0 to z1, narrowed to a lead-in at its leading end: the top, or the
// bottom.
module tongue(z0, z1, lead_up, c = c) {
  hull() {
    translate([0, 0, lead_up ? z0 : z0 + li]) linear_extrude(z1 - z0 - li) polygon(tongue_pts(c));
    translate([0, 0, lead_up ? z1 - eps : z0]) linear_extrude(eps) offset(delta = -li / 2) polygon(tongue_pts(c));
  }
}

// The closed box's outside, chamfered on every edge.
module envelope() {
  hull() {
    box([-o + chamfer, o - chamfer], [-o + chamfer, o - chamfer], [-cap_t, z_top]);
    box([-o, o], [-o + chamfer, o - chamfer],
        [-cap_t + chamfer, z_top - chamfer]);
    box([-o + chamfer, o - chamfer], [-o, o],
        [-cap_t + chamfer, z_top - chamfer]);
  }
}

// Cuts a 45° chamfer of size r into the edges along a -> b, with pyramid ends
// so that cuts meeting at a corner join cleanly.
module edge_cut(a, b, r) {
  hull() for (p = [a, b]) translate(p)
    polyhedron([[r, 0, 0], [-r, 0, 0], [0, r, 0], [0, -r, 0], [0, 0, r],
                [0, 0, -r]],
               [[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4], [2, 0, 5], [1, 2, 5],
                [3, 1, 5], [0, 3, 5]]);
}

// Along every outside seam.
module reveals() {
  f = h - c / 2;
  for (e = [// Front: up the right wall's end, over it, and under the front wall.
            [[f, o, 0], [f, o, z_s]], [[f, o, z_s], [o, o, z_s]], [[-o, o, 0], [f, o, 0]],
            // Right: under the lip.
            [[o, -o, z_s], [o, o, z_s]],
            // Back: up the left wall's end, under the lip, and under the left wall.
            [[-f, -o, 0], [-f, -o, z_s]], [[-f, -o, z_s], [o, -o, z_s]], [[-o, -o, 0], [-f, -o, 0]],
            // Left: under the left wall.
            [[-o, -o, 0], [-o, o, 0]]])
    edge_cut(e[0], e[1], reveal);
}

module stacker() {
  intersection() {
    envelope();
    difference() {
      union() {
        box([-o, o], [-o, o], [-cap_t, 0]);
        box([-h + c, o], [-o, -h], [-cap_t, z_s]);
        box([h, o], [-o, o], [-cap_t, z_s]);
        at_seam(1) tongue(-eps, z_s, true);
      }
      at_seam(0) groove(0, z_s, true);
      reveals();
      // Inner top edges of the right and back walls.
      edge_cut([h, -h, z_s], [h, h, z_s], chamfer);
      edge_cut([-h - gd, -h, z_s], [h, -h, z_s], chamfer);
    }
  }
}

module lid() {
  intersection() {
    envelope();
    difference() {
      union() {
        box([-o, o], [-o, o], [z_a, z_top]);
        // Lip over the stacker's back and right walls.
        box([-o, o], [-o, -h], [z_s, z_top]);
        box([h - c, o], [h, o], [z_s, z_top]);
        // Front and left walls.
        box([-o, h - c], [h, o], [z_l, z_top]);
        box([-o, -h], [-o, o], [z_l, z_top]);
        at_seam(0) tongue(z_l, z_top, false);
      }
      at_seam(1) groove(z_l, z_s + c, false);
      for (sy = [-1, 1]) lip_key(sy, z_s - eps);
      reveals();
      // Inner bottom edges of the front wall and its tongue, and of the left
      // wall.
      edge_cut([-h, h, z_l], [h + gd - c, h, z_l], chamfer);
      edge_cut([-h, -h, z_l], [-h, h, z_l], chamfer);
    }
  }
}

// A pointed end of the lip strip, at the back (sy = -1) or the front (1), from
// z0 up to the cap: a 45° point, so it prints in the strip and its notch in
// the lid.
module lip_key(sy, z0) {
  xm = (h - c + o) / 2;
  translate([xm, sy * h, z0]) linear_extrude(z_a - z0)
    polygon([[-lip_key - eps, -sy * eps], [0, sy * lip_key], [lip_key + eps, -sy * eps]]);
}

// The lip over the stacker's right wall. Ribs along each end's flanks crush
// into the notches and center it; they stop short of the top, to start it.
module lip_strip() {
  r = 0.4;
  // A flank's gap to its notch, square to it.
  gap = lip_c / sqrt(2);
  intersection() {
    envelope();
    difference() {
      union() {
        box([h - c, o], [-h + lip_c, h - lip_c], [z_s, z_a]);
        for (sy = [-1, 1]) translate([0, -sy * lip_c, 0]) {
          lip_key(sy, z_s);
          for (sx = [-1, 1])
            translate([(h - c + o) / 2 + sx * lip_key / 2, sy * (h + lip_key / 2), z_s])
              translate([sx, sy] * (gap + lip_crush - r) / sqrt(2)) cylinder(r = r, h = z_a - z_s - 1.5, $fn = 16);
        }
      }
      reveals();
    }
  }
}

module tower() {
  box([-tower_w / 2, tower_w / 2], [-tower_w / 2, tower_w / 2], [0, tower_h]);
}

/* Tests */

// A row of d = 2 notches, i + 1 of them, to tell the coupons apart.
module notches(i, len) {
  for (n = [0 : i]) translate([0, 0, 5 + 3.5 * n]) rotate([-90, 0, 0]) cylinder(d = 2, h = len, center = true);
}

// Coupon i's length of grooved wall, outside face on the bed, and beside it
// its length of tongued wall, standing.
module joint_test() {
  back = 12;
  for (i = [0 : len(joint_clears) - 1]) translate([0, i * (back + wall + 5), 0]) {
    jc = joint_clears[i];
    translate([0, 0, wall]) rotate([0, 90, 0]) difference() {
      box([0, wall], [-back, wall], [0, joint_len]);
      groove(-1, joint_len, true, jc);
      translate([wall, -back, 0]) notches(i, 2 * wall);
    }
    translate([-5, 0, back]) rotate([0, -90, 0]) translate([jc, 0, 0]) difference() {
      union() {
        box([-jc - back, -jc], [0, wall], [0, joint_len]);
        tongue(0, joint_len, false, jc);
      }
      translate([-jc - back, 0, 0]) notches(i, 3 * wall);
    }
  }
}

if (part == "stacker") {
  color("white") rotate([0, 0, 45]) translate([0, 0, o]) rotate([0, 90, 0]) stacker();
} else if (part == "lid") {
  color("white") rotate([0, 0, 45]) translate([0, 0, o]) rotate([0, -90, 0]) lid();
  // Along the lid, clear of its brim.
  color("white") rotate([0, 0, 45]) translate([-z_a / 2, 55 - z_s, o]) rotate([0, 0, 90]) rotate([0, 90, 0]) lip_strip();
} else if (part == "joint") {
  color("white") joint_test();
} else if (part == "stack") {
  // Cap up, resting on the tower.
  color("white") translate([0, 0, tower_h]) rotate([0, 180, 0]) stacker();
  color("burlywood", 0.4) tower();
} else {
  color("white") stacker();
  translate([0, 0, lid_raise]) {
    color("lightgray") lid();
    color("gainsboro") lip_strip();
  }
  color("burlywood", 0.4) tower();
}
