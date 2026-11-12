"""Export a .scad file's parts as Orca projects that apply the settings they need.

The .scad file lists its parts on an `// export:` line. An optional `// orca:`
line holds the slicer settings that matter for the print, as key=value pairs,
quoted where a value has spaces:

    // export: print test
    // orca: process="0.12 Fine" layer_height=0.1

Each key is an Orca setting, by its name in the preset JSON files. Opening the
project applies them on top of whatever presets Orca has selected, and leaves
everything else alone. `printer`, `process` and `filament` are not settings but
presets, which Orca keeps as selected: those are for you to pick by hand.

The whole line is also shown, as the name of the plate and of the object.

This uses Orca 2.5's "published" projects, which carry only the settings they
list. Orca reads no plate names from a project without settings, so a project
with none to apply still carries one, unlisted.

Each part becomes <out_dir>/<stem>-<part>.3mf: one object, with a part per
OpenSCAD object and color, each color on its own filament.

Orca's parts are numbered, unless the .scad file names them: one
`echo(piece = "name")` for each top-level statement, in order. For instance:

    module piece(name) { echo(piece = name); children(); }
    piece("lid") color("green") lid();

Usage: generate.py FILE.scad OUT_DIR
"""

import json
import re
import shlex
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

# Keys on the `// orca:` line that name presets, not settings.
PRESETS = {"printer", "process", "filament"}
# The U1's tool heads.
FILAMENTS = 4

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def directive(text: str, name: str) -> str:
    m = re.search(rf"^// {name}:(.*)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def write_stl(path: Path, tris: list) -> None:
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        f.writelines(
            struct.pack("<12fH", 0, 0, 0, *t[0], *t[1], *t[2], 0) for t in tris
        )


def split(src: Path, out: Path, names: list[str]) -> list[tuple[Path, str, str]]:
    """Write one STL per object and color in an OpenSCAD 3MF; return each with its color and name.

    `names` are the objects' names, if the .scad file gave one for each.
    """
    root = ET.fromstring(zipfile.ZipFile(src).read("3D/3dmodel.model"))
    colors = [
        b.get("displaycolor", "")[:7]
        for b in root.iterfind(".//m:basematerials/m:base", NS)
    ]
    parts = []
    objects = [
        o for o in root.iterfind(".//m:object", NS) if o.find("m:mesh", NS) is not None
    ]
    if names and len(names) != len(objects):
        print(
            f"  warning: {len(names)} piece names for {len(objects)} objects; numbering them"
        )
    named = len(names) == len(objects)
    for i, obj in enumerate(objects):
        mesh = obj.find("m:mesh", NS)
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
            label = f"{len(parts) + 1}-{color.lstrip('#') or 'plain'}"
            if named:
                label = names[i] if len(by_color) == 1 else f"{names[i]} {color}"
            path = out / f"{len(parts) + 1}.stl"
            write_stl(path, tris)
            parts.append((path, color, label))
    return parts


def annotate(
    src: Path,
    dst: Path,
    name: str,
    note: str,
    parts: list[tuple[str, int]],
    settings: dict[str, str],
) -> None:
    """Copy an Orca project as a published one, naming its object, parts and plate.

    `parts` is each part's name and filament, in order. `settings` are the ones to apply.
    """
    published = {
        "orca_published": "1",
        "orca_published_keys": json.dumps(list(settings)),
        # Orca imports only the geometry of a published project with no settings at all.
        "orca_published_config": "\n".join(
            f"{k} = {v}" for k, v in (settings or {"layer_height": "0.2"}).items()
        ),
    }
    # Orca escapes these values twice, and unescapes them twice.
    tags = "".join(
        f' <metadata name="{k}">{escape(escape(v))}</metadata>\n'
        for k, v in published.items()
    )

    def meta(key: str, value: str) -> str:
        return f"<metadata key={quoteattr(key)} value={quoteattr(value)}/>"

    each = iter(parts)

    def rename(m: re.Match) -> str:
        label, filament = next(each)
        return meta("name", label) + m[1] + meta("extruder", str(filament))

    with (
        zipfile.ZipFile(src) as zin,
        zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout,
    ):
        for item in zin.infolist():
            # A published project has no settings file; Orca's CLI writes its built-in defaults.
            if item.filename == "Metadata/project_settings.config":
                continue
            data = zin.read(item.filename)
            if item.filename == "3D/3dmodel.model":
                data = (
                    data.decode()
                    .replace(" <resources>", tags + " <resources>", 1)
                    .encode()
                )
            if item.filename == "Metadata/model_settings.config":
                xml = data.decode()
                # --assemble calls the one object "Assembly", and leaves the plate unnamed.
                xml = xml.replace(
                    meta("name", "Assembly"),
                    meta("name", f"{name} [{note}]" if note else name),
                    1,
                )
                xml = xml.replace(meta("plater_name", ""), meta("plater_name", note), 1)
                # Orca names each part after its file, and its own --load-filament-ids only
                # works with filament presets loaded.
                xml = re.sub(
                    r'<metadata key="name" value="\d+\.stl"/>((?:(?!<part ).)*?)'
                    r'<metadata key="extruder" value="1"/>',
                    rename,
                    xml,
                    flags=re.DOTALL,
                )
                data = xml.encode()
            zout.writestr(item, data)


def generate(scad: Path, out_dir: Path) -> None:
    text = scad.read_text()
    items = shlex.split(directive(text, "orca"))
    note = ", ".join(items)
    settings = dict(i.split("=", 1) for i in items if i.split("=")[0] not in PRESETS)

    for part in directive(text, "export").split():
        target = out_dir / f"{scad.stem}-{part}.3mf"
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            mesh = work / "mesh.3mf"
            # Not --quiet, which would drop the echoes.
            done = subprocess.run(
                [
                    "openscad",
                    "--enable=lazy-union",
                    "-D",
                    f'part="{part}"',
                    "-o",
                    mesh,
                    scad,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            log = done.stderr.splitlines()
            print(
                *[f"  {line}" for line in log if re.match("WARNING|ERROR|TRACE", line)],
                sep="\n",
                end="",
            )
            if done.returncode:
                sys.exit(f"openscad failed on {part}:\n{done.stderr}")
            names = [
                m[1]
                for line in log
                if (m := re.fullmatch(r'ECHO: piece = "(.*)"', line))
            ]
            parts = split(mesh, work, names)
            # Filaments in order of each color's first appearance.
            order = list(dict.fromkeys(c for _, c, _ in parts))
            if len(order) > FILAMENTS:
                print(
                    f"  warning: {len(order)} colors for {FILAMENTS} filaments; extras go on filament 1"
                )
            ids = [
                order.index(c) + 1 if order.index(c) < FILAMENTS else 1
                for _, c, _ in parts
            ]
            # Orca writes result.json into its working directory.
            done = subprocess.run(
                [
                    "orca-slicer",
                    "--assemble",
                    "--export-3mf",
                    work / "project.3mf",
                    *[p for p, _, _ in parts],
                ],
                check=False,
                cwd=work,
                capture_output=True,
                text=True,
            )
            if not (work / "project.3mf").exists():
                sys.exit(f"orca-slicer failed on {part}:\n{done.stdout}{done.stderr}")
            annotate(
                work / "project.3mf",
                target,
                target.stem,
                note,
                [(label, i) for (_, _, label), i in zip(parts, ids)],
                settings,
            )
        print(f"{target}: {len(parts)} parts, {len(order)} colors")


if __name__ == "__main__":
    generate(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
