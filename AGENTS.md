This repo is for 3d models with OpenSCAD and build123d for printing with a
Snapmaker U1. New projects should use build123d; OpenSCAD is deprecated.

I use OrcaSlicer, not Snapmaker Orca, and the Extended firmware.

The printer is available at 10.0.0.15.

## OrcaSlicer

`orca-slicer` comes from this repo's flake: an AppImage in a sandbox wrapper,
so don't go looking for its files through the binary.

* `$ORCA_SOURCE` is its source, at the same version. Look settings up in
  `$ORCA_SOURCE/src/libslic3r/PrintConfig.cpp`; a setting's key is its name
  there and in the preset JSON files.
* Presets: the bundled ones are in `$ORCA_SOURCE/resources/profiles/Snapmaker`,
  which Orca copies to `~/.config/OrcaSlicer/system/Snapmaker`. Mine are in
  `~/.config/OrcaSlicer/user`.
* A model becomes Orca projects, with settings for the whole print or for
  single parts: see build123d below. What does it is in `python/build`:
  `build.py` writes the projects, `orca.py` reads and writes Orca's files,
  `layout.py` packs plates, and `cad.py` (with `worker.py`) and `scad.py` are
  build123d's and OpenSCAD's sides. `python/generate.py`'s docstring has what
  comes out.
* `just slice gen/….3mf` slices such a project to `tmp/slice/`, to check
  settings in the G-code rather than guess. Orca's own CLI ignores a
  project's settings, which only the GUI applies; `python/slice.py` lays them
  on by hand.
* `solid_infill_direction` is the direction of the first layer's lines on the
  bed, in degrees counter-clockwise from +x: 0 runs along x, 90 along y.

## build123d

A project is a Python file that draws with build123d, where a solid is a value
to name, color and put together, and ends with `project()` from
`python/build/cad.py`, whose docstring has the details. `just generate` and
`f` take it, and the older .scad models too, which work as before.

* `project()` takes `objects`, the ones to print, and `views`, ones only to look
  at, each an `Object`: a function, giving one shape or a list of `Piece`s,
  and a description to show beside its name. Each piece is a part of the
  object in Orca, with its own name, color, filament and settings. Draw the
  assembly as it's used; the objects' functions turn their pieces to print.
* Generating draws the objects in other processes, each of which runs the
  file again up to `project()` (see `cad.workers()`): keep the file's own code
  quick, and don't count on a cache one object's drawing fills being there
  for another's.
* Slicer settings: `project(orca={...})` for the whole print, an `Object`'s
  `settings` for its own prints (a layer height, say, which Orca keeps for a
  whole object), a `Piece`'s `settings` for that piece. Keys are the
  settings' names in Orca. An `Object`'s `pauses=[z]` pauses the print to put
  something in; a plate pauses wherever one of its objects does.
* A project of several objects should always have an `assembly` view of them
  put together, and should specify `plates` when calling `project()`.
* `just view FILE.py OBJECT` writes `tmp/view/<stem>-<object>.step` and opens
  it in FreeCAD: the pieces by name, to hide, cut through and measure. OBJECT
  can be a view.
* A design more than one project draws, the card box say, is a module in
  `python/designs/`, imported as `designs.<name>`.
* Draw in 2D and extrude, rather than cut solids from solids. Something of many
  cells, a honeycomb say, is one `Face(outline, holes)` extruded once: cutting
  each cell, `chamfer()` on each cell's edges and `loft()` between faces with
  many holes all take minutes or never finish.
* build123d comes from PyPI by way of uv, and is the reason Python stops
  short of 3.15 in `python/pyproject.toml`; the flake's `uv` knows where the
  libraries it loads are.
* `extrude()` goes the way the face's normal points, which a polygon's winding
  decides: a clockwise one goes down. Pass a direction, `(0, 0, 1)`, when it
  matters.

## Directory structure

* First is general scope (home for home products, games for mostly boardgame
  inserts, etc.)
* Next folder is more specific.
* Then each build123d .py file (or older .scad file) for a full print.
* `gcode/` is the exception: scripts that write G-code directly, using
  `python/lib`, each to `tmp/<script name>.gcode`.
* `f` (`nix/f.sh`) is a TUI over all of these: it generates, previews and uploads
  to the printer. It never starts a print; I do that by hand.

## Instructions

Please generate any assets into `./tmp/`.

While these models are for 3d prints, I'm general fine with mixed media, gluing,
using bolts, etc. I'm usually more interested in the final product than in
getting a single print does everything. When in doubt, ask me.

## Design

Most edges should have chamfers or fillets. When designing parts for glue, use
crush ribs and joints; try to make installation easy and secure.

Don't design for particular slicer settings (layer height, etc) unless a part
truly requires it, in which case it should be set in `project()`'s `orca` or a
piece's `settings`, with a comment giving the reason.

## TODO

In TODO.md is a very brief list of the next steps for each project.
