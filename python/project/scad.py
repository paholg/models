"""The OpenSCAD side: render a part of a .scad file, and split what comes out into
an STL for each object and color, with what the file's echoes say of them."""

import json
import re
import shlex
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .tree import attr, child

# The 3MF core namespace.
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS = {"m": CORE}
# What to call a color in a plate's name: OpenSCAD's 3MF has only its value.
COLOR_NAMES = {
    "#000000": "black", "#FFFFFF": "white", "#FF0000": "red", "#0000FF": "blue",
    "#FFFF00": "yellow", "#008000": "green", "#FFA500": "orange", "#808080": "gray",
    "#C0C0C0": "silver", "#D2B48C": "tan", "#B0C4DE": "lightsteelblue",
    "#2F4F4F": "darkslategray", "#FF8C00": "darkorange", "#2E8B57": "seagreen",
    "#8B4513": "saddlebrown", "#D3D3D3": "lightgray", "#800080": "purple",
    "#FFC0CB": "pink", "#A52A2A": "brown", "#FFD700": "gold", "#000080": "navy",
    "#008080": "teal", "#00FF00": "lime", "#00FFFF": "cyan", "#FF00FF": "magenta",
}  # fmt: skip

# Each color a file has named, as OpenSCAD writes it.
_values: dict[str, str] = {}


@dataclass
class Solid:
    """One object of one color, as an STL."""

    stl: Path
    color: str
    name: str
    settings: dict[str, str]  # its piece's own
    piece: str  # its piece's name, if the pieces have names


@dataclass
class Render:
    """A part of a .scad file, rendered."""

    solids: list[Solid]
    box: tuple[tuple[float, ...], tuple[float, ...]]  # the corners round them all
    pauses: list[float]  # the heights to pause at
    filaments: dict[str, str]  # the filament a color stands for, where the file says


def pairs(line: str) -> dict[str, str]:
    """The key=value pairs on an orca line."""
    return dict(i.split("=", 1) for i in shlex.split(line))


def color_name(color: str) -> str:
    return COLOR_NAMES.get(color.upper(), color or "plain")


def write_stl(path: Path, tris: list) -> None:
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        f.writelines(
            struct.pack("<12fH", 0, 0, 0, *t[0], *t[1], *t[2], 0) for t in tris
        )


def meshes(path: Path) -> tuple[list[str], list[ET.Element]]:
    """An OpenSCAD 3MF's colors, and its objects that have a mesh."""
    root = ET.fromstring(zipfile.ZipFile(path).read("3D/3dmodel.model"))
    colors = [
        b.get("displaycolor", "")[:7]
        for b in root.iterfind(".//m:basematerials/m:base", NS)
    ]
    objects = [
        o for o in root.iterfind(".//m:object", NS) if o.find("m:mesh", NS) is not None
    ]
    return colors, objects


def color_values(names: set[str]) -> dict[str, str]:
    """What OpenSCAD makes of each color name, as it writes it in a 3MF."""
    if new := sorted(names - set(_values)):
        with tempfile.TemporaryDirectory() as tmp:
            scad, mesh = Path(tmp) / "colors.scad", Path(tmp) / "colors.3mf"
            scad.write_text(
                "".join(
                    f"translate([{2 * i}, 0, 0]) color({json.dumps(n)}) cube(1);\n"
                    for i, n in enumerate(new)
                )
            )
            subprocess.run(
                ["openscad", "--enable=lazy-union", "-o", mesh, scad],
                check=True,
                capture_output=True,
            )
            colors, objects = meshes(mesh)
        # A color is on the object's triangles, if not the object.
        for n, o in zip(new, objects):
            triangle = child(o, ".//m:triangle", NS)
            _values[n] = colors[int(triangle.get("p1", o.get("pindex", "0")))]
    return {n: _values[n] for n in names}


def split(
    src: Path, out: Path, pieces: list[tuple[str, str]], by_color: dict[str, str]
) -> tuple[list[Solid], tuple]:
    """Write one STL per object and color in an OpenSCAD 3MF.

    Returns them, and the corners of the box round them all. `pieces` are the
    objects' names and orca lines, if the .scad file gave one for each; `by_color`
    the names it gave by color.
    """
    colors, objects = meshes(src)
    solids: list[Solid] = []
    points = []
    if pieces and len(pieces) != len(objects):
        print(
            f"  warning: {len(pieces)} piece names for {len(objects)} objects; numbering them"
        )
    named = len(pieces) == len(objects)
    for i, obj in enumerate(objects):
        mesh = child(obj, "m:mesh", NS)
        verts = [
            tuple(float(attr(v, k)) for k in "xyz")
            for v in mesh.iterfind("m:vertices/m:vertex", NS)
        ]
        tris_by_color: dict[int, list] = {}
        for t in mesh.iterfind("m:triangles/m:triangle", NS):
            k = int(t.get("p1", obj.get("pindex", "0")))
            tris_by_color.setdefault(k, []).append(
                [verts[int(attr(t, v))] for v in ("v1", "v2", "v3")]
            )
        if len(tris_by_color) > 1:
            print(
                f"  warning: {obj.get('name')} mixes colors on one solid; give each color"
                " its own top-level statement in the .scad, or its parts won't be closed"
            )
        for k, tris in sorted(tris_by_color.items()):
            color = colors[k] if k < len(colors) else ""
            # Named for its color, with a number after the first of one color.
            label = by_color.get(color, color_name(color))
            if n := sum(1 for s in solids if s.color == color):
                label += f" {n + 1}"
            own, piece = {}, ""
            if named:
                piece, line = pieces[i]
                label = (
                    piece if len(tris_by_color) == 1 else f"{piece} {color_name(color)}"
                )
                own = pairs(line)
            path = out / f"{len(solids) + 1}.stl"
            write_stl(path, tris)
            solids.append(Solid(path, color, label, own, piece))
            points += [v for t in tris for v in t]
    box = tuple(tuple(f(v[k] for v in points) for k in range(3)) for f in (min, max))
    return solids, box


def render(scad: Path, part: str, work: Path) -> Render:
    """Render one part of a .scad file into `work`, showing OpenSCAD's log."""
    mesh = work / "mesh.3mf"
    # Not --quiet, which would drop the echoes.
    openscad = subprocess.Popen(
        ["openscad", "--enable=lazy-union", "-D", f'part="{part}"', "-o", mesh, scad],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert openscad.stderr is not None  # a pipe, as asked for
    # Show the log as it comes.
    log = []
    for line in openscad.stderr:
        log.append(line.rstrip("\n"))
        if log[-1]:
            print(f"  {log[-1]}")
    if openscad.wait():
        sys.exit(f"openscad failed on {part}")

    def echoes(pattern: str) -> list[re.Match]:
        return [m for line in log if (m := re.fullmatch(f"ECHO: {pattern}", line))]

    pieces = [
        (m[1], m[2] or "") for m in echoes(r'piece = "(.*?)"(?:, orca = "(.*)")?')
    ]
    pauses = [float(m[1]) for m in echoes(r"pause = ([\d.]+)")]
    # A color's name: what to call whatever is that color, and its filament.
    named = {
        m[1]: (m[2], m[3])
        for m in echoes(r'color = "(.*?)", piece = "(.*?)"(?:, filament = "(.*?)")?')
    }
    values = color_values(set(named))
    solids, box = split(
        mesh, work, pieces, {values[c]: n for c, (n, _) in named.items()}
    )
    return Render(
        solids, box, pauses, {values[c]: f for c, (_, f) in named.items() if f}
    )
