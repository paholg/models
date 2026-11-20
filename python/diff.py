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
import multiprocessing
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import diff_worker

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp/diff"
OLD = OUT / "old"
DRAWN = {"old": OUT / "drawn/old", "new": OUT / "drawn/new"}


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


def workers() -> ProcessPoolExecutor:
    """Processes to draw and compare in, each a fork of a server that has only
    loaded build123d (see diff_worker.py): loading it takes longer than most
    objects take to draw. One task to a fork, which leaves behind the tree's
    modules that a draw imports."""
    context = multiprocessing.get_context("forkserver")
    context.set_forkserver_preload(["build123d"])
    return ProcessPoolExecutor(os.cpu_count(), context, max_tasks_per_child=1)


def failure(e: BaseException) -> str:
    return f"{type(e).__name__}: {e}"


def folder(side: str, file: Path, name: str) -> Path:
    return DRAWN[side] / file.with_suffix("") / name


def brep(side: str, unit: Unit) -> Path:
    return folder(side, unit.file, unit.object) / f"{unit.piece}.brep"


def diffs(unit: Unit) -> Path:
    """Where a piece's diff goes."""
    return folder("new", unit.file, unit.object) / unit.piece


def pieces(side: str, file: Path, name: str, names: list[str]) -> list[Unit]:
    """What a worker drew of an object, each piece named for itself."""
    out = folder(side, file, name)
    units = []
    for i, piece in enumerate(names):
        # Two pieces of the same name are told apart by their order.
        if names.index(piece) != i:
            piece = f"{piece} {names[:i].count(piece) + 1}"
        (out / f"{i}.brep").rename(out / f"{piece}.brep")
        units.append(Unit(file, name, piece))
    return units


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

    # Here, not at the top: each worker runs this file's top again, and a
    # `build` imported there would be this tree's, not the one it draws.
    from build import progress

    print(f"drawing {len(files)} projects, at {ref} and now")
    with progress.shown(), workers() as pool:
        units = draw(pool, files)
        shown = compare(pool, units)
        if shown:
            path = OUT / "diff.step"
            objects: dict[str, dict[str, Path]] = {}
            for unit in shown:
                objects.setdefault(unit.label, {})[unit.piece] = diffs(unit)
            title = f"changes since {ref}"
            progress.expect(1)
            with progress.stage("writing diff.step"):
                pool.submit(diff_worker.view, objects, title, path).result()
    if not shown:
        return
    print(path.relative_to(ROOT))
    if show:
        subprocess.Popen(
            ["freecad", path, ROOT / "nix/fit.FCMacro"],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def counted[T](
    pool: ProcessPoolExecutor, what: str, fn: Callable[..., T], *args: object
) -> Future[T]:
    """Submit a task, shown on the progress bar as `what` while it runs, and
    counted as it finishes, not when it's waited on."""
    from build import progress

    progress.expect(1)
    progress.start(what)
    future = pool.submit(fn, *args)
    future.add_done_callback(lambda _: progress.finish(what))
    return future


def draw(pool: ProcessPoolExecutor, files: list[Path]) -> list[Unit]:
    """Draw each object of each file, at both sides that have it. Returns the
    pieces of those that drew at both, or at the one side that has the file."""
    sides = [(t, s, f) for f in files for t, s in ((OLD, "old"), (ROOT, "new"))]
    sides = [(t, s, f) for t, s, f in sides if (t / f).is_file()]
    listing = {
        counted(pool, f"listing {f.stem}, {s}", diff_worker.objects, t, f): (t, s, f)
        for t, s, f in sides
    }
    drawing: dict[Future, tuple[str, Path, str]] = {}
    units: dict[Unit, None] = {}
    # What failed on either side, to leave out rather than show all added or
    # all removed.
    failed: set[tuple[Path, str]] = set()
    # Each object drawn as soon as its file has been listed.
    for done in as_completed(listing):
        tree, side, file = listing[done]
        try:
            names = done.result()
        except Exception as e:  # noqa: BLE001  # whatever the project raises
            print(f"  {file}, {side}: {failure(e)}")
            failed.add((file, ""))
            continue
        for name in names:
            out = folder(side, file, name)
            what = f"drawing {file.stem} {name}, {side}"
            job = counted(pool, what, diff_worker.draw, tree, file, name, out)
            drawing[job] = (side, file, name)
    for done in as_completed(drawing):
        side, file, name = drawing[done]
        try:
            units.update(dict.fromkeys(pieces(side, file, name, done.result())))
        except Exception as e:  # noqa: BLE001  # whatever the project raises
            print(f"  {file} {name}, {side}: {failure(e)}")
            failed.add((file, name))
    kept = [
        u
        for u in units
        if (u.file, "") not in failed and (u.file, u.object) not in failed
    ]
    # In the order drawn, which is the files' order, each one's objects', and
    # each object's pieces'.
    order = {
        (t[2], name): i
        for i, (t, name) in enumerate(
            (listing[f], n) for f in listing if not f.exception() for n in f.result()
        )
    }
    return sorted(kept, key=lambda u: order[u.file, u.object])


def compare(pool: ProcessPoolExecutor, units: list[Unit]) -> list[Unit]:
    """The pieces that differ, each with its diff written."""
    # The same bytes are the same shape; the rest takes a closer look.
    differ = [
        u
        for u in units
        if not brep("old", u).exists()
        or not brep("new", u).exists()
        or brep("old", u).read_bytes() != brep("new", u).read_bytes()
    ]
    jobs = [
        counted(
            pool,
            f"comparing {u.file.stem} {u.piece}",
            diff_worker.compare,
            brep("old", u),
            brep("new", u),
            diffs(u),
        )
        for u in differ
    ]
    shown = []
    for unit, job in zip(differ, jobs):
        try:
            has = job.result()
        except Exception as e:  # noqa: BLE001  # whatever the project raises
            print(f"  {unit.label} {unit.piece}: {failure(e)}")
            continue
        if has:
            shown.append(unit)
            piece = "" if unit.piece == unit.object else f" {unit.piece}"
            print(f"  {unit.label}{piece}: {', '.join(has)}")
    print(f"  {len(units) - len(shown)} of {len(units)} pieces are the same")
    return shown


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
