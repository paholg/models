// A Feast for Odin + The Norwegians: whole-box layout.
//
// x is the box length (305), y its width (216), z up.
//
// Layer 1: two identical half trays of the small, often-used tiles and
// money, one per end of the table, side by side.
// Layer 2, as tall as a deck holder on its side, every column flush on top:
//   front strip: the deck holders; then the boat market, the VP stacks in
//   front of it, and the 2x5 money and penalty bins beside them.
//   back: two tiers, the big tiles and animals below, the islands and wooden
//   goods above.
// Layer 3, cardboard: in-game buildings, setup buildings (with the dice, moose
// and cube), mountain strips, vikings.
// Top: the big boards, and the special tiles' boards on them.
//
// Tile bins are shallow, each with a curved scoop up the front wall to slide
// tiles out on; each reports how many tiles it holds stacked neatly.
// Cardboard stacks sit in wells with finger notches to lift them out whole.

// export: half_a half_b big_a big_b boats vp money vikings islands wood buildings setup_buildings strips deck_setup deck_occupations deck_weapons special_forge special_others

include <special_layout.scad>

part = "assembly"; // [assembly, half, half_a, half_b, big, big_a, big_b, market, boats, money, vp, vikings, islands, wood, buildings, setup_buildings, strips, boards, special, special_forge, special_others, decks, deck_setup, deck_occupations, deck_weapons]
// Vertical gap between layers in the assembly view.
explode = 30;
// Assembly: show layers up to this one, bottom up (0 = all). 1: half trays;
// 2: decks, market, big trays; 3: islands, wood; 4: cardboard trays;
// 5: boards; 6: special boards.
layer = 0; // [0:6]
// Show only that layer, not the ones under it.
layer_only = false;

/* [Box] */
box = [305, 216, 117.5];
// Cardboard: see board_stack().
card_t = 2.25;
// Player boards, action board, round overview.
board_layers = 8;
board_stack_h = board_layers * card_t + 0.75;

/* [Trays] */
unit = 11;
tile_t = 2.25;
wall = 1.2;
// Corner posts of the open cardboard trays.
post_t = 2;
floor_t = 1.2;
// The cardboard trays.
tray_h = 17.2;
// The half trays.
half_h = 23.2;
scoop_min = 8;
scoop_max = 15;
// Wedge at the back of the bins of 2-wide tiles, to lean them on.
wedge_h = 10;
wedge_angle = 65;
// Warn when a bin holds fewer than this many times its tiles, stacked neatly.
min_cap = 1.3;

/* [Chamfers] */
// Well and pocket rims.
chamfer = 0.4;
// Outside top and bottom edges.
chamfer_out = 0.6;
// Outside vertical corners.
chamfer_corner = 1;
fillet_r = 1; // inside corners and floor edges of wells

/* [Decks] */
card = [46, 72];
card_clear = 1.5;
// Setup occupations, in-game occupations (72 mm, split in two), weapons.
deck_hs = [23, 36, 36, 24];
deck_wall = 1.6;
// Finger slot through each long wall.
slot_w = 22;
// How far above the floor the slots stop.
slot_bottom = 4;

/* [Special tiles] */
// Pocket depth; tiles are 2.25 thick.
pocket_d = 2.6;
pocket_clear = 0.4;
// Under one end of each tile the pocket floor drops by tilt_d, for tilt_a in
// from the tile's edge: press there and the far end tips up to grab.
tilt_d = 2.5;
tilt_a = 8;
// The step down is an S: rounded over at the top, where the tile pivots, and
// filleted at the bottom.
tilt_r = 1.25;
special_margin = 3;

/* [Hidden] */
// Colors: a piece is c_game, or c_setup if it's only used in setup ($setup);
// icons and labels are black. Viking bins keep their player colors.
// Printing: the part is exported once per color in print_colors, with $only
// set, and each piece of geometry shows only in its own pass. Unset (the
// preview), everything shows.
c_game = "lightsteelblue";
c_setup = "tan";
vik_colors = ["red", "blue", "yellow", "white"];
$only = undef;
$setup = false;
function role_color(c) =
    c == "black" ? c
    : len([for (v = vik_colors) if (v == c) 1]) > 0 ? c
    : $setup ? c_setup : c_game;
module paint(c) let (rc = role_color(c)) if (is_undef($only) || $only == rc) color(rc) children();
module body() paint("body") children();
eps = 0.01;
$fn = 64;
gap = 0.5;
// Two to the layer, one behind the other.
half = [box.x - 1, (box.y - 1 - gap) / 2];
// Layer 2: deck holders on their sides set its height and the front strip.
up_h = deck_size(0).x;
front_y = deck_size(0).y;
tier_h = up_h / 2;
decks_x = sum([for (h = deck_hs) deck_size(h).z + gap]) - gap;
// Behind the front strip.
back_y = box.y - 1 - front_y - gap;
// The big tiles' tray: a half tray's footprint.
big = [box.x - 1, half.y];
islands = [129 + 1.5 + 2 * post_t, back_y];
wood = [box.x - 1 - islands.x - gap, back_y];

c_food = "orange";
c_equip = "seagreen";
c_animal = "tan";
c_money = "silver";
c_wood = "saddlebrown";

function t(x, y) = [x * unit, y * unit];

// Each row: [depth (-1 fills the tray), bins]. A bin: [label, width (-1
// shares what's left equally), tile footprint (scoop sizing, capacity), tile
// count (0 for none), color, optional icon]. With an icon, the bin shows it on
// its back wall instead of its label. A last true gives it a wedge().

// Icons: a tile's cells as [col, row], col across. "grid" draws them as an
// outlined grid, "coin" as linked octagons.
function cells(c, r) = [for (y = [0:r - 1]) for (x = [0:c - 1]) [x, y]];
function grid(c, r) = ["grid", cells(c, r)];
function coin(c, r) = ["coin", cells(c, r)];
u_icon = ["grid", [[0, 0], [1, 0], [2, 0], [0, 1], [2, 1]]];

