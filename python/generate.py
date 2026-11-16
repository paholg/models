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
objects, if Orca lets an object have it, and is left out with a warning if not. Each line is a group
of parts to print together, with `*N` for copies:

    // plate: lid*2 base
    // plate: feet*4

A group that doesn't fit one plate goes on several. Its parts are packed by
their bounding boxes, turned a quarter where that helps; nothing keeps room
for a prime tower. Each plate's name says which filament goes on which tool
head. With more colors than heads, those that never print together share one.

Usage: generate.py FILE.scad
"""

import io
import math
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
    packed: list[list[tuple[str, float, float, bool]]],
    built: dict[str, orca.Assembly],
    colors: dict[str, list[str]],
    heads: dict[str, int],
    filaments: dict[str, str],
    own: dict[str, dict[str, str]],
) -> None:
    """Write one published project of the parts as packed, a plate for each of `packed`.

    `colors` are each part's and `heads` the tool head for each; `filaments` names
    the filament a color stands for, for the plates' names. `own` are the settings
    of each part alone, beyond `settings`.
    """
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
                    heads,
                    own.get(part, {}),
                )
            )
        name = ", ".join(p if n == 1 else f"{p} x{n}" for p, n in count.items())
        tools = ", ".join(
            f"T{k} {filaments.get(c) or scad.color_name(c)}"
            for k, c in sorted({(heads[c], c) for p in count for c in colors[p]})
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

    if any(line.startswith("// orca") for line in text.splitlines()):
        sys.exit("settings are no longer `// orca:` lines: see lib/orca.scad's orca()")

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
    wanted: dict[str, dict[str, str]] = {}  # each part's settings, presets and all
    filaments: dict[str, str] = {}  # the filament each color the file names stands for
    renders: dict[str, scad.Render] = {}
    for part in dict.fromkeys(exports + [p for g in groups for p in g]):
        target = out_dir / f"{file.stem}-{part}.3mf"
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            print(f"{part}: openscad")
            render = scad.render(file, part, work)
            if render.pauses and any(part in g for g in groups):
                print(f"  warning: {file.stem}-all won't pause for {part}")
            filaments.update(render.filaments)
            wanted[part] = render.settings
            print(f"{part}: orca-slicer, assembling {len(render.solids)} parts")
            built[part] = orca.assemble(render.solids, render.box, work)
            renders[part] = render
    colors = {
        p: list(dict.fromkeys(s.color for s in r.solids)) for p, r in renders.items()
    }
    sizes = {
        p: (a.box[1][0] - a.box[0][0], a.box[1][1] - a.box[0][1])
        for p, a in built.items()
    }
    packed = [plate for g in groups for plate in layout.pack(g, sizes)]
    # A color is on one tool head in every project, the plates' too.
    heads = layout.heads(
        list(colors.values())
        + [
            list(dict.fromkeys(c for p, *_ in plate for c in colors[p]))
            for plate in packed
        ]
    )
    for part in exports:
        target = out_dir / f"{file.stem}-{part}.3mf"
        render, assembly, order = renders[part], built[part], colors[part]
        note = ", ".join(f"{k}={v}" for k, v in render.settings.items())
        settings = {k: v for k, v in render.settings.items() if k not in PRESETS}
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
        # One project has one set of settings: those its parts agree on. The
        # rest go on each part's own objects, where Orca lets an object have one.
        parts = [wanted[p] for g in groups for p in g]
        shared = {
            k: v
            for k, v in parts[0].items()
            if k not in PRESETS and all(p.get(k) == v for p in parts)
        }
        rest = {
            p: {k: v for k, v in wanted[p].items() if k not in PRESETS | set(shared)}
            for g in groups
            for p in g
        }
        ownable = orca.own_keys() if any(rest.values()) else frozenset()
        own = {p: {k: v for k, v in r.items() if k in ownable} for p, r in rest.items()}
        if dropped := sorted({k for r in rest.values() for k in r} - ownable):
            print(
                f"  warning: {file.stem}-all leaves out {', '.join(dropped)}, which its parts"
                " don't share, and an object can't have of its own"
            )
        combine(
            out_dir / f"{file.stem}-all.3mf",
            shared,
            packed,
            built,
            colors,
            heads,
            filaments,
            own,
        )


if __name__ == "__main__":
    # Show each line as it is printed, even into a pipe.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    generate(Path(sys.argv[1]).resolve())
