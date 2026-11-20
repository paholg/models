"""What diff.py's workers do: each a fork of a server that has only loaded
build123d, which takes longer than drawing most objects, and each runs one task
(see diff.workers()).

A task that draws takes TREE, a checkout of the repo, the working tree or the
one diff.py extracted, and FILE, a project in it. What the project imports from
python/ comes from TREE's, not this one's, and `project()` only keeps what it's
given: so an old commit's project draws as it did then, though its cad.py
can't do this itself. Such a task is the only one its worker runs, so the next
can take another tree's.

Only the standard library is imported here, at first: this module is loaded
where the server's build123d isn't, in diff.py's own process too.
"""

import contextlib
import os
import runpy
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from build123d import Shape

    from build.cad import Object

HERE = Path(__file__).resolve().parent
# Between the objects, and for an object's label in front of it, in mm.
GAP = 20
LABEL = 12
# A solid thinner than this on average, in mm, is no change: the film a boolean
# of two near-equal shapes can leave.
FILM = 1e-3
COLORS = {
    "added": (0, 0.7, 0, 1),
    "removed": (0.85, 0, 0, 1),
    "common": (0.8, 0.8, 0.8, 0.25),
}


def given(tree: Path, file: Path) -> dict[str, "Object"]:
    """The objects FILE gives `project()`, as TREE has them."""
    python = (tree / "python").resolve()
    # Only TREE's python/: not this one, which uv's environment points at.
    sys.path[:] = [str(python)] + [p for p in sys.path if Path(p).resolve() != HERE]

    from build import cad

    found: dict[str, Object] = {}

    # Its signature, though only `objects` matters.
    def project(
        file: str,
        objects: Mapping[str, cad.Object],
        orca: Mapping[str, object] | None = None,
        plates: list[str] | None = None,
        views: Mapping[str, cad.Object] | None = None,
    ) -> None:
        found.update(objects)

    vars(cad)["project"] = project
    # What the project prints is for when it's generated.
    with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet):
        runpy.run_path(str(tree / file), run_name="__main__")
    return found


def objects(tree: Path, file: Path) -> list[str]:
    """The names of FILE's objects."""
    return list(given(tree, file))


def draw(tree: Path, file: Path, name: str, out: Path) -> list[str]:
    """Write an object's pieces to `out` as BREP files, 0.brep on. Returns
    their names, in order."""
    from build123d import export_brep

    obj = given(tree, file)[name]
    from build.cad import Piece  # TREE's, which given() imported

    with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet):
        drawn = obj.draw()
    if not isinstance(drawn, list):
        drawn = [Piece(drawn, name)]
    out.mkdir(parents=True, exist_ok=True)
    for i, piece in enumerate(drawn):
        export_brep(piece.shape, out / f"{i}.brep")
    return [p.name for p in drawn]


def thickness(shape: "Shape") -> float:
    """How thick a solid is on average: its volume over half its surface."""
    area = shape.area
    return 2 * shape.compute_volume() / area if area else 0.0


def compare(old: Path, new: Path, out: Path) -> list[str]:
    """Write the solids of a piece's diff to `out`: added, removed and common,
    of those there are. Returns which there are of added and removed."""
    from build123d import export_brep, import_brep

    out.mkdir(parents=True, exist_ok=True)
    if not old.exists() or not new.exists():
        # All of the one there is has been added, or removed.
        kind, path = ("added", new) if new.exists() else ("removed", old)
        (out / f"{kind}.brep").write_bytes(path.read_bytes())
        return [kind]
    a, b = import_brep(old), import_brep(new)
    found = []
    for kind, solid in (("added", b - a), ("removed", a - b), ("common", b & a)):
        if (
            solid is not None
            and solid.compute_volume()
            and (kind == "common" or thickness(solid) >= FILM)
        ):
            export_brep(solid, out / f"{kind}.brep")
            found.append(kind)
    return [k for k in found if k != "common"]


def view(objects: dict[str, dict[str, Path]], title: str, path: Path) -> None:
    """Write the diffs as one STEP file: each object's pieces' (the folders
    compare() wrote to, by name) to a spot, in rows, labeled."""
    from build123d import (
        Align,
        Color,
        Compound,
        Pos,
        Text,
        export_step,
        extrude,
        import_brep,
    )

    import build.cad  # noqa: F401  # for its fonts

    found = []
    for label, pieces in objects.items():
        shapes = []
        for piece, folder in pieces.items():
            for kind, color in COLORS.items():
                if (folder / f"{kind}.brep").exists():
                    shape = import_brep(folder / f"{kind}.brep")
                    shapes.append((f"{piece} {kind}", color, shape))
        box = Compound([s for *_, s in shapes]).bounding_box()
        # No narrower than its label.
        width = max(box.size.X, 0.7 * 5 * len(label)) + GAP
        found.append((label, shapes, box, width, box.size.Y + GAP + LABEL))
    # In rows, back to front, about as deep in all as they are wide.
    widest = max(
        max(w for *_, w, _ in found), 1.2 * sum(w * d for *_, w, d in found) ** 0.5
    )
    children = []
    x = y = deep = 0.0
    for label, shapes, box, width, depth in found:
        if x and x + width > widest:
            x, y, deep = 0.0, y - deep, 0.0
        deep = max(deep, depth)
        at = Pos(x - box.min.X, y - depth - box.min.Y, -box.min.Z)
        placed = []
        for name, color, shape in shapes:
            shape = at * shape
            shape.label, shape.color = name, Color(*color)
            placed.append(shape)
        text = Text(label, 5, "TeX Gyre Heros", align=(Align.MIN, Align.MIN))
        tag = Pos(x, y - depth - LABEL, 0) * extrude(text, 0.4)
        tag.label, tag.color = "label", Color("black")
        children.append(Compound(label=label, children=[*placed, tag]))
        x += width
    export_step(Compound(label=title, children=children), path)