// Columns run roughly smallest to biggest tile, the U last, the same in every row, so food and
// equipment line up as an upgrade path. Tiles lie long side along x.
half_cols = [28, 36, 32, 47, 37, 41, 37];
function shape_row(c, n) = [-1, [
    ["1x2", half_cols[0], t(2, 1), n[0], c, grid(2, 1)],
    ["1x3", half_cols[1], t(3, 1), n[1], c, grid(3, 1)],
    ["2x2", half_cols[2], t(2, 2), n[2], c, grid(2, 2), true],
    ["1x4", half_cols[3], t(4, 1), n[3], c, grid(4, 1)],
    ["2x3", half_cols[4], t(3, 2), n[4], c, grid(3, 2), true],
    ["3x3", half_cols[5], t(3, 3), n[5], c, grid(3, 3)],
    ["U", half_cols[6], t(3, 2), n[6], c, u_icon, true],
]];

// Small, often-used tiles: one copy per end of the table, half counts.
// Food in front, equipment behind.
half_rows = [
    shape_row(c_food, [18, 10, 10, 10, 9, 8, 12]),
    shape_row(c_equip, [24, 15, 15, 10, 10, 9, 11]),
];

// Money, in its own column at the end of each half tray, smallest in front.
money_rows = [
    [-1, [["M1x1", -1, t(1, 1), 40, c_money, coin(1, 1)]]],
    [-1, [["M1x2", -1, t(2, 1), 16, c_money, coin(2, 1)]]],
    [-1, [["M2x2", -1, t(2, 2), 9, c_money, coin(2, 2), true]]],
];

// Big tiles and animals: one shared copy, full counts. Animals in front,
// equipment behind. Each bin is two tiles wide and one deep behind its scoop,
// filled about as full as the half trays' bins.
big_cols = [89.5, 90, -1];
big_rows = [
    [-1, [
        ["A2x4", big_cols[0], t(4, 2), 18, c_animal],
        ["A3x4", big_cols[1], t(4, 3), 15, c_animal],
        ["A2x5", big_cols[2], t(5, 2), 21, c_animal],
    ]],
    [-1, [
        ["E2x4", big_cols[0], t(4, 2), 20, c_equip],
        ["E3x4", big_cols[1], t(4, 3), 15, c_equip],
        ["E2x5", big_cols[2], t(5, 2), 14, c_equip],
    ]],
];

// Boats: a market of stacks, like mini decks. Each well fits its tile
// lengthwise (long side front to back), with a pinch slot through the front
// and back walls. The slots leave a lip each side to hold the stack in.
// [label, tile footprint, count], left to right.
boats = [
    ["1x4", t(1, 4), 8],
    ["2x3", t(2, 3), 10],
    ["2x4", t(2, 4), 12],
    ["2x4", t(2, 4), 10],
];
boat_clear = 1;
boat_slot_w = 20;
boat_slot_lip = 2;
boat_slot_bottom = 2;
boat_well = [for (b = boats) b[1] + [boat_clear, boat_clear]];
boat_well_y = max([for (w = boat_well) w.y]);
// Just tall enough for the tallest stack.
boat_h = floor_t + max([for (b = boats) b[2]]) * tile_t;
// Each well's floor is raised so its full stack comes flush with the top.
function boat_floor(i) = max(floor_t, boat_h - boats[i][2] * tile_t);
function boat_x(i) = wall + sum([for (j = [0:1:i - 1]) boat_well[j].x + wall]);
boats_x = boat_x(len(boats));

boat = [boats_x, boat_well_y + 2 * wall];

// The boat market: its own piece, with the pinch slots open front and back.
module boat_tray() {
    body() difference() {
        cbox(boat, boat_h);
        for (i = [0:len(boats) - 1]) {
            w = boat_well[i];
            sw = min(boat_slot_w, w.x - 2 * boat_slot_lip);
            // Well, against the back.
            translate([boat_x(i), boat.y - wall - w.y, 0]) {
                well(w, boat_floor(i), boat_h);
                rim(w, boat_h);
            }
            // Pinch slot through the front and back walls, round-bottomed;
            // the skinny first well is too narrow for that, so its slot goes
            // through the outer side wall instead.
            wy = boat.y - wall - w.y;
            if (i == 0) translate([0, wy + w.y / 2, 0]) rotate(-90)
                u_slot(boat_slot_w, boat_floor(i) + boat_slot_bottom, boat_h + 1, 0, wall, [[0, 1], [wall, -1]]);
            else translate([boat_x(i) + w.x / 2, 0, 0])
                u_slot(sw, boat_floor(i) + boat_slot_bottom, boat_h + 1, 0, boat.y,
                       [[0, 1], [wy, -1], [wy + w.y, 1], [boat.y, -1]]);
        }
    }
    for (i = [0:len(boats) - 1]) paint("black")
        translate([boat_x(i) + boat_well[i].x / 2, boat.y - wall - 3, boat_floor(i)])
        rotate(90) linear_extrude(0.4) text(boats[i][0], size = 3.5, halign = "right", valign = "center");
}

