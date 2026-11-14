"""Slice an Orca project from the command line, to check what a print comes out as.

Orca's CLI knows nothing of the GUI's presets, and ignores the settings a
published project (see generate.py) carries, so this does both by hand: it
flattens a machine, a process and a filament preset from Orca's own folders,
lays the project's settings over them, and slices with the result.

The machine defaults to the one selected in Orca, the process to its 0.20
Standard, and the filament to the machine's default. A name is a preset's full name, or for a
process the part before its " @machine", like the `// orca:` line's.

The G-code goes to tmp/slice/<project>.gcode, or for a project of several plates
to a <project>-plate_<n>.gcode each, with every tool on the same filament. Parts keep the settings of their own, which Orca does read.

Usage: slice.py FILE.3mf [--machine NAME] [--process NAME] [--filament NAME]
"""

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from project.orca import published

ROOT = Path(__file__).resolve().parents[1]
ORCA = Path.home() / ".config/OrcaSlicer"
KINDS = ("machine", "process", "filament")


def presets() -> dict[str, dict[str, dict]]:
    """Every preset by kind and name: the bundled ones, then mine over them."""
    found: dict[str, dict[str, dict]] = {k: {} for k in KINDS}
    for base in (ORCA / "system", ORCA / "user"):
        for kind in KINDS:
            for path in sorted(base.glob(f"*/{kind}/**/*.json")):
                try:
                    d = json.loads(path.read_text(encoding="utf-8-sig"))
                except ValueError:
                    continue
                if "name" in d:
                    found[kind][d["name"]] = d
    return found


def flatten(group: dict[str, dict], name: str, kind: str) -> dict:
    """A preset with all it inherits, as the CLI wants it."""
    d = group[name]
    base = flatten(group, d["inherits"], kind) if d.get("inherits") else {}
    return {**base, **d, "inherits": "", "from": "system", "type": kind}


def pick(group: dict[str, dict], name: str, machine: str, kind: str) -> str:
    """The full name of the preset called `name`, or `name` for this machine."""
    for full in (name, f"{name} @{machine}"):
        if full in group:
            return full
    sys.exit(f"no {kind} preset named {name!r}")


def as_cli_reads(project: Path, machine: dict, out: Path) -> None:
    """Copy a published project, saying which bed its plates are laid out for.

    The GUI takes a published project's objects where they are, on plates laid out
    for the selected printer. The CLI takes a project with no settings to be for its
    default bed, 200 square, and moves everything to suit the real one.
    """
    with (
        zipfile.ZipFile(project) as zin,
        zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout,
    ):
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        zout.writestr(
            "Metadata/project_settings.config",
            json.dumps({k: machine[k] for k in ("printable_area", "printable_height")}),
        )


def slice_project(project: Path, args: argparse.Namespace) -> list[Path]:
    found = presets()
    selected = json.loads((ORCA / "OrcaSlicer.conf").read_text())["presets"]["machine"]
    machine_name = pick(found["machine"], args.machine or selected, "", "machine")
    machine = flatten(found["machine"], machine_name, "machine")
    # My machines are copies; processes are named for the one they come from.
    stock = machine_name
    while found["machine"][stock].get("from") == "User":
        stock = found["machine"][stock]["inherits"]
    # The CLI matches a process's compatible printers by name alone.
    machine["name"] = stock
    process_name = pick(
        found["process"],
        # The U1's own default names a preset that doesn't exist.
        args.process or "0.20 Standard",
        stock,
        "process",
    )
    process = flatten(found["process"], process_name, "process")
    default = machine["default_filament_profile"]
    filament_name = pick(
        found["filament"],
        args.filament or (default[0] if isinstance(default, list) else default),
        stock,
        "filament",
    )
    filament = flatten(found["filament"], filament_name, "filament")

    settings = published(project)
    for key, value in settings.items():
        # Each setting belongs to one kind of preset; new ones are the process's.
        target = next((p for p in (machine, filament) if key in p), process)
        target[key] = (
            [value] * len(target[key]) if isinstance(target.get(key), list) else value
        )

    print(f"machine:  {machine_name}")
    print(f"process:  {process_name}")
    print(f"filament: {filament_name}")
    for key, value in settings.items():
        print(f"  {key} = {value}")

    out = ROOT / "tmp" / "slice" / f"{project.stem}.gcode"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for kind, preset in zip(KINDS, (machine, process, filament)):
            (work / f"{kind}.json").write_text(json.dumps(preset))
        tools = len(machine["nozzle_diameter"])
        as_cli_reads(project, machine, work / "project.3mf")
        # Orca writes result.json into its working directory.
        done = subprocess.run(
            [
                "orca-slicer",
                "--load-settings",
                f"{work / 'machine.json'};{work / 'process.json'}",
                "--load-filaments",
                ";".join([str(work / "filament.json")] * tools),
                "--slice",
                "0",
                "--outputdir",
                work,
                work / "project.3mf",
            ],
            check=False,
            cwd=work,
            capture_output=True,
            text=True,
        )
        gcodes = sorted(work.glob("plate_*.gcode"), key=lambda g: int(g.stem[6:]))
        if not gcodes:
            result = work / "result.json"
            why = (
                json.loads(result.read_text())["error_string"]
                if result.exists()
                else ""
            )
            sys.exit(f"orca-slicer failed: {why}\n{done.stdout}{done.stderr}")
        # A project of several plates: one file each.
        outs = (
            [out]
            if len(gcodes) == 1
            else [out.with_stem(f"{out.stem}-{g.stem}") for g in gcodes]
        )
        for o, g in zip(outs, gcodes):
            o.write_bytes(g.read_bytes())
    return outs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("project", type=Path)
    for kind in KINDS:
        parser.add_argument(f"--{kind}")
    args = parser.parse_args()
    for gcode in slice_project(args.project.resolve(), args):
        print(gcode.relative_to(ROOT))
