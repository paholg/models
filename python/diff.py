"""Show what a change to the .scad files does to the prints, in OpenSCAD.

Takes the files that differ between a commit and the working tree, untracked
ones too, and renders each part of each design they reach, before and after: a
design is a .scad file with an `// export:` line (see generate.py), and a
change reaches it through what it includes, uses and imports. A changed .scad
file that is in no design is rendered as it is.

Each part that came out different goes in tmp/diff/diff.scad, in rows: green
for what the change adds, red for what it takes away, and what stays in clear
gray, which `common = false` hides. The commit's files are in tmp/diff/old, and
each part's meshes in tmp/diff/parts.

Usage: diff.py [REF] [--no-open]
"""

import argparse
import io
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from generate import directive

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp/diff"
OLD = OUT / "old"
# Between the parts, and for a part's label in front of it, in mm.
GAP = 20
LABEL = 12
# What a file brings in: `include <a>`, `use <a>`, `import("a")`.
DEPENDENCY = re.compile(r'(?:include|use)\s*<([^>]+)>|import\(\s*"([^"]+)"')
# The solids of a part's diff, with the boolean of old and new that makes each.
KINDS = {"added": "difference", "removed": "difference", "common": "intersection"}
# A solid thinner than this on average, in mm, is no change: OpenSCAD doesn't
# render a part to the same triangles twice, and what is between them is a
# film some millionths of a millimeter thick.
FILM = 1e-3
TRIANGLE = np.dtype([("normal", "<f4", 3), ("points", "<f4", (3, 3)), ("", "<u2")])
COLORS = {"added": '"green"', "removed": '"red"', "common": '"gray", 0.25'}


@dataclass
class Part:
    file: Path  # in the repo
    name: str  # "" for the whole of a file with no parts

    @property
    def label(self) -> str:
        return f"{self.file.with_suffix('')} {self.name}".strip()

    @property
    def dir(self) -> Path:
        return OUT / "parts" / self.label.replace("/", "-").replace(" ", "-")


def git(*args: str) -> list[str]:
    run = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return run.stdout.splitlines()


def reach(tree: Path, file: Path, seen: set[Path]) -> set[Path]:
    """`file` and all it brings in, as paths in `tree`."""
    path = tree / file
    if file in seen or not path.is_file():
        return seen
    seen.add(file)
    if file.suffix == ".scad":
        for m in DEPENDENCY.finditer(path.read_text()):
            found = (path.parent / (m[1] or m[2])).resolve()
            if found.is_relative_to(tree):
                reach(tree, found.relative_to(tree), seen)
    return seen


def parts_of(tree: Path, file: Path) -> list[str]:
    path = tree / file
    return directive(path.read_text(), "export").split() if path.is_file() else []


def openscad(scad: Path, out: Path, part: str | None = None) -> str:
    """Render to an STL. Returns what went wrong, if the STL isn't there."""
    define = ["-D", f'part="{part}"'] if part else []
    run = subprocess.run(
        ["openscad", *define, "--export-format", "binstl", "-o", out, scad],
        check=False,
        capture_output=True,
        text=True,
    )
    if out.exists() and not run.returncode:
        return ""
    out.unlink(missing_ok=True)
    errors = [line for line in run.stderr.splitlines() if "ERROR" in line]
    return "\n".join(errors) or "empty"


def render(job: tuple[Part, Path, str]) -> str:
    part, tree, side = job
    if not (tree / part.file).is_file():
        return "empty"
    part.dir.mkdir(parents=True, exist_ok=True)
    return openscad(tree / part.file, part.dir / f"{side}.stl", part.name or None)


def boolean(job: tuple[Part, str]) -> None:
    """Write one solid of a part's diff, if there is anything in it."""
    part, kind = job
    old, new = part.dir / "old.stl", part.dir / "new.stl"
    first, second = (old, new) if kind == "removed" else (new, old)
    if not first.exists() or not second.exists():
        # All of the one there is has been added, or removed.
        if kind != "common" and first.exists():
            shutil.copy(first, part.dir / f"{kind}.stl")
        return
    scad = part.dir / f"{kind}.scad"
    scad.write_text(
        f'{KINDS[kind]}() {{ import("{first.name}"); import("{second.name}"); }}\n'
    )
    out = part.dir / f"{kind}.stl"
    if not openscad(scad, out) and kind != "common" and thickness(out) < FILM:
        out.unlink()


def triangles(stl: Path) -> np.ndarray:
    """A binary STL's triangles, as three points each."""
    return np.fromfile(stl, TRIANGLE, offset=84)["points"].astype(float)


def thickness(stl: Path) -> float:
    """How thick a solid is on average: its volume over half its surface."""
    a, b, c = triangles(stl).transpose(1, 0, 2)
    volume = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() / 2
    return 2 * volume / area if area else 0.0


