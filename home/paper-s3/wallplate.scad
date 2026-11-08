// Wall plate that holds an M5Stack PaperS3 over a USB outlet.
//
// x is right, y is up, z is out from the wall (wall at z = 0). Gang 0 is the
// leftmost gang, centered at the origin.

// export: print

/* [Output] */
// "print" is the plate and cap side by side on the bed.
part = "assembly"; // [assembly, print, plate, cap]

/* [Layout] */
// USB port x relative to the outlet center. The frame moves to match.
usb_offset = 0;
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
// Material above the plug pocket.
floor_t = 1.2;

/* [Cap] */
// The PaperS3 slides up into the plug, then the cap goes on under it. Two M3
// socket head screws through counterbores in the cap face thread into heat-set
// inserts in the frame behind it.
// Cap height below the PaperS3. The top rim matches it.
cap_h = 9;
// Screw x from the frame center.
cap_screw_x = 25;
insert_d = 4.0;
insert_l = 5.7;
m3_clear_d = 3.4;
// Counterbore for the screw head.
m3_head_d = 6.0;
m3_head_h = 3.2;

/* [USB plug at the PaperS3] */
// Width along the PaperS3 edge.
plug_w = 12.8;
// How far it sticks out above the PaperS3.
plug_h = 2;
plug_clear = 0.2;

/* [Fit] */
clear_side = 0.2;
clear_end = 0.2;
clear_depth = 0.3;
cap_clear = 0.2;
btn_groove = 1.0;

/* [PaperS3, USB edge up, viewed from the front] */
dev_size = [67, 121.5, 7.7];
dev_r = 3;
// USB port x from the PaperS3 center.
usb_x = 22;
// The power button is on the left edge. z ranges are measured from the back.
btn_from_top = 21.2;
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
// The plug pocket is above the PaperS3, in the frame.
pocket_y1 = dev_top + clear_end + plug_h + plug_clear;
tub_y1 = max(pocket_y1 + floor_t, dev_top + cap_h);
tub_y0 = dev_bot - cap_h;
cap_cy = dev_bot - cap_h / 2;
tub_h = tub_y1 - tub_y0;
tub_cy = (tub_y0 + tub_y1) / 2;
btn_y = dev_top - btn_from_top;

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

tub_cx = gang_x(pi) + usb_offset - usb_x;
// Frame-local x of the frame edges. Each edge extends to cover the outlet
// opening under the PaperS3 if needed.
outlet_x = gang_x(pi) - tub_cx;
outlet_reach = rocker_opening.x / 2 + min_web;
tub_x0 = min(-tub_hw, outlet_x - outlet_reach);
tub_x1 = max(tub_hw, outlet_x + outlet_reach);

// Warn if the frame covers the neighboring opening.
side = pi == 0 ? 1 : -1;
neighbor = n > 1 ? gangs[pi + side] : "B";
frame_reach = side * (tub_cx - gang_x(pi)) + (side > 0 ? tub_x1 : -tub_x0);
max_reach = opening(neighbor).x > 0
  ? gang_pitch - opening(neighbor).x / 2 - min_web : 1e9;
if (frame_reach > max_reach)
  echo(str("WARNING: frame covers the neighboring opening by ",
           frame_reach - max_reach, " mm"));

plate_x0 = min(gang_x(0) - end_margin, tub_cx + tub_x0);
plate_x1 = max(gang_x(n - 1) + end_margin, tub_cx + tub_x1);
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
module csk_hole(top, d = screw_d, head_d = screw_head_d) {
  cone_h = (head_d - d) / 2 / tan(41);
  translate([0, 0, -1]) cylinder(d = d, h = top + 2);
  translate([0, 0, top - cone_h])
    cylinder(d1 = d, d2 = head_d, h = cone_h + eps);
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
  translate([(tub_x0 + tub_x1) / 2, tub_cy, 0]) slab([tub_x1 - tub_x0, tub_h], z_top);
}

// Frame-local. The full-width cap: everything below the PaperS3 and in front
// of the shelf at z_back.
module cap_zone(dy = 0) {
  box([tub_x0 - 1, tub_x1 + 1], [tub_y0 - 1, dev_bot + dy], [z_back, z_top + 1]);
}

