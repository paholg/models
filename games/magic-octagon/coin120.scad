// The coin of coin.scad with its arrows a third of a turn apart, not a
// quarter. Two shapes: round; and round with a reeded edge, which has a bump
// every 30 degrees, so that each arrow points at one.
//
// The halves glue as coin.scad's do, and only go together one way.

// export: print

use <coin.scad>
use <../../lib/piece.scad>

/* [Output] */
// `print` is one of each shape; the others show `shape`.
part = "assembled"; // [assembled, exploded, print]
shape = "round"; // [round, knurled]

/* [Hidden] */
$fn = 64;
shapes = ["round", "knurled"];
$shape = shape;
$bumps = 12;
// The holes are 1.5 deep, which leaves little under an arrow's inlay: here
// they are clear of both arrows.
$pin_a = 90;

// In each half's own frame; the top half is flipped over the x axis.
angles = [0, 120];
c_half = coin_colors()[0];
c_arrow = coin_colors()[1];

if (part == "print") {
  for (row = [0:len(shapes) - 1]) {
    $shape = shapes[row];
    $piece_prefix = $shape;
    for (i = [0, 1]) {
      piece(str("half ", i), half_settings($shape))
        color(c_half[i]) bed(i, row) half(angles[i]);
      piece(str("arrow ", i), arrow_settings(angles[i]))
        color(c_arrow[i]) bed(i, row) arrow(angles[i]);
    }
  }
} else {
  e = part == "exploded" ? 6 : 0;
  for (i = [0, 1]) {
    color(c_half[i]) place(i, e) half(angles[i]);
    color(c_arrow[i]) place(i, e) arrow(angles[i]);
  }
}
