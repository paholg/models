// A Feast for Odin + The Norwegians: whole-box layout.
//
// x is the box length (305), y its width (216), z up.
//
// Bottom to top:
// 1: the big boards, in a frame that fills the box round them, and the
//    rulebooks on top of those.
// 2: two identical half trays of the small, often-used tiles and money, one
//    per end of the table, side by side.
// 3: the special tiles' boards.
// 4 to 6: the rest, in columns of trays that all come to one height.
//    front strip, under the card trays (not ours: see card-trays/README.md):
//    the mountain strips, in two stacks. At its end: the boat market and the
//    misc bin (4), and over them the VP and penalty tokens and the 2x5 money
//    (6), beside a spacer.
//    back, at the big tiles' end: the setup buildings, and a riser behind
//    them (4); the big tiles, which reach over onto the vikings (5); the
//    wooden goods (6).
//    back, at the islands' end: the vikings (4); the islands (5); the in-game
//    buildings, which reach over onto the big tiles (6).
//
// Tile bins are shallow, each with a curved scoop up the front wall to slide
// tiles out on; each reports how many tiles it holds stacked neatly.
// Cardboard stacks sit in wells with finger notches to lift them out whole.

// export: half_a half_b big boats vp vikings_red vikings_blue vikings_yellow vikings_black islands wood buildings buildings_cap setup_buildings misc strips riser spacer frame_half deck_setup deck_occupations deck_weapons special_forge special_others special_test
// Everything, in one project: a line per set of filaments.
// plate: frame_half*2
// plate: half_a*2 half_b*2 big
// plate: setup_buildings misc strips riser spacer deck_setup islands
// plate: special_forge special_others
// plate: buildings buildings_cap wood boats vp deck_occupations deck_weapons
// plate: vikings_red vikings_blue vikings_yellow vikings_black

include <special_layout.scad>
use <../../lib/orca.scad>

part = "assembly"; // [assembly, half, half_a, half_b, big, boats, vp, vikings_red, vikings_blue, vikings_yellow, vikings_black, islands, wood, buildings, buildings_cap, buildings_demo, setup_buildings, misc, strips, riser, spacer, frame, frame_half, boards, special, special_forge, special_others, special_test, decks, deck_setup, deck_occupations, deck_weapons]
// Vertical gap between layers in the assembly view.
explode = 30;
// Assembly: show layers up to this one, bottom up (0 = all). 1: boards and
// frame; 2: half trays; 3: special boards; 4 to 6: the bottom, middle and top
// trays of the columns over them.
layer = 0; // [0:6]
// Show only that layer, not the ones under it.
layer_only = false;

/* [Box] */
// Inside, measured.
box = [306, 218, 119];
// What the inserts leave of the box, in all, along each of x and y. They sit
// touching: no gap is drawn between them.
box_clear = 1.5;
inner = [box.x - box_clear, box.y - box_clear];
// Cardboard: see board_stack().
card_t = 2.25;
// The rulebooks lie flat on the boards and their frame. Roughly: the player
// boards' length, and 25 mm wider.
rulebooks = [299, 215, 2.5];
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
// The half trays.
half_h = 26.2;
scoop_min = 8;
scoop_max = 15;
// Warn when a bin's tiles, as solid cardboard, fill more of it than this:
// they're thrown in loose.
max_fill = 0.5;

/* [Chamfers] */
// Well and pocket rims.
chamfer = 0.4;
// Outside top and bottom edges.
chamfer_out = 0.6;
// Outside vertical corners.
chamfer_corner = 1;
fillet_r = 1; // inside corners and floor edges of wells

/* [Decks] */
// The card trays are imported, not modeled here: "Remixed A Feast for Odin
// card trays" by DewLeen (@DewLeen_91662 on Printables),
// https://www.printables.com/model/1145265-remixed-a-feast-for-odin-card-trays,
// a remix of "A Feast for Odin (+exp) Organizer / Insert" by RiftForge 3D
// (@RiftForge3D3). Licensed CC BY-NC-SA 4.0; see card-trays/README.md. The
// STLs here are as downloaded; deck_tray() adapts them (shorter, and a lip at
// each end), and what's exported is under their license.
// Cards stand on their long edges, the deck running along the tray.
// [name, file, the STL's minimum corner, its size, setup-only]
// How much is cut out of each one's length: the decks are shorter than the
// trays.
deck_cut = [5, 10, 5];
// Where, from the tray's front, as a share of its length: in the plain
// stretch between the thumb notch and the sloped back.
deck_cut_at = 0.5;
deck_trays = [
    ["setup occupations", "card-trays/weapon_cards_tray_x2.stl", [-37, -5.09, 0.46], [74, 57.5, 46.6], true],
    ["occupations", "card-trays/occupation_cards_tray.stl", [-37, -13.4, 0.9], [74, 115, 46.6], false],
    ["weapons", "card-trays/weapon_cards_tray_x2.stl", [-37, -5.09, 0.46], [74, 57.5, 46.6], false],
];
// Sleeved cards stand this tall on the trays' 1 mm floors.
card_w = 46;
deck_floor = 1;

/* [Special tiles] */
// Pocket depth: the tiles sit flush with the top.
pocket_d = tile_t;
pocket_clear = 0.4;
// Under the ends of each tile the pocket floor drops by tilt_d, for tilt_a in
// from the tile's edge: press there and the far end tips up to grab. The tip
// angle goes as tilt_d / tilt_a (about 18 degrees), so they scale together.
tilt_d = 2.2;
tilt_a = 7;
// The step down is an S: rounded over at the top, where the tile pivots, and
// filleted at the bottom.
tilt_r = 1.1;
// Floor under the drops; the rest of the board is thicker.
special_floor = 0.8;
// 2, not 3: so the two boards fit the box side by side.
special_margin = 2;
// The boards' corners are rounded by special_corner_r, for room to lift them
// out; pack_special.py sets it, and keeps the pockets clear of them.
// The forge board's icon, inlaid in its top face: width, depth, center and
// rotation.
forge_icon_w = 32;
forge_icon_d = 0.6;
forge_icon_at = [45, 28];
forge_icon_rot = 180;
// Test board: [tile index in special_tiles, [x, y]] of a few doubtful tiles.
special_test_tiles = [[1, [0, 0]], [13, [0, 24.8]], [3, [57.8, 0]]];
// The pocket floors, both levels and the step between, are c_floor this deep.
floor_skin = 0.4;

/* [Hidden] */
// Colors: a piece is c_game, or c_setup if it's only used in setup ($setup),
// as are the frame and the islands, which aren't;
// icons are black. Viking bins keep their player colors.
// Printing: the part is exported once per color in print_colors, with $only
// set, and each piece of geometry shows only in its own pass. Unset (the
// preview), everything shows.
c_game = "lightsteelblue";
c_setup = "tan";
c_floor = "darkslategray";
c_forge = "darkorange";
vik_colors = ["red", "blue", "yellow", "black"];
$only = undef;
$setup = false;
// A bin tray's walls, outside and between bins.
$wall = wall;
function role_color(c) =
    c == "black" || c == c_floor || c == c_forge ? c
    : len([for (v = vik_colors) if (v == c) 1]) > 0 ? c
    : $setup ? c_setup : c_game;
module paint(c) let (rc = role_color(c)) if (is_undef($only) || $only == rc) color(rc) children();
module body() paint("body") children();
eps = 0.01;
$fn = 64;
// Two to the layer, one behind the other.
half = [inner.x, inner.y / 2];
// Over the special boards, columns of trays, all zone_h tall.
// The card trays, in a row along the front, set the front strip's depth, and
// their height (the cards stand a little proud of them) most of the zone's.
// They're cut shorter than they come, by deck_cut each: see deck_tray().
up_h = deck_floor + card_w + 0.5;
front_y = deck_trays[0][3].x;
function deck_len(i) = deck_trays[i][3].y - deck_cut[i];
decks_x = sum([for (i = [0:len(deck_trays) - 1]) deck_len(i)]);
// Behind the front strip.
back_y = inner.y - front_y;
// The top two tiers at the back are half the card trays' height each.
tier_h = up_h / 2;
// Under the card trays, and under the big tiles: as tall as the setup
// buildings' stack.
setup_n = 6;
base_h = floor_t + setup_n * card_t;
zone_h = base_h + up_h;
// The front strip's end, past the card trays.
corner_x = inner.x - decks_x;

c_food = "orange";
c_equip = "seagreen";
c_animal = "tan";
c_money = "silver";
c_wood = "saddlebrown";

function t(x, y) = [x * unit, y * unit];

// Each row: [depth (-1 fills the tray), bins]. A bin: [name, width (-1
// shares what's left equally), tile footprint (scoop sizing, capacity), tile
// count (0 for none), color, optional icon, optional front-only]. With an icon,
// the bin shows it on the tray's front face. Front-only
// leaves the bin's back wall square, whatever $back_scoop.

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
    ["2x2", half_cols[2], t(2, 2), n[2], c, grid(2, 2)],
    ["1x4", half_cols[3], t(4, 1), n[3], c, grid(4, 1)],
    ["2x3", half_cols[4], t(3, 2), n[4], c, grid(3, 2)],
    ["3x3", half_cols[5], t(3, 3), n[5], c, grid(3, 3)],
    ["U", half_cols[6], t(3, 2), n[6], c, u_icon],
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
    [-1, [["M2x2", -1, t(2, 2), 9, c_money, coin(2, 2)]]],
];

// Big tiles and animals: one shared copy, full counts. Animals in front,
// equipment behind. Each bin is one tile wide, with big_clear to spare, and
// scooped front and back. The 2-wide tiles stand on edge, long side down,
// leaning, in a stack running front to back. The 3x4 are too tall for that:
// they lie flat, in two stacks, one behind the other.
// The islands' tray is beside it; the big tiles' bins share out the tray's
// length, which is where big_clear comes from.
// Room round a cardboard stack in its well.
stack_clear = 1.5;
island = 129;
island_n = 8;
// The islands' tray is square, as they are, and as deep as the back of the
// box; the big tiles take the rest of its length.
islands = [back_y, back_y];
big = [inner.x - islands.x, back_y];
// It's a tier tall, standing on the vikings' bins, which are as low as the
// setup buildings beside them: what the islands don't need of that is floor, and the
// tray, big and open and lifted out full, is the stiffer for it.
islands_h = tier_h;
islands_floor = islands_h - island_n * card_t;
assert(islands_floor >= floor_t, "the islands' tray is too low for its stack");
assert(islands.x >= island + stack_clear + 2 * post_t, "the islands don't fit beside the big tiles");
big_clear = (big.x - 4 * wall - 13 * unit) / 3;
function big_w(n) = n * unit + big_clear;
// [name, tile, stacks deep (0: on edge)]
big_kinds = [["2x4", t(4, 2), 0], ["3x4", t(4, 3), 2], ["2x5", t(5, 2), 0]];
big_cols = [for (k = big_kinds) big_w(k[1].x / unit)];
// A bin's footprint is what lies on its floor: every flat stack. Its icon is
// the tile's shape, shown once per column on the tray's front face.
function big_row(c, p, n) = [-1, [
    for (ki = [0:len(big_kinds) - 1]) let (k = big_kinds[ki])
        [str(p, k[0]), big_cols[ki], [k[1].x, k[1].y * max(1, k[2])], n[ki], c,
         grid(k[1].x / unit, k[1].y / unit), k[2] > 0],
]];
big_rows = [
    big_row(c_animal, "A", [18, 15, 21]),
    big_row(c_equip, "E", [20, 15, 14]),
];
assert(abs(sum(big_cols) + (len(big_cols) + 1) * wall - big.x) < 0.01, "the big tiles' columns don't fill their tray");

