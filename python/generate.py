"""Export a .scad file's parts as Orca projects that apply the settings they need.

The .scad file lists its parts on an `// export:` line:

    // export: print test

Its slicer settings are in its code: lib/orca.scad's `orca()`, for the whole
print, with a function for each setting. That file has them.

    orca([orca_process("0.12 Fine"), orca_layer_height(0.1)]);

Opening the project applies them on top of whatever presets Orca has selected,
and leaves everything else alone. `printer`, `process` and `filament` are not
settings but presets, which Orca keeps as selected: those are for you to pick
by hand. All of them are also shown, as the name of the plate and of the
object. A part can have its own, or none, the file being rendered for each:

    if (part != "draft") orca([orca_layer_height(0.1)]);

This uses Orca 2.5's "published" projects, which carry only the settings they
list. Orca reads no plate names from a project without settings, so a project
with none to apply still carries one, unlisted.

Each part becomes gen/<dir>/<stem>-<part>.3mf, where <dir> is the .scad file's
directory in this repo: one object, with a part per OpenSCAD object and color,
each color on its own filament: the same one in every project of the file, the
`// plate:` one too. The file's earlier projects are removed first.

Orca's parts are named for their colors, unless the .scad file names them. One
way is by color, for a file that draws each color in one go:
`echo(color = "green", piece = "name")` names whatever is that color, and it's
no matter if nothing is. A `filament = "name"` after those names the filament
the color stands for, for the plates' names (see `// plate:`).

The other is by piece: lib/piece.scad's `piece("name")`, around every solid of
the print, wherever in the file it is drawn. For instance:

    use <../../lib/piece.scad>
    piece("lid") color("green") lid();

A piece says what it is in OpenSCAD's log, and this then renders the file once
for each, asking for that one alone: OpenSCAD has no other way to hand over one
piece of what it draws. That file has the rest of it.

A piece can carry settings of its own, which Orca applies to just its parts: a
list of them beside the name.

    piece("lid", [orca_bottom_pattern("concentric")]) color("green") lid();

Orca keeps some settings for a whole object, not a part: a brim or a raft, say.
A piece with one of those becomes an object of its own, where it is, beside the
object of everything else:

    piece("feet", [orca_brim("outer_only", 3)]) feet();

A print can pause, to put something inside it: `echo(pause = z)` pauses once
the print is z high, or a layer sooner: leave a layer's room over what goes in.

`// plate:` lines ask for one more project, gen/<dir>/<stem>-all.3mf, with
everything in it, laid out on as many plates as it takes. It applies the
settings its parts share; one that only some have goes on those parts' own
objects, if Orca lets an object have it, and is left out with a warning if not. A plate
pauses wherever one of its parts does, and everything on it with it. Each line is a group
of parts to print together, with `*N` for copies:

    // plate: lid*2 base
    // plate: feet*4

A group that doesn't fit one plate goes on several. Its parts are packed by
their bounding boxes, turned a quarter where that helps; nothing keeps room
for a prime tower. Each plate's name says which filament goes on which tool
head. With more colors than heads, those that never print together share one.

A project written in Python with build123d comes out the same way, by running
it: build/cad.py has that side.

Usage: generate.py FILE.scad
"""

import io
import sys
from pathlib import Path

from build import build, scad


def directives(text: str, name: str) -> list[str]:
    prefix = f"// {name}:"
    return [
        line.removeprefix(prefix).strip()
        for line in text.splitlines()
        if line.startswith(prefix)
    ]


def directive(text: str, name: str) -> str:
    return next(iter(directives(text, name)), "")


def generate(file: Path) -> None:
    text = file.read_text()

    if any(line.startswith("// orca") for line in text.splitlines()):
        sys.exit("settings are no longer `// orca:` lines: see lib/orca.scad's orca()")

    exports = directive(text, "export").split()
    groups = build.groups_of(directives(text, "plate"))
    build.run(file, exports, groups, "openscad", lambda p, w: scad.render(file, p, w))


if __name__ == "__main__":
    # Show each line as it is printed, even into a pipe.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    generate(Path(sys.argv[1]).resolve())
