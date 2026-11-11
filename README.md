# Models

## OpenSCAD

I have not found a good way to fully go from OpenSCAD -> Snapmaker Orca, so this
is the current process.

**Initial Setup**

1. Run `just generate $FILE.scad`. This will create an Orca project in
   `~/3d-project-generated/` for each part on the file's `// export:` line, with one part per
   color and the slicer settings from its `// orca:` line (see `python/generate.py`).
2. Open that project in Orca.
3. Do whatever in Orca.

## Python

The current python project is playing with emitting G-code directly, for
interesting lattices. Not sure if it will work at all yet.