// The column beside the decks, the layer's full height: the boat market at the
// back left, the VP stacks in front of it, the 2x5 money and penalty bins to
// the right.
market = [box.x - 1 - decks_x - gap, front_y];
// VP tokens, 25 mm square: 2x 4 VP, 6x 3 VP, 8x 2 VP, standing on edge in one
// row, biggest first at the front (x = 0), as you only ever need the next one.
// A well per value, walls as tall as the tokens; one pinch slot runs through
// the front face and every divider, to slide the front token up and out.
// Behind them, a round well holds the 7 penalty tokens (30 mm round) in a
// stack, with pinch slots through its other three sides.
vp_token = 25;
vp_counts = [2, 6, 8];
vp_slack = 1.5; // per value, so the tokens can lean
vp_clear = 1.5; // across
vp_wall_h = vp_token + 0.5;
vp_slot_w = 16;
vp_slot_bottom = 4;
pen_r = (30 + 1.5) / 2;
function vp_group(i) = vp_counts[i] * tile_t + vp_slack;
function vp_x(i) = wall + sum([for (j = [0:1:i - 1]) vp_group(j) + wall]);
vp_in_y = vp_token + vp_clear;
pen_c = [vp_x(len(vp_counts)) + pen_r, max(vp_in_y, 2 * pen_r) / 2 + wall];
vp = [pen_c.x + pen_r + wall, 2 * pen_c.y];
vp_h = floor_t + vp_wall_h;
module vp_tray() {
    n = len(vp_counts);
    y0 = (vp.y - vp_in_y) / 2;
    back = vp.x - pen_c.x;
    body() difference() {
        cbox(vp, vp_h);
        for (i = [0:n - 1]) translate([vp_x(i), y0, 0]) {
            w = [vp_group(i), vp_in_y];
            well(w, floor_t, vp_h);
            rim(w, vp_h);
        }
        translate([0, vp.y / 2, 0]) rotate(-90)
            u_slot(vp_slot_w, floor_t + vp_slot_bottom, vp_h + 1, 0, vp_x(n - 1),
                   [[0, 1], for (i = [0:n - 1]) each [[vp_x(i), -1], if (i < n - 1) [vp_x(i) + vp_group(i), 1]]]);
        // Penalty well and its slots: across through both sides, and out the
        // back. The flat outer faces get u_slot's chamfers; the round inner
        // one a bevel from an octahedron run round the opening.
        translate([pen_c.x, pen_c.y, 0]) round_well(pen_r, floor_t, vp_h);
        translate([pen_c.x, 0, 0])
            u_slot(vp_slot_w, floor_t + vp_slot_bottom, vp_h + 1, 0, vp.y, [[0, 1], [vp.y, -1]]);
        translate([pen_c.x, pen_c.y, 0]) rotate(-90)
            u_slot(vp_slot_w, floor_t + vp_slot_bottom, vp_h + 1, 0, back, [[back, -1]]);
        minkowski() {
            intersection() {
                translate([pen_c.x, pen_c.y, 0]) difference() {
                    cylinder(r = pen_r + 0.05, h = vp_h + 1, $fn = 96);
                    translate([0, 0, -1]) cylinder(r = pen_r, h = vp_h + 3, $fn = 96);
                }
                union() {
                    translate([pen_c.x, 0, 0]) u_slot(vp_slot_w, floor_t + vp_slot_bottom, vp_h + 1, 0, vp.y, []);
                    translate([pen_c.x, pen_c.y, 0]) rotate(-90)
                        u_slot(vp_slot_w, floor_t + vp_slot_bottom, vp_h + 1, 0, back, []);
                }
            }
            octahedron(chamfer_out);
        }
    }
}
// A round well, floor at z0, open past h: floor edge filleted, rim chamfered.
module round_well(r, z0, h, f = fillet_r, c = chamfer) rotate_extrude($fn = 96) polygon(concat(
    [[0, z0]],
    [for (a = [-90:15:0]) [r - f + f * cos(a), z0 + f + f * sin(a)]],
    [[r, h - c], [r + c, h], [r + c, h + 1], [0, h + 1]]
));
module octahedron(c) polyhedron(
    [[c, 0, 0], [-c, 0, 0], [0, c, 0], [0, -c, 0], [0, 0, c], [0, 0, -c]],
    [[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4], [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5]]);
// The 2x5 money, and the 7 penalty tokens (30 mm round) thrown in. Half the
// layer's height is plenty.
money_h = tier_h;
money_box = [market.x - boat.x - gap, market.y];
money_box_rows = [
    [39, [["M2x5", -1, t(5, 2), 5, c_money]]],
    [-1, [["penalty", -1, [30, 30], 0, "lightgray"]]],
];
module money_tray() bin_tray("money", money_box, money_h, money_box_rows);
module market() {
    translate([0, market.y - boat.y, 0]) boat_tray();
    vp_tray();
    translate([boat.x + gap, 0, 0]) money_tray();
}

wood_rows = [
    [-1, [
        ["ore", 50, [11, 11], 0, c_wood],
        ["stone", 50, [20, 13], 0, c_wood],
        ["wood", -1, [21, 14], 0, c_wood],
    ]],
];
module wood_tray() bin_tray("wood", wood, tier_h, wood_rows);

// Cardboard trays are open: a hex-grid floor and an L-shaped post at each
// well corner, no walls between. Stacks lift straight out, gripped from the
// open sides. Wells of one inner size, one above another in y, centered.
stack_clear = 1.5;
post_l = 15; // each leg, past the corner
hex_f = 12; // hole, across flats
hex_rib = 1.6;
hex_margin = 3; // solid floor inside each well edge
function stack_tray_size(well, n) = [well.x + stack_clear + 2 * post_t, n * (well.y + stack_clear + post_t) + post_t];
module stack_tray(size, h, well, labels, c) {
    n = len(labels);
    in = well + [stack_clear, stack_clear];
    x0 = (size.x - in.x) / 2;
    y0 = (size.y - (n * (in.y + post_t) - post_t)) / 2;
    body() open_tray(size, h, [for (i = [0:n - 1]) [[x0, y0 + i * (in.y + post_t)], in]]);
}

