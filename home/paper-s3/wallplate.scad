// Wall plate that holds an M5Stack PaperS3 over a USB outlet.
//
// x is right, y is up, z is out from the wall (wall at z = 0). Gang 0 is the
// leftmost gang, centered at the origin.

// export: print

/* [Output] */
// "print" is the plate and cap side by side on the bed.
part = "assembly"; // [assembly, print, plate, cap]

/* [Layout] */
// Frame shifts away from neighboring gangs as needed.
// Gangs, left to right: P = PaperS3 (first or last), R = rocker, T = toggle, B = blank
gangs = "PR";

// Height of the outlet face above the wall.
outlet_face_z = 5;

/* [Wall devices] */
gang_pitch = 46.04;
// Plate edge to the center of the outermost gang.
end_margin = 34.93;
std_plate_h = 114.3;
rocker_opening = [33.6, 67.0];
rocker_screw_spacing = 83.34;
toggle_opening = [10.3, 23.8];
toggle_screw_spacing = 60.33;
screw_d = 3.6;
screw_head_d = 7.2;

/* [Plate] */
plate_t = 3;
// Plate left between the frame and a neighboring opening.
min_web = 3;
edge_chamfer = 0.8;

/* [Frame] */
wall = 1.6;
lip_t = 1.0;
// How far the lips cover the PaperS3 bezel.
lip_overlap = 2;
// Width of the ledges the PaperS3 back rests on.
pad_w = 2;
// Space between the outlet face and the PaperS3 back: the outlet plug height.
cable_gap = 2;
// Material under the plug pocket.
floor_t = 1.2;

/* [USB plug at the PaperS3] */
// Width along the PaperS3 edge.
plug_w = 12.8;
// How far it sticks out below the PaperS3.
plug_h = 2;
plug_clear = 0.2;

/* [Fit] */
clear_side = 0.2;
clear_end = 0.2;
clear_depth = 0.3;
cap_clear = 0.2;
btn_groove = 1.0;

/* [PaperS3, USB edge down, viewed from the front] */
dev_size = [67, 121.5, 7.7];
dev_r = 3;
usb_x = -22;
// The power button is on the right edge. z ranges are measured from the back.
btn_from_bottom = 21.2;
btn_len = 10.8;
btn_z = [1.3, 6.1];
btn_proud = 0.7;

/* [Hidden] */
$fn = 48;

eps = 0.01;
dw = dev_size.x;
dh = dev_size.y;
dt = dev_size.z;

// Frame-local layout, with the PaperS3 centered at the origin.
z_back = outlet_face_z + cable_gap;
z_dev_front = z_back + dt;
z_chan = z_dev_front + clear_depth;
z_top = z_chan + lip_t;
chan_x = dw / 2 + clear_side;
lip_x = dw / 2 - lip_overlap;
tub_hw = chan_x + wall;
tub_r = dev_r + clear_side + wall;
dev_top = dh / 2;
dev_bot = -dh / 2;
floor_y = dev_bot - clear_end;
pocket_y = floor_y - plug_h - plug_clear;
tub_y0 = pocket_y - floor_t;
// The top rim matches the bottom rim.
tub_y1 = dev_top + (floor_y - tub_y0);
tub_h = tub_y1 - tub_y0;
tub_cy = (tub_y0 + tub_y1) / 2;
btn_y = dev_bot + btn_from_bottom;

n = len(gangs);
paper_idx = [for (i = [0 : n - 1]) if (gangs[i] == "P") i];
assert(len(paper_idx) == 1, "gangs needs exactly one P");
pi = paper_idx[0];
assert(pi == 0 || pi == n - 1, "P must be the first or last gang");

function gang_x(i) = i * gang_pitch;
function opening(t) =
  t == "R" ? rocker_opening : t == "T" ? toggle_opening : [0, 0];
function screw_spacing(t) =
  t == "R" ? rocker_screw_spacing
  : t == "T" ? toggle_screw_spacing : 0;

// Direction the frame shifts when it would cover the neighboring opening.
side = pi == 0 ? -1 : 1;
neighbor = n > 1 ? gangs[pi - side] : "B";
reach = opening(neighbor).x > 0
  ? gang_pitch - opening(neighbor).x / 2 - min_web : 1e9;
tub_cx = gang_x(pi) + side * max(0, tub_hw - reach);

plate_x0 = min(gang_x(0) - end_margin, tub_cx - tub_hw);
plate_x1 = max(gang_x(n - 1) + end_margin, tub_cx + tub_hw);
plate_h = max(std_plate_h, tub_h);

module rrect(size, r) {
  offset(r = r) square([size.x - 2 * r, size.y - 2 * r], center = true);
}

// Rounded-corner slab with a chamfered top edge.
module slab(size, h, r = tub_r, ch = edge_chamfer) {
  hull() {
    linear_extrude(h - ch) rrect(size, r);
    linear_extrude(h) rrect([size.x - 2 * ch, size.y - 2 * ch], max(r - ch, eps));
  }
}

