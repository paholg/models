// Jenga box in two three-sided halves. The stacker is the back and right walls
// plus an end cap, a little shorter than the tower. Cap up, it squares the
// tower in its back-right corner and slides off. Cap down, it holds the blocks,
// and the lid (front and left walls plus the other end cap) slides down onto
// it. A lip on the lid's back and right edges covers the rest of the tower.
//
// A store-bought draw latch holds them together.
//
// Storage orientation: x is right, y is toward the front, z is up. The tower
// stands on the stacker's cap at z = 0.
//
// Print the stacker on its right side and the lid face down. The stacker and lid are output at 45° to fit
// the bed diagonally.

// export: stacker lid

/* [Output] */
part = "assembly"; // [assembly, stack, stacker, lid]
// Lid height above closed, in the assembly view.
lid_raise = 0;

/* [Tower] */
// Measure your own tower; sets vary.
tower_w = 75;
tower_h = 270;
// Per side.
tower_clear = 0.5;
// How much shorter the stacker's walls are than the tower.
stacker_short = 5;

/* [Walls] */
wall = 3.6;
cap_t = 2;
// The lid's wall edges ride in dovetail grooves in the stacker's walls.
tongue_t = 1.6;
groove_depth = 1.6;
// Undercut angle on the groove's inner side.
dovetail = 20;

/* [Edges] */
// Outer edges, and the inner edges at each half's open end.
chamfer = 1;
// V-groove along the outside seams between the halves.
reveal = 0.5;

/* [Fit] */
slide_clear = 0.2;
// Chamfer on the tongue tips and groove mouths.
lead_in = 0.6;

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

assert(tb + c + li < wall && gd + li < wall,
       "tongue_t, groove_depth or lead_in too big for wall");

module box(x, y, z) {
  translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);
}

// Seam profiles: u runs into the groove from the stacker wall's inner face, s
// across it, with the dovetail side negative.
// The tongue's dovetail side runs from the lid wall's corner at u = -c; the
// groove's is c from it.
function tongue_s(u) = -(u + c) * t_dv;
function groove_s(u) = tongue_s(u) - c / cos(dovetail);
groove_pts = [[-eps, groove_s(-eps)], [gd, groove_s(gd)], [gd, tb + c],
              [-eps, tb + c]];
// Buried in the lid wall behind u = -c.
tongue_pts = [[-c - 1, tongue_s(-c - 1)], [gd - c, tongue_s(gd - c)],
              [gd - c, tb], [-c - 1, tb]];

// Places seam coordinates at the front-right seam and its mirror at back-left.
module at_seams() {
  for (m = [0, 1]) mirror([m, m, 0]) translate([h, h, 0])
    children();
}

// Flared to a lead-in at the wall top.
module groove() {
  linear_extrude(z_s + 1) polygon(groove_pts);
  hull() {
    translate([0, 0, z_s - li]) linear_extrude(eps) polygon(groove_pts);
    translate([0, 0, z_s]) linear_extrude(1) offset(delta = li)
      polygon(groove_pts);
  }
}

// Narrowed to a lead-in at the bottom.
module tongue() {
  hull() {
    translate([0, 0, li]) linear_extrude(z_top - li) polygon(tongue_pts);
    linear_extrude(eps) offset(delta = -li / 2) polygon(tongue_pts);
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

// On the front and right faces, and mirrored to the left and back.
module reveals() {
  for (m = [0, 1]) mirror([m, m, 0]) {
    edge_cut([h - c / 2, o, 0], [h - c / 2, o, z_s], reveal);
    edge_cut([h - c / 2, o, z_s], [o, o, z_s], reveal);
    edge_cut([-o, o, 0], [h - c / 2, o, 0], reveal);
    edge_cut([o, -o, z_s], [o, o, z_s], reveal);
  }
}

module stacker() {
  intersection() {
    envelope();
    difference() {
      union() {
        box([-o, o], [-o, o], [-cap_t, 0]);
        box([-o, o], [-o, -h], [-cap_t, z_s]);
        box([h, o], [-o, o], [-cap_t, z_s]);
      }
      // Grooves for the lid's front and left wall edges.
      at_seams() groove();
      reveals();
      // Inner top edges of the right wall, and mirrored, the back wall.
      for (m = [0, 1]) mirror([m, m, 0])
        edge_cut([h, -h, z_s], [h, h, z_s], chamfer);
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
        box([-o, o], [-o, -h + c], [z_s, z_top]);
        box([h - c, o], [-o, o], [z_s, z_top]);
        // Front and left walls.
        box([-o, h - c], [h, o], [0, z_top]);
        box([-o, -h], [-h + c, o], [0, z_top]);
        at_seams() tongue();
      }
      reveals();
      // Inner bottom edges of the front wall and its tongue, and mirrored, the
      // left wall.
      for (m = [0, 1]) mirror([m, m, 0])
        edge_cut([-h, h, 0], [h + gd - c, h, 0], chamfer);
    }
  }
}

module tower() {
  box([-tower_w / 2, tower_w / 2], [-tower_w / 2, tower_w / 2], [0, tower_h]);
}

if (part == "stacker") {
  rotate([0, 0, 45]) translate([0, 0, o]) rotate([0, 90, 0]) stacker();
} else if (part == "lid") {
  rotate([0, 0, 45]) translate([0, 0, o]) rotate([-90, 0, 0]) lid();
} else if (part == "stack") {
  // Cap up, resting on the tower.
  color("white") translate([0, 0, tower_h]) rotate([0, 180, 0]) stacker();
  color("burlywood", 0.4) tower();
} else {
  color("white") stacker();
  translate([0, 0, lid_raise]) color("lightgray") lid();
  color("burlywood", 0.4) tower();
}
