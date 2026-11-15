// Pieces: what a print is made of, as the slicer sees it.
//
//   use <../../lib/piece.scad>
//   piece("lid", "bottom_surface_pattern=concentric") color("green") lid();
//
// A piece is a part in Orca, with a name and, if it likes, slicer settings of
// its own, written like a `// orca:` line (see python/generate.py, which makes
// the projects). Draw every solid of a print inside one; they can be anywhere,
// in a module as well as at the top of the file, but not inside each other.
// Either mistake stops the export: a solid in no piece would be in all of them.
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

module piece(name, orca = "") {
  assert(name != "", "a piece wants a name");
  outer = is_undef($in_piece) ? "" : $in_piece;
  assert(outer == "", str("piece ", name, " is inside piece ", outer, ", and would never be drawn"));
  full = is_undef($piece_prefix) || $piece_prefix == "" ? name : str($piece_prefix, " ", name);
  echo(piece = full, orca = orca);
  if (is_undef($only) || $only == [full, orca]) {
    $in_piece = full;
    children();
  }
}

// Settings for a piece: the pattern its outside face prints in, on the bed.
function piece_bottom(pattern) = str("bottom_surface_pattern=", pattern);
// Monotonic lines at angle a on the bed, from +x.
function piece_lines(a) = str(piece_bottom("monotonic"), " solid_infill_direction=", a);
