"""The Orca side: have Orca assemble STLs into a project, and write projects of
what it made, as published ones that apply settings."""

import copy
import functools
import io
import json
import os
import re
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape, unescape

from .scad import CORE, Solid
from .tree import attr, child

PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
# Orca reads these names as they're written, prefix and all, whatever they're bound to.
ET.register_namespace("", CORE)
ET.register_namespace("p", PRODUCTION)

MODEL = "3D/3dmodel.model"
MESHES = "3D/Objects/Assembly_1.model"
CONFIG = "Metadata/model_settings.config"
# What any project carries as Orca's CLI wrote it.
AS_IS = ("[Content_Types].xml", "_rels/.rels", "Metadata/slice_info.config")
PLATE_FILES = {
    "thumbnail_file": "Metadata/plate_{}.png",
    "thumbnail_no_light_file": "Metadata/plate_no_light_{}.png",
    "top_file": "Metadata/top_{}.png",
    "pick_file": "Metadata/pick_{}.png",
}


def core(tag: str) -> str:
    return f"{{{CORE}}}{tag}"


def production(tag: str) -> str:
    return f"{{{PRODUCTION}}}{tag}"


@dataclass
class Volume:
    """One of an object's parts, as Orca assembled it."""

    number: int  # its place among the STLs, from 1: its id in Orca's project
    name: str
    color: str
    settings: dict[str, str]  # its own
    mesh: ET.Element  # its <object> among the meshes
    component: ET.Element  # where it goes in its object
    part: ET.Element  # Orca's notes on it, in the model settings


@dataclass
class Object:
    """What Orca shows as one object."""

    name: str  # none for the object of everything left, which is named on writing
    settings: dict[str, str]  # the ones Orca keeps for a whole object
    volumes: list[Volume]


@dataclass
class Assembly:
    """A part of a .scad file, as Orca assembled it: an object, or several."""

    objects: list[Object]
    box: tuple[tuple[float, ...], tuple[float, ...]]  # its corners, as in the .scad
    transform: str  # where Orca put it
    meshes: ET.Element  # the model of its volumes' meshes
    archive: bytes  # Orca's project, for the files any project carries as they are


@dataclass
class Placed:
    """An assembly on a plate."""

    assembly: Assembly
    name: str  # for its object of everything left
    transform: str
    filaments: dict[str, int]  # the tool head for each color


@dataclass
class Plate:
    name: str
    placed: list[Placed]


@functools.cache
def object_keys() -> frozenset[str]:
    """The settings Orca keeps for a whole object, which a part can't carry."""
    if "ORCA_SOURCE" not in os.environ:
        sys.exit("a piece has settings, which takes $ORCA_SOURCE to sort them")
    header = Path(os.environ["ORCA_SOURCE"]) / "src/libslic3r/PrintConfig.hpp"
    block = re.search(
        r"^PRINT_CONFIG_CLASS_DEFINE\(\s*PrintObjectConfig,(.*?)^\)",
        header.read_text(),
        re.DOTALL | re.MULTILINE,
    )
    if not block:
        sys.exit(f"no PrintObjectConfig in {header}")
    return frozenset(re.findall(r"\(\(\s*ConfigOption[^,]*,\s*(\w+)\)\)", block[1]))


def metadata(parent: ET.Element, key: str) -> ET.Element:
    """The <metadata> of the model settings with this key."""
    return next(m for m in parent.iterfind("metadata") if m.get("key") == key)


def add_metadata(parent: ET.Element, values: dict[str, str], at: int = -1) -> None:
    """Add a <metadata> of the model settings for each value, from index `at`."""
    for i, (key, value) in enumerate(values.items()):
        m = ET.Element("metadata", key=key, value=value)
        parent.append(m) if at < 0 else parent.insert(at + i, m)


def to_xml(root: ET.Element, indent: bool = True) -> bytes:
    if indent:
        ET.indent(root, " ")
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True)


