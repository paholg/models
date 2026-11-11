"""Export a .scad file's parts as Orca projects with slicer settings baked in.

The .scad file lists its parts on an `// export:` line. An optional `// orca:`
line holds settings for all of them, as key=value pairs, quoted where a value
has spaces:

    // export: print test
    // orca: process="0.12 Fine @Snapmaker U1 (0.4 nozzle)" layer_height=0.1

`printer`, `process` and `filament` name the presets to start from; any other
key is an Orca setting, by its name in the preset JSON files, and shows in Orca
as changed from the preset.

Each part becomes <out_dir>/<stem>-<part>.3mf: one object, with a part per
OpenSCAD object and color, each color on its own filament.

Usage: generate.py FILE.scad OUT_DIR
"""

import re
import shlex
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PRESETS = Path.home() / ".config/OrcaSlicer/system"
DEFAULTS = {
    "printer": "Snapmaker U1 (0.4 nozzle)",
    "process": "0.20 Standard @Snapmaker U1 (0.4 nozzle)",
    "filament": "Generic PLA @System",
}
# The U1's tool heads.
FILAMENTS = 4

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def directive(text: str, name: str) -> str:
    m = re.search(rf"^// {name}:(.*)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def preset(kind: str, name: str) -> Path:
    found = sorted(PRESETS.glob(f"*/{kind}/{name}.json"))
    if not found:
        sys.exit(f"no {kind} preset named {name!r} under {PRESETS}")
    return found[0]


def write_stl(path: Path, tris: list) -> None:
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        f.writelines(
            struct.pack("<12fH", 0, 0, 0, *t[0], *t[1], *t[2], 0) for t in tris
        )


def split(src: Path, out: Path) -> list[tuple[Path, str]]:
    """Write one STL per object and color in an OpenSCAD 3MF; return each with its color."""
    root = ET.fromstring(zipfile.ZipFile(src).read("3D/3dmodel.model"))
    colors = [
        b.get("displaycolor", "")[:7]
        for b in root.iterfind(".//m:basematerials/m:base", NS)
    ]
    parts = []
    for obj in root.iterfind(".//m:object", NS):
        mesh = obj.find("m:mesh", NS)
        if mesh is None:
            continue
        verts = [
            (float(v.get("x")), float(v.get("y")), float(v.get("z")))
            for v in mesh.iterfind("m:vertices/m:vertex", NS)
        ]
        by_color: dict[int, list] = {}
        for t in mesh.iterfind("m:triangles/m:triangle", NS):
            k = int(t.get("p1", obj.get("pindex", "0")))
            by_color.setdefault(k, []).append(
                [verts[int(t.get(v))] for v in ("v1", "v2", "v3")]
            )
        if len(by_color) > 1:
            print(
                f"  warning: {obj.get('name')} mixes colors on one solid; give each color"
                " its own top-level statement in the .scad, or its parts won't be closed"
            )
        for k, tris in sorted(by_color.items()):
            color = colors[k] if k < len(colors) else ""
            path = out / f"{len(parts) + 1}-{color.lstrip('#') or 'plain'}.stl"
            write_stl(path, tris)
            parts.append((path, color))
    return parts


def generate(scad: Path, out_dir: Path) -> None:
    text = scad.read_text()
    opts = dict(DEFAULTS)
    settings = {}
    for item in shlex.split(directive(text, "orca")):
        key, _, value = item.partition("=")
        (opts if key in opts else settings)[key] = value

    filament = preset("filament", opts["filament"])
    load = [
        "--load-settings",
        f"{preset('machine', opts['printer'])};{preset('process', opts['process'])}",
        "--load-filaments",
        ";".join([str(filament)] * FILAMENTS),
    ]
    for key, value in settings.items():
        load += [f"--{key.replace('_', '-')}", value]

    for part in directive(text, "export").split():
        target = out_dir / f"{scad.stem}-{part}.3mf"
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            mesh = work / "mesh.3mf"
            subprocess.run(
                [
                    "openscad",
                    "-q",
                    "--enable=lazy-union",
                    "-D",
                    f'part="{part}"',
                    "-o",
                    mesh,
                    scad,
                ],
                check=True,
            )
            parts = split(mesh, work)
            # Filaments in order of each color's first appearance.
            order = list(dict.fromkeys(c for _, c in parts))
            if len(order) > FILAMENTS:
                print(
                    f"  warning: {len(order)} colors for {FILAMENTS} filaments; extras go on filament 1"
                )
            ids = [
                order.index(c) + 1 if order.index(c) < FILAMENTS else 1
                for _, c in parts
            ]
            shown = [c or "#808080" for c in order[:FILAMENTS]]
            shown += [shown[-1]] * (FILAMENTS - len(shown))
            # Orca writes result.json into its working directory.
            done = subprocess.run(
                [
                    "orca-slicer",
                    *load,
                    "--filament-colour",
                    ";".join(shown),
                    "--load-filament-ids",
                    ",".join(map(str, ids)),
                    "--assemble",
                    "--export-3mf",
                    target,
                    *[p for p, _ in parts],
                ],
                check=False,
                cwd=work,
                capture_output=True,
                text=True,
            )
            if not target.exists():
                sys.exit(f"orca-slicer failed on {part}:\n{done.stdout}{done.stderr}")
        print(f"{target}: {len(parts)} parts, {len(order)} colors")


if __name__ == "__main__":
    generate(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
