"""From a model's parts to its Orca projects, whatever drew them: OpenSCAD
(generate.py) or build123d (cad.py). generate.py's docstring has what comes out."""

import io
import math
import os
import sys
import tempfile
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Self

from . import layout, orca, scad

ROOT = Path(__file__).resolve().parents[2]

# Keys among the settings that name presets, not settings.
PRESETS = {"printer", "process", "filament"}


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


def run(
    file: Path,
    exports: list[str],
    groups: list[list[str]],
    tool: str,
    render_part: Callable[[str, Path], scad.Render],
) -> None:
    """Write the projects of a model file: one for each of `exports`, and one of
    the plates in `groups`, if any. `render_part` renders a part into a folder;
    `tool` is what to say is doing it.
    """
    out_dir = ROOT / "gen" / file.parent.relative_to(ROOT)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{file.stem}-*.3mf"):
        old.unlink()

    built: dict[str, orca.Assembly] = {}
    wanted: dict[str, dict[str, str]] = {}  # each part's settings, presets and all
    filaments: dict[str, str] = {}  # the filament each color the file names stands for
    renders: dict[str, scad.Render] = {}

    def build(part: str) -> tuple[scad.Render, orca.Assembly]:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            print(f"{part}: {tool}")
            render = render_part(part, work)
            if render.pauses and any(part in g for g in groups):
                print(f"  warning: {file.stem}-all won't pause for {part}")
            print(f"{part}: orca-slicer, assembling {len(render.solids)} parts")
            return render, orca.assemble(render.solids, render.box, work)

    # The parts at once: they wait on OpenSCAD and Orca, a core apiece.
    names = list(dict.fromkeys(exports + [p for g in groups for p in g]))
    with Told() as told, ThreadPoolExecutor(os.cpu_count()) as pool:
        runs = [
            (said := io.StringIO(), pool.submit(told.to, said, build, part))
            for part in names
        ]
        for part, (said, run) in zip(names, runs):
            try:
                renders[part], built[part] = run.result()
            except BaseException:
                pool.shutdown(cancel_futures=True)
                raise
            finally:
                told.out.write(said.getvalue())
            filaments.update(renders[part].filaments)
            wanted[part] = renders[part].settings
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
