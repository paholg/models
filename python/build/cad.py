"""Projects drawn with build123d: a project file ends with `project()`."""

import contextlib
import io
import multiprocessing
import os
import sys
import warnings
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from build123d import Color, Compound, Shape, export_step

# OCP has no stubs for these; build123d imports them where ty can see them.
from build123d.exporters3d import BRepMesh_IncrementalMesh, StlAPI_Writer
from build123d.text import Font_FontMgr

from . import build, progress
from .orca import Solid

# build123d points fontconfig at /etc/fonts/fonts.conf when it first sets
# text, whose files are newer than the fontconfig OCP bundles and warn at every
# line. Starting OCCT's font manager first, on the flake's list of the fonts,
# keeps those out and the fonts the same everywhere.
if fonts := os.environ.get("CAD_FONTCONFIG_FILE"):
    system = os.environ.get("FONTCONFIG_FILE")
    os.environ["FONTCONFIG_FILE"] = fonts
    Font_FontMgr.GetInstance_s()
    if system is not None:
        os.environ["FONTCONFIG_FILE"] = system

# How far a mesh may stray from the shape it is made of: at most TOLERANCE mm
# anywhere, and ANGULAR_TOLERANCE radians of a curve's turn between facets.
# 0.02 mm is a fifth of a 0.1 mm layer and a twentieth of the nozzle, too
# little to see or to change a fit: a pocket's or pin's facets stand at most
# that far inside its circle. The angle only matters below about 1 mm radius,
# where 0.3 keeps a fillet's facets within 0.03 mm. build123d's export_stl
# takes the tolerance as a fraction of each face's size instead, which lets a
# large curve, the ghost's skin say, stray by a millimeter at the same angle.
TOLERANCE = 0.02
ANGULAR_TOLERANCE = 0.3


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
    """A color as #RRGGBB, which is what the plates go by."""
    if not name:
        return ""
    r, g, b = (round(255 * c) for c in tuple(Color(name))[:3])
    return f"#{r:02X}{g:02X}{b:02X}"


def write_stl(shape: Shape, path: Path) -> None:
    """A binary STL of the shape, to TOLERANCE in mm, not a fraction of its size."""
    BRepMesh_IncrementalMesh(
        shape.wrapped, TOLERANCE, False, ANGULAR_TOLERANCE, True
    ).Perform()
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    if not writer.Write(shape.wrapped, str(path)):
        sys.exit(f"couldn't write {path}")


def render(
    name: str, obj: Object, orca: Mapping[str, object], work: Path, step: Path
) -> build.Render:
    """Draw an object, write a mesh of each of its pieces into `work`, and all of
    them as a STEP file to `step`."""
    solids = []
    filaments = {}
    low, high = [float("inf")] * 3, [float("-inf")] * 3
    drawn = pieces(name, obj)
    for i, piece in enumerate(drawn, 1):
        if not piece.shape.is_valid:
            sys.exit(f"{name}: {piece.name} is not a valid solid")
        stl = work / f"{i}.stl"
        write_stl(piece.shape, stl)
        color = hex_color(piece.color)
        solids.append(Solid(stl, color, piece.name, texts(piece.settings)))
        # Called what the piece calls it, or by its color's name.
        if name := piece.filament or (piece.color if color != piece.color else ""):
            filaments.setdefault(color, name)
        box = piece.shape.bounding_box()
        low = [min(a, b) for a, b in zip(low, tuple(box.min))]
        high = [max(a, b) for a, b in zip(high, tuple(box.max))]
    write_step(drawn, step)
    return build.Render(
        solids,
        (tuple(low), tuple(high)),
        list(obj.pauses),
        filaments,
        texts({**orca, **obj.settings}),
    )


# In a worker, what its project() was given, to draw from; none elsewhere. The
# server that workers fork from sets it (see worker.py).
given: dict | None = None


def draw(name: str, work: Path, step: Path) -> tuple[build.Render, str]:
    """In a worker, render an object (see render())."""
    assert given is not None
    return heard(render, name, given["objects"][name], given["orca"], work, step)


def draw_view(name: str, step: Path) -> tuple[None, str]:
    """In a worker, write a view as a STEP file."""
    assert given is not None
    return heard(write_step_of, name, given["views"][name], step)


def write_step_of(name: str, obj: Object, out: Path) -> None:
    """Draw an object or view, and write it as a STEP file."""
    write_step(pieces(name, obj), out)


def heard[T](work: Callable[..., T], *args) -> tuple[T, str]:
    """In a worker, run `work`, hearing what it says. Returns what it returns and
    what it printed, which an error it raises carries instead, as `said`."""
    from . import worker  # the server's, so only in a worker

    said = io.StringIO()
    try:
        with (
            warnings.catch_warnings(),
            contextlib.redirect_stdout(said),
            contextlib.redirect_stderr(said),
        ):
            # The warnings the server quieted, heard again, and the file's
            # deprecations too, as they are where it runs as __main__.
            warnings.filters = list(worker.heard)
            warnings.filterwarnings(
                "default", category=DeprecationWarning, module="__mp_main__"
            )
            done = work(*args)
    except BaseException as e:
        vars(e)["said"] = said.getvalue()  # for project() to show
        raise
    return done, said.getvalue()


