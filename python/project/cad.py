"""The build123d side: a model written in Python, into the same Orca projects.

A model is a Python file where its .scad would be. It draws its parts with
build123d, and ends by saying what they are:

    from build123d import *
    from project.cad import Piece, main

    def lid() -> Part: ...

    main(__file__, parts={"lid": lid, "base": base}, orca={"layer_height": 0.1})

A part is a function, called only when the part is wanted. It gives one shape,
or for a print of several pieces a list of them, each a part in Orca with its
own name, color, filament and settings:

    def lid() -> list[Piece]:
        return [
            Piece(body, "body", "lightsteelblue", filament="main"),
            Piece(text, "text", "black", settings={"top_surface_pattern": "concentric"}),
        ]

`orca` is the whole print's settings, by their names in Orca's presets, and
`plates` the groups of parts to print together, as a .scad file's `// plate:`
lines have them: `plates=["lid*2 base"]`. generate.py's docstring has what
becomes of all of these.

Run with no arguments, the model writes its projects to gen/. With
`--view PART` it writes tmp/view/<stem>-<part>.step instead, to look at in
FreeCAD: a tree of the pieces by name, in their colors. `--parts` lists the parts.
"""

import io
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from build123d import Color, Compound, Shape, export_step, export_stl

from . import build, scad

# How far a mesh may stray from the shape it is made of, in mm and in radians
# of a curve's turn: well under what a printer can show.
TOLERANCE = 0.01
ANGULAR_TOLERANCE = 0.1


@dataclass
class Piece:
    """One part of a print, as Orca has it."""

    shape: Shape
    name: str
    color: str = ""  # a name build123d knows, or none for the filament's own
    filament: str = ""  # what to call the filament the color stands for
    settings: Mapping[str, object] = field(default_factory=dict)  # its own


Part = Callable[[], Shape | list[Piece]]


def pieces(part: str, draw: Part) -> list[Piece]:
    drawn = draw()
    return drawn if isinstance(drawn, list) else [Piece(drawn, part)]


def texts(settings: Mapping[str, object]) -> dict[str, str]:
    """Settings as Orca writes them."""
    return {
        k: str(int(v)) if isinstance(v, bool) else str(v) for k, v in settings.items()
    }


def hex_color(name: str) -> str:
    """A color as an OpenSCAD 3MF would have it, which is what the plates go by."""
    if not name:
        return ""
    r, g, b = (round(255 * c) for c in tuple(Color(name))[:3])
    return f"#{r:02X}{g:02X}{b:02X}"


def render(
    part: str, draw: Part, orca: Mapping[str, object], work: Path
) -> scad.Render:
    """Draw a part, and write a mesh of each of its pieces into `work`."""
    solids = []
    filaments = {}
    low, high = [float("inf")] * 3, [float("-inf")] * 3
    for i, piece in enumerate(pieces(part, draw), 1):
        if not piece.shape.is_valid:
            sys.exit(f"{part}: {piece.name} is not a valid solid")
        stl = work / f"{i}.stl"
        export_stl(piece.shape, stl, TOLERANCE, ANGULAR_TOLERANCE)
        color = hex_color(piece.color)
        solids.append(
            scad.Solid(stl, color, piece.name, texts(piece.settings), piece.name)
        )
        if piece.filament:
            filaments[color] = piece.filament
        box = piece.shape.bounding_box()
        low = [min(a, b) for a, b in zip(low, tuple(box.min))]
        high = [max(a, b) for a, b in zip(high, tuple(box.max))]
    return scad.Render(solids, (tuple(low), tuple(high)), [], filaments, texts(orca))


def view(file: Path, part: str, draw: Part) -> Path:
    """Write a part as a STEP file: its pieces by name, in their colors."""
    shapes = []
    for piece in pieces(part, draw):
        piece.shape.label = piece.name
        if piece.color:
            piece.shape.color = Color(piece.color)
        shapes.append(piece.shape)
    out = build.ROOT / "tmp/view" / f"{file.stem}-{part}.step"
    out.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(label=f"{file.stem} {part}", children=shapes), out)
    return out


def main(
    file: str,
    parts: Mapping[str, Part],
    orca: Mapping[str, object] | None = None,
    plates: list[str] | None = None,
) -> None:
    """What a model file ends with: see this module's docstring."""
    # Show each line as it is printed, even into a pipe.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    path = Path(file).resolve()
    match sys.argv[1:]:
        case []:
            build.run(
                path,
                list(parts),
                build.groups_of(plates or []),
                "build123d",
                lambda part, work: render(part, parts[part], orca or {}, work),
            )
        case ["--parts"]:
            print("\n".join(parts))
        case ["--view", part] if part in parts:
            print(view(path, part, parts[part]).relative_to(build.ROOT))
        case _:
            sys.exit(f"usage: {path.name} [--parts | --view PART]")
