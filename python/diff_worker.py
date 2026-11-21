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
# How far, in mm³, added, removed and common may be from adding up to the two
# shapes before the booleans are taken to have gone wrong, as OCCT's can on
# faces of the two that nearly coincide.
SLACK = 0.05
COLORS = {
    "added": (0, 0.7, 0, 1),
    "removed": (0.85, 0, 0, 1),
    "common": (0.8, 0.8, 0.8, 0.25),
    # Of a piece the booleans failed on, each shape whole, side by side.
    "old": (0.85, 0, 0, 0.5),
    "new": (0, 0.7, 0, 0.5),
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
        # As printed: where a tree's pieces have a place for that, at it.
        printed = getattr(piece, "printed", None)
        export_brep(printed().shape if printed else piece.shape, out / f"{i}.brep")
    return [p.name for p in drawn]


def thickness(shape: "Shape") -> float:
    """How thick a solid is on average: its volume over half its surface."""
    area = shape.area
    return 2 * shape.compute_volume() / area if area else 0.0


def volume(shape: "Shape | None") -> float:
    return shape.compute_volume() if shape is not None else 0.0


def compare(old: Path, new: Path, out: Path) -> tuple[list[str], str | None]:
    """Write the solids of a piece's diff to `out`: added, removed and common,
    of those there are. Returns which there are of added and removed, and
    whether the booleans failed, when it writes old and new whole instead."""
    from build123d import export_brep, import_brep

    out.mkdir(parents=True, exist_ok=True)
    if not old.exists() or not new.exists():
        # All of the one there is has been added, or removed.
        kind, path = ("added", new) if new.exists() else ("removed", old)
        (out / f"{kind}.brep").write_bytes(path.read_bytes())
        return [kind], None
    a, b = import_brep(old), import_brep(new)
    va, vb = volume(a), volume(b)
    try:
        solids = {"added": b - a, "removed": a - b}
        # What stays is only there to see the change by, and to check the
        # others with, and is the slowest of the three: a piece drawn the same,
        # though not to the same bytes, skips it.
        if volume(solids["added"]) or volume(solids["removed"]):
            solids["common"] = b & a
        else:
            solids["common"] = b
        sums = [
            volume(solids["common"]) + volume(solids[k]) for k in ("added", "removed")
        ]
        if abs(sums[0] - vb) > SLACK or abs(sums[1] - va) > SLACK:
            raise ValueError(
                f"common and added come to {sums[0]:.3f} mm³ of {vb:.3f}, "
                f"common and removed to {sums[1]:.3f} of {va:.3f}"
            )
    # OCCT's own, or the ValueError build123d raises on what comes out null.
    except Exception as e:  # noqa: BLE001
        export_brep(a, out / "old.brep")
        export_brep(b, out / "new.brep")
        return ["old", "new"], f"booleans failed: {type(e).__name__}: {e}"
    found = []
    for kind in ("added", "removed"):
        solid = solids[kind]
        if solid is not None and volume(solid) and thickness(solid) >= FILM:
            export_brep(solid, out / f"{kind}.brep")
            found.append(kind)
    common = solids["common"]
    if found and common is not None and volume(common):
        export_brep(common, out / "common.brep")
    return found, None


def unhollowed(shape: "Shape") -> "Shape":
    """`shape` with each solid's cavities filled: just its outer shell. FreeCAD
    1.1 (OCCT 7.9) segfaults healing a solid of more than one shell as it
    reads a STEP file, as booleans leave where a piece has a hidden pocket,
    and a cavity can't be seen anyway."""
    from build123d import Compound, Solid

    solids = shape.solids()
    if all(len(s.shells()) < 2 for s in solids):
        return shape
    # The outer shell is the one around the others: the biggest.
    return Compound(
        [
            Solid(max(s.shells(), key=lambda h: h.bounding_box().diagonal))
            for s in solids
        ]
    )


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
                    shape = unhollowed(import_brep(folder / f"{kind}.brep"))
                    if kind == "new" and (folder / "old.brep").exists():
                        # Beside the old, not in it: STEP keeps no
                        # transparency, so the one would hide the other.
                        before = shapes[-1][2].bounding_box()
                        right = before.max.X - shape.bounding_box().min.X
                        shape = Pos(right + GAP / 2, 0, 0) * shape
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
