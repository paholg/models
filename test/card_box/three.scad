// Three card boxes in one file: each has a name, which goes before its
// pieces', and its own size.

// export: simple

use <../../lib/card_box.scad>

part = "closed"; // [closed, open, exploded, panels, simple]

decks = [["thin", 20], ["mid", 34], ["fat", 52]];

for (i = [0 : 2]) translate([i * 170, 0, 0])
  card_box(part, whole = true, name = decks[i][0], stack = decks[i][1] + 2 * i, front_art = "dot")
    translate([0, 30]) circle(8 + 2 * i);