// A floor size.x by size.y, holed in a hex grid inside each well ([corner,
// size]), with corner posts h tall round each well.
module open_tray(size, h, wells) {
    render() difference() {
        cbox(size, floor_t, 0.4);
        translate([0, 0, -1]) linear_extrude(floor_t + 2) hex_holes(size, wells);
        rim_2d(floor_t) hex_holes(size, wells);
        translate([0, 0, chamfer]) mirror([0, 0, 1]) rim_2d(chamfer) hex_holes(size, wells);
    }
    for (w = wells, sx = [0, 1], sy = [0, 1])
        translate(w[0] + [sx * w[1].x, sy * w[1].y]) mirror([sx, 0, 0]) mirror([0, sy, 0]) corner_post(h);
}
module hex_holes(size, wells) intersection() {
    p = hex_f + hex_rib;
    for (i = [0:size.x / (p * cos(30)) + 1], j = [-1:size.y / p + 1])
        translate([i * p * cos(30), (j + (i % 2) / 2) * p]) circle(r = hex_f / sqrt(3), $fn = 6);
    for (w = wells) translate(w[0] + [hex_margin, hex_margin]) square(w[1] - 2 * [hex_margin, hex_margin]);
}
// An L round the corner at the origin of a well lying in +x, +y. Each leg's
// free end curves down to the floor on a radius of half its reach, leaving a
// flat on top; every edge is rounded.
module corner_post(h) {
    r = 0.6;
    len = post_l + post_t;
    R = min(post_l / 2, h - 2); // leaves len - R flat on top
    module side() intersection() {
        square([len, h]);
        hull() {
            square([len - R, h]);
            square([len, h - R]);
            translate([len - R, h - R]) circle(R, $fn = 64);
        }
    }
    module leg() minkowski() {
        translate([-post_t, -r, 0]) rotate([90, 0, 0]) linear_extrude(post_t - 2 * r) offset(delta = -r) side();
        sphere(r, $fn = 12);
    }
    leg();
    multmatrix([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]]) leg();
}

// Islands, one stack, on the wood tray's tier.
island = 129;
module islands_tray() stack_tray(islands, tier_h, [island, island], ["islands"], "lightsteelblue");

// Layer 3, cardboard: buildings, mountain strips, and the vikings.
card_h = tray_h;
building = [139, 54.5];
// In-game types stacked 3 on 3, then 5. The 6 setup buildings get their own
// tray: nothing setup-only shares a piece with in-game pieces.
building_labels = ["buildings 3 + 3", "buildings 5"];
buildings = stack_tray_size(building, len(building_labels));
module buildings_tray() stack_tray(buildings, card_h, building, building_labels, "sienna");
// The setup buildings, with a bin in front for the dice, moose and cube (all
// setup-only), filling the depth beside the in-game buildings.
setup_buildings = [buildings.x, box.y - 1 - buildings.y - gap];
misc_rows = [[-1, [["dice, moose, cube", -1, [16, 16], 0, "lightgray"]]]];
module setup_buildings_tray() {
    $setup = true;
    sz = setup_buildings;
    h = card_h;
    in = building + [stack_clear, stack_clear];
    x0 = (sz.x - in.x) / 2;
    wy = sz.y - post_t - in.y;
    // The bin's back wall sits inside the buildings' front posts.
    bin = [sz.x, wy - post_t + wall];
    body() {
        open_tray(sz, h, [[[x0, wy], in]]);
        difference() {
            cbox(bin, h);
            bin_cuts(bin, h, misc_rows);
        }
    }
    bin_check("setup", bin, h, misc_rows);
    paint("black") bin_labels(bin, misc_rows);
}
// 9 mountain strips in two stacks, the 192 mm one in the first. The tray lies
// turned 90° in the box.
long_strip = [192, 30];
// The wells run the box's full width, so the tray leaves no gap.
strip_well = [box.y - 1 - 2 * post_t - stack_clear, long_strip.y];
strip_labels = ["strips 5", "strips 4"];
strips = stack_tray_size(strip_well, len(strip_labels));
module strips_tray() stack_tray(strips, card_h, strip_well, strip_labels, "gray");
// Vikings: a bin per player color, one layer deep.
vik = [box.x - 1 - buildings.x - strips.y - 2 * gap, box.y - 1];
vik_rows = [for (c = vik_colors) [-1, [["vikings", -1, [13, 21], 0, c]]]];
module vik_tray() bin_tray("vikings", vik, card_h, vik_rows);

function sum(v) = len(v) == 0 ? 0 : v[0] + sum([for (i = [1:1:len(v) - 1]) v[i]]);
function cumsum(v, i) = sum([for (j = [0:1:i - 1]) v[j]]);

function row_depths(rows, size) =
    let (fixed = sum([for (r = rows) r[0] > 0 ? r[0] : 0]),
         n = len([for (r = rows) if (r[0] < 0) 1]),
         fill = (size.y - wall * (len(rows) + 1) - fixed) / max(1, n))
    [for (r = rows) r[0] > 0 ? r[0] : fill];

function bin_widths(bins, size) =
    let (fixed = sum([for (b = bins) b[1] > 0 ? b[1] : 0]),
         n = len([for (b = bins) if (b[1] < 0) 1]),
         fill = (size.x - wall * (len(bins) + 1) - fixed) / max(1, n))
    [for (b = bins) b[1] > 0 ? b[1] : fill];

// Scoop up the front wall, leaving the tile room to lie flat behind it.
function scoop(w, d, fp) = [min(scoop_max, max(scoop_min, d - fp.y)), true];

// Tiles that fit stacked neatly on the flat floor behind the scoop.
function neat_cap(w, flat_d, in_h, fp) =
    let (a = fp + [0.5, 0.5])
    max(floor(w / a.x) * floor(flat_d / a.y), floor(w / a.y) * floor(flat_d / a.x)) * floor(in_h / tile_t);

// A box with every outside edge chamfered.
module cbox(size, h, co = chamfer_out, cc = chamfer_corner) {
    module sh(d) offset(delta = cc, chamfer = true)
        translate([cc + d, cc + d])
        square([size.x - 2 * (cc + d), size.y - 2 * (cc + d)]);
    hull() {
        linear_extrude(eps) sh(co);
        translate([0, 0, co]) linear_extrude(h - 2 * co) sh(0);
        translate([0, 0, h - eps]) linear_extrude(eps) sh(co);
    }
}

