"""Projects drawn with build123d: a project file ends with `project()`."""

import contextlib
import copy
import io
import json
import multiprocessing
import os
import shutil
import sys
import threading
import warnings
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path

from build123d import (
    Color,
    Compound,
    Location,
    Part,
    Shape,
    Sketch,
    Vector,
    export_brep,
    export_step,
    import_brep,
)

# OCP has no stubs for these; build123d imports them where ty can see them.
from build123d.exporters3d import BRepMesh_IncrementalMesh, StlAPI_Writer
from build123d.text import Font_FontMgr

from . import audit, build, progress
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


def sketch(shape: Shape) -> Sketch:
    """A 2D shape as a Sketch, to extrude or pass on as one: build123d's
    operators make one of sketches, but type it as a Compound or a Wire."""
    return shape if isinstance(shape, Sketch) else Sketch(shape.faces())


def part(shape: Shape) -> Part:
    """A solid shape as a Part, likewise."""
    return shape if isinstance(shape, Part) else Part(shape.solids())


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
    # The object it's a part of in Orca, by name, beside the rest: pieces with
    # the same one are its parts, the first giving it its filament. For what's
    # to print on its own, one object at a time say.
    orca_object: str = ""
    # The group it goes under in FreeCAD, to show and hide with the rest of it,
    # as a path of groups in groups: "lid/top", say. Orca doesn't see it.
    parent: str = ""
    # Where it sits, put together, and where it's printed, from where it's
    # drawn: moves and turns, never a mirror, which is another piece.
    at: Location = field(default_factory=Location)
    place: Location = field(default_factory=Location)

    def sitting(self) -> "Piece":
        """Where it sits, put together: as a view gets it."""
        return replace(self, shape=self.at * self.shape, at=Location())

    def printed(self) -> "Piece":
        return replace(self, shape=self.place * self.shape, place=Location())


@dataclass
class View:
    """To look at: the objects it `uses`, each a list of its pieces where they
    sit (see Piece.sitting()), arranged. It gets them once they're drawn, for
    their own prints, so a view doesn't draw them again; what it adds, a magnet
    say, it draws itself. It returns pieces as they're to be shown."""

    arrange: Callable[[Mapping[str, list[Piece]]], list[Piece]]
    description: str  # shown beside its name
    uses: Sequence[str] = ()


@dataclass
class Object:
    """An object to print, or a view that draws what it shows itself."""

    draw: Callable[[], Shape | list[Piece]]  # called only when it's wanted
    description: str  # shown beside its name
    # Its prints' own, over the project's: a layer height, say, which Orca keeps
    # for a whole object, so that no piece can carry it for the rest.
    settings: Mapping[str, object] = field(default_factory=dict)
    # Heights to pause at, to put something in: the print pauses once it's that
    # high, or a layer sooner, so leave a layer's room over what goes in.
    pauses: Sequence[float] = ()
    count: int = 1  # how many to print: a plate it's on gets that many
    # What its audit is to pass over, as left sharp on purpose: see audit.py.
    skip_audit: Sequence[audit.Skip] = ()


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


# Beside an object's kept pieces, what a view needs of each beyond its shape:
# its name, color, filament and parent. Written last, so a folder with one is
# whole.
SEEN = "seen.json"


def keep_pieces(made: list[Piece], keep: Path) -> None:
    """Write an object's pieces where they sit into `keep`, 0.brep on, for the
    views that use it: this run's, and a later one's that doesn't draw the
    object again (see generate())."""
    shutil.rmtree(keep, ignore_errors=True)
    keep.mkdir(parents=True)
    for i, piece in enumerate(made):
        export_brep(piece.sitting().shape, keep / f"{i}.brep")
    seen = [(p.name, p.color, p.filament, p.parent) for p in made]
    (keep / SEEN).write_text(json.dumps(seen))


def render(
    name: str,
    obj: Object,
    orca: Mapping[str, object],
    work: Path,
    step: Path,
    keep: Path | None = None,
) -> build.Render:
    """Draw an object, write a mesh of each of its pieces, as printed, into
    `work`, and all of them as a STEP file to `step`. With `keep`, keep its
    pieces there too, for views (see keep_pieces())."""
    solids = []
    filaments = {}
    low, high = [float("inf")] * 3, [float("-inf")] * 3
    made = pieces(name, obj)
    if keep is not None:
        keep_pieces(made, keep)
    drawn = [p.printed() for p in made]
    for i, piece in enumerate(drawn, 1):
        if not piece.shape.is_valid:
            sys.exit(f"{name}: {piece.name} is not a valid solid")
        stl = work / f"{i}.stl"
        write_stl(piece.shape, stl)
        color = hex_color(piece.color)
        solids.append(
            Solid(stl, color, piece.name, texts(piece.settings), piece.orca_object)
        )
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


