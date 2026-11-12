This repo is for 3d models with OpenSCAD for printing with a Snapmaker U1.

I use OrcaSlicer, not Snapmaker Orca, and the Extended firmware.

The printer is available at 10.0.0.15.

## OrcaSlicer

`orca-slicer` comes from the system, not this repo's flake: an AppImage in a
sandbox wrapper, so don't go looking for its files through the binary.

* `$ORCA_SOURCE` is its source, at the same version. Look settings up in
  `$ORCA_SOURCE/src/libslic3r/PrintConfig.cpp`; a setting's key is its name
  there and in the preset JSON files.
* Presets: the bundled ones are in `$ORCA_SOURCE/resources/profiles/Snapmaker`,
  which Orca copies to `~/.config/OrcaSlicer/system/Snapmaker`. Mine are in
  `~/.config/OrcaSlicer/user`.
* `python/generate.py` turns a .scad file into Orca projects, with settings
  for the whole print or for single parts. Its docstring has the details.

## Directory structure

* First is general scope (home for home products, game for mostly boardgame
  inserts, etc.)
* Next folder is more specific.
* Then each .scad file for a full print.

## Instructions

Please generate any assets into `./tmp/`.

Focus on fast, interactive iteration, rather than trying to get out final
products. I'd much rather see something quickly that's unfinished than wait for
the final product. Optimize for more interactions with me; it's okay if you have
to wait for me.

While these models are for 3d prints, I'm general fine with mixed media, gluing,
using bolts, etc. I'm usually more interested in the final product than in
getting a single print does everything. When in doubt, ask me.

## Design

Most edges should have chamfers or fillets. When designing parts for glue, use
crush ribs and joints; try to make installation easy and secure.