module box(x, y, z) {
  translate([x[0], y[0], z[0]]) cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]);
}

// Countersunk hole for a #6-32 oval head screw, head flush at z = top.
module csk_hole(top) {
  cone_h = (screw_head_d - screw_d) / 2 / tan(41);
  translate([0, 0, -1]) cylinder(d = screw_d, h = top + 2);
  translate([0, 0, top - cone_h])
    cylinder(d1 = screw_d, d2 = screw_head_d, h = cone_h + eps);
}

module gang_cuts(t) {
  o = opening(t);
  if (o.x > 0) {
    translate([0, 0, -1]) linear_extrude(plate_t + 2) rrect(o, 1);
    for (s = [-1, 1])
      translate([0, s * screw_spacing(t) / 2, 0]) csk_hole(plate_t);
  }
}

module on_frame() {
  translate([tub_cx, -tub_cy, 0]) children();
}

module tub_body() {
  translate([0, tub_cy, 0]) slab([2 * tub_hw, tub_h], z_top);
}

module tub_cuts() {
  // The PaperS3 and cap slide down this channel from the top.
  box([-chan_x, chan_x], [floor_y, tub_y1 + 1], [z_back, z_chan]);
  // Window between the lips.
  win_y0 = dev_bot + lip_overlap;
  translate([0, (win_y0 + tub_y1 + 2) / 2, z_chan - eps])
    linear_extrude(lip_t + 1) rrect([2 * lip_x, tub_y1 + 2 - win_y0], 1);
  // Cable space behind the PaperS3.
  box([-chan_x + pad_w, chan_x - pad_w], [floor_y + pad_w, dev_top - pad_w],
      [plate_t, z_back + eps]);
  // Plug pocket, with a slot through the bottom ledge into the cable space.
  box([usb_x - plug_w / 2 - plug_clear, usb_x + plug_w / 2 + plug_clear],
      [pocket_y, floor_y + pad_w + eps], [plate_t, z_chan]);
  // Groove the button slides down.
  box([chan_x - eps, chan_x + btn_groove], [btn_y - btn_len / 2 - 1, tub_y1 + 1],
      [z_back + btn_z[0] - 0.5, z_back + btn_z[1] + 0.5]);
}

module plate() {
  difference() {
    union() {
      translate([(plate_x0 + plate_x1) / 2, 0, 0])
        slab([plate_x1 - plate_x0, plate_h], plate_t);
      on_frame() tub_body();
    }
    for (i = [0 : n - 1])
      if (gangs[i] != "P") translate([gang_x(i), 0, 0]) gang_cuts(gangs[i]);
    // The outlet under the PaperS3 is a rocker-style device.
    translate([gang_x(pi), 0, 0]) gang_cuts("R");
    on_frame() tub_cuts();
  }
}

// Frame-local, in its installed position, resting on the PaperS3 top edge.
module cap() {
  cx = lip_x - cap_clear;
  intersection() {
    union() {
      // Rails under the lips.
      box([-chan_x + cap_clear, chan_x - cap_clear], [dev_top, tub_y1],
          [z_back + cap_clear, z_chan - cap_clear]);
      // Front face between the lips, overlapping the top bezel.
      box([-cx, cx], [dev_top, tub_y1], [z_back + cap_clear, z_top]);
      box([-cx, cx], [dev_top - lip_overlap, dev_top], [z_dev_front + cap_clear, z_top]);
    }
    tub_body();
  }
}

// Frame-local, in its installed position.
module papers3() {
  translate([0, 0, z_back]) {
    linear_extrude(dt) rrect([dw, dh], dev_r);
    box([dw / 2 - 1, dw / 2 + btn_proud], [btn_y - btn_len / 2, btn_y + btn_len / 2], btn_z);
  }
}

// Frame-local. Plug end of the ribbon, centered in the PaperS3 thickness.
module plug() {
  box([usb_x - plug_w / 2, usb_x + plug_w / 2], [dev_bot - plug_h, dev_bot],
      [z_back + dt / 2 - 3.5, z_back + dt / 2 + 3.5]);
}

// Front face down, centered on the origin.
module print_cap() {
  translate([0, 0, z_top]) rotate([180, 0, 0])
    translate([0, -(dev_top + tub_y1) / 2, 0]) cap();
}

if (part == "print") {
  color("white") plate();
  color("lightgray") translate([(plate_x0 + plate_x1) / 2, -plate_h / 2 - 10, 0])
    print_cap();
} else if (part == "plate") {
  plate();
} else if (part == "cap") {
  print_cap();
} else {
  color("white") plate();
  on_frame() {
    color("lightgray") cap();
    color("dimgray") papers3();
    color("orange") plug();
  }
  // Outlet face, for reference.
  color("ivory", 0.5) translate([gang_x(pi), 0, 0])
    linear_extrude(outlet_face_z) rrect(rocker_opening - [0.6, 0.6], 1);
}
