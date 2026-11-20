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
* `python/generate.py` turns a .scad file into Orca projects, with settings
  for the whole print or for single parts. Its docstring has the details. What
  it's made of is in `python/project`: `scad.py` for OpenSCAD's side, `orca.py`
  for reading and writing Orca's projects, `layout.py` for packing plates.
* `just slice gen/….3mf` slices such a project to `tmp/slice/`, to check
  settings in the G-code rather than guess. Orca's own CLI ignores a
  project's settings, which only the GUI applies; `python/slice.py` lays them
  on by hand.
* `solid_infill_direction` is the direction of the first layer's lines on the
  bed, in degrees counter-clockwise from +x: 0 runs along x, 90 along y.

## build123d

A model can be a Python file instead of a .scad one: it draws with build123d,
where a solid is a value to name, color and put together, and ends with
`model()` from `python/project/cad.py`, whose docstring has the details. `just
generate` and `f` take either kind. New models are being tried this way; the
.scad ones work as before.

* `just view FILE.py PART` writes `tmp/view/<stem>-<part>.step` and opens it in
  FreeCAD: the pieces by name, to hide, cut through and measure.
* Draw in 2D and extrude, rather than cut solids from solids. Something of many
  cells, a honeycomb say, is one `Face(outline, holes)` extruded once: cutting
  each cell, `chamfer()` on each cell's edges and `loft()` between faces with
  many holes all take minutes or never finish.
* build123d comes from PyPI by way of uv, and is the reason Python stops
  short of 3.15 in `python/pyproject.toml`; the flake's `uv` knows where the
  libraries it loads are.
* Multi-part objects should always have an `assembly` view with the object as
  assembled, and should specify `plates` when calling `model()`. 

## Directory structure

* First is general scope (home for home products, games for mostly boardgame
  inserts, etc.)
* Next folder is more specific.
* Then each .scad file, or build123d .py file, for a full print.
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
truly requires it, in which case it should be set with `orca()` with a reason.

## TODO

In TODO.md is a very brief list of the next steps for each project.
