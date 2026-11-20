"""Show what a change does to the build123d projects' prints, in FreeCAD.

Takes the files that differ between a commit and the working tree, untracked
ones too, and draws each piece of each object of each project they reach,
before and after. A project is a .py file outside python/ and gcode/ that calls
`project()`, and a change reaches it through itself, what it imports from
python/, transitively, and any other file beside one of those, an SVG say.
Name projects to draw just those.

Pieces whose shapes are the same are left out; the rest are compared by
OCCT's booleans, not meshes. Each that came out different goes in
tmp/diff/diff.step, an object to a spot, labeled: green for what the change
adds, red for what it takes away, and what stays in gray, as "<piece> common"
to hide (STEP keeps no transparency). The commit's files are in tmp/diff/old,
and the pieces' shapes in tmp/diff/drawn.

Usage: diff.py [REF] [PROJECT...] [--no-open]
"""

import argparse
import ast
import io
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from build123d import (
    Align,
    Color,
    Compound,
    Pos,
    Shape,
    Text,
    export_brep,
    export_step,
    extrude,
    import_brep,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp/diff"
OLD = OUT / "old"
DRAWN = {"old": OUT / "drawn/old", "new": OUT / "drawn/new"}
DRAW = Path(__file__).with_name("diff_draw.py")
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


@dataclass(frozen=True)
class Unit:
    """One piece of one object of one project."""

    file: Path  # in the repo
    object: str
    piece: str

    @property
    def label(self) -> str:
        """The object's."""
        return f"{self.file.with_suffix('')} {self.object}"


def git(*args: str) -> list[str]:
    run = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return run.stdout.splitlines()


def module(tree: Path, name: str) -> Path | None:
    """Where in `tree` a module of python/ is, if it's there."""
    base = Path("python", *name.split("."))
    for path in (base.with_suffix(".py"), base / "__init__.py"):
        if (tree / path).is_file():
            return path
    return None


def reach(tree: Path, file: Path, seen: set[Path]) -> set[Path]:
    """`file` and what it imports from python/, as paths in `tree`."""
    path = tree / file
    if file in seen or not path.is_file():
        return seen
    seen.add(file)
    try:
        nodes = ast.walk(ast.parse(path.read_bytes()))
    except SyntaxError:
        return seen
    for node in nodes:
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level:
            # Relative, within a package of python/.
            package = file.parent.relative_to("python").parts
            package = package[: len(package) - node.level + 1]
            base = ".".join([*package, *filter(None, [node.module])])
            names = [base] + [f"{base}.{a.name}" for a in node.names]
        for name in names:
            # A package's __init__ too, which importing it runs.
            parts = name.split(".")
            for i in range(1, len(parts) + 1):
                if found := module(tree, ".".join(parts[:i])):
                    reach(tree, found, seen)
    return seen


def is_project(tree: Path, file: Path) -> bool:
    path = tree / file
    return (
        file.suffix == ".py"
        and file.parts[0] not in ("python", "gcode")
        and path.is_file()
        and "project(" in path.read_text()
    )


def run(tree: Path, file: Path, *args: str) -> tuple[str, str]:
    """diff_draw.py, on `file` as `tree` has it. Returns what it printed, and
    the last line of what went wrong, if it did."""
    done = subprocess.run(
        [sys.executable, DRAW, tree, file, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = done.stderr.strip().splitlines() or ["failed"]
    return done.stdout, lines[-1] if done.returncode else ""


def folder(side: str, file: Path, name: str) -> Path:
    return DRAWN[side] / file.with_suffix("") / name


def brep(side: str, unit: Unit) -> Path:
    return folder(side, unit.file, unit.object) / f"{unit.piece}.brep"


def diffs(unit: Unit) -> Path:
    """Where a piece's diff goes."""
    return folder("new", unit.file, unit.object) / unit.piece


def pieces(side: str, file: Path, name: str) -> list[Unit]:
    """What diff_draw.py drew of an object, each piece named for itself."""
    out = folder(side, file, name)
    names = json.loads((out / "pieces.json").read_text())
    units = []
    for i, piece in enumerate(names):
        # Two pieces of the same name are told apart by their order.
        if names.index(piece) != i:
            piece = f"{piece} {names[:i].count(piece) + 1}"
        (out / f"{i}.brep").rename(out / f"{piece}.brep")
        units.append(Unit(file, name, piece))
    return units


def thickness(shape: Shape) -> float:
    """How thick a solid is on average: its volume over half its surface."""
    area = shape.area
    return 2 * shape.compute_volume() / area if area else 0.0


def compare(unit: Unit) -> list[str]:
    """Write the solids of a piece's diff beside its new shape. Returns which
    there are of added and removed."""
    old, new = brep("old", unit), brep("new", unit)
    out = diffs(unit)
    out.mkdir(parents=True, exist_ok=True)
    if not old.exists() or not new.exists():
        # All of the one there is has been added, or removed.
        kind, path = ("added", new) if new.exists() else ("removed", old)
        shutil.copy(path, out / f"{kind}.brep")
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


def viewer(units: list[Unit], ref: str) -> Path:
    """The diffs as one STEP file: an object to a spot, in rows, labeled."""
    import build.cad  # noqa: F401  # for its fonts

    objects: dict[str, list[Unit]] = {}
    for unit in units:
        objects.setdefault(unit.label, []).append(unit)
    found = []
    for label, pieces in objects.items():
        shapes = []
        for unit in pieces:
            for kind, color in COLORS.items():
                if (diffs(unit) / f"{kind}.brep").exists():
                    shape = import_brep(diffs(unit) / f"{kind}.brep")
                    shapes.append((f"{unit.piece} {kind}", color, shape))
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
    path = OUT / "diff.step"
    export_step(Compound(label=f"changes since {ref}", children=children), path)
    return path


def diff(ref: str, named: list[Path], show: bool) -> None:
    changed = {
        Path(f)
        for f in git("diff", "--name-only", ref)
        + git("ls-files", "--others", "--exclude-standard")
    }
    shutil.rmtree(OUT, ignore_errors=True)
    OLD.mkdir(parents=True)
    archive = subprocess.run(
        ["git", "archive", ref], cwd=ROOT, check=True, capture_output=True
    )
    subprocess.run(["tar", "-x", "-C", OLD], input=archive.stdout, check=True)

    if named:
        files = named
    else:
        if not changed:
            sys.exit(f"nothing differs from {ref}")
        candidates = {Path(f) for f in git("ls-files", "-co", "--exclude-standard")}
        candidates |= {f.relative_to(OLD) for f in OLD.rglob("*.py")}
        files = []
        for file in sorted(candidates):
            if not (is_project(OLD, file) or is_project(ROOT, file)):
                continue
            brings = reach(OLD, file, set()) | reach(ROOT, file, set())
            # And what is beside them: the SVGs a project imports, say.
            dirs = {f.parent for f in brings}
            if any(
                f in brings or f.parent in dirs and f.suffix != ".py" for f in changed
            ):
                files.append(file)
        if not files:
            sys.exit("the changes reach no project")

    print(f"drawing {len(files)} projects, at {ref} and now")
    sides = [(t, s, f) for f in files for t, s in ((OLD, "old"), (ROOT, "new"))]
    sides = [(t, s, f) for t, s, f in sides if (t / f).is_file()]
    units: dict[Unit, None] = {}
    # What failed on either side, to leave out rather than show all added or
    # all removed.
    failed: set[tuple[Path, str]] = set()
    with ThreadPoolExecutor(os.cpu_count()) as pool:
        listed = pool.map(lambda j: run(j[0], j[2]), sides)
        objects = []
        for (tree, side, file), (out, error) in zip(sides, listed):
            if error:
                print(f"  {file}, {side}: {error}")
                failed.add((file, ""))
            objects += [(tree, side, file, name) for name in out.splitlines()]

        def one(job: tuple[Path, str, Path, str]) -> str:
            tree, side, file, name = job
            return run(tree, file, name, str(folder(side, file, name)))[1]

        for (_, side, file, name), error in zip(objects, pool.map(one, objects)):
            if error:
                print(f"  {file} {name}, {side}: {error}")
                failed.add((file, name))
            else:
                units.update(dict.fromkeys(pieces(side, file, name)))

    # The same bytes are the same shape; the rest takes a closer look.
    drawn = [
        u
        for u in units
        if (u.file, "") not in failed and (u.file, u.object) not in failed
    ]
    differ = [
        u
        for u in drawn
        if not brep("old", u).exists()
        or not brep("new", u).exists()
        or brep("old", u).read_bytes() != brep("new", u).read_bytes()
    ]
    shown = []
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(mp_context=context) as pool:
        for unit, has in zip(differ, pool.map(compare, differ)):
            if has:
                shown.append(unit)
                piece = "" if unit.piece == unit.object else f" {unit.piece}"
                print(f"  {unit.label}{piece}: {', '.join(has)}")
    print(f"  {len(drawn) - len(shown)} of {len(drawn)} pieces are the same")
    if not shown:
        return
    path = viewer(shown, ref)
    print(path.relative_to(ROOT))
    if show:
        subprocess.Popen(
            ["freecad", path],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("args", nargs="*", metavar="[REF] [PROJECT...]")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    ref, named = "HEAD", list(args.args)
    # A first argument that isn't a file is the commit.
    if named and not Path(named[0]).exists():
        ref = named.pop(0)
    files = []
    for name in named:
        path = Path(name).resolve()
        if not path.is_relative_to(ROOT):
            sys.exit(f"{name} isn't in the repo")
        files.append(path.relative_to(ROOT))
    diff(ref, files, not args.no_open)


if __name__ == "__main__":
    main()
