# Models

## OpenSCAD

I have not found a good way to fully go from OpenSCAD -> Snapmaker Orca, so this
is the current process.

**Initial Setup**

1. Run `just generate $FILE.scad`. This will create a 3mf file in `~/3d-project-generated/`.
2. Run Orca, import that file.
3. Do whatever in Orca.

## Python

The current python project is playing with emitting G-code directly, for
interesting lattices. Not sure if it will work at all yet.