def workers(n: int) -> ProcessPoolExecutor:
    """Processes to draw objects in: build123d draws under the GIL, so threads
    draw one at a time.

    Each is a fork of a server that has only loaded build123d (see worker.py),
    not of the project's own process: a fork of that can hang, where OCCT runs
    threads it started that the fork leaves behind. So each runs the project
    file again, as multiprocessing does, and its `project()` only keeps what
    it's given, for draw().
    """
    context = multiprocessing.get_context("forkserver")
    context.set_forkserver_preload([f"{__package__}.worker"])
    return ProcessPoolExecutor(n, mp_context=context)


def write_step(drawn: list[Piece], out: Path) -> None:
    """Write pieces as a STEP file, for FreeCAD: by name, in their colors."""
    shapes = []
    for piece in drawn:
        piece.shape.label = piece.name
        if piece.color:
            piece.shape.color = Color(piece.color)
        shapes.append(piece.shape)
    out.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(label=out.stem, children=shapes), out)


def project(
    file: str,
    objects: Mapping[str, Object],
    orca: Mapping[str, object] | None = None,
    plates: list[str] | None = None,
    views: Mapping[str, Object] | None = None,
) -> None:
    """Write the project's .3mf files to gen/<dir>/: one per object, and one of `plates`,
    each a group like "lid*2 base". `orca` is settings for all of them, an
    object's own `settings` for its prints, and a piece's for that piece; views
    are only to look at. The plates' project applies what its objects share, and
    puts the rest on each object, where Orca lets an object have it, and pauses
    each plate wherever one of its objects pauses, stopping the rest there too.

    Beside them, for FreeCAD, go <stem>-<name>.step for each view and object,
    an object as it's printed, and <stem>-views.tsv, which lists views, then
    objects: kind, name and description, tabbed.

    With more than one thing to draw, they're drawn in workers, each of which
    runs the file again (see workers()).

    `--view NAME` writes just tmp/view/<stem>-<name>.step instead.
    """
    views = views or {}
    if given is not None:
        # In a worker, which then draws what it's asked to (see workers()).
        given.update(objects=objects, views=views, orca=orca or {})
        return
    if both := sorted(objects.keys() & views.keys()):
        sys.exit(f"both an object and a view: {', '.join(both)}")
    # Show each line as it is printed, even into a pipe.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    path = Path(file).resolve()
    shown = {**views, **objects}
    match sys.argv[1:]:
        case []:
            with progress.shown():
                generate(path, objects, views, orca or {}, plates or [])
        case ["--view", name] if name in shown:
            out = build.ROOT / "tmp/view" / f"{path.stem}-{name}.step"
            write_step_of(name, shown[name], out)
            print(out.relative_to(build.ROOT))
        case _:
            sys.exit(f"usage: {path.name} [--view OBJECT]")


def generate(
    path: Path,
    objects: Mapping[str, Object],
    views: Mapping[str, Object],
    orca: Mapping[str, object],
    plates: list[str],
) -> None:
    """project()'s work with no arguments: everything it writes to gen/."""
    out_dir = build.ROOT / "gen" / path.parent.relative_to(build.ROOT)
    for old in [
        *out_dir.glob(f"{path.stem}-*.step"),
        out_dir / f"{path.stem}-views.tsv",
    ]:
        old.unlink(missing_ok=True)

    def step(name: str) -> Path:
        return out_dir / f"{path.stem}-{name}.step"

    def result[T](future: Future[tuple[T, str]]) -> T:
        try:
            done, said = future.result()
        except BaseException as e:
            # What it printed before it failed, to see why.
            print(vars(e).get("said", ""), end="")
            raise
        print(said, end="")
        return done

    def look(pool: ProcessPoolExecutor, name: str) -> Future[tuple[None, str]]:
        """Start drawing a view, counted as it finishes, not when it's waited on."""
        what = f"drawing {name}"
        progress.start(what)
        future = pool.submit(draw_view, name, step(name))
        future.add_done_callback(lambda _: progress.finish(what))
        return future

    # Each in a worker, but for one alone, which isn't worth starting one for.
    count = len(objects) + len(views)
    with (
        workers(min(count, os.cpu_count() or 1))
        if count > 1
        else contextlib.nullcontext() as pool,
    ):
        # The views go first, to draw while the objects are assembled in Orca.
        # With any, there are workers.
        progress.expect(len(views))
        looks = {n: look(pool, n) for n in views if pool}

        def drawn(name: str, work: Path) -> build.Render:
            if pool is None:
                return render(name, objects[name], orca, work, step(name))
            return result(pool.submit(draw, name, work, step(name)))

        build.run(path, list(objects), build.groups_of(plates), drawn)
        for drawing in looks.values():
            result(drawing)

    rows = [("view", n, o) for n, o in views.items()]
    rows += [("object", n, o) for n, o in objects.items()]
    listed = out_dir / f"{path.stem}-views.tsv"
    # One line each, however the description is written.
    listed.write_text(
        "".join(f"{k}\t{n}\t{' '.join(o.description.split())}\n" for k, n, o in rows)
    )
    print(
        f"{listed.relative_to(build.ROOT)}: {len(views)} views, {len(objects)} objects"
    )