// Boats: a market of stacks, like mini decks. Each well fits its tile
// lengthwise (long side front to back), with a pinch slot through the front
// and back walls. The slots leave a lip each side to hold the stack in.
// [label, footprint, count], left to right.
// A boat is bigger than the tiles it's named for: the 4-long ones are 46
// long, their widths the tiles', and the 2x3 is 26 x 34.
boat_l = 46;
boats = [
    ["1x4", [unit, boat_l], 8],
    ["2x3", [26, 34], 10],
    ["2x4", [2 * unit, boat_l], 12],
    ["2x4", [2 * unit, boat_l], 10],
];
boat_clear = 1;
// Between its sides; the round-overs widen it at the rim.
boat_slot_w = 15;
// The 1x4 well's slot, through the side wall, where there's more room.
boat_side_slot_w = 25;
// Smaller than the standard, to leave more wall between neighboring slots.
boat_slot_r = 2;
boat_slot_lip = 2;
boat_well = [for (b = boats) b[1] + [boat_clear, boat_clear]];
boat_well_y = max([for (w = boat_well) w.y]);
// Just tall enough for the tallest stack.
boat_h = floor_t + max([for (b = boats) b[2]]) * tile_t;
// Each well's floor is raised so its full stack comes flush with the top.
function boat_floor(i) = max(floor_t, boat_h - boats[i][2] * tile_t);
// It's as long as the front strip's end: the walls between wells take up the
// slack.
boat = [corner_x, boat_well_y + 2 * wall];
boat_wall = (boat.x - sum([for (w = boat_well) w.x])) / (len(boats) + 1);
function boat_x(i) = boat_wall + sum([for (j = [0:1:i - 1]) boat_well[j].x + boat_wall]);

// The floor's notch at a slot len wide, through a wall t thick: its corners
// start where the floor's fillet ends.
module boat_notch(len, t, fl) let (inset = boat_clear / 2 + floor_inset)
    floor_notch(len, t, inset, fl, chamfer_out, top_from = fillet_r, r = inset - fillet_r);
// Where a short well leaves a thick wall, front or back, the wall is cut back
// to the usual thickness across the well, so its slot is no deeper to reach
// into than the others'. The outside face is y = 0, the tray in +y; the cut is
// w wide, centered on x = 0, and d deep. It's a bite out of the tray's
// outline, with the outline's own chamfers: chamfer_out round its top and
// bottom edges, and chamfer_corner on the two corners at its mouth.
// Convex pieces, each chamfer hulled a piece at a time: 0 the bite, 1 and 2
// the corners.
module boat_recess(w, d) {
    k = chamfer_out;
    cc = chamfer_corner;
    module piece(i, g = 0) offset(delta = g)
        if (i == 0) translate([-w / 2, -1]) square([w, d + 1]);
        else mirror([i - 1, 0]) polygon([[w / 2 - eps, -1], [w / 2 + cc + 1, -1], [w / 2 - eps, cc + eps]]);
    for (i = [0:2]) {
        translate([0, 0, -1]) linear_extrude(boat_h + 2) piece(i);
        hull() {
            translate([0, 0, -eps]) linear_extrude(eps) piece(i, k);
            translate([0, 0, k]) linear_extrude(eps) piece(i);
        }
        hull() {
            translate([0, 0, boat_h - k]) linear_extrude(eps) piece(i);
            translate([0, 0, boat_h]) linear_extrude(eps) piece(i, k);
        }
    }
}
// The boat market: its own piece, with the pinch slots open front and back.
module boat_tray() {
    body() difference() {
        cbox(boat, boat_h);
        for (i = [0:len(boats) - 1]) {
            w = boat_well[i];
            sw = min(boat_slot_w, w.x - 2 * boat_slot_lip);
            // Well, centered front to back: a short one has thicker walls there.
            wy = (boat.y - w.y) / 2;
            translate([boat_x(i), wy, 0]) {
                well(w, boat_floor(i), boat_h);
                rim(w, boat_h);
            }
            // Pinch slots through the front and back walls, all the way
            // down, the floor cut back from each (see floor_notch()); the
            // skinny first well is too narrow for that, so its slot goes
            // through the outer side wall instead.
            fl = boat_floor(i);
            if (i == 0) {
                translate([0, wy + w.y / 2, 0]) rotate(-90)
                    pinch_slot(boat_side_slot_w, -10, boat_h, 0, boat_wall, [[0, 1]], boat_slot_r);
                translate([boat_wall, wy + w.y / 2, 0]) rotate(90)
                    slot_ease(boat_side_slot_w, -10, boat_h, fl, fillet_r, boat_slot_r);
                translate([boat_wall, wy + (w.y + boat_side_slot_w) / 2, 0]) rotate(-90)
                    boat_notch(boat_side_slot_w, boat_wall, fl);
            }
            else translate([boat_x(i) + w.x / 2, 0, 0]) {
                // The walls there are no thicker than wall.
                if (wy > wall + eps) for (m = [0, 1]) translate([0, m * boat.y, 0]) mirror([0, m, 0])
                    boat_recess(w.x, wy - wall);
                // No further out than that: where a slot runs on through a
                // recess, the preview draws a stray face.
                pinch_slot(sw, -10, boat_h, wy - wall, wy, [[wy - wall, 1]], boat_slot_r);
                pinch_slot(sw, -10, boat_h, wy + w.y, wy + w.y + wall, [[wy + w.y + wall, -1]], boat_slot_r);
                translate([0, wy, 0]) mirror([0, 1, 0]) slot_ease(sw, -10, boat_h, fl, fillet_r, boat_slot_r);
                translate([0, wy + w.y, 0]) slot_ease(sw, -10, boat_h, fl, fillet_r, boat_slot_r);
                translate([-sw / 2, wy, 0]) boat_notch(sw, wall, fl);
                translate([-sw / 2, wy + w.y, 0]) mirror([0, 1, 0]) boat_notch(sw, wall, fl);
            }
        }
    }
}

// The VP tray, over the boats.
// VP tokens, 25 mm square: 2x 4 VP, 6x 3 VP, 8x 2 VP, standing on edge in one
// row, biggest first at the front (x = 0), as you only ever need the next one.
// A well per value, walls as tall as the tokens; one pinch slot runs through
// the front face and every divider, to slide the front token up and out.
// Behind them, in the tray's corner, a round well holds the 7 penalty tokens
// (30 mm round) in a stack, flush with the top. The corner itself is open: the quarter of the
// well's wall that faces it is gone, down to the bottom, and the floor there
// stops short of the stack's edge.
vp_token = 25;
vp_counts = [2, 6, 8];
vp_slack = 1.5; // per value, so the tokens can lean
vp_clear = 1.5; // across
vp_wall_h = vp_token + 0.5;
vp_slot_w = 16;
vp_slot_bottom = 4;
// Smaller than the standard round-over, to leave more of the dividers.
vp_slot_r = 2;
pen_clear = 1.5;
pen_n = 7;
pen_r = (30 + pen_clear) / 2;
function vp_group(i) = vp_counts[i] * tile_t + vp_slack;
function vp_x(i) = wall + sum([for (j = [0:1:i - 1]) vp_group(j) + wall]);
vp_in_y = vp_token + vp_clear;
// The stacks' block, front to back; the penalty well shares its back wall.
vp_block_y = vp_in_y + 2 * wall;
// The 2x5 money, in a stack of its own down the tray's other side, like a
// boat's.
money_n = 5;
money_clear = 1;
money_well = t(2, 5) + [money_clear, money_clear];
money_slot_w = 25;
// As long as it needs; a spacer takes the rest of the front strip's end.
vp = [72.5, front_y];
vp_need = [vp_x(len(vp_counts)) + money_well.x + wall, max(vp_block_y + 2 * pen_r + wall, money_well.y + 2 * wall)];
assert(vp_need.x <= vp.x && vp_need.y <= vp.y, str("the VP tray needs ", vp_need, " of ", vp));
// A wall's thickness from the tray's side and its back.
pen_c = [wall + pen_r, vp.y - wall - pen_r];
// From the boats to the zone's top: more than the tokens need, so their
// wells' floor is thick, and the tokens stand flush with the top.
vp_h = zone_h - boat_h;
vp_floor = vp_h - vp_wall_h;
assert(vp_floor >= floor_t, "the VP tray is too low for its tokens");
module vp_tray() {
    n = len(vp_counts);
    bz = vp_floor + vp_slot_bottom;
    // The penalty well's corner opening: a square, from the corner to the
    // well's center, so the walls end where the well is nearest them.
    pen_a = wall + pen_r;
    pen_gap = pen_clear / 2 + floor_inset;
    // Raised, so the stack comes flush with the top.
    pen_floor = vp_h - pen_n * tile_t;
    // The end of the side wall, as one side of a pinch slot twice as wide,
    // and its easing into the well.
    module pen_wall_end() translate([wall, vp.y, 0]) rotate(90) {
        // Through the wall, and no further: the floor's tongue is beyond.
        pinch_slot(2 * pen_a, -10, vp_h, -fillet_r, wall, [[wall, -1]], vp_slot_r);
        slot_ease(2 * pen_a, -10, vp_h, pen_floor, fillet_r, vp_slot_r);
    }
    // What's cut from the floor: the opening, less a tongue under the stack.
    // Its corners by the walls are rounded, from where the floor's fillet
    // ends.
    module pen_floor_2d() let (r = pen_gap - fillet_r) offset(r = r) offset(delta = -r) difference() {
        translate([-5, pen_c.y]) square([pen_a + 5, pen_a + 5]);
        translate(pen_c) circle(pen_r - pen_gap, $fn = 96);
    }
    // Its top edge, clear of the walls' ends, which slot_ease() does.
    module pen_floor_top_2d() intersection() {
        pen_floor_2d();
        translate([wall + fillet_r, 0]) square([vp.x, vp.y - wall - fillet_r]);
    }
    module pen_opening() {
        // Mirrored in the corner's diagonal, for the back wall's end.
        pen_wall_end();
        translate([0, vp.y, 0]) mirror([1, 1, 0]) translate([0, -vp.y, 0]) pen_wall_end();
        translate([-1, pen_c.y, pen_floor]) cube([pen_a + 1, pen_a + 1, vp_h]);
        translate([0, 0, -1]) linear_extrude(pen_floor + 1 + eps) pen_floor_2d();
        // Chamfers: the cut's bottom edge, and the tongue's top one. The cut
        // isn't convex, so each is its outline swept round with a cone, not a
        // hull.
        translate([0, 0, -eps]) minkowski() {
            linear_extrude(eps) pen_floor_2d();
            cylinder(r1 = chamfer_out, r2 = 0, h = chamfer_out, $fn = 24);
        }
        translate([0, 0, pen_floor - chamfer]) minkowski() {
            linear_extrude(eps) pen_floor_top_2d();
            cylinder(r1 = 0, r2 = chamfer, h = chamfer + eps, $fn = 24);
        }
    }
    money_at = [vp.x - wall - money_well.x, (vp.y - money_well.y) / 2];
    money_floor = vp_h - money_n * tile_t;
    body() difference() {
        cbox(vp, vp_h);
        for (i = [0:n - 1]) translate([vp_x(i), wall, 0]) {
            w = [vp_group(i), vp_in_y];
            well(w, vp_floor, vp_h);
            rim(w, vp_h);
        }
        translate([0, vp_block_y / 2, 0]) rotate(-90)
            pinch_slot(vp_slot_w, bz, vp_h, 0, vp_x(n - 1),
                   [[0, 1], for (i = [0:n - 1]) each [[vp_x(i), -1], if (i < n - 1) [vp_x(i) + vp_group(i), 1]]],
                   vp_slot_r);
        translate([pen_c.x, pen_c.y, 0]) round_well(pen_r, pen_floor, vp_h);
        pen_opening();
        // The money: its floor raised so the stack comes flush, and a pinch
        // slot through the outside wall, all the way down. The floor stops
        // short of the stack's edge there: see floor_notch().
        translate([money_at.x, money_at.y, 0]) {
            well(money_well, money_floor, vp_h);
            rim(money_well, vp_h);
        }
        // Below the floor the notch cuts the same opening as the slot, and
        // chamfers its bottom edge. Inside, the slot's sides run straight on
        // into the notch's, and are eased into the well.
        money_inset = money_clear / 2 + floor_inset;
        translate([vp.x - wall, vp.y / 2, 0]) rotate(-90) {
            pinch_slot(money_slot_w, -10, vp_h, 0, wall, [[wall, -1]], vp_slot_r);
            slot_ease(money_slot_w, -10, vp_h, money_floor, fillet_r, vp_slot_r);
        }
        // The notch's corners start where the floor's fillet ends, so the
        // two meet on flat floor.
        translate([vp.x - wall, (vp.y - money_slot_w) / 2, 0]) rotate(90)
            floor_notch(money_slot_w, wall, money_inset, money_floor, chamfer_out, top_from = fillet_r,
                        r = money_inset - fillet_r);
    }
}
// Beside the VP tray, a spacer: see honeycomb().
spacer = [corner_x - vp.x, front_y];
// A round well, floor at z0, open past h: floor edge filleted, rim chamfered.
module round_well(r, z0, h, f = fillet_r, c = chamfer) rotate_extrude($fn = 96) polygon(concat(
    [[0, z0]],
    [for (a = [-90:15:0]) [r - f + f * cos(a), z0 + f + f * sin(a)]],
    [[r, h - c], [r + c, h], [r + c, h + 1], [0, h + 1]]
));
module octahedron(c) polyhedron(
    [[c, 0, 0], [-c, 0, 0], [0, c, 0], [0, -c, 0], [0, 0, c], [0, 0, -c]],
    [[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4], [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5]]);