// Cut for the chamfer round the rim of a rectangular well, [0, 0] to size, in
// a body h tall.
module rim(size, h, c = chamfer, r = fillet_r) {
    translate([0, 0, h - c]) hull() {
        linear_extrude(eps) rrect(size, r);
        translate([-c, -c, c]) linear_extrude(eps * 2) rrect(size + [2 * c, 2 * c], r + c);
    }
}

module rrect(size, r) offset(r = r) translate([r, r]) square(size - [2 * r, 2 * r]);

// A rectangular well, [0, 0] to size, floor at z0, open past h: vertical
// corners and floor edges rounded by r, and the front floor edge (y = 0)
// rounded by the scoop radius s instead when s > r.
module well(size, z0, h, s = 0, r = fillet_r) {
    sf = max(s, r);
    hull() {
        translate([0, 0, z0 + sf]) linear_extrude(h + 1 - z0 - sf) rrect(size, r);
        for (x = [r, size.x - r]) {
            translate([x, size.y - r, z0 + r]) sphere(r, $fn = 24);
            if (s > r) intersection() {
                translate([x, s, z0 + s]) rotate([0, 90, 0])
                    rotate_extrude($fn = 96) translate([s - r, 0]) circle(r, $fn = 24);
                translate([x - r - 1, -1, z0 - 1]) cube([2 * r + 2, s + 1, s + 1]);
            }
            else translate([x, r, z0 + r]) sphere(r, $fn = 24);
        }
    }
}
// A wedge along the back wall of a well, floor at z0: tiles standing on edge
// lean back on its slope, feet on the floor.
module wedge(size, z0) {
    base = wedge_h / tan(wedge_angle);
    translate([-1, 0, 0]) rotate([90, 0, 90]) linear_extrude(size.x + 2) polygon([
        [size.y - base, z0 - 1], [size.y - base, z0], [size.y, z0 + wedge_h],
        [size.y + 1, z0 + wedge_h], [size.y + 1, z0 - 1]]);
}
// The well filled 0.4 deep, for a floor color.
module floor_slab(size, z0, h, s = 0) intersection() {
    translate([0, 0, z0]) cube([size.x, size.y, 0.4]);
    well(size, z0, h, s);
}

// Same, for any 2D outline (children).
// In steps of a printed layer (0.2 mm), which is what prints anyway; the
// parts using it are render()ed so the preview doesn't shimmer on the steps.
// (A true slope needs a minkowski() per outline, some 20x slower.)
module rim_2d(h, c = chamfer, steps = 2) {
    for (i = [0:steps - 1]) translate([0, 0, h - c + i * c / steps])
        linear_extrude(c / steps + eps) offset(delta = (i + 1) * c / steps) children();
}
// A round-bottomed pinch slot along y, centered on x = 0: a U of width w with
// its bottom at z = bz, open to z = tz. faces are [y, dir] for every wall face
// it crosses, dir pointing into the material; each gets a chamfer of c.
module u_2d(w, bz, tz) hull() {
    translate([0, bz + w / 2]) circle(d = w, $fn = 64);
    translate([-w / 2, tz]) square([w, eps]);
}
module u_slot(w, bz, tz, y0, y1, faces, c = chamfer_out) {
    xzy = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]];
    multmatrix(xzy) {
        translate([0, 0, y0 - eps]) linear_extrude(y1 - y0 + 2 * eps) u_2d(w, bz, tz);
        for (f = faces) hull() {
            translate([0, 0, f[0] - eps]) linear_extrude(2 * eps) offset(delta = c) u_2d(w, bz, tz + c);
            translate([0, 0, f[0] + f[1] * c - eps]) linear_extrude(2 * eps) u_2d(w, bz, tz);
        }
    }
}

// A bin tray's wells, with their rim chamfers, to subtract from a body.
module bin_cuts(size, h, rows) {
    ds = row_depths(rows, size);
    for (ri = [0:len(rows) - 1]) {
        ws = bin_widths(rows[ri][1], size);
        for (bi = [0:len(ws) - 1])
            translate([wall + cumsum(ws, bi) + bi * wall, wall + cumsum(ds, ri) + ri * wall, 0]) difference() {
                b = rows[ri][1][bi];
                union() {
                    well([ws[bi], ds[ri]], floor_t, h, scoop(ws[bi], ds[ri], b[2])[0]);
                    rim([ws[bi], ds[ri]], h);
                }
                if (len(b) > 6 && b[6]) wedge([ws[bi], ds[ri]], floor_t);
            }
    }
}

// A bin tray's scoops, floor colors and labels; reports capacity.
// Runs children once per bin, with $b the bin, $pos its corner, $wd its
// [width, depth], $s its scoop radius, and $first / $last per axis.
module for_bins(size, rows) {
    ds = row_depths(rows, size);
    for (ri = [0:len(rows) - 1]) {
        bins = rows[ri][1];
        ws = bin_widths(bins, size);
        for (bi = [0:len(bins) - 1])
            let ($b = bins[bi], $wd = [ws[bi], ds[ri]],
                 $pos = [wall + cumsum(ws, bi) + bi * wall, wall + cumsum(ds, ri) + ri * wall],
                 $s = scoop(ws[bi], ds[ri], bins[bi][2])[0],
                 $first = [bi == 0, ri == 0], $last = [bi == len(bins) - 1, ri == len(rows) - 1])
                children();
    }
}

// Reports each bin's capacity.
module bin_check(name, size, h, rows) {
    for (ri = [0:len(rows) - 1]) for (w = bin_widths(rows[ri][1], size))
        assert(w > 0 && row_depths(rows, size)[ri] > 0, str(name, ": row ", ri, " doesn't fit"));
    for_bins(size, rows) if ($b[3] > 0) {
        c = neat_cap($wd.x, $wd.y - $s, h - floor_t, $b[2]);
        echo(str(c < min_cap * $b[3] ? "TIGHT " : "", name, " ", $b[0], ": ", round($wd.x), "x", round($wd.y),
                 " holds ", c, " neatly, needs ", $b[3]));
    }
}