def assemble(solids: list[Solid], box: tuple, work: Path) -> Assembly:
    """Have Orca make a project of the solids, in `work`.

    Orca makes one object of everything. A piece with settings Orca keeps for a
    whole object, a brim say, gets one of its own instead, where it is.
    """
    project = work / "project.3mf"
    # Orca writes result.json into its working directory.
    done = subprocess.run(
        ["orca-slicer", "--assemble", "--export-3mf", project]
        + [s.stl for s in solids],
        check=False,
        cwd=work,
        capture_output=True,
        text=True,
    )
    if not project.exists():
        sys.exit(f"orca-slicer failed:\n{done.stdout}{done.stderr}")
    archive = project.read_bytes()
    with zipfile.ZipFile(project) as z:
        model, meshes, config = (
            ET.fromstring(z.read(name)) for name in (MODEL, MESHES, CONFIG)
        )
    mesh = {o.get("id"): o for o in meshes.iter(core("object"))}
    component = {c.get("objectid"): c for c in model.iter(core("component"))}

    whole = object_keys() if any(s.settings for s in solids) else frozenset()
    objects = {"": Object("", {}, [])}
    for part in config.iterfind("object/part"):
        # Orca names each part after its file, which is its number.
        number = int(Path(attr(metadata(part, "name"), "value")).stem)
        solid = solids[number - 1]
        of_object = {k: v for k, v in solid.settings.items() if k in whole}
        own = {k: v for k, v in solid.settings.items() if k not in whole}
        obj = objects.setdefault(
            solid.piece if of_object else "", Object(solid.piece, of_object, [])
        )
        i = attr(part, "id")
        obj.volumes.append(
            Volume(number, solid.name, solid.color, own, mesh[i], component[i], part)
        )
    return Assembly(
        [o for o in objects.values() if o.volumes],
        box,
        attr(child(model, f"{core('build')}/{core('item')}"), "transform"),
        meshes,
        archive,
    )


def publish(model: ET.Element, settings: dict[str, str]) -> None:
    """Make a project's model a published one, which applies `settings`."""
    published = {
        "orca_published": "1",
        "orca_published_keys": json.dumps(list(settings)),
        # Orca imports only the geometry of a published project with no settings at all.
        "orca_published_config": "\n".join(
            f"{k} = {v}" for k, v in (settings or {"layer_height": "0.2"}).items()
        ),
    }
    at = list(model).index(child(model, core("resources")))
    for i, (name, value) in enumerate(published.items()):
        tag = ET.Element(core("metadata"), name=name)
        # Orca unescapes these values twice: once more than XML has it.
        tag.text = escape(value)
        model.insert(at + i, tag)


def published(project: Path) -> dict[str, str]:
    """The settings a published project applies."""
    model = ET.fromstring(zipfile.ZipFile(project).read(MODEL))
    tags = {
        m.get("name"): unescape(m.text or "") for m in model.iterfind(core("metadata"))
    }
    config = dict(
        line.split(" = ", 1)
        for line in tags.get("orca_published_config", "").splitlines()
    )
    # A project with nothing to apply still carries a setting, unlisted.
    return {k: config[k] for k in json.loads(tags.get("orca_published_keys") or "[]")}


def pause_xml(heights: Sequence[float], layer: float) -> bytes:
    """Orca's custom G-code for the first plate: a pause at each height."""
    root = ET.Element("custom_gcodes_per_layer")
    plate = ET.SubElement(root, "plate")
    ET.SubElement(plate, "plate_info", id="1")
    for z in heights:
        # Orca gives each of these to the layer whose top is nearest, and runs it
        # before that layer: so name the layer above the pause. Type 1 is a pause.
        ET.SubElement(
            plate,
            "layer",
            top_z=f"{z + layer:.4f}",
            type="1",
            extruder="1",
            color="",
            extra="",
            gcode="",
        )
    ET.SubElement(plate, "mode", value="MultiExtruder")
    return to_xml(root)


