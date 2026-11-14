"""Export a .scad file's parts as Orca projects that apply the settings they need.

The .scad file lists its parts on an `// export:` line. An optional `// orca:`
line holds the slicer settings that matter for the print, as key=value pairs,
quoted where a value has spaces:

    // export: print test
    // orca: process="0.12 Fine" layer_height=0.1

Each key is an Orca setting, by its name in the preset JSON files. Opening the
project applies them on top of whatever presets Orca has selected, and leaves
everything else alone. `printer`, `process` and `filament` are not settings but
presets, which Orca keeps as selected: those are for you to pick by hand.

The whole line is also shown, as the name of the plate and of the object.

This uses Orca 2.5's "published" projects, which carry only the settings they
list. Orca reads no plate names from a project without settings, so a project
with none to apply still carries one, unlisted.

Each part becomes gen/<dir>/<stem>-<part>.3mf, where <dir> is the .scad file's
directory in this repo: one object, with a part per OpenSCAD object and color,
each color on its own filament. The file's earlier projects are removed first.

Orca's parts are named for their colors, unless the .scad file names them. One
way is by color, for a file that draws each color in one go:
`echo(color = "green", piece = "name")` names whatever is that color, and it's
no matter if nothing is. A `filament = "name"` after those names the filament
the color stands for, for the plates' names (see `// plate:`).

The other is one `echo(piece = "name")` for each top-level statement, in order.
For instance:

    module piece(name) { echo(piece = name); children(); }
    piece("lid") color("green") lid();

A piece can carry settings of its own, which Orca applies to just its parts: an
`orca` string beside the name, written like the `// orca:` line.

    module piece(name, orca = "") { echo(piece = name, orca = orca); children(); }
    piece("lid", "bottom_surface_pattern=concentric") color("green") lid();

Orca keeps some settings for a whole object, not a part: a brim or a raft, say.
A piece with one of those becomes an object of its own, where it is, beside the
object of everything else:

    piece("feet", "brim_type=outer_only brim_width=3") feet();

A print can pause, to put something inside it: `echo(pause = z)` pauses once
the print is z high, before the layer above. That takes a `layer_height` on the
`// orca:` line, to find that layer.

`// plate:` lines ask for one more project, gen/<dir>/<stem>-all.3mf, with
everything in it, laid out on as many plates as it takes. Each line is a group
of parts to print together, with `*N` for copies:

    // plate: lid*2 base
    // plate: feet*4

A group that doesn't fit one plate goes on several. Its parts are packed by
their bounding boxes, turned a quarter where that helps; nothing keeps room
for a prime tower. There being more colors than tool heads, each plate's name
says which filament goes on which: they're shared out to change as few as can
be from one plate to the next, in the order of the lines.

Usage: generate.py FILE.scad
"""

import io
import math
import shlex
import sys
import tempfile
from pathlib import Path

from project import layout, orca, scad

ROOT = Path(__file__).resolve().parents[1]

# Keys on the `// orca:` line that name presets, not settings.
PRESETS = {"printer", "process", "filament"}


def directives(text: str, name: str) -> list[str]:
    prefix = f"// {name}:"
    return [
        line.removeprefix(prefix).strip()
        for line in text.splitlines()
        if line.startswith(prefix)
    ]


def directive(text: str, name: str) -> str:
    return next(iter(directives(text, name)), "")