def audited(name: str, obj: Object) -> tuple[list[audit.Spot], int]:
    """An object's pieces, together where they sit, audited (see audit.py)."""
    made = pieces(name, obj)
    return audit.audit([p.sitting().shape for p in made], obj.skip_audit)


def shapes_of(
    name: str, shown: Object | View, objects: Mapping[str, Object]
) -> list[Shape]:
    """What an object or view shows, where it sits."""
    if isinstance(shown, View):
        sitting = {n: [p.sitting() for p in pieces(n, objects[n])] for n in shown.uses}
        return [p.shape for p in arranged(shown, sitting)]
    return [p.sitting().shape for p in pieces(name, shown)]


def run_audit(names: Sequence[str], objects: Mapping[str, Object]) -> None:
    """Print each object's spots, and fail if there are any."""
    if unknown := [n for n in names if n not in objects]:
        sys.exit(f"not an object: {', '.join(unknown)}")
    bad = 0
    for name in names or objects:
        spots, skipped = audited(name, objects[name])
        bad += len(spots)
        print(
            f"{name}: {len(spots)} spots" + (f", {skipped} skipped" if skipped else "")
        )
        for spot in spots:
            print(f"  {spot}")
    if bad:
        sys.exit(1)


def run_shots(
    stem: str,
    name: str,
    where: Sequence[str],
    shown: Object | View,
    objects: Mapping[str, Object],
) -> None:
    """Write pictures of an object or view to tmp/shots/: from all round, or
    close up at each of `where`, an "X,Y,Z" or, for an object, "audit" for
    each of its audit's spots."""
    shapes = shapes_of(name, shown, objects)
    spots: list[Vector] | None = None
    for w in where:
        spots = spots or []
        if w == "audit":
            skip = shown.skip_audit if isinstance(shown, Object) else ()
            spots += [s.at for s in audit.audit(shapes, skip)[0]]
        else:
            spots.append(Vector(*[float(v) for v in w.split(",")]))
    out = build.ROOT / "tmp/shots" / f"{stem}-{name}"
    for old in out.parent.glob(f"{out.name}-*.png"):
        old.unlink()
    for path in audit.shots(shapes, out, spots):
        print(path.relative_to(build.ROOT))


def arranged(view: View, objects: Mapping[str, list[Piece]]) -> list[Piece]:
    """What a view shows, of the objects it uses, where they sit."""
    return view.arrange({n: objects[n] for n in view.uses})


def kept(folder: Path) -> list[Piece]:
    """An object's pieces as keep_pieces() kept them, where they sit."""
    seen = json.loads((folder / SEEN).read_text())
    return [
        Piece(import_brep(folder / f"{i}.brep"), name, color, filament, parent=parent)
        for i, (name, color, filament, parent) in enumerate(seen)
    ]


# In a worker, what its project() was given, to draw from; none elsewhere. The
# server that workers fork from sets it (see worker.py).
given: dict | None = None


def draw(
    name: str, work: Path, step: Path, keep: Path | None
) -> tuple[build.Render, str]:
    """In a worker, render an object (see render())."""
    assert given is not None
    obj = given["objects"][name]
    return heard(render, name, obj, given["orca"], work, step, keep)


def draw_kept(name: str, keep: Path) -> tuple[None, str]:
    """In a worker, draw an object only to keep its pieces, for a view."""
    assert given is not None
    obj = given["objects"][name]
    return heard(lambda: keep_pieces(pieces(name, obj), keep))


def draw_view(name: str, step: Path, uses: Mapping[str, Path]) -> tuple[None, str]:
    """In a worker, write a view as a STEP file: an arranged one from the
    objects it uses, as kept in their folders."""
    assert given is not None
    view = given["views"][name]

    def write() -> None:
        if isinstance(view, View):
            objects = {n: kept(uses[n]) for n in view.uses}
            write_step(arranged(view, objects), step)
        else:
            write_step(pieces(name, view), step)

    return heard(write)