// The wooden goods, in the top tier beside the buildings: a bin each. Ore and
// stone are as wide as each other, a little over what stone needs for all of
// its pieces to lie about one deep; wood has the rest, still more than the
// 61 mm bin it was roomy in.
wood_bin = 48;
wood_rows = [
    [-1, [
        ["ore", wood_bin, [11, 11], 0, c_wood],
        ["stone", wood_bin, [20, 13], 0, c_wood],
        ["wood", -1, [21, 14], 0, c_wood],
    ]],
];
module wood_tray() let ($back_scoop = true) bin_tray("wood", wood, tier_h, wood_rows);

// Cardboard trays are open: a plain floor and an L-shaped post at each
// well corner, no walls between. Stacks lift straight out, gripped from the
// open sides, where the floor is cut back to under the stack's edge. Wells of one inner size, one above another in y, centered.
post_l = 15; // each leg, past the corner
// Where a neat stack's well is open at the side, the floor stops this far
// inside the stack's edge, to get a fingertip under the stack.
floor_inset = wall;
// The cut for that, through the wall and the floor, in plan: along an opening
// from x = 0 to len in a wall t thick, whose inside face is y = 0, the well in
// +y, the floor, fl thick, is cut back to y = inset. The opening's corners are
// chamfered, so it widens to the wall's faces: by chamfer_out at the outside
// one, and by k_in at the inside one, where the notch in the floor is as wide.
// The notch's inside corners are rounded by r. The whole cut's bottom edge is
// chamfered by cb, and the floor's new top edge by ct, from y = top_from on:
// a walled well's slot does the part by the wall itself (see slot_ease()).
// Its outline is a union of convex pieces, so a chamfer can be hulled a piece
// at a time: 0 the notch, 1 the way through the wall, 2 and 3 the outside
// corners' chamfers, 4 and 5 the inside ones'.
module floor_notch_piece(i, len, t, inset, k_in, r) {
    k = chamfer_out;
    module ends() for (m = [0, 1]) translate([m * len, 0]) mirror([m, 0]) children();
    if (i == 0) hull() {
        translate([-k_in, 0]) square([len + 2 * k_in, inset - r]);
        for (x = [r - k_in, len + k_in - r]) translate([x, inset - r]) circle(r, $fn = 24);
    }
    else if (i == 1) translate([0, -t - 1]) square([len, t + 1 + eps]);
    else if (i < 4) ends() if (i % 2 == 0) polygon([[-k - 1, -t - 1], [eps, -t - 1], [eps, -t + k]]);
    else if (k_in > 0) ends() if (i % 2 == 0) polygon([[-k_in, eps], [eps, eps], [eps, -k_in]]);
}
// Without outside, the wall has no outside face at t, only more wall (it's
// between two wells, say): so no corners there to chamfer.
module floor_notch(len, t, inset, fl, cb = chamfer, ct = chamfer, k_in = 0, top_from = 0, r = fillet_r,
                   outside = true) {
    module piece(i, g = 0) offset(r = g) floor_notch_piece(i, len, t, inset, k_in, r);
    // The part inside the wall's face, where the floor has a top edge.
    module inner(g = 0, y0 = 0) intersection() {
        piece(0, g);
        translate([-k_in - g - 1, y0]) square([len + 2 * (k_in + g + 1), inset + g + 1]);
    }
    for (i = [0:5]) if (outside || (i != 2 && i != 3)) {
        translate([0, 0, -1]) linear_extrude(fl + 1 + eps) piece(i);
        hull() {
            translate([0, 0, -eps]) linear_extrude(eps) piece(i, cb);
            translate([0, 0, cb]) linear_extrude(eps) piece(i);
        }
    }
    hull() {
        translate([0, 0, fl - ct]) linear_extrude(eps) inner(0, top_from);
        translate([0, 0, fl]) linear_extrude(eps) inner(ct, top_from);
    }
    // A walled well's floor is filleted into the wall: that goes too.
    translate([0, 0, fl]) linear_extrude(fillet_r + eps) inner();
}
function stack_tray_size(well, n) = [well.x + stack_clear + 2 * post_t, n * (well.y + stack_clear + post_t) + post_t];
module stack_tray(size, h, well, n) {
    in = well + [stack_clear, stack_clear];
    x0 = (size.x - in.x) / 2;
    y0 = (size.y - (n * (in.y + post_t) - post_t)) / 2;
    // The posts thicken to reach the tray's edges.
    body() open_tray(size, h, [for (i = [0:n - 1]) [[x0, y0 + i * (in.y + post_t)], in]], undef, x0, y0);
}

// A floor size.x by size.y, with corner posts h tall round each well
// ([corner, size]).
// h_end is the height of the posts' legs along y, if not h.
// $tray_floor is the floor's thickness. t_end is the thickness of the posts'
// legs along y, and t_side of those along x, if not post_t.
// Between the posts the floor is notched, to floor_inset inside the stack,
// which has clear round it: along each side from side_span[0] to
// side_span[1] of the well's length, and each end likewise by end_span;
// from post to post if undef, not at all if false.
// The floor's edges are rounded like the posts', so the two run flush.
$tray_floor = floor_t;
post_r = 0.6;
module open_tray(size, h, wells, h_end, t_end = post_t, t_side = post_t, clear = [stack_clear, stack_clear],
                 side_span, end_span) {
    // One notch, in a wall whose inside face is y = 0: its inside corners
    // rounded.
    module notch_2d(span, inset) if (span != false) hull() {
        translate([span[0], -1000]) square([span[1] - span[0], 1000 + inset - fillet_r]);
        for (x = [span[0] + fillet_r, span[1] - fillet_r]) translate([x, inset - fillet_r]) circle(fillet_r, $fn = 24);
    }
    module plan() difference() {
        square(size);
        for (w = wells) translate(w[0]) {
            in = w[1];
            ss = is_undef(side_span) ? [post_l, in.x - post_l] : side_span;
            es = is_undef(end_span) ? [post_l, in.y - post_l] : end_span;
            for (m = [0, 1]) {
                translate([0, m * in.y]) mirror([0, m]) notch_2d(ss, clear.y / 2 + floor_inset);
                translate([m * in.x, 0]) mirror([m, 0]) mirror([1, -1]) notch_2d(es, clear.x / 2 + floor_inset);
            }
        }
    }
    // A thin floor's edges are rounded by a little less than half of it.
    r = min(post_r, $tray_floor / 2 - 0.1);
    // How far sphere($fn = 12) reaches up and down: not quite its radius.
    rz = r * cos(15);
    minkowski() {
        translate([0, 0, rz]) linear_extrude($tray_floor - 2 * rz) offset(delta = -r) plan();
        sphere(r, $fn = 12);
    }
    for (w = wells, sx = [0, 1], sy = [0, 1])
        translate(w[0] + [sx * w[1].x, sy * w[1].y]) mirror([sx, 0, 0]) mirror([0, sy, 0])
            corner_post(h, is_undef(h_end) ? h : h_end, t_end, t_side);
}
// An L round the corner at the origin of a well lying in +x, +y. Each leg's
// free end is one side of a pinch slot: rounded over at the top on a radius
// of half its reach, leaving a flat on top, and straight down from there, to
// run on into the side of the floor's notch. Every edge is rounded.
module corner_post(h, h_y, t_y = post_t, t_x = post_t) {
    r = post_r;
    gap_w = 100; // the opening: only its near side matters
    // A leg's side, len long past the corner. On a short post (over a thick
    // floor) the round-over shrinks to fit.
    module side(h, len) difference() {
        R = min(post_l / 2, h - $tray_floor - 1); // leaves len - R flat on top
        square([len, h]);
        translate([len + gap_w / 2, 0]) pinch_2d(gap_w, -10, h, R);
    }
    // A leg along x, t thick, reaching c back past the corner to cover the
    // other leg's end.
    module leg(h, t, c) minkowski() {
        translate([-c, -r, 0]) rotate([90, 0, 0]) linear_extrude(t - 2 * r) offset(delta = -r) side(h, post_l + c);
        sphere(r, $fn = 12);
    }
    leg(h, t_x, t_y);
    multmatrix([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]]) leg(is_undef(h_y) ? h : h_y, t_y, t_x);
}

// Islands, one stack, beside the big tiles, over the vikings.
module islands_tray() let ($setup = true, $tray_floor = islands_floor) stack_tray(islands, islands_h, [island, island], 1);

// The setup buildings, 6 of them, in one stack: an open tray.
building = [139, 54.5];
// Front to back, these stacks get less room than stack_clear.
card_clear_y = 1;
bld = [building.x + stack_clear + 2 * post_t, building.y + card_clear_y + 2 * post_t];
// A piece that only fills a gap, or holds up what's over it, is a honeycomb:
// the 2D outline (children), h tall, its outside edges chamfered top and
// bottom, with a border as thick as a wall, and inside that big cells,
// honey_cell from flat to flat, in walls thinner than the border, as all they
// do is hold something up.
// The cells' walls run along y, half a pitch apart, or along x if turned. The
// cells are set across those so that no wall runs close beside an edge of the
// outline, leaving a slot: edges are where its edges that way are, and of the
// shifts within half a pitch, the one that leaves the nearest wall furthest
// from any of them is used.
// render(): the preview can't draw this many cells cut from one body, and
// shows their walls as holes.
honey_cell = 20;
honey_wall = 0.8;
honey_pitch = honey_cell + honey_wall;
function honey_near(s, edges) = min([for (e = edges)
    let (d = ((e - s) % (honey_pitch / 2) + honey_pitch / 2) % (honey_pitch / 2)) min(d, honey_pitch / 2 - d)]);
function honey_shift(edges) = let (shifts = [for (s = [0:0.1:honey_pitch / 2]) s],
                                   nears = [for (s = shifts) honey_near(s, edges)])
    shifts[search(max(nears), nears)[0]];
