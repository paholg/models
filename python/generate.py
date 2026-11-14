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

Each part becomes gen/<dir>/<stem>-<part>.3mf, where <dir> is the .scad file's
directory in this repo: one object, with a part per OpenSCAD object and color,
each color on its own filament. The file's earlier projects are removed first.

Orca's parts are named for their colors, unless the .scad file names them. One
way is by color, for a file that draws each color in one go:
`echo(color = "green", piece = "name")` names whatever is that color, and it's
no matter if nothing is. A `filament = "name"` after those names the filament
the color stands for, for the plates' names (see `// plate:`).

The other is one `echo(piece = "name")` for each top-level statement, in order.
For instance:

    module piece(name) { echo(piece = name); children(); }
    piece("lid") color("green") lid();

A piece can carry settings of its own, which Orca applies to just its parts: an
`orca` string beside the name, written like the `// orca:` line.

    module piece(name, orca = "") { echo(piece = name, orca = orca); children(); }
    piece("lid", "bottom_surface_pattern=concentric") color("green") lid();

A print can pause, to put something inside it: `echo(pause = z)` pauses once
the print is z high, before the layer above. That takes a `layer_height` on the
`// orca:` line, to find that layer.

`// plate:` lines ask for one more project, gen/<dir>/<stem>-all.3mf, with
everything in it, laid out on as many plates as it takes. Each line is a group
of parts to print together, with `*N` for copies:

    // plate: lid*2 base
    // plate: feet*4

A group that doesn't fit one plate goes on several. Its parts are packed by
their bounding boxes, turned a quarter where that helps; nothing keeps room
for a prime tower. There being more colors than tool heads, each plate's name
says which filament goes on which: they're shared out to change as few as can
be from one plate to the next, in the order of the lines.

