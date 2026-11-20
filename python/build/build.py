"""From a build123d project's objects, which cad.py draws, to its Orca projects.

Each object becomes gen/<dir>/<stem>-<object>.3mf, where <dir> is the project
file's directory in this repo: one object in Orca, with a part for each of its
pieces, each color on its own filament: the same one in every project of the
file, the plates' too. The file's earlier projects are removed first.

Beside them, cad.py writes <stem>-<name>.step of each object and view, for
FreeCAD, and <stem>-views.tsv listing them (see its project()).

Opening a project applies its settings on top of whatever presets Orca has
selected, and leaves everything else alone. `printer`, `process` and
`filament` are not settings but presets, which Orca keeps as selected: those
are for you to pick by hand. All of them are also shown, as the name of the
plate and of the object.

This uses Orca 2.5's "published" projects, which carry only the settings they
list. Orca reads no plate names from a project without settings, so a project
with none to apply still carries one, unlisted.

A piece's own settings apply to just its part. Orca keeps some settings for a
whole object, not a part: a brim or a raft, say. A piece with one of those
becomes an object of its own, where it is, beside the object of everything
else.

An object can pause, to put something inside it: once the print is z high, or
a layer sooner, so leave a layer's room over what goes in.

The plates ask for one more project, gen/<dir>/<stem>-all.3mf, with everything
in it, laid out on as many plates as it takes. It applies the settings its
objects share; one that only some have goes on those objects' own, if Orca lets
an object have it, and is left out with a warning if not. A plate pauses
wherever one of its objects does, and everything on it with it. Each plate is a
group of objects to print together, with `*N` for copies: "lid*2 base".

A group that doesn't fit one plate goes on several. Its objects are packed by
their bounding boxes, turned a quarter where that helps; nothing keeps room for
a prime tower. Each plate's name says which filament goes on which tool head.
With more colors than heads, those that never print together share one.
"""

import functools
import io
import math
import os
import sys
import tempfile
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from . import layout, orca, progress

ROOT = Path(__file__).resolve().parents[2]

# Keys among the settings that name presets, not settings.
PRESETS = {"printer", "process", "filament"}


@dataclass
class Render:
    """An object, drawn."""

    solids: list[orca.Solid]
    box: tuple[tuple[float, ...], tuple[float, ...]]  # the corners round them all
    pauses: list[float]  # the heights to pause at
    filaments: dict[str, str]  # what to call the filament each color stands for
    settings: dict[str, str]  # for the whole print, presets and all


def groups_of(lines: list[str]) -> list[list[str]]:
    """Each plate line's parts, a copy at a time: "lid*2 base" is lid, lid, base."""
    return [
        [
            part
            for item in line.split()
            for part, _, n in [item.partition("*")]
            for _ in range(int(n or 1))
        ]
        for line in lines
    ]


class Told:
    """Stands in for stdout while threads work, keeping what each prints apart."""

    def __enter__(self) -> Self:
        self.out, self.local = sys.stdout, threading.local()
        sys.stdout = self
        return self

    def __exit__(self, *exc: object) -> None:
        sys.stdout = self.out

    def write(self, text: str) -> int:
        return getattr(self.local, "said", self.out).write(text)

    def flush(self) -> None:
        self.out.flush()

    def to(self, said: io.StringIO, work, *args):
        """Run `work` in this thread, with what it prints going to `said`."""
        self.local.said = said
        try:
            return work(*args)
        finally:
            del self.local.said


def at_once[T](
    told: Told, pool: ThreadPoolExecutor, works: list[Callable[[], T]]
) -> list[T]:
    """Run each of `works` in the pool, all at once, and show what each prints
    as if each ran after the one before."""
    runs = [(said := io.StringIO(), pool.submit(told.to, said, w)) for w in works]
    done = []
    for said, run in runs:
        try:
            done.append(run.result())
        except BaseException:
            pool.shutdown(cancel_futures=True)
            raise
        finally:
            told.out.write(said.getvalue())
    return done