// Each bin's icon, inlaid icon_d into its back wall, icon_top below the rim,
// so it shows over a part-full bin.
icon_d = 0.4;
icon_top = 2.5;
function icon_n(icon) = [max([for (c = icon[1]) c.x]) + 1, max([for (c = icon[1]) c.y]) + 1];
function icon_z(icon, h) = h - icon_top - (icon_n(icon).y * icon_cell + icon_line) / 2;
module bin_icons(size, h, rows) for_bins(size, rows) if (len($b) > 5)
    translate([$pos.x + $wd.x / 2, $pos.y + $wd.y + icon_d, icon_z($b[5], h)])
        rotate([90, 0, 0]) linear_extrude(icon_d + eps) icon_2d($b[5]);
// The front row's icons again, inlaid in the tray's outside front face at the
// same height (so they add no tool-change layers), to show however full the
// bins are.
module bin_front_icons(size, h, rows) for_bins(size, rows) if (len($b) > 5 && $first.y)
    translate([$pos.x + $wd.x / 2, icon_d, icon_z($b[5], h)])
        rotate([90, 0, 0]) linear_extrude(icon_d + eps) icon_2d($b[5]);
// Labels, raised on the floor, for bins without an icon.
module bin_labels(size, rows) for_bins(size, rows) if (len($b) <= 5)
    translate([$pos.x + $wd.x / 2, $pos.y + $s + ($wd.y - $s) / 2, floor_t])
        rotate($wd.x < 25 ? 90 : 0)
        linear_extrude(0.4) text($b[0], size = 3.5, halign = "center", valign = "center");

// Paints children (a tray body) in its bins' colors: each bin owns its cell
// out to the middle of the walls around it, and to clip on the outside.
module bin_paint(size, rows, clip = [[-1, 1000], [-1, 1000]]) for_bins(size, rows) {
    lo = [for (k = [0:1]) $first[k] ? clip[k][0] : $pos[k] - wall / 2];
    hi = [for (k = [0:1]) $last[k] ? clip[k][1] : $pos[k] + $wd[k] + wall / 2];
    // render() so the preview shows the colors too.
    paint($b[4]) render() intersection() {
        children();
        translate([lo.x, lo.y, -1]) cube([hi.x - lo.x, hi.y - lo.y, 1000]);
    }
}

// Icons, drawn on a icon_cell grid in icon_line wide lines, centered.
icon_cell = 4;
icon_line = 0.8;
module icon_2d(icon) {
    cs = icon[1];
    n = icon_n(icon);
    translate(-n * icon_cell / 2) for (c = cs) translate(c * icon_cell) {
        if (icon[0] == "grid") difference() {
            translate([-icon_line / 2, -icon_line / 2]) square(icon_cell + icon_line);
            translate([icon_line / 2, icon_line / 2]) square(icon_cell - icon_line);
        }
        else translate([icon_cell / 2, icon_cell / 2]) rotate(22.5) difference() {
            // Flat to flat one cell, so neighbors share an edge.
            r = icon_cell / 2 / cos(22.5);
            circle(r = r + icon_line / 2 / cos(22.5), $fn = 8);
            circle(r = r - icon_line / 2 / cos(22.5), $fn = 8);
        }
    }
}

// A bin tray: the body in its bins' colors, icons and labels in black.
module bin_tray(name, size, h, rows) {
    bin_check(name, size, h, rows);
    bin_paint(size, rows) difference() {
        cbox(size, h);
        bin_cuts(size, h, rows);
        bin_icons(size, h, rows);
        bin_front_icons(size, h, rows);
    }
    paint("black") {
        bin_icons(size, h, rows);
        bin_front_icons(size, h, rows);
        bin_labels(size, rows);
    }
}

function slice(v, a, b) = [for (i = [a:b - 1]) v[i]];
function slice_rows(rows, a, b) = [for (r = rows) [r[0], slice(r[1], a, b)]];
function tray_x(cols) = sum(cols) + (len(cols) + 1) * wall;

// Each long tray is two pieces to fit the 270 mm bed.
half_split = 4;
half_a = [tray_x(slice(half_cols, 0, half_split)), half.y];
half_b = [half.x - half_a.x - gap, half.y];
half_b_tiles_x = tray_x(slice(half_cols, half_split, len(half_cols)));
module half_a() bin_tray("half a", half_a, half_h, slice_rows(half_rows, 0, half_split));
// The money column shares the tile bins' last wall.
module half_b() {
    tiles = [half_b_tiles_x, half.y];
    mx = half_b_tiles_x - wall;
    money = [half_b.x - mx, half.y];
    tile_rows = slice_rows(half_rows, half_split, len(half_cols));
    bin_check("half b", tiles, half_h, tile_rows);
    bin_check("money", money, half_h, money_rows);
    module tray_body() difference() {
        cbox(half_b, half_h);
        bin_cuts(tiles, half_h, tile_rows);
        bin_icons(tiles, half_h, tile_rows);
        bin_front_icons(tiles, half_h, tile_rows);
        translate([mx, 0, 0]) {
            bin_cuts(money, half_h, money_rows);
            bin_icons(money, half_h, money_rows);
        }
    }
    // The shared wall splits down its middle.
    bin_paint(tiles, tile_rows, [[-1, half_b_tiles_x - wall / 2], [-1, 1000]]) tray_body();
    translate([mx, 0, 0]) bin_paint(money, money_rows, [[wall / 2, 1000], [-1, 1000]]) translate([-mx, 0, 0]) tray_body();
    paint("black") {
        bin_icons(tiles, half_h, tile_rows);
        bin_front_icons(tiles, half_h, tile_rows);
        translate([mx, 0, 0]) bin_icons(money, half_h, money_rows);
    }
}
module half_tray() {
    half_a();
    translate([half_a.x + gap, 0, 0]) half_b();
}

