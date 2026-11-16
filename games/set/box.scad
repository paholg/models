// Upright card box for SET: the 81 cards standing on end, with a lift-off
// lid held on by magnets.
//
// The box is lib/card_box.scad's, which has how it's made and printed. This
// file is what goes in it, its colors, and its art: three cards on the front,
// and the logo in the lid's top.
//
// Five colors, so the body and the lid print apart: the body in purple,
// white, green and red, the lid in lavender, purple and white.

// export: body lid

use <../../lib/card_box.scad>

/* [Output] */
part = "closed"; // [closed, open, exploded, panels, body, lid]

/* [Contents] */
// TODO: measure. A card, in its sleeve if it has one, at its largest: width,
// length. (A bare SET card is 57 x 89.)
sleeve = [66.5, 92.5];
// TODO: measure. The 81 cards, as they stand in the box.
deck = 50;

/* [Colors] */
box_color = "purple";
lid_color = "lavender";
card_color = "white";

/* [Cards] */
// A card on the front: its width. Its length is as a real card's.
card_w = 19;
card_r = 1.6;
// Between cards.
card_gap = 2.5;
// The row of them leans this far, counter-clockwise.
cards_lean = 12;
// The row's center, as a share of the front's height below the seam. Low
// enough to keep the cards off the magnets' pockets, 10 mm under the seam,
// where the wall is too thin for an inlay.
cards_at = 0.43;
// The symbols, as measured off a picture of the cards, in card widths: each
// one's size, along the card's width and across, and from one to the next.
diamond_size = [0.683, 0.354];
oval_size = [0.659, 0.311];
squiggle_size = [0.634, 0.323];
symbol_pitch = 0.442;
// The line an open or shaded symbol is drawn in.
symbol_line = 0.8;
// A shaded symbol's stripes: their width, and from one to the next.
shade = [0.45, 0.9];

/* [Logo] */
// Across the lid's top, all of it.
logo_w = 62;
// What the letters are set in.
logo_font = "TeX Gyre Termes:style=Bold";
logo_s_font = "TeX Gyre Termes:style=Bold Italic";

$fn = 48;

/* The cards. Each is drawn upright at the origin, its symbols lying across
   it, one above the next. */

card = [card_w, card_w * 89 / 57];

module diamond() {
  d = card_w * diamond_size;
  polygon([[-d.x / 2, 0], [0, -d.y / 2], [d.x / 2, 0], [0, d.y / 2]]);
}

module oval() {
  d = card_w * oval_size;
  hull() for (s = [-1, 1]) translate([s * (d.x - d.y) / 2, 0]) circle(d = d.y);
}

// Traced from the same picture (squiggle.svg).
module squiggle() {
  resize(card_w * squiggle_size) import("squiggle.svg", center = true);
}

// Its outline alone.
module open() {
  difference() {
    children();
    offset(delta = -symbol_line) children();
  }
}

// Its outline, and stripes across it.
module shaded() {
  open() children();
  intersection() {
    children();
    // Evenly either side of its middle. As one: a loop's turns are otherwise
    // each intersected with the rest, under lazy-union, leaving nothing.
    n = floor(card.x / 2 / shade[1]);
    union() for (k = [-n : n]) translate([k * shade[1], 0]) square([shade[0], card.x], center = true);
  }
}

// n of a symbol, as they go on a card.
module symbols(n) {
  for (i = [0 : n - 1]) translate([0, (i - (n - 1) / 2) * symbol_pitch * card_w]) children();
}

// The cards' places, in a leaning row under the seam: all of them, or one.
// $card_i is which.
module cards_row(only) {
  translate([0, cards_at * $cb_seam[0]]) rotate(cards_lean)
    for (i = [0 : 2]) if (is_undef(only) || i == only) translate([(i - 1) * (card.x + card_gap), 0]) {
      $card_i = i;
      children();
    }
}

module card_blank() {
  offset(card_r) square([card.x - 2 * card_r, card.y - 2 * card_r], center = true);
}

// The front, a layer at a time: the cards themselves, then what's on them.
// The open squiggle is the box showing through its card.
module cards() {
  if ($cb_art == "cards") cards_row() difference() {
    card_blank();
    if ($card_i == 2) open() squiggle();
  }
  else if ($cb_art == "diamonds") cards_row(0) symbols(3) diamond();
  else if ($cb_art == "ovals") cards_row(1) symbols(2) shaded() oval();
}

/* The logo: for each letter a white tile, edged in purple, in front of a
   purple one and one striped purple and white, each up and to the right of the last. */

// A tile's side, with the row of them logo_w across.
tile = logo_w / (2 * 1.4 + 1.44);
tile_size = [tile, 0.88 * tile];
tile_pitch = 1.4 * tile;
tile_edge = 0.06 * tile;
// The tiles behind: how far each is from the front one.
tile_mid = [0.22 * tile, 0.16 * tile];
tile_far = [0.44 * tile, 0.3 * tile];
tile_stripes = 8;

module tile_at(i) {
  translate([(i - 1) * tile_pitch - tile_far.x / 2, -tile_far.y / 2]) children();
}

module letter(i) {
  if (i == 0)
    translate([-0.06 * tile, -0.13 * tile])
      text("S", size = 1.12 * tile, font = logo_s_font, halign = "center", valign = "center");
  else text("SET"[i], size = 0.58 * tile, font = logo_font, halign = "center", valign = "center");
}

// The striped tile's bars.
module tile_bars() {
  pitch = tile_size.y / tile_stripes;
  for (k = [0 : tile_stripes - 1]) translate([-tile_size.x / 2, -tile_size.y / 2 + k * pitch])
    square([tile_size.x, pitch / 2]);
}

module logo() {
  if ($cb_art == "logo") for (i = [0 : 2]) tile_at(i) {
    // Striped: a frame, and bars across it.
    translate(tile_far) {
      difference() {
        square(tile_size, center = true);
        offset(delta = -tile_edge) square(tile_size, center = true);
      }
      tile_bars();
    }
    translate(tile_mid) square(tile_size, center = true);
    // The front tile's edge, and its letter, through the white.
    offset(delta = tile_edge) square(tile_size, center = true);
    letter(i);
  } else {
    for (i = [0 : 2]) tile_at(i) difference() {
      square(tile_size, center = true);
      letter(i);
    }
    // Between the striped tiles' bars, where they show past the tiles in
    // front of them: their own, and the next letter's.
    difference() {
      for (i = [0 : 2]) tile_at(i) translate(tile_far) difference() {
        offset(delta = -tile_edge) square(tile_size, center = true);
        tile_bars();
      }
      for (i = [0 : 2]) tile_at(i) {
        translate(tile_mid) square(tile_size, center = true);
        offset(delta = tile_edge) square(tile_size, center = true);
        letter(i);
      }
    }
  }
}

card_box(part, sleeve = sleeve, stack = deck, box_color = box_color, lid_color = lid_color,
         front_art = [["cards", card_color], ["diamonds", "green"], ["ovals", "red"]],
         front_art_turn = cards_lean,
         top_art = [["logo", box_color], ["logo white", "white"]]) {
  cards();
  square(0);
  logo();
}