def combine(
    dst: Path,
    settings: dict[str, str],
    packed: list[list[tuple[str, float, float, bool]]],
    built: dict[str, orca.Assembly],
    colors: dict[str, list[str]],
    heads: dict[str, int],
    filaments: dict[str, str],
    own: dict[str, dict[str, str]],
    pauses: dict[str, list[float]],
) -> None:
    """Write one published project of the parts as packed, a plate for each of `packed`.

    `colors` are each part's and `heads` the tool head for each; `filaments` names
    the filament a color stands for, for the plates' names: its own hex, if not. `own` are the settings
    of each part alone, beyond `settings`. A plate pauses wherever one of its parts
    does, at each of `pauses`, which stops everything else on it there too.
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
            f"T{k} {filaments.get(c) or c or 'plain'}"
            for k, c in sorted({(heads[c], c) for p in count for c in colors[p]})
        )
        stops = sorted({z for p in count for z in pauses[p]})
        print(
            f"  plate {i + 1}: {name}: {tools}"
            + "".join(f", pause at {z:g} mm" for z in stops)
        )
        plates.append(orca.Plate(f"{name}: {tools}", placed, stops))
    objects = orca.write(dst, settings, plates)
    print(f"{dst.relative_to(ROOT)}: {len(plates)} plates, {objects} objects")


def run(
    file: Path,
    exports: list[str],
    groups: list[list[str]],
    render_part: Callable[[str, Path], Render],
) -> None:
    """Write the projects of a model file: one for each of `exports`, and one of
    the plates in `groups`, if any. `render_part` draws a part into a folder.
    """
    out_dir = ROOT / "gen" / file.parent.relative_to(ROOT)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{file.stem}-*.3mf"):
        old.unlink()

    built: dict[str, orca.Assembly] = {}
    wanted: dict[str, dict[str, str]] = {}  # each part's settings, presets and all
    filaments: dict[str, str] = {}  # the filament each color the file names stands for
    renders: dict[str, Render] = {}

    def build(part: str) -> tuple[Render, orca.Assembly]:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            print(f"{part}: build123d")
            with progress.stage(f"drawing {part}"):
                render = render_part(part, work)
            print(f"{part}: orca-slicer, assembling {len(render.solids)} parts")
            with progress.stage(f"assembling {part}"):
                return render, orca.assemble(render.solids, render.box, work)

    def export(part: str) -> None:
        with progress.stage(f"writing {part}"):
            target = out_dir / f"{file.stem}-{part}.3mf"
            render, assembly, order = renders[part], built[part], colors[part]
            note = ", ".join(f"{k}={v}" for k, v in render.settings.items())
            settings = {k: v for k, v in render.settings.items() if k not in PRESETS}
            name = f"{target.stem} [{note}]" if note else target.stem
            placed = orca.Placed(assembly, name, assembly.transform, heads)
            objects = orca.write(
                target, settings, [orca.Plate(note, [placed], render.pauses)]
            )
            print(
                f"{target.relative_to(ROOT)}: {len(render.solids)} parts, {len(order)} colors"
                + (f", {objects} objects" if objects > 1 else "")
                + "".join(f", pause at {z:g} mm" for z in render.pauses)
            )

    def plates() -> None:
        with progress.stage("writing plates"):
            # One project has one set of settings: those its parts agree on. The
            # rest go on each part's own objects, where Orca lets an object have one.
            parts = [wanted[p] for g in groups for p in g]
            shared = {
                k: v
                for k, v in parts[0].items()
                if k not in PRESETS and all(p.get(k) == v for p in parts)
            }
            rest = {
                p: {
                    k: v for k, v in wanted[p].items() if k not in PRESETS | set(shared)
                }
                for g in groups
                for p in g
            }
            ownable = orca.own_keys() if any(rest.values()) else frozenset()
            own = {
                p: {k: v for k, v in r.items() if k in ownable} for p, r in rest.items()
            }
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
                {p: r.pauses for p, r in renders.items()},
            )

    names = list(dict.fromkeys(exports + [p for g in groups for p in g]))
    progress.expect(2 * len(names) + len(exports) + bool(groups))
    with Told() as told, ThreadPoolExecutor(os.cpu_count()) as pool:
        # The parts at once: they wait on build123d's workers and Orca, a core
        # apiece.
        for part, (render, assembly) in zip(
            names, at_once(told, pool, [functools.partial(build, p) for p in names])
        ):
            renders[part], built[part] = render, assembly
            filaments.update(render.filaments)
            wanted[part] = render.settings
        colors = {
            p: list(dict.fromkeys(s.color for s in r.solids))
            for p, r in renders.items()
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
        # The projects at once too: they spend their time compressing, which
        # threads do side by side.
        at_once(
            told,
            pool,
            [functools.partial(export, p) for p in exports]
            + ([plates] if groups else []),
        )