big_split = 2;
big_a = [tray_x(slice(big_cols, 0, big_split)), big.y];
big_b = [big.x - big_a.x - gap, big.y];
module big_a() bin_tray("big a", big_a, tier_h, slice_rows(big_rows, 0, big_split));
module big_b() bin_tray("big b", big_b, tier_h, slice_rows(big_rows, big_split, len(big_cols)));
module big_tray() {
    big_a();
    translate([big_a.x + gap, 0, 0]) big_b();
}

// The special tiles' boards: a pocket per tile, the forge tiles on their
// own board. Layout from pack_special.py.
special_h = floor_t + tilt_d + pocket_d;
special_others_x0 = special_forge_w + special_gap;
special_forge = [special_forge_w, special_size.y] + 2 * [special_margin, special_margin];
special_others = [special_size.x - special_others_x0, special_size.y] + 2 * [special_margin, special_margin];
// A tile's pocket outline, in board coordinates: outside corners rounded by
// the clearance, inside corners sharp.
module pocket_2d(st) offset(r = pocket_clear) translate(st[2]) for (c = st[1]) translate(c * unit) square(unit);
// The chamfer round a pocket's rim, at z = 0 to c: a true slope, built a cell
// at a time (each cell's is convex, and their union is the whole outline's).
module pocket_rim(st, c = chamfer) translate(st[2]) for (cell = st[1]) translate(cell * unit) hull() {
    linear_extrude(eps) offset(r = pocket_clear) square(unit);
    translate([0, 0, c]) linear_extrude(eps) offset(r = pocket_clear + c) square(unit);
}
// The parts of the pocket whose floor drops: a strip along each side of the
// tile's bounding box that can be a press end. A side is one if the tile is at
// least tilt_min_cells long that way (for leverage), and its center of mass is
// tilt_balance clear of the strip (so it rests flat). So a cross tips from any
// arm, a bar from either end.
tilt_min_cells = 3;
tilt_balance = 3;
function tile_n(st) = [max([for (c = st[1]) c.x]) + 1, max([for (c = st[1]) c.y]) + 1];
function tile_com(st) = [for (k = [0, 1]) sum([for (c = st[1]) (c[k] + 0.5) * unit]) / len(st[1])];
// [[left, right], [front, back]]
function tilt_sides(st) = let (n = tile_n(st), com = tile_com(st)) [for (k = [0, 1]) [
    n[k] >= tilt_min_cells && com[k] >= tilt_a + tilt_balance,
    n[k] >= tilt_min_cells && com[k] <= n[k] * unit - tilt_a - tilt_balance]];
module tilt_2d(st) intersection() {
    pocket_2d(st);
    n = tile_n(st) * unit;
    sides = tilt_sides(st);
    translate(st[2]) {
        if (sides.x[0]) translate([-1, -1]) square([tilt_a + 1, n.y + 2]);
        if (sides.x[1]) translate([n.x - tilt_a, -1]) square([tilt_a + 1, n.y + 2]);
        if (sides.y[0]) translate([-1, -1]) square([n.x + 2, tilt_a + 1]);
        if (sides.y[1]) translate([-1, n.y - tilt_a]) square([n.x + 2, tilt_a + 1]);
    }
}
// The drop's cross-section, the tile's edge at x = 0, the drop's floor at
// y = 0 and the pocket's at y = tilt_d.
assert(tilt_r <= tilt_d / 2);
module tilt_profile() {
    r = tilt_r;
    w = tilt_a - r; // the step's wall
    polygon(concat(
        [[-1, 0]],
        [for (t = [-90:15:0]) [w - r + r * cos(t), r + r * sin(t)]],
        [for (t = [180:-15:90]) [w + r + r * cos(t), tilt_d - r + r * sin(t)]],
        [[tilt_a, tilt_d + eps], [-1, tilt_d + eps]]
    ));
}
// The drop along the left side of a box [0, 0] to n, and the cut for a whole
// tile, from the drop's floor at z = 0.
module tilt_strip(n) translate([0, n.y + 1, 0]) rotate([90, 0, 0]) linear_extrude(n.y + 2) tilt_profile();
module tilt_cut(st) intersection() {
    linear_extrude(tilt_d + 2 * eps) pocket_2d(st);
    n = tile_n(st) * unit;
    sides = tilt_sides(st);
    swap = [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]];
    translate(st[2]) {
        if (sides.x[0]) tilt_strip(n);
        if (sides.x[1]) translate([n.x, 0, 0]) mirror([1, 0, 0]) tilt_strip(n);
        if (sides.y[0]) multmatrix(swap) tilt_strip([n.y, n.x]);
        if (sides.y[1]) translate([0, n.y, 0]) mirror([0, 1, 0]) multmatrix(swap) tilt_strip([n.y, n.x]);
    }
}
module special_board(section) {
    m = special_margin;
    size = section == "forge" ? special_forge : special_others;
    x0 = section == "forge" ? 0 : special_others_x0;
    body() render() difference() {
        cbox(size, special_h);
        for (st = special_tiles) if (st[0] == section) translate([m - x0, m, 0]) {
            // Straight walls, so the tile has its full clearance all the way down.
            translate([0, 0, special_h - pocket_d]) linear_extrude(pocket_d + eps) pocket_2d(st);
            translate([0, 0, special_h - chamfer]) pocket_rim(st);
            translate([0, 0, special_h - pocket_d - tilt_d]) tilt_cut(st);
        }
    }
    // Preview only: tint the dropped floors, which are otherwise hard to see.
    if ($preview && (is_undef($only) || $only == role_color("body"))) color("steelblue")
        for (st = special_tiles) if (st[0] == section)
            translate([m - x0, m, special_h - pocket_d - tilt_d]) linear_extrude(0.05) tilt_2d(st);
}
module special_boards() {
    special_board("forge");
    translate([special_forge.x + gap, 0, 0]) special_board("others");
}

// A deck holder: open-topped, cards lying flat, with a finger slot through
// both long walls to pinch the top card. In the box it lies on its side, so
// the cards stand on edge.
function deck_size(h) = [card.x + card_clear + 2 * deck_wall, card.y + card_clear + 2 * deck_wall,
                         h + card_clear + floor_t];
