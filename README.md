# Models

## OpenSCAD

I have not found a good way to fully go from OpenSCAD -> OrcaSlicer, so this
is the current process.

**Initial Setup**

1. Run `just generate $FILE.scad`. This will create an Orca project in
   `gen/`, under the file's own directory (`gen/game/jenga/` for `game/jenga/box.scad`), for
   each part on the file's `// export:` line, with one part per color. Opening it applies the slicer settings on the file's `// orca:` line on top of your
   selected presets, and shows that line as the plate's name (see `python/generate.py`).
2. Open that project in Orca.
3. Do whatever in Orca.

To check what a project slices to without opening Orca, `just slice` it: the
G-code lands in `tmp/slice/` (see `python/slice.py`).

## G-code

The scripts in `gcode/` emit G-code directly, with the library in `python/lib`,
for interesting lattices. Not sure if it will work at all yet.

Each writes `tmp/<script name>.gcode`, and most a 3D preview beside it. Run `f`
and pick one to generate it, view it, and upload it to the printer; printing is
then started by hand, from the printer's page.