module honeycomb(size, h, edges, turned = false) let ($setup = true, shift = honey_shift(edges)) body()
    render(convexity = 4) difference() {
        union() {
            chamfered(chamfer_out) children();
            translate([0, 0, chamfer_out - eps]) linear_extrude(h - 2 * chamfer_out + 2 * eps) children();
            translate([0, 0, h - chamfer_out]) chamfered(chamfer_out, true) children();
        }
        // union(): generate.py runs OpenSCAD with lazy-union, under which a
        // bare for's iterations would each be intersected.
        translate([0, 0, -1]) linear_extrude(h + 2) intersection() {
            offset(r = -wall) children();
            union() for (j = [-1:ceil(max(size) / (honey_pitch * sqrt(3) / 2)) + 1], i = [-1:ceil(max(size) / honey_pitch) + 1])
                let (across = shift + (i + (j % 2) / 2) * honey_pitch, along = j * honey_pitch * sqrt(3) / 2)
                    translate(turned ? [along, across] : [across, along]) rotate(turned ? 0 : 30)
                        circle(honey_cell / sqrt(3), $fn = 6);
        }
    }
// A rectangle with its corners rounded, for one.
module honey_rect(size) offset(r = chamfer_corner) offset(delta = -chamfer_corner) square(size);

// The riser fills the gap behind the setup buildings' tray, as long as it
// is, for the big tiles to sit on; the vikings' bins take what's beside the
// two.
riser = [bld.x, back_y - bld.y];
module riser() honeycomb(riser, base_h, [wall, riser.x - wall]) honey_rect(riser);
// The spacer is narrow, so its cells are turned: their walls cross it.
module spacer() honeycomb(spacer, vp_h, [wall, spacer.y - wall], true) honey_rect(spacer);

module setup_buildings_tray() let ($setup = true, $tray_floor = base_h - setup_n * card_t) {
    in = building + [stack_clear, card_clear_y];
    body() open_tray(bld, base_h, [[[post_t, post_t], in]], clear = [stack_clear, card_clear_y]);
}
// 9 mountain strips: eight 169 mm ones and a 192 mm one. Under the card trays
// they lie in two stacks, in one solid tray: four short ones in the front
// well, and four with the long one on top in the back well, each well's floor
// as high as brings its stack flush with the top. What room the wells leave
// is between them, and at their ends.
// The back well is the long strip's length, for one strip's depth; under that
// it's the short ones' length, so the long one rests on a ledge past their
// end.
// A stack is pinched through a slot in its outside wall and one in the wall
// between the two. Each goes down through the floor, which is cut back from it
// to just under the stack's edge (see floor_notch()), to get a fingertip
// under.
// The setup buildings' tray stands behind this one, from the box's end, with
// a post at each front corner and an opening between them. The back wall's
// slot is that opening exactly: as wide, and its sides rounded over at the top
// as the posts' ends are (see corner_post()), so the two trays' walls run on
// from each other. The front wall's is the same slot, turned half round with
// the tray, which can then go in either way round. The wells are set so each
// slot leaves a post's length of wall at its well's end: the back one from
// one end of the tray, the front one from the other.
strip = [169, 30];
long_strip = [192, 30];
strips = [decks_x, front_y];
strips_n = [4, 4];
// Along the tray: the outside slots' span, at the wall's foot, from the end
// the setup buildings start at; how much wall a slot leaves at a well's end;
// and the radius its sides round over on at the top. All the posts'.
strips_slot = [post_t + post_l, bld.x - post_t - post_l];
strips_end = post_l;
strips_slot_r = post_l / 2;
module strips_tray() {
    $setup = true;
    short = strip + [stack_clear, card_clear_y];
    long = long_strip + [stack_clear, card_clear_y];
    // The wells' ends: the back one's at the low end of x, the front one's at
    // the high end.
    x = [strips.x - post_t - short.x, post_t];
    y = [wall, strips.y - wall - short.y];
    fl = [base_h - strips_n[0] * card_t, base_h - (strips_n[1] + 1) * card_t];
    ledge = base_h - card_t;
    inset = card_clear_y / 2 + floor_inset;
    out_w = strips_slot[1] - strips_slot[0];
    out_x = [strips.x - (strips_slot[0] + strips_slot[1]) / 2, (strips_slot[0] + strips_slot[1]) / 2];
    // Between the wells, where both run, less a post's length at each end.
    mid = [max(x[0], x[1]) + strips_end, min(x[0], x[1]) + short.x - strips_end];
    mid_w = mid[1] - mid[0];
    mid_t = y[1] - y[0] - short.y;
    assert(min(fl) >= floor_t, "the strips' stacks are too tall for their tray");
    for (k = [0, 1]) assert(out_x[k] - out_w / 2 >= x[k] + strips_end - eps
                            && out_x[k] + out_w / 2 <= x[k] + short.x - strips_end + eps,
                            "a strips' slot runs past its well");
    // The floor's notch at a slot len wide through a wall t thick: its corners
    // start where the floor's fillet ends.
    module notch(len, t, f, outside = true)
        floor_notch(len, t, inset, f, chamfer_out, top_from = fillet_r, r = inset - fillet_r, outside = outside);
    body() difference() {
        cbox(strips, base_h);
        translate([x[0], y[0], 0]) {
            well(short, fl[0], base_h);
            rim(short, base_h);
        }
        translate([x[1], y[1], 0]) {
            well(short, fl[1], base_h);
            well(long, ledge, base_h);
            rim(long, base_h);
            // The ledge's edge, where the short strips' well ends.
            translate([short.x - eps, 0, ledge - chamfer]) rotate([-90, 0, 0])
                linear_extrude(short.y) polygon([[0, 0], [chamfer + eps, -chamfer - eps], [0, -chamfer - eps]]);
        }
        // The outside slots: through the front wall, and the back one.
        translate([out_x[0], 0, 0]) {
            pinch_slot(out_w, -10, base_h, 0, wall, [[0, 1]], strips_slot_r);
            translate([0, wall, 0]) mirror([0, 1, 0]) slot_ease(out_w, -10, base_h, fl[0], fillet_r, strips_slot_r);
            translate([-out_w / 2, wall, 0]) notch(out_w, wall, fl[0]);
        }
        translate([out_x[1], strips.y, 0]) mirror([0, 1, 0]) {
            pinch_slot(out_w, -10, base_h, 0, wall, [[0, 1]], strips_slot_r);
            translate([0, wall, 0]) mirror([0, 1, 0]) slot_ease(out_w, -10, base_h, fl[1], fillet_r, strips_slot_r);
            translate([-out_w / 2, wall, 0]) notch(out_w, wall, fl[1]);
        }
        // The slot between the wells, and the floor's notch into each.
        translate([(mid[0] + mid[1]) / 2, 0, 0]) {
            pinch_slot(mid_w, -10, base_h, y[0] + short.y, y[1], [], strips_slot_r);
            translate([0, y[0] + short.y, 0]) slot_ease(mid_w, -10, base_h, fl[0], fillet_r, strips_slot_r);
            translate([0, y[1], 0]) mirror([0, 1, 0]) slot_ease(mid_w, -10, base_h, fl[1], fillet_r, strips_slot_r);
            translate([-mid_w / 2, y[0] + short.y, 0]) mirror([0, 1, 0]) notch(mid_w, mid_t / 2, fl[0], false);
            translate([-mid_w / 2, y[1], 0]) notch(mid_w, mid_t / 2, fl[1], false);
        }
    }
}
// The in-game buildings, in one tray: a stack per kind, each leaning on its
// own ramp, like shingles, all at one angle. A stack's low edge is on the
// floor, against a stop; its high half lies over the next stack, whose ramp
// carries it. A ramp stops short of its stack's high edge, to get a finger
// under and lift, and reaches a little over the low edge of the stack before
// it; the front wall has a lip that does the same for the last stack. So a
// building comes out up its ramp, and the stacks over it stay put.
// The tray is one section from end to end, between two end walls, and prints
// standing on one of them, with no overhangs. The other is a cap, glued on.
// Its section is drawn in [u, v]: u from the tray's front to its back, v up.

// Buildings a stack, back stack first: the one with nothing under it.
bld_stacks = [3, 3, 5];
// How much of a covered stack shows, of a building's width. More, and the
// tray is deeper and leans less, so it's lower: this much brings it under
// the tier's height.
bld_show = 0.75;
bld_ramp_t = 1.2;
// Between a stack and the ramp, or lip, over it.
bld_over = 0.6;
// A ramp stops this short of its buildings' high edge. The back stack's too:
// the back wall stands under its ramp's end, with the buildings' overhang
// behind it.
bld_grip = 8;
// Under that overhang, from the back wall to the tray's edge, the tray is
// solid this far up from the floor: a face for the next tray to sit against,
// and low enough to leave the way in under the buildings.
bld_lip = 4;
bld_end_t = 1.2;
// Along the buildings, in all: it has to turn into the back of the box.
bld_len_clear = 1;
// The section's own edges are rounded over by this, and filleted by that where
// its walls meet. (The end walls' outline has chamfer_corner for both.)
bld_round = 0.4;
bld_fillet = 0.5;
// The cap's plugs: how tall, their fit in the hollows each side, and how far
// their crush ribs stand out.
bld_plug_h = 4;
bld_plug_clear = 0.2;
bld_rib = 0.35;
// The hollows under the ramps are closed off just below the plugs, making each
// a socket. A plug is glued by its end alone, to its socket's floor, which it
// stops bld_glue_gap short of; what glue is pushed aside has the room round
// the end's chamfer (bld_plug_lead).
// The socket's floor is bld_socket_floor thick, on a roof that closes in from
// the hollow's walls at 45 degrees: no bridge, which the slicer would run the
// long way.
bld_socket_floor = 1;
bld_glue_gap = 0.2;
// A plug's top edge is chamfered by this, to lead it in.
bld_plug_lead = 0.6;

bld_last = len(bld_stacks) - 1;
function bld_t(i) = bld_stacks[i] * card_t;
// The thickest stack with another over it sets the angle.
bld_a = atan((max([for (i = [0:bld_last - 1]) bld_t(i)]) + bld_over + bld_ramp_t) / (bld_show * building.y));
// Along and square to the ramps.
bld_d = [cos(bld_a), sin(bld_a)];
bld_n = [-sin(bld_a), cos(bld_a)];
// From one stack's low corner to the next's.
bld_step = bld_show * building.y / cos(bld_a);
// How far a ramp reaches over the stack under it, from that stack's low edge.
bld_reach = building.y - bld_grip - bld_step * cos(bld_a);
// Stack i: where its ramp leaves the floor, under its low edge; and the low
// and high corners of its top.
function bld_p(i) = [wall + bld_t(bld_last) * sin(bld_a) + (bld_last - i) * bld_step, floor_t];
function bld_low(i) = bld_p(i) + bld_t(i) * bld_n;
function bld_high(i) = bld_low(i) + building.y * bld_d;
// Its top's height at u, and beyond.
function bld_top(i, u) = bld_low(i).y + (u - bld_low(i).x) * tan(bld_a);
// The lip over the last stack: its top's low and high ends.
bld_front = bld_p(bld_last) + (bld_t(bld_last) + bld_over + bld_ramp_t) * bld_n;
bld_front_end = bld_front + bld_reach * bld_d;
bld_front_h = bld_front.y - bld_front.x * tan(bld_a);
bld_depth = bld_p(0).x + building.y * bld_d.x;
// The back wall's outside face.
bld_back = bld_p(0).x + (building.y - bld_grip) * bld_d.x;
// A plug's foot is its hollow, 1 + bld_plug_clear in from every side: so it
// starts this far from the hollow's point, where the ramp meets the floor.
bld_plug_from = (1 + bld_plug_clear) / tan(bld_a / 2);
bld_in_x = building.x + bld_len_clear;
bld_tray = [bld_in_x + 2 * bld_end_t, bld_depth, max([for (i = [0:bld_last]) bld_high(i).y])];
echo(bld_angle = bld_a, bld_tray = bld_tray);
assert(bld_tray.x <= back_y && bld_tray.z <= tier_h, str("the buildings tray doesn't fit its tier: ", bld_tray));
// The wooden goods take the rest of the top tier at the back.
wood = [inner.x - bld_tray.y, back_y];