module deck_holder(h) {
    s = deck_size(h);
    body() difference() {
        cbox(s, s.z);
        translate([deck_wall, deck_wall, 0]) {
            well([card.x + card_clear, card.y + card_clear], floor_t, s.z);
            rim([card.x + card_clear, card.y + card_clear], s.z);
        }
        // Slots, round-bottomed.
        translate([0, s.y / 2, 0]) rotate(-90)
            u_slot(slot_w, floor_t + slot_bottom, s.z + 1, 0, s.x,
                   [[0, 1], [deck_wall, -1], [s.x - deck_wall, 1], [s.x, -1]]);
    }
}
// Holders side by side on their sides, open tops facing -x, so each deck is
// closed by its neighbor's floor or the box wall.
module deck_holders() {
    translate([decks_x, 0, 0]) mirror([1, 0, 0]) for (i = [0:len(deck_hs) - 1]) {
        x = sum([for (j = [0:1:i - 1]) deck_size(deck_hs[j]).z + gap]);
        translate([x, 0, deck_size(deck_hs[i]).x]) rotate([0, 90, 0]) let ($setup = i == 0) deck_holder(deck_hs[i]);
    }
}

// The board stack, bottom to top, one card_t layer each: [label, pos, size,
// color], within the box.
overview = [224, 96];
board_stack = [
    for (w = [183, 162, 134]) [["action board", [(box.x - 266) / 2, (box.y - w) / 2], [266, w], "tan"]],
    [["round overview", [(box.x - overview.x) / 2, (box.y - overview.y) / 2], overview, "wheat"]],
    for (i = [0:3]) [["player board", [(box.x - 299) / 2, (box.y - 190) / 2], [299, 190], "burlywood"]],
];
assert(len(board_stack) == board_layers, str("board stack has ", len(board_stack), " layers"));
module board_stack(explode_layers = 0) {
    for (i = [0:len(board_stack) - 1]) translate([0, 0, i * (card_t + explode_layers)])
        for (pc = board_stack[i]) translate(pc[1]) color(pc[3]) cube([pc[2].x, pc[2].y, card_t - 0.1]);
}

function show(n) = layer == 0 || (layer_only ? n == layer : n <= layer);
module assembly() {
    if (explode == 0 && layer == 0) color("white", 0.15) translate([-1, -1, 0]) difference() {
        cube([box.x + 2, box.y + 2, box.z]);
        translate([1, 1, -eps]) cube([box.x, box.y, box.z + 1]);
    }
    if (show(1)) for (i = [0, 1]) translate([0.5, 0.5 + i * (half.y + gap), 0]) half_tray();
    z2 = half_h + explode;
    translate([0.5, 0.5, z2]) {
        if (show(2)) deck_holders();
        if (show(2)) translate([decks_x + gap, 0, 0]) market();
        translate([0, front_y + gap, 0]) {
            if (show(2)) big_tray();
            if (show(3)) translate([0, 0, tier_h + explode / 2]) {
                islands_tray();
                translate([islands.x + gap, 0, 0]) wood_tray();
            }
        }
    }
    z3 = z2 + up_h + explode;
    if (show(4)) translate([0.5, 0.5, z3]) {
        buildings_tray();
        translate([0, buildings.y + gap, 0]) setup_buildings_tray();
        translate([buildings.x + gap + strips.y, 0, 0]) rotate(90) strips_tray();
        translate([buildings.x + strips.y + 2 * gap, 0, 0]) vik_tray();
    }
    z4 = z3 + card_h + explode;
    if (show(5)) translate([0, 0, z4]) board_stack(explode / 6);
    if (show(6)) translate([(box.x - special_forge.x - gap - special_others.x) / 2, (box.y - special_forge.y) / 2,
               z4 + board_stack_h + board_layers * explode / 6 + explode]) special_boards();
}

total_h = half_h + up_h + card_h + board_stack_h + special_h;
echo(total_h = total_h, over_box = total_h - box.z);

bed = 270;
for (s = [["half a", half_a], ["half b", half_b], ["big a", big_a], ["big b", big_b],
          ["boats", boat], ["money", money_box], ["vp", vp], for (h = deck_hs) ["deck", deck_size(h)], ["wood", wood], ["vikings", vik],
          ["islands", islands], ["buildings", buildings], ["setup buildings", setup_buildings], ["strips", strips],
          ["special forge", special_forge], ["special others", special_others]])
    assert(max(s[1]) <= bed, str(s[0], " is too big for the bed: ", s[1]));

module the_part() {
    if (part == "half") half_tray();
    else if (part == "half_a") half_a();
    else if (part == "half_b") half_b();
    else if (part == "big") big_tray();
    else if (part == "big_a") big_a();
    else if (part == "big_b") big_b();
    else if (part == "market") market();
    else if (part == "boats") boat_tray();
    else if (part == "money") money_tray();
    else if (part == "vp") vp_tray();
    else if (part == "islands") islands_tray();
    else if (part == "buildings") buildings_tray();
    else if (part == "setup_buildings") setup_buildings_tray();
    else if (part == "strips") strips_tray();
    else if (part == "wood") wood_tray();
    else if (part == "vikings") vik_tray();
    else if (part == "special") special_boards();
    else if (part == "special_forge") special_board("forge");
    else if (part == "special_others") special_board("others");
    else if (part == "decks") deck_holders();
    else if (part == "deck_setup") let ($setup = true) deck_holder(deck_hs[0]);
    else if (part == "deck_occupations") deck_holder(deck_hs[1]);
    else if (part == "deck_weapons") deck_holder(deck_hs[3]);
}
// Every color the parts use. New colors go last, so a saved Orca project's
// objects keep their order.
print_colors = concat([c_game, c_setup], vik_colors, ["black"]);
if (part == "assembly") assembly();
else if (part == "boards") board_stack(4);
else for (c = print_colors) let ($only = c) the_part();

