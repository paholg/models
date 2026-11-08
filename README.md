# Models

## OpenSCAD

I have not found a good way to fully go from OpenSCAD -> Snapmaker Orca, so this
is the current process.

**Initial Setup**

1. Run `just export $FILE.scad`. This will create a 3mf file in `gen/`.
2. Run Snapmaker Orca, import that file.
3. Do whatever in Orca
4. Save the project next to the `.scad` file, so it will be tracked by git.

**Edits**
1. Run `just export $FILE.scad`
2. In Snapmaker Orca, in Pepare, right click the object and "Reload from disk".

*NOTE:* This only works for editing parts, not for adding/removing parts. On
add/remove, it's probably easiest to start the Orca project over.

## Python

The current python project is playing with emitting G-code directly, for
interesting lattices. Not sure if it will work at all yet.