// The end walls' outline: the tray's silhouette with its buildings in. From
// the front it's the lip's top, a step down to the last stack's, then each
// stack's top to the high corner of the next, where it steps straight up. At
// the back it runs on to the tray's edge, and straight down. Every corner is
// rounded.
module bld_outline() offset(r = chamfer_corner) offset(delta = -chamfer_corner)
    offset(r = -chamfer_corner) offset(delta = chamfer_corner) polygon([
        [0, 0], [bld_depth, 0], [bld_depth, bld_top(0, bld_depth)],
        for (i = [1:bld_last]) each [[bld_high(i).x, bld_top(i - 1, bld_high(i).x)], bld_high(i)],
        [bld_front_end.x, bld_top(bld_last, bld_front_end.x)], bld_front_end, [0, bld_front_h],
    ]);
// A slab along the ramps' slope from p: len long, t thick, under the line.
module bld_slab(p, len, t) polygon([p, p + len * bld_d, p + len * bld_d - t * bld_n, p - t * bld_n]);
// The section. It's all within the outline, which only takes its outside
// corners off.
module bld_section() intersection() {
    bld_outline();
    offset(r = -bld_fillet) offset(delta = bld_fillet) offset(r = bld_round) offset(delta = -bld_round) union() {
        square([bld_depth, floor_t]);
        for (i = [0:bld_last]) let (p = bld_p(i), up = bld_step * sin(bld_a) - bld_ramp_t / 2) {
            // Ramp: down through the floor.
            intersection() {
                bld_slab(p - 5 * bld_d, 5 + building.y - bld_grip, bld_ramp_t);
                square([bld_depth, bld_tray.z]);
            }
            // Stop at the stack's low edge, up into the next ramp.
            if (i < bld_last) polygon([p, p + up * bld_n, p - wall * bld_d + up * bld_n, p - wall * bld_d]);
        }
        // The last stack's stop is the front wall, with its lip.
        let (p = bld_p(bld_last), under = bld_front - bld_ramp_t * bld_n)
            polygon([[0, 0], [p.x, 0], p, under, under + bld_reach * bld_d, bld_front_end, [0, bld_front_h]]);
        // Back wall, under the end of the back stack's ramp; and the solid
        // part behind it.
        translate([bld_back - wall, 0]) square([wall, bld_top(0, bld_back) - bld_t(0) / cos(bld_a) - bld_ramp_t / 2]);
        translate([bld_back - wall, 0]) square([bld_depth - bld_back + wall, floor_t + bld_lip]);
    }
}
// The hollow under ramp i: floor, ramp, and the stop (or back wall) of the
// stack before.
function bld_hollow(i) = let (p = bld_p(i), a = [p.x + bld_ramp_t / sin(bld_a), floor_t])
    i == 0 ? [a, [bld_back - wall, floor_t],
              [bld_back - wall, floor_t + (bld_back - wall - p.x) * tan(bld_a) - bld_ramp_t / cos(bld_a)]]
    : let (q = bld_p(i - 1)) [a, [q.x - wall / cos(bld_a), floor_t],
                              q - wall * bld_d + (bld_step * sin(bld_a) - bld_ramp_t) * bld_n];
// The circle that fits a triangle, as [center, radius]: where its sides meet
// if they all come in at one rate, and how far in that is.
function bld_incircle(h) = let (a = norm(h[2] - h[1]), b = norm(h[0] - h[2]), c = norm(h[1] - h[0]),
                               area = abs((h[1] - h[0]).x * (h[2] - h[0]).y - (h[1] - h[0]).y * (h[2] - h[0]).x) / 2)
    [(a * h[0] + b * h[1] + c * h[2]) / (a + b + c), 2 * area / (a + b + c)];

// The end walls' outline, chamfered: see chamfered().
module bld_chamfered(c, flip = false) chamfered(c, flip) bld_outline();
// An end wall: a plate of the outline, bld_end_t thick, outside face down.
// Its outside edge is chamfered all round, by chamfer_out. Its inside edge is
// chamfered, by chamfer, where the wall stands clear of the section: where
// that meets the edge, it's left whole, to run flush.
module bld_end_plate() {
    mid = bld_end_t - chamfer_out - chamfer;
    bld_chamfered(chamfer_out);
    translate([0, 0, chamfer_out - eps]) linear_extrude(mid + 2 * eps) bld_outline();
    translate([0, 0, bld_end_t - chamfer]) {
        bld_chamfered(chamfer, true);
        linear_extrude(chamfer) bld_section();
    }
}
// As it lies in the box: x along the buildings, u along y.
module bld_upright() multmatrix([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]]) children();
// A hollow, filled, and grown into the walls round it.
module bld_fill(h) intersection() {
    offset(delta = 0.6) polygon(h);
    bld_outline();
}
// union(), and no bare for inside an intersection(): generate.py runs OpenSCAD
// with lazy-union.
module buildings_tray() body() bld_upright() union() {
    bld_end_plate();
    translate([0, 0, bld_end_t - eps]) linear_extrude(bld_in_x + eps) bld_section();
    // The sockets' floors, and the roof under each: the hollow ends in a
    // pyramid, its faces at 45 degrees, its point over the middle.
    for (i = [0:bld_last]) let (h = bld_hollow(i), ic = bld_incircle(h),
                                z1 = bld_end_t + bld_in_x - bld_plug_h - bld_glue_gap - bld_socket_floor) {
        translate([0, 0, z1 - eps]) linear_extrude(bld_socket_floor + eps) bld_fill(h);
        translate([0, 0, z1 - ic[1]]) difference() {
            linear_extrude(ic[1]) bld_fill(h);
            hull() {
                translate([0, 0, -eps]) linear_extrude(eps) polygon(h);
                translate([ic[0].x, ic[0].y, ic[1]]) cube(eps, center = true);
            }
        }
    }
}
// The cap: the other end wall, with a plug for each socket. Drawn as printed,
// outside face down: so the section is mirrored, as it's seen from the tray's
// other end.
module bld_plug_foot(i) offset(r = 1) offset(delta = -1 - bld_plug_clear) polygon(bld_hollow(i));
module buildings_cap() body() translate([bld_depth, 0, 0]) mirror([1, 0, 0]) union() {
    bld_end_plate();
    for (i = [0:bld_last]) let (h = bld_hollow(i), c = (h[0] + h[1] + h[2]) / 3) translate([0, 0, bld_end_t - eps]) {
        // A plug, its top edge chamfered.
        hull() {
            linear_extrude(bld_plug_h - bld_plug_lead) bld_plug_foot(i);
            linear_extrude(bld_plug_h) offset(delta = -bld_plug_lead) bld_plug_foot(i);
        }
        // Crush ribs, in pairs: one on the floor's side and one on the ramp's,
        // squeezing the plug between them. Two pairs, a fifth of the way in
        // from each end of the plug, which starts where the hollow is tall
        // enough for it: bld_plug_from along either side from the hollow's
        // point (h[0]). They stand out past the clearance and taper in toward
        // the top. None on the short side: the plug needs no squeezing there.
        for (k = [1, 2], f = [0.2, 0.8]) let (e = (h[k] - h[0]) / norm(h[k] - h[0]),
                                              to = min(norm(h[1] - h[0]), norm(h[2] - h[0])) - 1 - bld_plug_clear,
                                              m = h[0] + (bld_plug_from + f * (to - bld_plug_from)) * e,
                                              v0 = [-e.y, e.x], v = v0 * (c - m) > 0 ? v0 : -v0)
            hull() {
                translate(m + (bld_plug_clear + 0.5 - bld_rib) * v) cylinder(r = 0.5, h = bld_plug_h - 2, $fn = 16);
                translate(m + (bld_plug_clear + 1.2) * v) cylinder(r = 0.3, h = bld_plug_h - 1, $fn = 16);
            }
    }
}
// The tray with its cap on.
module buildings_capped() {
    buildings_tray();
    // Turned onto the tray's end, not mirrored: as the printed part goes on.
    translate([bld_tray.x, bld_depth, 0]) rotate(180) bld_upright() buildings_cap();
}
// And its buildings in.
module buildings_demo() {
    buildings_capped();
    for (i = [0:bld_last], k = [0:bld_stacks[i] - 1]) color(["peru", "sienna", "goldenrod"][i]) bld_upright()
        translate([0, 0, bld_end_t + bld_len_clear / 2]) linear_extrude(building.x) translate(k * card_t * bld_n)
            polygon([for (c = [[0, 0.1], [building.y, 0.1], [building.y, card_t - 0.1], [0, card_t - 0.1]])
                bld_p(i) + c.x * bld_d + c.y * bld_n]);
}
// Behind the boats, a bin for the moose (35 x 30 x 11), the d8 and d12, and
// the cube: all setup-only. The d12 is 22 across and 18.8 tall, and the bin no
// wider than the boats leave: so thinner walls, and less of a chamfer each
// side of their top, to leave a rim between the two.
misc = [corner_x, front_y - boat.y];
misc_wall = 0.8;
misc_rim = 0.2;
misc_rows = [[-1, [["", -1, [16, 16], 0, "lightgray"]]]];
module misc_tray() let ($setup = true, $side_scoop = true, $wall = misc_wall, $rim = misc_rim) body() difference() {
    cbox(misc, boat_h, ct = misc_rim);
    bin_cuts(misc, boat_h, misc_rows);
}
// Vikings: a bin per player color, each a piece of its own, scooped up every
// wall, and all its color: no icon, the color says whose it is. The four sit
// two by two beside the setup buildings and the riser, as tall as those, so
// the whole of the back is level there: under the islands, and under the end
// of the big tiles.
vik = [inner.x - bld.x, back_y];
vik_bin = vik / 2;
vik_h = base_h;
vik_scoop = 10;
// A bin's volume, less what its four scoops fill in.
vik_in = vik_bin - 2 * [wall, wall];
echo(viking_bin_ml = (vik_in.x * vik_in.y * (vik_h - floor_t) - (1 - PI / 4) * vik_scoop * vik_scoop * 2 * (vik_in.x + vik_in.y)) / 1000);
module vik_bin(k) let ($all_scoop = true, $scoop_r = vik_scoop)
    bin_tray(str("viking ", vik_colors[k]), vik_bin, vik_h, [[-1, [["", -1, [13, 21], 0, vik_colors[k]]]]]);

function sum(v) = len(v) == 0 ? 0 : v[0] + sum([for (i = [1:1:len(v) - 1]) v[i]]);
function cumsum(v, i) = sum([for (j = [0:1:i - 1]) v[j]]);

function row_depths(rows, size) =
    let (fixed = sum([for (r = rows) r[0] > 0 ? r[0] : 0]),
         n = len([for (r = rows) if (r[0] < 0) 1]),
         fill = (size.y - $wall * (len(rows) + 1) - fixed) / max(1, n))
    [for (r = rows) r[0] > 0 ? r[0] : fill];

function bin_widths(bins, size) =
    let (fixed = sum([for (b = bins) b[1] > 0 ? b[1] : 0]),
         n = len([for (b = bins) if (b[1] < 0) 1]),
         fill = (size.x - $wall * (len(bins) + 1) - fixed) / max(1, n))
    [for (b = bins) b[1] > 0 ? b[1] : fill];