def combine(
    dst: Path,
    settings: dict[str, str],
    groups: list[list[str]],
    built: dict[str, orca.Assembly],
    filaments: dict[str, str],
) -> None:
    """Write one published project of every group's parts, on as many plates as it takes.

    `filaments` names the filament a color stands for, for the plates' names.
    """
    sizes = {
        p: (a.box[1][0] - a.box[0][0], a.box[1][1] - a.box[0][1])
        for p, a in built.items()
    }
    packed = [plate for g in groups for plate in layout.pack(g, sizes)]
    colors = [
        list(
            dict.fromkeys(
                v.color for p, *_ in plate for o in built[p].objects for v in o.volumes
            )
        )
        for plate in packed
    ]
    heads = layout.loadouts(colors)
    cols = math.ceil(math.sqrt(len(packed)))

    plates = []
    copies: dict[str, int] = {}
    for i, plate in enumerate(packed):
        origin = (
            i % cols * layout.BED[0] * layout.PLATE_STRIDE,
            -(i // cols) * layout.BED[1] * layout.PLATE_STRIDE,
        )
        placed = []
        count: dict[str, int] = {}
        for part, x, y, turned in plate:
            copy = copies[part] = copies.get(part, 0) + 1
            count[part] = count.get(part, 0) + 1
            # The box's corner to (x, y) on the plate, its bottom to the bed.
            (x0, y0, z0), (_x1, y1, _z1) = built[part].box
            if turned:
                at = "0 1 0 -1 0 0 0 0 1", origin[0] + x + y1, origin[1] + y - x0
            else:
                at = "1 0 0 0 1 0 0 0 1", origin[0] + x - x0, origin[1] + y - y0
            placed.append(
                orca.Placed(
                    built[part],
                    part if copy == 1 else f"{part} {copy}",
                    f"{at[0]} {at[1]:.4f} {at[2]:.4f} {-z0:.4f}",
                    heads[i],
                )
            )
        name = ", ".join(p if n == 1 else f"{p} x{n}" for p, n in count.items())
        tools = ", ".join(
            f"T{k} {filaments.get(c) or scad.color_name(c)}"
            for c, k in sorted(heads[i].items(), key=lambda h: h[1])
        )
        print(f"  plate {i + 1}: {name}: {tools}")
        plates.append(orca.Plate(f"{name}: {tools}", placed))
    objects = orca.write(dst, settings, plates)
    print(f"{dst.relative_to(ROOT)}: {len(plates)} plates, {objects} objects")


def generate(file: Path) -> None:
    out_dir = ROOT / "gen" / file.parent.relative_to(ROOT)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{file.stem}-*.3mf"):
        old.unlink()

    text = file.read_text()
    note = ", ".join(shlex.split(directive(text, "orca")))
    settings = {
        k: v for k, v in scad.pairs(directive(text, "orca")).items() if k not in PRESETS
    }

    exports = directive(text, "export").split()
    # Each `// plate:` line's parts, a copy at a time.
    groups = [
        [
            part
            for item in line.split()
            for part, _, n in [item.partition("*")]
            for _ in range(int(n or 1))
        ]
        for line in directives(text, "plate")
    ]
    built: dict[str, orca.Assembly] = {}
    filaments: dict[str, str] = {}  # the filament each color the file names stands for
    for part in dict.fromkeys(exports + [p for g in groups for p in g]):
        target = out_dir / f"{file.stem}-{part}.3mf"
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            print(f"{part}: openscad")
            render = scad.render(file, part, work)
            if render.pauses and "layer_height" not in settings:
                sys.exit(f"{part} pauses, which takes a layer_height on the orca line")
            if render.pauses and any(part in g for g in groups):
                print(f"  warning: {file.stem}-all won't pause for {part}")
            filaments.update(render.filaments)
            print(f"{part}: orca-slicer, assembling {len(render.solids)} parts")
            assembly = built[part] = orca.assemble(render.solids, render.box, work)
        if part not in exports:
            continue
        # Filaments in order of each color's first appearance.
        order = list(dict.fromkeys(s.color for s in render.solids))
        if len(order) > layout.FILAMENTS:
            print(
                f"  warning: {len(order)} colors for {layout.FILAMENTS} filaments; extras go on filament 1"
            )
        heads = {c: i + 1 for i, c in enumerate(order[: layout.FILAMENTS])}
        name = f"{target.stem} [{note}]" if note else target.stem
        placed = orca.Placed(assembly, name, assembly.transform, heads)
        objects = orca.write(
            target, settings, [orca.Plate(note, [placed])], render.pauses
        )
        print(
            f"{target.relative_to(ROOT)}: {len(render.solids)} parts, {len(order)} colors"
            + (f", {objects} objects" if objects > 1 else "")
            + "".join(f", pause at {z:g} mm" for z in render.pauses)
        )
    if groups:
        combine(out_dir / f"{file.stem}-all.3mf", settings, groups, built, filaments)


if __name__ == "__main__":
    # Show each line as it is printed, even into a pipe.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    generate(Path(sys.argv[1]).resolve())
