// Upright card box for The Fox in the Forest Deluxe: the 61 standard-size
// cards in sleeves, standing on end, with the score tracker (score.scad)
// behind them, and a lift-off lid held on by magnets.
//
// The box is lib/card_box.scad's, which has how it's made and printed. This
// file is what goes in it, its colors, and its art.

// export: panels simple seam magnets

use <../../lib/card_box.scad>

/* [Output] */
part = "closed"; // [closed, open, exploded, panels, simple, seam, magnets]
// Show closed, open and exploded as the one-piece box, not the panels.
whole = false;

/* [Contents] */
// Dragon Shield Matte standard sleeve, outside, at its largest: width, length.
sleeve = [66.5, 92.5];
// 61 sleeved cards, as they stand in a printed box: they filled a 47 mm
// cavity, a little loose. (Counted up at ~0.61 mm a card they'd be 37.5.)
deck = 46.5;
// The score tracker, rupees and all (score.scad: top_h + rupee_lift +
// rupee_t).
tracker = 9.2;

/* [Colors] */
box_color = "forestgreen";
art_color = "yellow";

/* [Fox] */
// Fox silhouette, in the body's front, below the seam.
fox_h = 50;
// Center height of the fox on the front.
fox_z = 30;
// Its outline's center, right of the front's: the fox's weight is ~0.9 mm left
// of its outline's center, and it looked left of center in print.
fox_x = 1;

/* [Forest] */
// Forest entrance, in the body's back, stretched to fill it up to the seam.
// Left clear around it, to the back's edges and the seam; 0 is full bleed.
forest_margin = 2;

/* [Logo] */
// Title traced from the Deluxe box front, in the lid top.
logo_w = 60;

module fox() {
  translate([fox_x, fox_z]) resize([0, fox_h], auto = true) import("fox.svg", center = true);
}

module forest() {
  h = $cb_seam[1];
  translate([0, h / 2]) resize([$cb_size.x - 2 * forest_margin, h - 2 * forest_margin])
    import("forest.svg", center = true);
}

module logo() {
  resize([logo_w, 0], auto = true) import("logo.svg", center = true);
}

card_box(part, whole, sleeve = sleeve, stack = deck + tracker, box_color = box_color, art_color = art_color,
         front_art = "fox", front_art_pattern = "octagramspiral",
         back_art = "forest", back_art_pattern = "archimedeanchords", top_art = "logo") {
  fox();
  forest();
  logo();
}