module tub_cuts() {
  // Space for the cap.
  cap_zone(cap_clear);
  // The PaperS3 slides up this channel from the bottom.
  box([-chan_x, chan_x], [tub_y0 - 1, dev_top + clear_end], [z_back, z_chan]);
  // Window between the lips, open at the bottom for the cap face.
  win_y1 = dev_top - lip_overlap;
  translate([0, (tub_y0 - 2 + win_y1) / 2, z_chan - eps])
    linear_extrude(lip_t + 1) rrect([2 * lip_x, win_y1 - tub_y0 + 2], 1);
  // Cable space behind the PaperS3.
  box([-chan_x + pad_w, chan_x - pad_w], [dev_bot + pad_w, dev_top - pad_w],
      [plate_t, z_back + eps]);
  // Slot through the top ledge from the plug pocket into the cable space.
  box([usb_x - plug_w / 2 - plug_clear, usb_x + plug_w / 2 + plug_clear],
      [dev_top - pad_w - eps, pocket_y1], [plate_t, z_chan]);
  // Groove the button slides up.
  box([-chan_x - btn_groove, -chan_x + eps], [tub_y0 - 1, btn_y + btn_len / 2 + 1],
      [z_back + btn_z[0] - 0.5, z_back + btn_z[1] + 0.5]);
  // Heat-set inserts behind the cap.
  for (s = [-1, 1])
    translate([s * cap_screw_x, cap_cy, z_back - insert_l - 0.5])
      cylinder(d = insert_d, h = insert_l + 1);
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
    // Clearance over the outlet face, under the frame walls and ledges.
    translate([gang_x(pi), 0, -1])
      linear_extrude(outlet_face_z + clear_depth + 1) rrect(rocker_opening, 1);
    on_frame() tub_cuts();
  }
}

// Frame-local, in its installed position, holding up the PaperS3 bottom edge.
// It covers the ends of the side walls and sits on the shelf at z_back.
module cap() {
  cx = lip_x - cap_clear;
  difference() {
    union() {
      intersection() {
        tub_body();
        cap_zone();
      }
      // Overlaps the bottom bezel, between the lips.
      box([-cx, cx], [dev_bot - eps, dev_bot + lip_overlap], [z_dev_front + cap_clear, z_top]);
    }
    for (s = [-1, 1])
      translate([s * cap_screw_x, cap_cy, 0]) {
        translate([0, 0, z_back - 1]) cylinder(d = m3_clear_d, h = z_top - z_back + 2);
        translate([0, 0, z_top - m3_head_h]) cylinder(d = m3_head_d, h = m3_head_h + 1);
      }
  }
}

// Frame-local. M3 x 10 socket head screws, for reference.
module cap_screws() {
  for (s = [-1, 1])
    translate([s * cap_screw_x, cap_cy, z_top - m3_head_h]) {
      translate([0, 0, -10]) cylinder(d = 3, h = 10);
      cylinder(d = 5.5, h = 3);
    }
}

// Frame-local, in its installed position.
module papers3() {
  translate([0, 0, z_back]) {
    linear_extrude(dt) rrect([dw, dh], dev_r);
    box([-dw / 2 - btn_proud, -dw / 2 + 1], [btn_y - btn_len / 2, btn_y + btn_len / 2], btn_z);
  }
}

// Frame-local. Plug end of the ribbon, centered in the PaperS3 thickness.
module plug() {
  box([usb_x - plug_w / 2, usb_x + plug_w / 2], [dev_top, dev_top + plug_h],
      [z_back + dt / 2 - 3.5, z_back + dt / 2 + 3.5]);
}

// Front face down, centered on the origin.
module print_cap() {
  translate([0, 0, z_top]) rotate([180, 0, 0])
    translate([0, -cap_cy, 0]) cap();
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
    color("silver") cap_screws();
  }
  // Outlet face, for reference.
  color("ivory", 0.5) translate([gang_x(pi), 0, 0])
    linear_extrude(outlet_face_z) rrect(rocker_opening - [0.6, 0.6], 1);
}