// Scoop up the front wall, leaving the tile room to lie flat behind it. With
// $back_scoop, the back wall gets the same scoop.
// With $scoop_fit too, the two scoops share the room the tile leaves.
// With $side_scoop, a bin's two scoops are up its left and right walls
// instead.
$back_scoop = false;
$scoop_fit = false;
$side_scoop = false;
// With $all_scoop, it's scooped up all four walls.
$all_scoop = false;
// A bin's rim is chamfered by $rim.
$rim = chamfer;
// With $scoop_r, every scoop is that radius instead.
$scoop_r = undef;
function scoop_for(d, fp) = min(scoop_max, max(scoop_min, (d - fp.y) / ($back_scoop && $scoop_fit ? 2 : 1)));
function scoop(w, d, fp) = [is_undef($scoop_r) ? scoop_for(d, fp) : $scoop_r, true];

// A 2D outline (children), c in from its edge at z = 0 and sloping out to it
// at z = c: a true chamfer, for an outline that isn't convex and so can't be
// hulled. With flip, the other way up. Its corners must be rounded by c or
// more.
module chamfered(c, flip = false) minkowski() {
    linear_extrude(eps) offset(r = -c) children();
    cylinder(r1 = flip ? c : 0, r2 = flip ? 0 : c, h = c, $fn = 24);
}
// A box with every outside edge chamfered: its top edges by ct, if that's not
// to be co.
module cbox(size, h, co = chamfer_out, cc = chamfer_corner, ct) {
    top = is_undef(ct) ? co : ct;
    module sh(d) offset(delta = cc, chamfer = true)
        translate([cc + d, cc + d])
        square([size.x - 2 * (cc + d), size.y - 2 * (cc + d)]);
    hull() {
        linear_extrude(eps) sh(co);
        translate([0, 0, co]) linear_extrude(h - co - top) sh(0);
        translate([0, 0, h - eps]) linear_extrude(eps) sh(top);
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
// rounded by the scoop radius s instead when s > r; the back one by sb.
module well(size, z0, h, s = 0, sb = 0, r = fillet_r) {
    sf = max(s, sb, r);
    // The floor edge at y = 0, at x: a ball, or a slice of the scoop.
    module edge(x, s) {
        if (s > r) intersection() {
            translate([x, s, z0 + s]) rotate([0, 90, 0])
                rotate_extrude($fn = 96) translate([s - r, 0]) circle(r, $fn = 24);
            translate([x - r - 1, -1, z0 - 1]) cube([2 * r + 2, s + 1, s + 1]);
        }
        else translate([x, r, z0 + r]) sphere(r, $fn = 24);
    }
    hull() {
        translate([0, 0, z0 + sf]) linear_extrude(h + 1 - z0 - sf) rrect(size, r);
        for (x = [r, size.x - r]) {
            edge(x, s);
            translate([0, size.y, 0]) mirror([0, 1, 0]) edge(x, sb);
        }
    }
}
// A well scooped up all four walls, [0, 0] to size, floor at z0, open past h:
// the scoops, of radius s, run round the corners on a ball of that radius,
// and from there the corners draw in to the rim's, rounded by r. A bin tray's
// are rounded by bowl_r: more than a square bin's corners, to read as a bowl.
bowl_r = 4;
module bowl(size, z0, h, s, r = bowl_r) hull() {
    translate([0, 0, h]) linear_extrude(1) rrect(size, r);
    for (x = [s, size.x - s], y = [s, size.y - s]) translate([x, y, z0 + s]) sphere(s, $fn = 96);
}
// The well filled 0.4 deep, for a floor color.
module floor_slab(size, z0, h, s = 0) intersection() {
    translate([0, 0, z0]) cube([size.x, size.y, 0.4]);
    well(size, z0, h, s);
}

// The standard pinch slot: an opening w wide down to z = bz in a wall h
// tall. The wall rounds over into it at the top, on a radius of top_r (so the
// opening is w + 2 * top_r wide at the rim), and its floor corners are
// filleted by fillet. The corner posts of the open trays are the same shape.
pinch_top_r = 4;
pinch_fillet = 3;
pinch_arc_n = 6;
// Its outline is a union of convex pieces, so a chamfer can be hulled a piece
// at a time: the body, then pinch_arc_n slices of each round-over.
function pinch_pieces() = 1 + 2 * pinch_arc_n;
module pinch_piece(i, w, bz, h, top_r = pinch_top_r, fillet = pinch_fillet) {
    top = h + 1;
    if (i == 0) hull() {
        for (sx = [-1, 1]) translate([sx * (w / 2 - fillet), bz + fillet]) circle(fillet, $fn = 32);
        translate([-w / 2, top - eps]) square([w, eps]);
    }
    else {
        k = (i - 1) % pinch_arc_n;
        sx = i - 1 < pinch_arc_n ? 1 : -1;
        p = [for (j = [k, k + 1]) let (a = 180 - 90 * j / pinch_arc_n)
            [sx * (w / 2 + top_r + top_r * cos(a)), h - top_r + top_r * sin(a)]];
        polygon([p[0], p[1], [p[1].x, top], [p[0].x, top]]);
    }
}
module pinch_2d(w, bz, h, top_r = pinch_top_r, fillet = pinch_fillet)
    for (i = [0:pinch_pieces() - 1]) pinch_piece(i, w, bz, h, top_r, fillet);
// A pinch slot through walls along y, centered on x = 0, from y0 to y1. faces
// are [y, dir] for every wall face it crosses, dir pointing into the
// material; each gets a chamfer of c.
module pinch_slot(w, bz, h, y0, y1, faces, top_r = pinch_top_r, fillet = pinch_fillet, c = chamfer_out) {
    xzy = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]];
    multmatrix(xzy) {
        translate([0, 0, y0 - eps]) linear_extrude(y1 - y0 + 2 * eps) pinch_2d(w, bz, h, top_r, fillet);
        for (f = faces, i = [0:pinch_pieces() - 1]) hull() {
            translate([0, 0, f[0] - eps]) linear_extrude(2 * eps) offset(r = c) pinch_piece(i, w, bz, h, top_r, fillet);
            translate([0, 0, f[0] + f[1] * c - eps]) linear_extrude(2 * eps) pinch_piece(i, w, bz, h, top_r, fillet);
        }
    }
}

// Eases a pinch slot into the well behind its wall, in pinch_slot's frame: the
// wall's face on the well is y = 0, the well in -y, its floor's top at fl and
// filleted into the wall by fillet_r. Every edge where the slot's sides meet
// the well's inside is chamfered by c: up the wall, round the end of the
// floor's fillet, and along the floor's edge for reach, if the floor is cut
// away under the slot (see floor_notch()).
// A point goes if it's within c of the slot and the well together: both are
// convex (the slot a piece at a time), so that's a hull of a few steps.
module slot_ease(w, bz, h, fl, reach, top_r = pinch_top_r, fillet = pinch_fillet, c = chamfer, n = 4) {
    xzy = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]];
    big = 2 * (w + h);
    // The well's section, as [y, z].
    module well_2d() hull() {
        translate([-big, fl + fillet_r]) square([big, big]);
        translate([-big, fl]) square([big - fillet_r, 1]);
        translate([-fillet_r, fl + fillet_r]) circle(fillet_r, $fn = 32);
    }
    for (j = [0:pinch_pieces() - 1]) hull() for (i = [0:n]) let (d = c * i / n, e = c - d) intersection() {
        multmatrix(xzy) translate([0, 0, -reach]) linear_extrude(reach + c + eps)
            offset(r = d) pinch_piece(j, w, bz, h, top_r, fillet);
        rotate([90, 0, 90]) linear_extrude(big, center = true) offset(r = e) well_2d();
    }
}

// A bin tray's wells, with their rim chamfers, to subtract from a body.
module bin_cuts(size, h, rows) {
    ds = row_depths(rows, size);
    for (ri = [0:len(rows) - 1]) {
        ws = bin_widths(rows[ri][1], size);
        for (bi = [0:len(ws) - 1])
            translate([$wall + cumsum(ws, bi) + bi * $wall, $wall + cumsum(ds, ri) + ri * $wall, 0]) {
                fp = rows[ri][1][bi][2];
                if ($all_scoop) bowl([ws[bi], ds[ri]], floor_t, h, scoop(ws[bi], ds[ri], fp)[0], bowl_r);
                else if ($side_scoop) {
                    sc = scoop(ds[ri], ws[bi], [fp.y, fp.x])[0];
                    multmatrix([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]]) well([ds[ri], ws[bi]], floor_t, h, sc, sc);
                }
                else {
                    sc = scoop(ws[bi], ds[ri], fp)[0];
                    b = rows[ri][1][bi];
                    well([ws[bi], ds[ri]], floor_t, h, sc, $back_scoop && !(len(b) > 6 && b[6]) ? sc : 0);
                }
                rim([ws[bi], ds[ri]], h, $rim, $all_scoop ? bowl_r : fillet_r);
            }
    }
}

// A bin tray's scoops, floor colors and icons; reports capacity.
// Runs children once per bin, with $b the bin, $pos its corner, $wd its
// [width, depth], $s its scoop radius, and $first / $last per axis.
module for_bins(size, rows) {
    ds = row_depths(rows, size);
    for (ri = [0:len(rows) - 1]) {
        bins = rows[ri][1];
        ws = bin_widths(bins, size);
        for (bi = [0:len(bins) - 1])
            let ($b = bins[bi], $wd = [ws[bi], ds[ri]],
                 $pos = [$wall + cumsum(ws, bi) + bi * $wall, $wall + cumsum(ds, ri) + ri * $wall],
                 $s = scoop(ws[bi], ds[ri], bins[bi][2])[0],
                 $first = [bi == 0, ri == 0], $last = [bi == len(bins) - 1, ri == len(rows) - 1])
                children();
    }
}

// Reports how full each bin is: its tiles' volume, their footprints taken as
// solid, over the well's, less what the scoops fill in.
module bin_check(name, size, h, rows) {
    for (ri = [0:len(rows) - 1]) for (w = bin_widths(rows[ri][1], size))
        assert(w > 0 && row_depths(rows, size)[ri] > 0, str(name, ": row ", ri, " doesn't fit"));
    for_bins(size, rows) if ($b[3] > 0) {
        scoops = ($back_scoop ? 2 : 1) * (1 - PI / 4) * $s * $s * $wd.x;
        fill = $b[3] * $b[2].x * $b[2].y * tile_t / ($wd.x * $wd.y * (h - floor_t) - scoops);
        echo(str(fill > max_fill ? "TIGHT " : "", name, " ", $b[0], ": ", round($wd.x), "x", round($wd.y),
                 ", ", $b[3], " tiles fill ", round(fill * 100), "%"));
    }
}

// Icons are inlaid icon_d deep, icon_top below the rim.
icon_d = 0.4;
icon_top = 2.5;
function icon_n(icon) = [max([for (c = icon[1]) c.x]) + 1, max([for (c = icon[1]) c.y]) + 1];
function icon_z(icon, h) = h - icon_top - (icon_n(icon).y * icon_cell + icon_line) / 2;
// The front row's icons, one per column, in the tray's outside front face.
module bin_front_icons(size, h, rows) for_bins(size, rows) if (len($b) > 5 && $first.y)
    translate([$pos.x + $wd.x / 2, icon_d, icon_z($b[5], h)])
        rotate([90, 0, 0]) linear_extrude(icon_d + eps) icon_2d($b[5]);
