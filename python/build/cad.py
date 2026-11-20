"""Projects drawn with build123d: a project file ends with `project()`."""

import io
import sys
from collections.abc import Callable, Mapping, Sequence
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
    """One part of an object, as Orca has it."""

    shape: Shape
    name: str
    color: str = ""  # a name build123d knows, or none for the filament's own
    filament: str = ""  # what to call the filament the color stands for
    # Its own. One that Orca keeps for a whole object, a brim say, makes the
    # piece an object of its own, beside the rest.
    settings: Mapping[str, object] = field(default_factory=dict)


@dataclass
class Object:
    """An object to print or a view."""

    draw: Callable[[], Shape | list[Piece]]  # called only when it's wanted
    description: str  # shown beside its name
    # Its prints' own, over the project's: a layer height, say, which Orca keeps
    # for a whole object, so that no piece can carry it for the rest.
    settings: Mapping[str, object] = field(default_factory=dict)
    # Heights to pause at, to put something in: the print pauses once it's that
    # high, or a layer sooner, so leave a layer's room over what goes in.
    pauses: Sequence[float] = ()


def pieces(name: str, obj: Object) -> list[Piece]:
    drawn = obj.draw()
    return drawn if isinstance(drawn, list) else [Piece(drawn, name)]


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
    name: str, obj: Object, orca: Mapping[str, object], work: Path
) -> scad.Render:
    """Draw an object, and write a mesh of each of its pieces into `work`."""
    solids = []
    filaments = {}
    low, high = [float("inf")] * 3, [float("-inf")] * 3
    for i, piece in enumerate(pieces(name, obj), 1):
        if not piece.shape.is_valid:
            sys.exit(f"{name}: {piece.name} is not a valid solid")
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
    return scad.Render(
        solids,
        (tuple(low), tuple(high)),
        list(obj.pauses),
        filaments,
        texts({**orca, **obj.settings}),
    )


def view(file: Path, name: str, obj: Object) -> Path:
    """Write an object as a STEP file: its pieces by name, in their colors."""
    shapes = []
    for piece in pieces(name, obj):
        piece.shape.label = piece.name
        if piece.color:
            piece.shape.color = Color(piece.color)
        shapes.append(piece.shape)
    out = build.ROOT / "tmp/view" / f"{file.stem}-{name}.step"
    out.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(label=f"{file.stem} {name}", children=shapes), out)
    return out


def project(
    file: str,
    objects: Mapping[str, Object],
    orca: Mapping[str, object] | None = None,
    plates: list[str] | None = None,
    views: Mapping[str, Object] | None = None,
) -> None:
    """Write the project's .3mf files to gen/: one per object, and one of `plates`,
    each a group like "lid*2 base". `orca` is settings for all of them, an
    object's own `settings` for its prints, and a piece's for that piece; views
    are only to look at. The plates' project applies what its objects share, and
    puts the rest on each object, where Orca lets an object have it; it doesn't
    pause.

    `--view NAME` writes tmp/view/<stem>-<name>.step instead, for FreeCAD.
    `--objects` lists views, then objects: kind, name and description, tabbed.
    """
    # Show each line as it is printed, even into a pipe.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    path = Path(file).resolve()
    shown = {**(views or {}), **objects}
    match sys.argv[1:]:
        case []:
            build.run(
                path,
                list(objects),
                build.groups_of(plates or []),
                "build123d",
                lambda name, work: render(name, objects[name], orca or {}, work),
            )
        case ["--objects"]:
            for name, obj in shown.items():
                kind = "object" if name in objects else "view"
                # One line each, however the description is written.
                description = " ".join(obj.description.split())
                print(f"{kind}\t{name}\t{description}")
        case ["--view", name] if name in shown:
            print(view(path, name, shown[name]).relative_to(build.ROOT))
        case _:
            sys.exit(f"usage: {path.name} [--objects | --view OBJECT]")
