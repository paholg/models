3D models in build123d for a Snapmaker U1 (Extended firmware, 10.0.0.15),
sliced in OrcaSlicer.

## Layout

* `<scope>/<thing>/<print>.py`: projects, one per print.
* `python/build/`: what turns a project into Orca projects.
* `python/designs/`: designs shared between projects.
* `gcode/`: scripts that write G-code to `tmp/`.
* `f` (`nix/f.sh`): TUI to generate, preview and upload. Never starts prints.
* `TODO.md`: next steps per project.
* Scratch output goes in `tmp/`.

## Projects

A project is a Python file that draws with build123d and ends by calling
`project()` from `python/build/cad.py`, whose docstring has the details. It
passes `project()` the objects to print and views to only look at, each a
function that draws it and a description. An object is one or more pieces,
each with its own name, color and slicer settings, which become its parts in
Orca.

Each piece has its own color, and two positions from where it's drawn: `at`,
where it sits when assembled, and `place`, where it's printed. Both are moves
and turns, never mirrors: a mirrored part is a piece of its own. A `View`
draws nothing of an object's: it takes the pieces of the objects it `uses`,
where they sit, and arranges them, adding whatever isn't printed, like bought
hardware. A project's views are its assemblies; one with several objects
passes `plates` to lay them out for printing. Some views still draw what they
show themselves, as an `Object`, until they're converted.

Give pieces a `parent`, to group them in FreeCAD.

Generating, with `just generate FILE.py`, writes the project's Orca projects
to `gen/`, and a STEP file of each object and view for FreeCAD. **Run it after
each set of changes to a project.** It draws in worker processes, each of
which runs the file again up to `project()`, so keep the file's top-level code
fast, and don't rely on a cache one object fills being there for another.

`just view FILE.py OBJECT` opens an object or view in FreeCAD, and
`just diff [REF]` shows in FreeCAD what the changes since REF (HEAD by
default) do to each piece.

## build123d

* Draw in 2D and extrude, rather than cutting solids from solids.
* Draw something with many cells, like a honeycomb, as one
  `Face(outline, holes)` extruded once: cutting, chamfering or lofting each
  cell separately takes minutes or never finishes.
* A clockwise polygon extrudes down: pass a direction, `(0, 0, 1)`, when it
  matters.

## OrcaSlicer

* It's a sandboxed AppImage: look in `$ORCA_SOURCE`, not the binary.
  Settings are in `src/libslic3r/PrintConfig.cpp`, bundled presets in
  `resources/profiles/Snapmaker`; user presets in `~/.config/OrcaSlicer/user`.
* `just slice gen/….3mf` slices to `tmp/slice/` to check settings in G-code.
* `solid_infill_direction` is the angle of the first layer's lines on the
  bed, counter-clockwise from +x: 0 runs along x, 90 along y.

## Design

* Glue, bolts and mixed media are fine; when in doubt, ask.
* Chamfer or fillet most edges. Glued parts get crush ribs and joints.
* Only set slicer settings a part truly needs, with a comment saying why.