// For a single column of bins: each bin's icon behind the front one, inlaid
// in the front of the wall ahead of it (the back wall of the bin in front),
// to read from the front like the outside ones. With cut, it's the shape to
// cut from the body, which also runs out into the well: stopped at the wall's
// face, it would leave slivers of body over the icon.
module column_icons(size, h, rows, cut = false) {
    ds = row_depths(rows, size);
    w = bin_widths(rows[0][1], size)[0];
    for (ri = [1:1:len(rows) - 1]) {
        icon = rows[ri][1][0][5];
        // The bin in front, whose back wall it is.
        d = ds[ri - 1];
        sc = scoop(w, d, rows[ri - 1][1][0][2])[0];
        translate([$wall, $wall + cumsum(ds, ri - 1) + (ri - 1) * $wall, 0]) render() intersection() {
            difference() {
                translate([0, icon_d, 0]) well([w, d], floor_t, h, sc, $back_scoop ? sc : 0);
                if (!cut) well([w, d], floor_t, h, sc, $back_scoop ? sc : 0);
            }
            translate([w / 2, d + icon_d + 1, icon_z(icon, h)])
                rotate([90, 0, 0]) linear_extrude(sc + 2 + icon_d) icon_2d(icon);
        }
    }
}

// Paints children (a tray body) in its bins' colors: each bin owns its cell
// out to the middle of the walls around it, and to clip on the outside.
module bin_paint(size, rows, clip = [[-1, 1000], [-1, 1000]]) for_bins(size, rows) {
    lo = [for (k = [0:1]) $first[k] ? clip[k][0] : $pos[k] - $wall / 2];
    hi = [for (k = [0:1]) $last[k] ? clip[k][1] : $pos[k] + $wd[k] + $wall / 2];
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

// A bin tray: the body in its bins' colors, icons in black.
module bin_tray(name, size, h, rows) {
    bin_check(name, size, h, rows);
    bin_paint(size, rows) difference() {
        cbox(size, h);
        bin_cuts(size, h, rows);
        bin_front_icons(size, h, rows);
    }
    paint("black") bin_front_icons(size, h, rows);
}

function slice(v, a, b) = [for (i = [a:b - 1]) v[i]];
function slice_rows(rows, a, b) = [for (r = rows) [r[0], slice(r[1], a, b)]];
function tray_x(cols) = sum(cols) + (len(cols) + 1) * wall;

// Each long tray is two pieces to fit the 270 mm bed.
half_split = 4;
half_a = [tray_x(slice(half_cols, 0, half_split)), half.y];
half_b = [half.x - half_a.x, half.y];
half_b_tiles_x = tray_x(slice(half_cols, half_split, len(half_cols)));
module half_a() let ($back_scoop = true) bin_tray("half a", half_a, half_h, slice_rows(half_rows, 0, half_split));
// The money column shares the tile bins' last wall.
module half_b() {
    $back_scoop = true;
    // Every scoop the biggest, as the tile bins' are anyway: the 2x2 money's
    // would be less, for the room its tiles leave.
    $scoop_r = scoop_max;
    tiles = [half_b_tiles_x, half.y];
    mx = half_b_tiles_x - wall;
    money = [half_b.x - mx, half.y];
    tile_rows = slice_rows(half_rows, half_split, len(half_cols));
    bin_check("half b", tiles, half_h, tile_rows);
    bin_check("money", money, half_h, money_rows);
    module tray_body() difference() {
        cbox(half_b, half_h);
        bin_cuts(tiles, half_h, tile_rows);
        bin_front_icons(tiles, half_h, tile_rows);
        translate([mx, 0, 0]) {
            bin_cuts(money, half_h, money_rows);
            bin_front_icons(money, half_h, money_rows);
            column_icons(money, half_h, money_rows, true);
        }
    }
    // The shared wall splits down its middle.
    bin_paint(tiles, tile_rows, [[-1, half_b_tiles_x - wall / 2], [-1, 1000]]) tray_body();
    translate([mx, 0, 0]) bin_paint(money, money_rows, [[wall / 2, 1000], [-1, 1000]]) translate([-mx, 0, 0]) tray_body();
    paint("black") {
        bin_front_icons(tiles, half_h, tile_rows);
        translate([mx, 0, 0]) {
            bin_front_icons(money, half_h, money_rows);
            column_icons(money, half_h, money_rows);
        }
    }
}
module half_tray() {
    half_a();
    translate([half_a.x, 0, 0]) half_b();
}

module big_tray() {
    $back_scoop = true;
    $scoop_fit = true;
    in_h = tier_h - floor_t;
    // One radius for every bin, the biggest, like every other tray's. The flat
    // stacks fill their bins, so those are scooped at the front only: the back
    // stack lies flat against the square back wall, and the front one, the
    // shorter, up the scoop.
    let ($scoop_r = scoop_max) {
        for (ki = [0:len(big_kinds) - 1], ri = [0:len(big_rows) - 1]) {
            k = big_kinds[ki];
            bin = big_rows[ri][1][ki];
            d = row_depths(big_rows, big)[ri];
            sc = scoop(bin[1], d, bin[2])[0];
            if (k[2] == 0)
                echo(str("big ", bin[0], ": on edge, stack ", bin[3] * tile_t, " in ", round(d * 10) / 10, " deep"));
            else
                echo(str("big ", bin[0], ": flat, ", k[2], " stacks of ", ceil(bin[3] / k[2]) * tile_t, " in ", in_h,
                         " high; ", bin[2].y, " long in ", round(d * 10) / 10, ", ", round((d - sc) * 10) / 10,
                         " of it flat floor (front scoop ", sc, ")"));
        }
        bin_paint(big, big_rows) difference() {
            cbox(big, tier_h);
            bin_cuts(big, tier_h, big_rows);
            bin_front_icons(big, tier_h, big_rows);
        }
        paint("black") bin_front_icons(big, tier_h, big_rows);
    }
}

// The special tiles' boards: a pocket per tile, the forge tiles on their
// own board. Layout from pack_special.py.
special_h = special_floor + tilt_d + pocket_d;
special_others_x0 = special_forge_w + special_gap;
// As deep as the box, so they can't slide; the pockets are centered. The
// others' board takes what the forge's leaves of the box's length, so the
// layer is as long as the rest: its margin is a little over special_margin.
special_forge = [special_forge_w + 2 * special_margin, inner.y];
special_others = [inner.x - special_forge.x, inner.y];
assert(special_others.x >= special_size.x - special_others_x0 + 2 * special_margin, "the special boards are too long for the box");
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
// tilt_balance clear of the strip (so it rests flat). So most tiles tip from
// any side, a bar from either end.
tilt_min_cells = 2;
tilt_balance = 2;
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
// A board with a pocket for each of tiles, moved by at. The skin of each
// pocket's floor is its own color.
// corner_r rounds the board's corners, to leave room in the box's to get a
// finger under it.
module special_solid(size, tiles, at, corner_r = 0) render() difference() {
    if (corner_r > 0) hull() {
        // A circle per corner, so the radius can be half the board's width.
        for (x = [corner_r, size.x - corner_r], y = [corner_r, size.y - corner_r]) translate([x, y, 0]) {
            cylinder(r1 = corner_r - chamfer_out, r2 = corner_r, h = chamfer_out, $fn = 128);
            translate([0, 0, chamfer_out]) cylinder(r = corner_r, h = special_h - 2 * chamfer_out, $fn = 128);
            translate([0, 0, special_h - chamfer_out])
                cylinder(r1 = corner_r, r2 = corner_r - chamfer_out, h = chamfer_out, $fn = 128);
        }
    }
    else cbox(size, special_h);
    for (st = tiles) translate(at) {
        // Straight walls, so the tile has its full clearance all the way down.
        translate([0, 0, special_h - pocket_d]) linear_extrude(pocket_d + eps) pocket_2d(st);
        translate([0, 0, special_h - chamfer]) pocket_rim(st);
        translate([0, 0, special_h - pocket_d - tilt_d]) tilt_cut(st);
    }
}
// What's c_floor: under each pocket, floor_skin deep below the drops and the
// rest (the island), and all of the step between them.
module special_floors(tiles, at) {
    z0 = special_h - pocket_d - tilt_d - floor_skin;
    for (st = tiles) translate(at) difference() {
        translate([0, 0, z0]) linear_extrude(tilt_d + floor_skin) pocket_2d(st);
        translate([0, 0, z0 - eps]) linear_extrude(tilt_d) difference() {
            pocket_2d(st);
            tilt_2d(st);
        }
    }
}
// Children are cut from the body, for inlays.
module special_plate(size, tiles, at, corner_r = 0) {
    body() render() difference() {
        special_solid(size, tiles, at, corner_r);
        special_floors(tiles, at);
        children();
    }
    paint(c_floor) render() intersection() {
        special_solid(size, tiles, at, corner_r);
        special_floors(tiles, at);
    }
}
module special_board(section) {
    size = section == "forge" ? special_forge : special_others;
    x0 = section == "forge" ? 0 : special_others_x0;
    // The section's width: it's centered on its board.
    w = section == "forge" ? special_forge_w : special_size.x - x0;
    special_plate(size, [for (st = special_tiles) if (st[0] == section) st],
                  [(size.x - w) / 2 - x0, (size.y - special_size.y) / 2, 0],
                  special_corner_r)
        if (section == "forge") for (id = ["black", "orange"]) forge_icon(id, eps);
    if (section == "forge") {
        paint("black") forge_icon("black");
        paint(c_forge) forge_icon("orange");
    }
}
// One color of forge.svg (id "black" or "orange"), let into the forge
// board's top face. At dpi 25.4 an SVG unit is 1 mm, the viewBox's bottom
// left the origin of x; the icon spans [5.67, -38.23] to [168, 100.81].
module forge_icon(id, above = 0) {
    s = forge_icon_w / 162.33;
    translate([forge_icon_at.x, forge_icon_at.y, special_h - forge_icon_d])
        linear_extrude(forge_icon_d + above, convexity = 6)
            rotate(forge_icon_rot) scale(s) translate([-86.83, -31.29]) import("forge.svg", id = id, dpi = 25.4);
}
// A few doubtful tiles on a small board, to try the fit and the tip.
module special_test() {
    m = special_margin;
    tiles = [for (t = special_test_tiles) let (st = special_tiles[t[0]]) [st[0], st[1], t[1]]];
    size = [for (k = [0, 1]) max([for (st = tiles) st[2][k] + tile_n(st)[k] * unit]) + 2 * pocket_clear + 2 * m];
    special_plate(size, tiles, [m + pocket_clear, m + pocket_clear, 0]);
}
module special_boards() {
    special_board("forge");
    translate([special_forge.x, 0, 0]) special_board("others");
}

// A card tray (see deck_trays), its corner at the origin, with deck_cut cut
// out of its length (its y): a slice from where its section is the same all
// along, the back part moved up to the front one.
module deck_whole(i) let (d = deck_trays[i]) translate(-d[2]) import(d[1], convexity = 4);
// At each end it gets a lip across the floor, deck_lip high over it, from side
// wall to side wall: the trays come with only the floor's edge there, and the
// side walls' ends, for the next thing in the box to sit against.
// render(): the preview draws the cut STL's faces striped.
deck_lip = 4;
module deck_tray(i) let (d = deck_trays[i], $setup = d[4], c = deck_cut[i], y0 = deck_cut_at * d[3].y,
                         len = d[3].y - c, h = deck_floor + deck_lip, r = chamfer)
    body() render(convexity = 6) union() {
        intersection() {
            deck_whole(i);
            translate([-1, -1, -1]) cube([d[3].x + 2, y0 + 1, d[3].z + 2]);
        }
        translate([0, -c, 0]) intersection() {
            deck_whole(i);
            translate([-1, y0 + c, -1]) cube([d[3].x + 2, d[3].y, d[3].z + 2]);
        }
        // The lips, their top edges rounded, and trimmed to the tray's own
        // outside: its corners and bottom edges are rounded over, and a
        // square bar would stand proud of them.
        // union(): a bare for is a child apiece, under generate.py's
        // lazy-union, and the two lips have nothing in common.
        intersection() {
            union() for (y = [0, len - wall]) translate([0, y, 0]) rotate([90, 0, 90]) linear_extrude(d[3].x) hull() {
                square([wall, h - r]);
                for (x = [r, wall - r]) translate([x, h - r]) circle(r, $fn = 24);
            }
            hull() {
                intersection() {
                    deck_whole(i);
                    translate([-1, -1, -1]) cube([d[3].x + 2, y0 + 1, d[3].z + 2]);
                }
                translate([0, -c, 0]) intersection() {
                    deck_whole(i);
                    translate([-1, y0 + c, -1]) cube([d[3].x + 2, d[3].y, d[3].z + 2]);
                }
            }
        }
    }
// In a row along the front, each deck running along x.
module deck_holders() for (i = [0:len(deck_trays) - 1]) {
    x = sum([for (j = [0:1:i - 1]) deck_len(j)]);
    translate([x + deck_len(i), 0, 0]) rotate(90) deck_tray(i);
}

// The board stack, bottom to top, one card_t layer each: [label, pos, size,
// color], within the box. Smallest at the bottom, the player boards, the
// biggest, on top: so the frame can be thick round the small ones, under the
// player boards' edges.
overview = [224, 96];
player_board = [299, 190];
action_board = [266, 183]; // the biggest of its layers
board_stack = [
    [["round overview", [(box.x - overview.x) / 2, (box.y - overview.y) / 2], overview, "wheat"]],
    for (w = [134, 162, action_board.y]) [["action board", [(box.x - action_board.x) / 2, (box.y - w) / 2], [action_board.x, w], "tan"]],
    for (i = [0:3]) [["player board", [(box.x - player_board.x) / 2, (box.y - player_board.y) / 2], player_board, "burlywood"]],
];
// The layers under the player boards.
boards_under = 4;
assert(len(board_stack) == board_layers, str("board stack has ", len(board_stack), " layers"));
module board_stack(explode_layers = 0) {
    for (i = [0:len(board_stack) - 1]) translate([0, 0, i * (card_t + explode_layers)])
        for (pc = board_stack[i]) translate(pc[1]) color(pc[3]) cube([pc[2].x, pc[2].y, card_t - 0.1]);
}
// The frame round the board stack: it fills the box round the player boards,
// so they can't slide, and is the stack's height, for what's above to sit on.
// Two halves, one per end of the box, each a C; print two.
// Under the player boards it's a shelf, in to the action boards: the boards'
// edges rest on it, and it stiffens the thin wall round them.
frame_clear = 1.5;
frame_half = [inner.x / 2, inner.y];
frame_shelf_h = boards_under * card_t;
module frame_half() let ($setup = true) body() difference() {
    cbox(frame_half, board_stack_h);
    for (c = [[player_board, frame_shelf_h], [action_board, -1]]) {
        in = c[0] + [frame_clear, frame_clear];
        translate([(inner.x - in.x) / 2, (frame_half.y - in.y) / 2, c[1]]) cube([in.x, in.y, board_stack_h + 2]);
    }
    // The shelf's inside top edge.
    in = action_board + [frame_clear, frame_clear];
    translate([(inner.x - in.x) / 2, (frame_half.y - in.y) / 2, frame_shelf_h - chamfer_out]) hull() {
        linear_extrude(eps) square(in);
        translate([-chamfer_out, -chamfer_out, chamfer_out]) linear_extrude(eps) square(in + 2 * [chamfer_out, chamfer_out]);
    }
    // Finger detents, one in each long side: round holes down through the
    // wall and the shelf, to get a fingertip under the player boards' edge.
    for (m = [0, 1]) translate([frame_detent_x, m * frame_half.y, 0]) mirror([0, m, 0])
        translate([0, frame_detent_skin + frame_detent_r, 0]) {
            translate([0, 0, -1]) cylinder(r = frame_detent_r, h = board_stack_h + 2);
            // Its rims: bottom, top, and the shelf's, inside the boards' well.
            translate([0, 0, -eps]) cylinder(r1 = frame_detent_r + chamfer_out, r2 = frame_detent_r, h = chamfer_out);
            translate([0, 0, board_stack_h - chamfer_out]) cylinder(r1 = frame_detent_r, r2 = frame_detent_r + chamfer_out, h = chamfer_out + eps);
            intersection() {
                translate([0, 0, frame_shelf_h - chamfer_out]) cylinder(r1 = frame_detent_r, r2 = frame_detent_r + chamfer_out, h = chamfer_out + eps);
                translate([-frame_detent_r - 1, frame_side - frame_detent_skin - frame_detent_r, 0]) cube([2 * frame_detent_r + 2, 2 * frame_detent_r, board_stack_h]);
            }
        }
}
// The long sides' thickness, round the player boards.
frame_side = (frame_half.y - player_board.y - frame_clear) / 2;
// The detents: their radius, the wall left outside them, and where along the
// half they sit.
frame_detent_r = 14;
frame_detent_skin = 3;
frame_detent_x = frame_half.x / 2;
assert(frame_detent_skin + 2 * frame_detent_r > frame_side + (player_board.y - action_board.y) / 2, "detent doesn't reach through the shelf");
module board_frame() {
    frame_half();
    translate([inner.x, 0, 0]) mirror([1, 0, 0]) frame_half();
}

function show(n) = layer == 0 || (layer_only ? n == layer : n <= layer);
module assembly() {
    if (explode == 0 && layer == 0) color("white", 0.15) translate([-1, -1, 0]) difference() {
        cube([box.x + 2, box.y + 2, box.z]);
        translate([1, 1, -eps]) cube([box.x, box.y, box.z + 1]);
    }
    // 1: the boards, in their frame, and the rulebooks on them.
    zb = board_stack_h + board_layers * explode / 6 + explode / 2;
    if (show(1)) {
        translate([box_clear / 2, box_clear / 2, 0]) board_frame();
        board_stack(explode / 6);
        translate([(box.x - rulebooks.x) / 2, (box.y - rulebooks.y) / 2, zb]) color("ivory") cube(rulebooks);
    }
    z2 = zb + rulebooks.z + explode;
    if (show(2)) for (i = [0, 1]) translate([box_clear / 2, box_clear / 2 + i * half.y, z2]) half_tray();
    z3 = z2 + half_h + explode;
    // Turned half round: the forge board at the right, its icon at the back.
    if (show(3)) translate([(box.x + special_forge.x + special_others.x) / 2, box_clear / 2 + special_forge.y, z3])
        rotate(180) special_boards();
    z4 = z3 + special_h + explode;
    // 4 to 6: the columns' bottom, middle and top trays.
    e = explode;
    translate([box_clear / 2, box_clear / 2, z4]) {
        if (show(4)) {
            strips_tray();
            translate([decks_x, 0, 0]) boat_tray();
            translate([decks_x, boat.y, 0]) misc_tray();
            translate([0, front_y, 0]) {
                setup_buildings_tray();
                translate([0, bld.y, 0]) riser();
                for (k = [0:3]) translate([bld.x + (k % 2) * vik_bin.x, floor(k / 2) * vik_bin.y, 0]) vik_bin(k);
            }
        }
        if (show(5)) translate([0, 0, e]) {
            translate([0, 0, base_h]) deck_holders();
            translate([0, front_y, base_h]) big_tray();
            translate([big.x, front_y, vik_h]) islands_tray();
        }
        if (show(6)) translate([0, 0, 2 * e]) {
            translate([decks_x, 0, boat_h]) {
                vp_tray();
                translate([vp.x, 0, 0]) spacer();
            }
            translate([0, front_y, base_h + tier_h]) {
                wood_tray();
                // Turned, its low side at the end of the box.
                translate([inner.x, 0, 0]) rotate(90) buildings_capped();
            }
        }
    }
}

total_h = rulebooks.z + board_stack_h + half_h + special_h + zone_h;
echo(total_h = total_h, over_box = total_h - box.z);

bed = 270;
for (s = [["half a", half_a], ["half b", half_b], ["big", big],
          ["boats", boat], ["vp", vp], for (d = deck_trays) [d[0], d[3]], ["wood", wood], ["viking bin", vik_bin],
          ["islands", islands], ["setup buildings", bld], ["buildings", bld_tray], ["misc", misc], ["strips", strips],
          ["riser", riser], ["spacer", spacer],
          ["special forge", special_forge], ["special others", special_others], ["frame half", frame_half]])
    assert(max(s[1]) <= bed, str(s[0], " is too big for the bed: ", s[1]));

module the_part() {
    if (part == "half") half_tray();
    else if (part == "half_a") half_a();
    else if (part == "half_b") half_b();
    else if (part == "big") big_tray();
    else if (part == "boats") boat_tray();
    else if (part == "vp") vp_tray();
    else if (part == "islands") islands_tray();
    // As printed: standing on its end wall.
    else if (part == "buildings") rotate([0, -90, 0]) buildings_tray();
    else if (part == "buildings_cap") buildings_cap();
    else if (part == "buildings_demo") buildings_demo();
    else if (part == "misc") misc_tray();
    else if (part == "setup_buildings") setup_buildings_tray();
    else if (part == "strips") strips_tray();
    else if (part == "riser") riser();
    else if (part == "spacer") spacer();
    else if (part == "frame") board_frame();
    else if (part == "frame_half") frame_half();
    else if (part == "wood") wood_tray();
    else if (part == "vikings_red") vik_bin(0);
    else if (part == "vikings_blue") vik_bin(1);
    else if (part == "vikings_yellow") vik_bin(2);
    else if (part == "vikings_black") vik_bin(3);
    else if (part == "special") special_boards();
    else if (part == "special_forge") special_board("forge");
    else if (part == "special_others") special_board("others");
    else if (part == "special_test") special_test();
    else if (part == "decks") deck_holders();
    else if (part == "deck_setup") deck_tray(0);
    else if (part == "deck_occupations") deck_tray(1);
    else if (part == "deck_weapons") deck_tray(2);
}
// The open trays' floors are thick, and only thin posts go on above them: where
// a floor's solid top layers end, they push a ridge out into the posts. Less
// so with the outside wall drawn first.
open_tray_parts = ["islands", "setup_buildings"];
function has(list, x) = len([for (p = list) if (p == x) 1]) > 0;
orca([
    if (has(open_tray_parts, part)) orca_wall_sequence("outer wall/inner wall"),
    // Across a slot cut down to the bed Orca travels without retracting, after
    // infill and inner walls, and leaves a thread each time. It's a setting of
    // the whole print, so every part has it, for the plates to.
    orca_setting("reduce_infill_retraction", 0),
]);
// Every color the parts use. New colors go last, so a saved Orca project's
// objects keep their order.
// Each once: black is a viking color too.
all_colors = concat([c_game, c_setup], vik_colors, ["black", c_floor, c_forge]);
print_colors = [for (i = [0:len(all_colors) - 1]) if (search([all_colors[i]], all_colors)[0] == i) all_colors[i]];
if (part == "assembly") assembly();
else if (part == "boards") board_stack(4);
else for (c = print_colors) let ($only = c) {
    echo(color = c, piece = piece_name(c), filament = filament_name(c));
    the_part();
}
// The filament a color stands for: the preview's colors aren't the real ones.
function filament_name(c) =
    c == c_game ? "main" : c == c_setup ? "setup" : c == c_floor ? "pocket floor" : c == c_forge ? "orange" : c;
// What a color is, in the part: for Orca's list of its pieces.
function piece_name(c) =
    c == c_game || c == c_setup ? "body"
    : c == c_floor ? "pocket floors"
    : c == c_forge ? "tongs' jaws and rock"
    : c != "black" ? str(c, " bin")
    : part == "vikings_black" ? "black bin"
    : part == "special_forge" ? "tongs' handles"
    : "icons";

