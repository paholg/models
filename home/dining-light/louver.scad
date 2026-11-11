// Honeycomb louver for the down-facing side of the dining table light.
//
// x is along the light, y is across it, z is up (into the light). Printed as
// modeled. The honeycomb sits up inside the light; flat tabs at the bottom
// reach out under the wood sides and take a screw each, driven up from below.

// export: print

/* [Output] */
part = "print"; // [print]

/* [Light] */
// Interior width of the prism: 4 15/16 in.
interior_w = 125.4;
// Total side-to-side slop.
fit_clearance = 0.6;
length = 265;

/* [Honeycomb] */
// Cell opening, across flats. Flats face across the light, so this is the
// tighter direction; along the light the cutoff is about 4 degrees wider.
cell = 10;
// Louver depth. Cutoff from straight down is atan(cell / depth). The light is
// 50 in above a 37 in wide table: the table edge is 20 degrees out, a seated
// eye roughly 31, so aim for about 30.
depth = 17;
wall = 0.8;
// Cells in the middle of the louver are stretched this much along the light,
// to let more light through. Shielding across the table is unchanged; only
// people sitting in line with the light lose some. 1 = regular hexagons.
stretch = 2;
// Regular cells are kept for this far in from each end. 0 for this test piece;
// the full-length light will want regular cells at its two ends.
end_len = 0;
// Length over which the stretch eases in.
ramp_len = 0;

/* [Frame] */
rail_t = 3;
end_t = 1.2;

/* [Tabs] */
// Flat tabs stick out under the bottom edge of the wood sides; screws go up
// through them into the wood.
tabs_per_side = 3;
tab_w = 16;
tab_t = 3;
// Thickness of the wood sides: 3/4 in. The screw is centered in it.
side_t = 19;
// Clearance for a #6 / 3.5 mm wood screw.
screw_d = 4;
// Tab center to the end of the louver, for the outermost tabs.
tab_inset = 25;

width = interior_w - fit_clearance;
pitch = cell + wall;

echo(str("cutoff across flats: ", atan(cell / depth), " deg from straight down"));
echo(str("cutoff across corners: ", atan(cell * 2 / sqrt(3) / depth), " deg"));

// The hex grid is laid out unstretched along u, then mapped to x: stretched
// in the middle, eased over the ramp, unstretched at the ends.
mid_x = max(0, length / 2 - end_len - ramp_len);
mid_u = mid_x / stretch;
ramp_u = ramp_len * 2 / (stretch + 1);

function warp(u) =
    let (a = abs(u), t = a - mid_u)
    sign(u) * (
        a <= mid_u ? stretch * a
        : t <= ramp_u ? mid_x + stretch * t - (stretch - 1) * t * t / (2 * ramp_u)
        : mid_x + ramp_len + t - ramp_u);

module hex_holes() {
    // Flats face +-y, columns step along u.
    r = pitch / sqrt(3);
    du = pitch * sqrt(3) / 2;
    nu = ceil((mid_u + ramp_u + end_len) / du) + 1;
    ny = ceil(width / 2 / pitch) + 1;
    for (i = [-nu:nu], j = [-ny:ny]) {
        cu = i * du;
        cy = (j + (i % 2 == 0 ? 0 : 0.5)) * pitch;
        offset(delta = -wall / 2)
            polygon([for (k = [0:5]) [warp(cu + r * cos(60 * k)), cy + r * sin(60 * k)]]);
    }
}

module honeycomb() {
    linear_extrude(depth) {
        difference() {
            square([length, width], center = true);
            intersection() {
                hex_holes();
                square([length - 2 * end_t, width - 2 * rail_t], center = true);
            }
        }
    }
}

module tab() {
    // Centered on x, reaching out in -y from the wall's inside face at y = 0.
    screw_y = -side_t / 2;
    linear_extrude(tab_t) difference() {
        hull() {
            translate([-tab_w / 2, 0]) square([tab_w, fit_clearance / 2 + 0.01]);
            translate([0, screw_y]) circle(d = tab_w, $fn = 48);
        }
        translate([0, screw_y]) circle(d = screw_d, $fn = 32);
    }
}

module tabs() {
    span = length - 2 * tab_inset;
    for (side = [0, 1]) mirror([0, side, 0])
        for (k = [0:tabs_per_side - 1])
            translate([-span / 2 + k * span / max(1, tabs_per_side - 1), -interior_w / 2, 0])
                tab();
}

module louver() {
    honeycomb();
    tabs();
}

if (part == "print") louver();