Usage: generate.py FILE.scad
"""

import io
import json
import math
import random
import re
import shlex
import struct
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parents[1]

# Keys on the `// orca:` line that name presets, not settings.
PRESETS = {"printer", "process", "filament"}
# The U1's tool heads.
FILAMENTS = 4
# The U1's bed, and how Orca spaces its plates: a fifth of the bed apart.
BED = (270.0, 270.0)
PLATE_STRIDE = 1.2
# Around a plate's parts, and between them.
PLATE_MARGIN = 3.0
PLATE_GAP = 5.0
# Orders to try packing a group's parts in.
PACK_TRIES = 300
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

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def color_name(color: str) -> str:
    return COLOR_NAMES.get(color.upper(), color or "plain")


def directives(text: str, name: str) -> list[str]:
    return [m.strip() for m in re.findall(rf"^// {name}:(.*)$", text, re.MULTILINE)]


def directive(text: str, name: str) -> str:
    return next(iter(directives(text, name)), "")


@dataclass
class Built:
    """A part, as Orca assembled it: one object, still unnamed."""

    project: bytes  # Orca's 3MF
    parts: list[tuple[str, str, dict[str, str]]]  # each one's name, color and settings
    box: tuple[tuple[float, ...], tuple[float, ...]]  # its corners, as in the .scad


def write_stl(path: Path, tris: list) -> None:
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        f.writelines(
            struct.pack("<12fH", 0, 0, 0, *t[0], *t[1], *t[2], 0) for t in tris
        )


def pairs(line: str) -> dict[str, str]:
    """The key=value pairs on an orca line."""
    return dict(i.split("=", 1) for i in shlex.split(line))


def color_values(names: list[str]) -> dict[str, str]:
    """What OpenSCAD makes of each color name, as it writes it in a 3MF."""
    with tempfile.TemporaryDirectory() as tmp:
        scad, mesh = Path(tmp) / "colors.scad", Path(tmp) / "colors.3mf"
        scad.write_text(
            "".join(
                f"translate([{2 * i}, 0, 0]) color({json.dumps(n)}) cube(1);\n"
                for i, n in enumerate(names)
            )
        )
        subprocess.run(
            ["openscad", "--enable=lazy-union", "-o", mesh, scad],
            check=True,
            capture_output=True,
        )
        root = ET.fromstring(zipfile.ZipFile(mesh).read("3D/3dmodel.model"))
    bases = [
        b.get("displaycolor", "")[:7]
        for b in root.iterfind(".//m:basematerials/m:base", NS)
    ]
    objects = [
        o for o in root.iterfind(".//m:object", NS) if o.find("m:mesh", NS) is not None
    ]
    # A color is on the object's triangles, if not the object.
    return {
        n: bases[int(o.find(".//m:triangle", NS).get("p1", o.get("pindex", "0")))]
        for n, o in zip(names, objects)
    }


def split(
    src: Path, out: Path, pieces: list[tuple[str, str]], by_color_name: dict[str, str]
) -> tuple[list[tuple[Path, str, str, dict[str, str]]], tuple]:
    """Write one STL per object and color in an OpenSCAD 3MF.

    Returns each with its color, name and own settings, and the corners of the box
    round them all. `pieces` are the objects' names and orca lines, if the .scad
    file gave one for each; `by_color_name` the names it gave by color.
    """
    root = ET.fromstring(zipfile.ZipFile(src).read("3D/3dmodel.model"))
    colors = [
        b.get("displaycolor", "")[:7]
        for b in root.iterfind(".//m:basematerials/m:base", NS)
    ]
    parts = []
    points = []
    objects = [
        o for o in root.iterfind(".//m:object", NS) if o.find("m:mesh", NS) is not None
    ]
    if pieces and len(pieces) != len(objects):
        print(
            f"  warning: {len(pieces)} piece names for {len(objects)} objects; numbering them"
        )
    named = len(pieces) == len(objects)
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
            # Named for its color, with a number after the first of one color.
            label = by_color_name.get(color, color_name(color))
            if n := sum(1 for p in parts if p[1] == color):
                label += f" {n + 1}"
            own = {}
            if named:
                name, line = pieces[i]
                label = name if len(by_color) == 1 else f"{name} {color_name(color)}"
                own = pairs(line)
            path = out / f"{len(parts) + 1}.stl"
            write_stl(path, tris)
            parts.append((path, color, label, own))
            points += [v for t in tris for v in t]
    box = tuple(tuple(f(v[k] for v in points) for k in range(3)) for f in (min, max))
    return parts, box


def meta(key: str, value: str) -> str:
    return f"<metadata key={quoteattr(key)} value={quoteattr(value)}/>"


def published_tags(settings: dict[str, str]) -> str:
    """What makes a project a published one, applying `settings`: for its model."""
    published = {
        "orca_published": "1",
        "orca_published_keys": json.dumps(list(settings)),
        # Orca imports only the geometry of a published project with no settings at all.
        "orca_published_config": "\n".join(
            f"{k} = {v}" for k, v in (settings or {"layer_height": "0.2"}).items()
        ),
    }
    # Orca escapes these values twice, and unescapes them twice.
    return "".join(
        f' <metadata name="{k}">{escape(escape(v))}</metadata>\n'
        for k, v in published.items()
    )


def name_parts(xml: str, parts: list[tuple[str, int, dict[str, str]]]) -> str:
    """Give the parts in Orca's model settings their names, filaments and settings.

    Orca names each part after its file, and its own --load-filament-ids only works
    with filament presets loaded.
    """
    each = iter(parts)

    def rename(m: re.Match) -> str:
        label, filament, own = next(each)
        return (
            meta("name", label)
            + m[1]
            + meta("extruder", str(filament))
            + "".join(meta(k, v) for k, v in own.items())
        )

    return re.sub(
        r'<metadata key="name" value="\d+\.stl"/>((?:(?!<part ).)*?)'
        r'<metadata key="extruder" value="1"/>',
        rename,
        xml,
        flags=re.DOTALL,
    )


def annotate(
    src: Path,
    dst: Path,
    name: str,
    note: str,
    parts: list[tuple[str, int, dict[str, str]]],
    settings: dict[str, str],
    pauses: list[float],
) -> None:
    """Copy an Orca project as a published one, naming its object, parts and plate.

    `parts` is each part's name, filament and own settings, in order. `settings` are
    the ones to apply to everything. `pauses` are the heights to pause at.
    """
    tags = published_tags(settings)

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
                data = name_parts(xml, parts).encode()
            zout.writestr(item, data)
        if pauses:
            # Orca gives each of these to the layer whose top is nearest, and runs it
            # before that layer: so name the layer above the pause. Type 1 is a pause.
            layer = float(settings["layer_height"])
            zout.writestr(
                "Metadata/custom_gcode_per_layer.xml",
                '<?xml version="1.0" encoding="utf-8"?>\n<custom_gcodes_per_layer>\n'
                '<plate>\n<plate_info id="1"/>\n'
                + "".join(
                    f'<layer top_z="{z + layer:.4f}" type="1" extruder="1" color=""'
                    ' extra="" gcode=""/>\n'
                    for z in pauses
                )
                + '<mode value="MultiExtruder"/>\n</plate>\n</custom_gcodes_per_layer>\n',
            )


def pack(group: list[str], sizes: dict[str, tuple[float, float]]) -> list[list[tuple]]:
    """Lay a group's parts out on as few plates as it can.

    Returns each plate's (part, x, y, turned): where the part's box goes on the bed,
    and whether it's turned a quarter. The best of many orders: biggest first, then
    shuffled ones.
    """
    rng = random.Random(0)
    orders = [
        sorted(group, key=lambda p: -max(sizes[p])),
        sorted(group, key=lambda p: -sizes[p][0] * sizes[p][1]),
    ]
    orders += [rng.sample(group, len(group)) for _ in range(PACK_TRIES)]
    return min((pack_in_order(o, sizes) for o in orders), key=len)


def pack_in_order(
    group: list[str], sizes: dict[str, tuple[float, float]]
) -> list[list[tuple]]:
    """Lay parts out in the order given, each on the first plate with room, where it
    leaves the least of the free rectangle it best fits (MaxRects)."""
    room = [BED[k] - 2 * PLATE_MARGIN + PLATE_GAP for k in (0, 1)]
    plates: list[tuple[list, list]] = []  # each one's free rectangles, and its parts
    for part in group:
        w, h = (v + PLATE_GAP for v in sizes[part])
        if not any(a <= room[0] and b <= room[1] for a, b in ((w, h), (h, w))):
            sys.exit(f"{part} is too big for the bed: {sizes[part]}")
        for n in range(len(plates) + 1):
            if n == len(plates):
                plates.append(([(0.0, 0.0, *room)], []))
            free, placed = plates[n]
            fits = [
                (min(fw - a, fh - b), fx, fy, a, b, turned)
                for fx, fy, fw, fh in free
                for a, b, turned in ((w, h, False), (h, w, True))
                if a <= fw + 1e-6 and b <= fh + 1e-6
            ]
            if fits:
                break
        _, x, y, a, b, turned = min(fits)
        placed.append((part, x, y, turned))
        # Cut what it covers out of every free rectangle, and drop those inside others.
        cut = []
        for fx, fy, fw, fh in free:
            if x >= fx + fw or x + a <= fx or y >= fy + fh or y + b <= fy:
                cut.append((fx, fy, fw, fh))
                continue
            if x > fx:
                cut.append((fx, fy, x - fx, fh))
            if x + a < fx + fw:
                cut.append((x + a, fy, fx + fw - x - a, fh))
            if y > fy:
                cut.append((fx, fy, fw, y - fy))
            if y + b < fy + fh:
                cut.append((fx, y + b, fw, fy + fh - y - b))
        free[:] = [
            r
            for i, r in enumerate(cut)
            if not any(
                j != i
                and (
                    o[0] <= r[0]
                    and o[1] <= r[1]
                    and o[0] + o[2] >= r[0] + r[2]
                    and o[1] + o[3] >= r[1] + r[3]
                )
                and (o != r or j < i)
                for j, o in enumerate(cut)
            )
        ]
    out = []
    for _free, placed in plates:
        # Centered on the bed.
        spans = [
            (x, y, x + sizes[p][turned], y + sizes[p][not turned])
            for p, x, y, turned in placed
        ]
        dx = (BED[0] - max(s[2] for s in spans) - min(s[0] for s in spans)) / 2
        dy = (BED[1] - max(s[3] for s in spans) - min(s[1] for s in spans)) / 2
        out.append([(p, x + dx, y + dy, turned) for p, x, y, turned in placed])
    return out


def loadouts(plates: list[list[str]]) -> list[dict[str, int]]:
    """Which tool head each plate's colors go on, changing as few as can be.

    A color stays where it is while it's loaded; a new one takes an empty head, or
    else the place of the color that's needed again last.
    """
    heads: list[str | None] = [None] * FILAMENTS
    out = []
    for i, colors in enumerate(plates):
        if len(colors) > FILAMENTS:
            print(
                f"  warning: plate {i + 1} has {len(colors)} colors for {FILAMENTS} filaments; extras go on filament 1"
            )
        colors = colors[:FILAMENTS]

        def next_use(c: str | None, i: int = i) -> int:
            return next(
                (j for j in range(i + 1, len(plates)) if c in plates[j]), len(plates)
            )

        for c in colors:
            if c not in heads:
                spare = [k for k, h in enumerate(heads) if h not in colors]
                k = max(spare, key=lambda k: (heads[k] is None, next_use(heads[k]), -k))
                heads[k] = c
        out.append({c: heads.index(c) + 1 for c in colors})
    return out


def combine(
    dst: Path,
    note: str,
    settings: dict[str, str],
    groups: list[list[str]],
    built: dict[str, Built],
    filaments: dict[str, str],
) -> None:
    """Write one published project of every group's parts, on as many plates as it takes.

    `filaments` names the filament a color stands for, for the plates' names.
    """
    sizes = {
        p: tuple(b.box[1][k] - b.box[0][k] for k in (0, 1)) for p, b in built.items()
    }
    plates = [plate for g in groups for plate in pack(g, sizes)]
    colors = [
        list(dict.fromkeys(c for p, *_ in plate for _, c, _ in built[p].parts))
        for plate in plates
    ]
    heads = loadouts(colors)
    cols = math.ceil(math.sqrt(len(plates)))

    first = zipfile.ZipFile(io.BytesIO(next(iter(built.values())).project))
    # An object for each part and each set of tool heads it prints with.
    objects: dict[tuple, int] = {}
    next_id = 1
    models, resources, configs, items, plate_xml = {}, [], [], [], []
    made: dict[int, int] = {}  # instances so far, by object
    for i, plate in enumerate(plates):
        origin = (
            i % cols * BED[0] * PLATE_STRIDE,
            -(i // cols) * BED[1] * PLATE_STRIDE,
        )
        instances = []
        for part, x, y, turned in plate:
            b = built[part]
            ids = tuple(heads[i].get(c, 1) for _, c, _ in b.parts)
            if (part, ids) not in objects:
                zin = zipfile.ZipFile(io.BytesIO(b.project))
                base = next_id
                oid = objects[part, ids] = base + len(b.parts)
                next_id = oid + 1

                def moved(m: re.Match, base: int = base) -> str:
                    return f'{m[1]}"{base - 1 + int(m[2])}"'

                path = f"3D/Objects/{part}_{oid}.model"
                models[path] = re.sub(
                    r'(<object id=)"(\d+)"',
                    moved,
                    zin.read("3D/Objects/Assembly_1.model").decode(),
                )
                comps = re.findall(
                    r"<component [^>]*/>", zin.read("3D/3dmodel.model").decode()
                )
                comps = [
                    re.sub(r'( objectid=)"(\d+)"', moved, c).replace(
                        "/3D/Objects/Assembly_1.model", "/" + path
                    )
                    for c in comps
                ]
                resources.append(
                    f'  <object id="{oid}" p:UUID="{uuid.uuid5(uuid.NAMESPACE_OID, path)}" type="model">\n'
                    "   <components>\n"
                    + "".join(f"    {c}\n" for c in comps)
                    + "   </components>\n  </object>\n"
                )
                config = re.search(
                    r"  <object id=.*?</object>\n",
                    zin.read("Metadata/model_settings.config").decode(),
                    re.DOTALL,
                )[0]
                config = re.sub(r'(<object id=)"(\d+)"', f'\\1"{oid}"', config, count=1)
                config = re.sub(r'(<part id=)"(\d+)"', moved, config)
                config = config.replace(meta("name", "Assembly"), meta("name", part), 1)
                configs.append(
                    name_parts(
                        config,
                        [(label, k, own) for (label, _, own), k in zip(b.parts, ids)],
                    )
                )
            oid = objects[part, ids]
            # The box's corner to (x, y) on the plate, its bottom to the bed.
            (x0, y0, z0), (_x1, y1, _z1) = b.box
            if turned:
                at = "0 1 0 -1 0 0 0 0 1", origin[0] + x + y1, origin[1] + y - x0
            else:
                at = "1 0 0 0 1 0 0 0 1", origin[0] + x - x0, origin[1] + y - y0
            n = len(items)
            items.append(
                f'  <item objectid="{oid}" p:UUID="{uuid.uuid5(uuid.NAMESPACE_OID, f"item {n}")}"'
                f' transform="{at[0]} {at[1]:.4f} {at[2]:.4f} {-z0:.4f}" printable="1"/>\n'
            )
            instances.append((oid, made.get(oid, 0), 1000 + n))
            made[oid] = made.get(oid, 0) + 1
        count: dict[str, int] = {}
        for part, *_ in plate:
            count[part] = count.get(part, 0) + 1
        name = ", ".join(p if n == 1 else f"{p} x{n}" for p, n in count.items())
        tools = ", ".join(
            f"T{k} {filaments.get(c) or color_name(c)}"
            for c, k in sorted(heads[i].items(), key=lambda h: h[1])
        )
        print(f"  plate {i + 1}: {name}: {tools}")
        k = i + 1
        plate_xml.append(
            "  <plate>\n"
            + "".join(
                f"    {meta(key, value)}\n"
                for key, value in {
                    "plater_id": str(k),
                    "plater_name": f"{name}: {tools}",
                    "locked": "false",
                    "filament_map_mode": "Auto For Flush",
                    "gcode_file": "",
                    "thumbnail_file": f"Metadata/plate_{k}.png",
                    "thumbnail_no_light_file": f"Metadata/plate_no_light_{k}.png",
                    "top_file": f"Metadata/top_{k}.png",
                    "pick_file": f"Metadata/pick_{k}.png",
                }.items()
            )
            + "".join(
                "    <model_instance>\n"
                f"      {meta('object_id', str(o))}\n      {meta('instance_id', str(n))}\n"
                f"      {meta('identify_id', str(ident))}\n    </model_instance>\n"
                for o, n, ident in instances
            )
            + "  </plate>\n"
        )

    model = first.read("3D/3dmodel.model").decode()
    head = model[: model.index(" <resources>")]
    build = re.search(r" <build[^>]*>", model)[0]
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr(
            "3D/3dmodel.model",
            head
            + published_tags(settings)
            + " <resources>\n"
            + "".join(resources)
            + f" </resources>\n{build}\n"
            + "".join(items)
            + " </build>\n</model>\n",
        )
        zout.writestr(
            "3D/_rels/3dmodel.model.rels",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            + "".join(
                f' <Relationship Target="/{path}" Id="rel-{n + 1}"'
                ' Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                for n, path in enumerate(models)
            )
            + "</Relationships>\n",
        )
        for path, data in models.items():
            zout.writestr(path, data)
        zout.writestr(
            "Metadata/model_settings.config",
            '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
            + "".join(configs)
            + "".join(plate_xml)
            + "  <assemble>\n  </assemble>\n</config>\n",
        )
        zout.writestr(
            "Metadata/filament_sequence.json",
            json.dumps(
                {
                    f"plate_{k + 1}": {
                        "nozzle_sequence": [],
                        "optimal_assignment": [],
                        "sequence": [],
                    }
                    for k in range(len(plates))
                }
            ),
        )
        for name in (
            "[Content_Types].xml",
            "_rels/.rels",
            "Metadata/slice_info.config",
        ):
            zout.writestr(name, first.read(name))
        # Every plate wants its pictures; Orca draws them again on saving.
        for name in first.namelist():
            if m := re.fullmatch(r"(Metadata/\w*?)1((?:_small)?\.png)", name):
                for k in range(len(plates)):
                    zout.writestr(f"{m[1]}{k + 1}{m[2]}", first.read(name))
    print(f"{dst.relative_to(ROOT)}: {len(plates)} plates, {len(objects)} objects")


def generate(scad: Path) -> None:
    out_dir = ROOT / "gen" / scad.parent.relative_to(ROOT)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{scad.stem}-*.3mf"):
        old.unlink()

    text = scad.read_text()
    items = shlex.split(directive(text, "orca"))
    note = ", ".join(items)
    settings = {
        k: v for k, v in pairs(directive(text, "orca")).items() if k not in PRESETS
    }

    exports = directive(text, "export").split()
    # Each `// plate:` line's parts, a copy at a time.
    groups = [
        [
            part
            for item in line.split()
            for part, _, n in [item.partition("*")]
            for _ in range(int(n or 1))
        ]
        for line in directives(text, "plate")
    ]
    built: dict[str, Built] = {}
    values: dict[str, str] = {}  # each color the file names, as OpenSCAD writes it
    filaments: dict[str, str] = {}  # the filament each of those stands for
    for part in dict.fromkeys(exports + [p for g in groups for p in g]):
        target = out_dir / f"{scad.stem}-{part}.3mf"
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            mesh = work / "mesh.3mf"
            print(f"{part}: openscad")
            # Not --quiet, which would drop the echoes.
            openscad = subprocess.Popen(
                [
                    "openscad",
                    "--enable=lazy-union",
                    "-D",
                    f'part="{part}"',
                    "-o",
                    mesh,
                    scad,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Show the log as it comes.
            log = []
            for line in openscad.stderr:
                log.append(line.rstrip("\n"))
                if log[-1]:
                    print(f"  {log[-1]}")
            if openscad.wait():
                sys.exit(f"openscad failed on {part}")
            pieces = [
                (m[1], m[2] or "")
                for line in log
                if (
                    m := re.fullmatch(
                        r'ECHO: piece = "(.*?)"(?:, orca = "(.*)")?', line
                    )
                )
            ]
            pauses = [
                float(m[1])
                for line in log
                if (m := re.fullmatch(r"ECHO: pause = ([\d.]+)", line))
            ]
            if pauses and "layer_height" not in settings:
                sys.exit(f"{part} pauses, which takes a layer_height on the orca line")
            if pauses and any(part in g for g in groups):
                print(f"  warning: {scad.stem}-all won't pause for {part}")
            named = {
                m[1]: (m[2], m[3])
                for line in log
                if (
                    m := re.fullmatch(
                        r'ECHO: color = "(.*?)", piece = "(.*?)"(?:, filament = "(.*?)")?',
                        line,
                    )
                )
            }
            if set(named) - set(values):
                values.update(color_values(sorted(set(named) - set(values))))
            filaments.update({values[c]: f for c, (_, f) in named.items() if f})
            parts, box = split(
                mesh, work, pieces, {values[c]: n for c, (n, _) in named.items()}
            )
            # Filaments in order of each color's first appearance.
            order = list(dict.fromkeys(p[1] for p in parts))
            if len(order) > FILAMENTS:
                print(
                    f"  warning: {len(order)} colors for {FILAMENTS} filaments; extras go on filament 1"
                )
            ids = [
                order.index(c) + 1 if order.index(c) < FILAMENTS else 1
                for _, c, _, _ in parts
            ]
            print(f"{part}: orca-slicer, assembling {len(parts)} parts")
            # Orca writes result.json into its working directory.
            done = subprocess.run(
                [
                    "orca-slicer",
                    "--assemble",
                    "--export-3mf",
                    work / "project.3mf",
                    *[p[0] for p in parts],
                ],
                check=False,
                cwd=work,
                capture_output=True,
                text=True,
            )
            if not (work / "project.3mf").exists():
                sys.exit(f"orca-slicer failed on {part}:\n{done.stdout}{done.stderr}")
            built[part] = Built(
                (work / "project.3mf").read_bytes(),
                [(label, color, own) for _, color, label, own in parts],
                box,
            )
            if part not in exports:
                continue
            annotate(
                work / "project.3mf",
                target,
                target.stem,
                note,
                [(label, i, own) for (_, _, label, own), i in zip(parts, ids)],
                settings,
                pauses,
            )
        print(
            f"{target.relative_to(ROOT)}: {len(parts)} parts, {len(order)} colors"
            + "".join(f", pause at {z:g} mm" for z in pauses)
        )
    if groups:
        combine(
            out_dir / f"{scad.stem}-all.3mf", note, settings, groups, built, filaments
        )


if __name__ == "__main__":
    # Show each line as it is printed, even into a pipe.
    sys.stdout.reconfigure(line_buffering=True)
    generate(Path(sys.argv[1]).resolve())
