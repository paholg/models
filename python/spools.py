"""Check that the printer's loaded filaments and Spoolman agree, so Orca's filament sync picks the
right presets.

The printer (Extended firmware) takes each tool's sub type from the Spoolman filament's `variant`
extra field, which SpoolmanDB imports leave empty, and Orca matches presets by finding that word in
their names. A missing or stale variant makes Orca pick a wrong preset without saying so. This
flags, for each tool and filament, what would cause that.
"""

import json
import re
import sys
import urllib.request
from typing import Any

PRINTER = "http://10.0.0.15"


def get(path: str) -> Any:
    with urllib.request.urlopen(PRINTER + path, timeout=10) as r:
        return json.load(r)["result"]


def spoolman(path: str) -> Any:
    body = json.dumps(
        {"request_method": "GET", "path": path, "use_v2_response": True}
    ).encode()
    request = urllib.request.Request(
        PRINTER + "/server/spoolman/proxy", body, {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=10) as r:
        result = json.load(r)["result"]
    if result["error"]:
        sys.exit(f"Spoolman {path}: {result['error']}")
    return result["response"]


def extra(entity: dict[str, Any], key: str) -> str:
    """An extra field's value: Spoolman stores them JSON-encoded."""
    value = entity.get("extra", {}).get(key)
    return json.loads(value) if value else ""


def sub_type(value: str) -> str:
    return "" if value.upper() == "NONE" else value


def main() -> int:
    status = get("/printer/objects/query?print_task_config&filament_detect")["status"]
    config = status["print_task_config"]
    tags = status["filament_detect"]["info"]
    filaments = {f["id"]: f for f in spoolman("/v1/filament")}
    spools = {s["id"]: s for s in spoolman("/v1/spool")}
    fields = spoolman("/v1/field/filament")
    variants = next((f.get("choices", []) for f in fields if f["key"] == "variant"), [])

    problems: list[str] = []

    for i, loaded in enumerate(config["filament_exist"]):
        tool = f"E{i + 1}"
        if not loaded:
            continue
        reported = sub_type(config["filament_sub_type"][i])
        spool_id = config["filament_spool_id"][i]
        tag = tags[i]
        tag_sub = sub_type(tag["SUB_TYPE"]) if tag["CARD_UID"] else None
        line = f"{tool}: {config['filament_vendor'][i]} {config['filament_type'][i]} {reported or '(no variant)'}"
        spool = spools.get(spool_id)
        if spool is None:
            problems.append(
                f"{line}: no Spoolman spool assigned; pick one from Spoolman"
            )
            print(line)
            continue
        filament = spool["filament"]
        variant = extra(filament, "variant")
        print(f"{line}, spool #{spool_id} ({filament['name']})")
        if variant != reported:
            fix = (
                "Refresh the tool"
                if tag_sub is not None
                else "pick the spool from Spoolman again"
            )
            problems.append(
                f"{tool}: printer reports {reported or 'no variant'}, Spoolman filament "
                f"#{filament['id']} says {variant or 'none'}; {fix}"
            )
        if tag_sub and tag_sub != variant:
            problems.append(
                f"{tool}: tag says {tag_sub}, Spoolman filament #{filament['id']} says "
                f"{variant or 'none'}"
            )

    for filament in filaments.values():
        variant = extra(filament, "variant")
        name = (
            f"{filament.get('vendor', {}).get('name', '')} {filament.get('name', '')}"
        )
        named = [
            v
            for v in variants
            if re.search(rf"\b{re.escape(v)}\b", name, re.IGNORECASE)
        ]
        if not variant and named:
            problems.append(
                f"filament #{filament['id']} ({name}): name says {named[0]}, no variant set"
            )
        elif variant and named and variant not in named:
            problems.append(
                f"filament #{filament['id']} ({name}): name says {', '.join(named)}, variant is {variant}"
            )

    for spool in spools.values():
        uids = [u for u in extra(spool, "card_uids").split(",") if u]
        vendor = spool["filament"].get("vendor", {}).get("name", "")
        if len(uids) == 1 and vendor.lower() == "snapmaker":
            problems.append(
                f"spool #{spool['id']}: one tag UID; Snapmaker spools have one per side, so loaded the "
                "other way round it won't be recognized"
            )

    if problems:
        print()
        for p in problems:
            print("- " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