def write_step_of(
    name: str, shown: Object | View, objects: Mapping[str, Object], out: Path
) -> None:
    """Draw an object, as printed, or a view, and write it as a STEP file."""
    if isinstance(shown, View):
        sitting = {n: [p.sitting() for p in pieces(n, objects[n])] for n in shown.uses}
        write_step(arranged(shown, sitting), out)
    elif name in objects:
        write_step([p.printed() for p in pieces(name, shown)], out)
    else:
        write_step(pieces(name, shown), out)


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
    """Write pieces as a STEP file, for FreeCAD: by name, in their colors, each
    in its parent's groups."""
    # Each group's shapes and groups, (name, group), in the order they come.
    top: list = []
    groups = {"": top}
    used: list[Shape] = []
    for piece in drawn:
        shape = piece.shape
        # One shape placed twice is one to STEP, under the last name it's given.
        if any(shape.wrapped.IsPartner(u.wrapped) for u in used):
            shape = copy.deepcopy(shape)
        used.append(shape)
        shape.label = piece.name
        if piece.color:
            shape.color = Color(piece.color)
        path, group = "", top
        for name in filter(None, piece.parent.split("/")):
            path += f"/{name}"
            if path not in groups:
                groups[path] = []
                group.append((name, groups[path]))
            group = groups[path]
        group.append(shape)

    def built(group: list) -> list[Shape]:
        """A group's shapes and groups, a group moved as one where all it holds
        is: so that FreeCAD gives the group that placement, and its children
        none, and the group's box turns with them, as a placed piece's does."""
        out = []
        for e in group:
            if not isinstance(e, tuple):
                out.append(e)
                continue
            children = built(e[1])
            at = children[0].location if children else None
            if at is None or any(c.location != at for c in children):
                out.append(Compound(label=e[0], children=children))
                continue
            undo = at.inverse()
            children = [c.moved(undo) for c in children]
            out.append(Compound(label=e[0], children=children).moved(at))
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(label=out.stem, children=built(top)), out)


def project(
    file: str,
    objects: Mapping[str, Object],
    orca: Mapping[str, object] | None = None,
    plates: Sequence[Sequence[str]] | None = None,
    views: Mapping[str, Object | View] | None = None,
    plate_gap: float = 5,
) -> None:
    """Write the project's .3mf files to gen/<dir>/: one per object, and one of `plates`,
    each the names of the objects to print together, `plate_gap` apart: more
    for a brim, say. `orca` is settings for all of them, an
    object's own `settings` for its prints, and a piece's for that piece; views
    are only to look at. The plates' project applies what its objects share, and
    puts the rest on each object, where Orca lets an object have it, and pauses
    each plate wherever one of its objects pauses, stopping the rest there too.
    A view is a View, which arranges objects drawn for their prints, or an
    Object, which draws what it shows itself.

    Beside them, for FreeCAD, go <stem>-<name>.step for each view and object,
    an object as it's printed, and <stem>-views.tsv, which lists views, then
    objects: kind, name and description, tabbed.

    With more than one thing to draw, they're drawn in workers, each of which
    runs the file again (see workers()).

    `NAME...` writes just those objects' and views' files, and leaves the rest
    of gen/ as it is, plates and all: to see a change to one without waiting
    on the others. A view named takes the objects it uses that aren't as they
    were last drawn, by any run: so what it shows of them may be older than
    the file.

    `--view NAME` writes just tmp/view/<stem>-<name>.step instead. `--audit
    [OBJECT...]` looks the objects over for sharp edges and slivers, and fails
    if it finds any. `--shots NAME [X,Y,Z |
    audit]...` writes pictures of an object or view to tmp/shots/ (see
    audit.py).
    """
    views = views or {}
    if given is not None:
        # In a worker, which then draws what it's asked to (see workers()).
        given.update(objects=objects, views=views, orca=orca or {})
        return
    if both := sorted(objects.keys() & views.keys()):
        sys.exit(f"both an object and a view: {', '.join(both)}")
    for name, view in views.items():
        if isinstance(view, View) and (missing := set(view.uses) - set(objects)):
            sys.exit(f"view {name} uses what isn't an object: {', '.join(missing)}")
    for plate in plates or []:
        if isinstance(plate, str) or not set(plate) <= set(objects):
            sys.exit(f"a plate is a list of objects' names, not {plate!r}")
    # Show each line as it is printed, even into a pipe.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    path = Path(file).resolve()
    shown = {**views, **objects}
    match sys.argv[1:]:
        case []:
            with progress.shown():
                generate(path, objects, views, orca or {}, plates or [], plate_gap)
        case [*names] if not any(n.startswith("-") for n in names):
            if unknown := [n for n in names if n not in shown]:
                sys.exit(
                    f"not an object or view: {', '.join(unknown)}."
                    f" There are: {', '.join(shown)}"
                )
            with progress.shown():
                generate(
                    path, objects, views, orca or {}, plates or [], plate_gap, names
                )
        case ["--view", name] if name in shown:
            out = build.ROOT / "tmp/view" / f"{path.stem}-{name}.step"
            write_step_of(name, shown[name], objects, out)
            print(out.relative_to(build.ROOT))
        case ["--audit", *names]:
            run_audit(names, objects)
        case ["--shots", name, *where] if name in shown:
            run_shots(path.stem, name, where, shown[name], objects)
        case _:
            sys.exit(
                f"usage: {path.name} [NAME... | --view OBJECT | --audit [OBJECT...] |"
                " --shots OBJECT [X,Y,Z | audit]...]"
            )