def box(stl: Path) -> tuple[np.ndarray, np.ndarray]:
    """The corners round a binary STL."""
    points = triangles(stl).reshape(-1, 3)
    return points.min(axis=0), points.max(axis=0)


def viewer(parts: list[Part], ref: str) -> Path:
    lines = [
        f"// What the working tree changes from {ref}, by python/diff.py.",
        "// Green is added, red removed.",
        "",
        "// Show what stays, too.",
        "common = true;",
        "",
    ]
    # Each part's solids, and the corners round them.
    found = []
    for part in parts:
        there = [k for k in KINDS if (part.dir / f"{k}.stl").exists()]
        boxes = [box(part.dir / f"{k}.stl") for k in there]
        low = np.min([b[0] for b in boxes], axis=0)
        high = np.max([b[1] for b in boxes], axis=0)
        # No narrower than its label.
        width = max(high[0] - low[0], 5 * 0.8 * len(part.label)) + GAP
        found.append((part, there, low, width, high[1] - low[1] + GAP + LABEL))
    # In rows, back to front, about as deep in all as they are wide.
    widest = max(
        max(w for *_, w, _ in found), 1.2 * sum(w * d for *_, w, d in found) ** 0.5
    )
    x = y = deep = 0.0
    for part, there, low, width, depth in found:
        if x and x + width > widest:
            x, y, deep = 0.0, y - deep, 0.0
        deep = max(deep, depth)
        at = f"[{x - low[0]:.3f}, {y - depth - low[1]:.3f}, 0]"
        lines.append(f"// {part.label}")
        lines.append(
            f'color("black") translate([{x:.3f}, {y - depth - LABEL:.3f}, 0])'
            f' linear_extrude(0.4) text("{part.label}", size = 5);'
        )
        # The clear one last, for what is behind it to show through.
        for kind in there:
            path = (part.dir / f"{kind}.stl").relative_to(OUT)
            show = "if (common) " if kind == "common" else ""
            lines.append(
                f'{show}translate({at}) color({COLORS[kind]}) import("{path}");'
            )
        lines.append("")
        x += width
    path = OUT / "diff.scad"
    path.write_text("\n".join(lines))
    return path


def diff(ref: str, show: bool) -> None:
    changed = {
        Path(f)
        for f in git("diff", "--name-only", ref)
        + git("ls-files", "--others", "--exclude-standard")
    }
    if not changed:
        sys.exit(f"nothing differs from {ref}")

    shutil.rmtree(OUT, ignore_errors=True)
    OLD.mkdir(parents=True)
    archive = subprocess.run(
        ["git", "archive", ref], cwd=ROOT, check=True, capture_output=True
    )
    subprocess.run(["tar", "-x", "-C", OLD], input=archive.stdout, check=True)

    files = {Path(f) for f in git("ls-files", "-co", "--exclude-standard", "*.scad")}
    files |= {f.relative_to(OLD) for f in OLD.rglob("*.scad")}
    parts: list[Part] = []
    reached: set[Path] = set()
    for file in sorted(files):
        names = dict.fromkeys(parts_of(OLD, file) + parts_of(ROOT, file))
        brings = reach(OLD, file, set()) | reach(ROOT, file, set())
        if names and brings & changed:
            parts += [Part(file, name) for name in names]
            reached |= brings
    # What is in no design: a file of one print, or a library nothing uses.
    parts += [Part(f, "") for f in sorted(changed - reached) if f.suffix == ".scad"]
    if not parts:
        sys.exit("the changes reach no .scad file")

    print(f"rendering {len(parts)} parts, at {ref} and now")
    jobs = [(p, t, s) for p in parts for t, s in ((OLD, "old"), (ROOT, "new"))]
    with ThreadPoolExecutor() as pool:
        for (part, _, side), error in zip(jobs, pool.map(render, jobs)):
            if error and error != "empty":
                print(f"  {part.label}, {side}: {error}".replace("\n", "\n    "))
        # The same bytes are the same solid; the rest takes a closer look.
        differ = [
            p
            for p in parts
            if not (p.dir / "old.stl").exists()
            or not (p.dir / "new.stl").exists()
            or (p.dir / "old.stl").read_bytes() != (p.dir / "new.stl").read_bytes()
        ]
        list(pool.map(boolean, [(p, k) for p in differ for k in KINDS]))

    shown = []
    for part in differ:
        has = [k for k in ("added", "removed") if (part.dir / f"{k}.stl").exists()]
        if has:
            shown.append(part)
            print(f"  {part.label}: {', '.join(has)}")
    print(f"  {len(parts) - len(shown)} of {len(parts)} parts are the same")
    if not shown:
        return
    path = viewer(shown, ref)
    print(path.relative_to(ROOT))
    if show:
        subprocess.Popen(
            ["openscad", path],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ref", nargs="?", default="HEAD")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    diff(args.ref, not args.no_open)