def write(
    dst: Path,
    settings: dict[str, str],
    plates: list[Plate],
    pauses: Sequence[float] = (),
) -> int:
    """Write a published project of the plates, applying `settings` to everything.

    `pauses` are the heights to pause the first plate at. Returns how many objects
    it has: one for every copy of one, as Orca's GUI won't slice a plate that has
    only further instances of an object on another plate.
    """
    src = zipfile.ZipFile(io.BytesIO(plates[0].placed[0].assembly.archive))
    model = ET.fromstring(src.read(MODEL))
    resources, build = child(model, core("resources")), child(model, core("build"))
    for parent in (resources, build):
        for old in list(parent):
            parent.remove(old)
    publish(model, settings)

    config = ET.Element("config")
    plate_tags = []
    files: dict[str, bytes] = {}  # each placed assembly's meshes
    next_id = 1
    count = 0
    for k, plate in enumerate(plates, 1):
        plate_tag = ET.Element("plate")
        plate_tags.append(plate_tag)
        add_metadata(
            plate_tag,
            {
                "plater_id": str(k),
                "plater_name": plate.name,
                "locked": "false",
                "filament_map_mode": "Auto For Flush",
                "gcode_file": "",
                **{key: name.format(k) for key, name in PLATE_FILES.items()},
            },
        )
        for placed in plate.placed:
            a = placed.assembly
            volumes = [v for o in a.objects for v in o.volumes]
            # Every id in a project its own: the volumes', then their objects'.
            ids = {v.number: next_id - 1 + v.number for v in volumes}
            next_id += len(volumes)
            path = f"3D/Objects/object_{next_id}.model"
            for v in volumes:
                v.mesh.set("id", str(ids[v.number]))
            files[path] = to_xml(a.meshes, indent=False)
            for o in a.objects:
                oid, next_id = str(next_id), next_id + 1

                def named(what: str, oid: str = oid) -> str:
                    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"{what} {oid}"))

                obj = ET.SubElement(
                    resources,
                    core("object"),
                    {"id": oid, production("UUID"): named("object"), "type": "model"},
                )
                components = ET.SubElement(obj, core("components"))
                noted = ET.SubElement(config, "object", id=oid, auto_drop="1")
                add_metadata(noted, {"name": o.name or placed.name, **o.settings})
                for v in o.volumes:
                    vid = str(ids[v.number])
                    ET.SubElement(
                        components,
                        core("component"),
                        {
                            **v.component.attrib,
                            production("path"): "/" + path,
                            "objectid": vid,
                        },
                    )
                    part = copy.deepcopy(v.part)
                    part.set("id", vid)
                    metadata(part, "name").set("value", v.name)
                    # Orca's own --load-filament-ids only works with filament presets loaded.
                    extruder = metadata(part, "extruder")
                    extruder.set("value", str(placed.filaments.get(v.color, 1)))
                    add_metadata(part, v.settings, list(part).index(extruder) + 1)
                    noted.append(part)
                ET.SubElement(
                    build,
                    core("item"),
                    {
                        "objectid": oid,
                        production("UUID"): named("item"),
                        "transform": placed.transform,
                        "printable": "1",
                    },
                )
                instance = ET.SubElement(plate_tag, "model_instance")
                add_metadata(
                    instance,
                    {
                        "object_id": oid,
                        "instance_id": "0",
                        "identify_id": str(1000 + count),
                    },
                )
                count += 1
    config.extend(plate_tags)
    ET.SubElement(config, "assemble")

    relationships = ET.Element(
        "Relationships",
        xmlns="http://schemas.openxmlformats.org/package/2006/relationships",
    )
    for n, path in enumerate(files, 1):
        ET.SubElement(
            relationships,
            "Relationship",
            Target="/" + path,
            Id=f"rel-{n}",
            Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel",
        )

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr(MODEL, to_xml(model))
        zout.writestr("3D/_rels/3dmodel.model.rels", to_xml(relationships))
        for path, data in files.items():
            zout.writestr(path, data)
        zout.writestr(CONFIG, to_xml(config))
        zout.writestr(
            "Metadata/filament_sequence.json",
            json.dumps(
                {
                    f"plate_{k}": {
                        "nozzle_sequence": [],
                        "optimal_assignment": [],
                        "sequence": [],
                    }
                    for k in range(1, len(plates) + 1)
                }
            ),
        )
        for name in AS_IS:
            zout.writestr(name, src.read(name))
        # Every plate wants its pictures; Orca draws them again on saving.
        for name in src.namelist():
            if m := re.fullmatch(r"(Metadata/\w*?)1((?:_small)?\.png)", name):
                for k in range(1, len(plates) + 1):
                    zout.writestr(f"{m[1]}{k}{m[2]}", src.read(name))
        if pauses:
            zout.writestr(
                "Metadata/custom_gcode_per_layer.xml",
                pause_xml(pauses, float(settings["layer_height"])),
            )
    return count