def generate(
    path: Path,
    objects: Mapping[str, Object],
    views: Mapping[str, Object | View],
    orca: Mapping[str, object],
    plates: Sequence[Sequence[str]],
    plate_gap: float,
    only: Sequence[str] = (),
) -> None:
    """project()'s work with no arguments: everything it writes to gen/. Or,
    with `only`, just what it writes of those objects and views."""
    out_dir = build.ROOT / "gen" / path.parent.relative_to(build.ROOT)
    if not only:
        for old in [
            *out_dir.glob(f"{path.stem}-*.step"),
            out_dir / f"{path.stem}-views.tsv",
        ]:
            old.unlink(missing_ok=True)
    wanted = [n for n in objects if not only or n in only]
    looked = [n for n in views if not only or n in only]

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

    def uses(name: str) -> Sequence[str]:
        view = views[name]
        return view.uses if isinstance(view, View) else ()

    # Where the pieces are kept of each object a view uses, any view: for this
    # run's views, and for those of a later run that doesn't draw the object.
    used = {n for v in views for n in uses(v)}
    cache = build.cache(path)
    # What this run's views use that it doesn't draw: as last drawn, where
    # that was kept, and the rest drawn now, only to keep.
    rest = [n for n in objects if n not in wanted and any(n in uses(v) for v in looked)]
    old = [n for n in rest if (cache / n / SEEN).exists()]
    fresh = [n for n in rest if n not in old]
    for name in looked:
        if stale := [n for n in uses(name) if n in old]:
            print(f"{name}: with {', '.join(stale)} as last drawn")

    # Each in a worker, but for one object alone, which isn't worth starting
    # one for.
    count = len(wanted) + len(looked) + len(fresh)
    with (
        workers(min(count, os.cpu_count() or 1))
        if looked or count > 1
        else contextlib.nullcontext() as pool
    ):
        # Each view goes once the objects it uses are drawn, the rest at once,
        # to draw while the objects are assembled in Orca. With any, there are
        # workers.
        progress.expect(len(looked) + len(fresh))
        looks: dict[str, Future[tuple[None, str]]] = {}
        made = {n: cache / n for n in old}
        lock = threading.Lock()

        def start[T](what: str, work: Callable[..., T], *args) -> Future[T]:
            """Start a stage in a worker, counted as it finishes, not when
            it's waited on."""
            assert pool is not None
            progress.start(what)
            future = pool.submit(work, *args)
            future.add_done_callback(lambda _: progress.finish(what))
            return future

        def ready() -> None:
            """Start the views whose objects are all drawn."""
            with lock:
                for name in looked:
                    if name not in looks and set(uses(name)) <= made.keys():
                        given_over = {n: made[n] for n in uses(name)}
                        looks[name] = start(
                            f"drawing {name}", draw_view, name, step(name), given_over
                        )

        fills = {n: start(f"drawing {n}", draw_kept, n, cache / n) for n in fresh}
        if pool:
            ready()

        def drawn(name: str, work: Path) -> build.Render:
            keep = cache / name if name in used else None
            if pool is None:
                return render(name, objects[name], orca, work, step(name), keep)
            done = result(pool.submit(draw, name, work, step(name), keep))
            if keep is not None:
                with lock:
                    made[name] = keep
                ready()
            return done

        # Each plate's objects, a copy at a time: with everything.
        groups = [
            [n for n in plate for _ in range(objects[n].count)]
            for plate in ([] if only else plates)
        ]
        build.run(path, wanted, groups, drawn, plate_gap, whole=not only)
        for name, fill in fills.items():
            result(fill)
            with lock:
                made[name] = cache / name
            ready()
        for drawing in list(looks.values()):
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
