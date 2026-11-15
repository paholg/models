// Pieces: what a print is made of, as the slicer sees it.
//
//   use <../../lib/orca.scad>
//   use <../../lib/piece.scad>
//   piece("lid", [orca_bottom_pattern("concentric")]) color("green") lid();
//
// A piece is a part in Orca, with a name and, if it likes, slicer settings of
// its own: a list of them, from orca.scad (python/generate.py makes the
// projects). Draw every solid of a print inside one; they can be anywhere,
// in a module as well as at the top of the file, but not inside each other.
// Either mistake stops the export: a solid in no piece would be in all of them.
//
// Orca keeps some settings for a whole object, not a part: a layer height, a
// seam's place, a brim. A piece with one of those becomes an object of its
// own, beside the object of everything else, along with any that share its
// name.
//
// OpenSCAD has no way to hand over one piece of what it draws, or to name
// it. So a piece says what it is in the log, and generate.py asks for each in
// turn, by setting $only: then every other piece draws nothing.
//
// Pieces that share a name and settings come out together. Give them
// different colors and each is still a part of its own, so long as they are
// separate statements at the top of the file; drawn inside a module they are
// one solid, and want names of their own.
//
// $piece_prefix goes before the names of the pieces drawn under it, to tell
// apart those of a module drawn more than once.

use <orca.scad>

module piece(name, settings = []) {
  assert(name != "", "a piece wants a name");
  outer = is_undef($in_piece) ? "" : $in_piece;
  assert(outer == "", str("piece ", name, " is inside piece ", outer, ", and would never be drawn"));
  full = is_undef($piece_prefix) || $piece_prefix == "" ? name : str($piece_prefix, " ", name);
  flat = orca_flat(settings);
  echo(piece = full, orca = flat);
  // Asked for as they are written in the log.
  if (is_undef($only) || $only == [full, str(flat)]) {
    $in_piece = full;
    children();
  }
}
