"""What's inherent to the Snapmaker U1: bed, tools, and firmware G-code.

Start/end/tool-change G-code is a hand-trimmed, single-tool version of the
stock machine profile "Snapmaker U1 (0.4 nozzle).json" (machine_start_gcode,
machine_end_gcode, change_filament_gcode) from Snapmaker Orca 2.4.1, with its
template values filled in from Python. Per-print values live in settings.py.
"""

from pathlib import Path

import fullcontrol as fc

from . import TMP, orca
from .settings import DEFAULT, Settings

# From the stock machine profile: printable_area / printable_height.
BED_X = (0.5, 270.5)
BED_Y = (1.0, 271.0)
MAX_Z = 270.0
TOOLS = 4
# Stock profile's retract_length_toolchange.
TOOLCHANGE_RETRACT = 10
# Where the start G-code's purge line ends.
PURGE_END = (185, 1)


def start_gcode(tool: int, nozzle: int, bed: int) -> str:
    standby = nozzle - 90
    return f"""\
;===== U1 start (from stock U1 slicer profile) =====
PRINT_START
M140 S{bed}
M104 T{tool} S140
M204 S10000
G28 X Y
T{tool}
G90
SM_PRINT_CHECK_SWITCH_EXTRUDER

; pre-extrude
M104 T{tool} S{nozzle}
T{tool}
M109 T{tool} S{nozzle}
SM_PRINT_PREEXTRUDE_FILAMENT INDEX={tool}
M104 T{tool} S{standby}

; rough home
M106 S255
M106 P2 S0
MOVE_TO_DISCARD_FILAMENT_POSITION
M109 T{tool} S{standby}
ROUGHLY_CLEAN_NOZZLE_WITH_DISCARD
MOVE_TO_XY_IDLE_POSITION_EXTRUDER
M107
G28 Z I140 J140

M107
DETECT_BED_PLATE

; deep clean nozzle
M106 S255
G90
G0 Z5 F10000
MOVE_TO_DISCARD_FILAMENT_POSITION
M109 S{nozzle - 50}
ROUGHLY_CLEAN_NOZZLE
MOVE_TO_XY_IDLE_POSITION_EXTRUDER
FINELY_CLEAN_NOZZLE_STAGE_1
M104 S{standby}
G0 Z5 F10000
MOVE_TO_DISCARD_FILAMENT_POSITION
ROUGHLY_CLEAN_NOZZLE
MOVE_TO_XY_IDLE_POSITION_EXTRUDER
FINELY_CLEAN_NOZZLE_STAGE_2

; fine home (textured PEI plate)
M106 S255
M109 S{standby}
M190 S{bed}
M107 P2
G90
G0 Z5 F10000
M107
G28 Z

; bed mesh
M107
BED_MESH_CALIBRATE PROBE_COUNT=11,11

; purge line
G90
G1 Z1.5
G0 X85 Y1 Z2 F18000
M109 S{nozzle}
G1 Z0.2
M83
G1 X185 E15 F360
G1 Z1.5
G90
M106 S0
;===== end U1 start ====="""


def tool_change(
    tool: int,
    at: fc.Point,
    s: Settings = DEFAULT,
    lift: float = 1.5,
    to: fc.Point | None = None,
    travel_z: float | None = None,
    unretract: bool = False,
) -> list:
    """Steps to switch to `tool` at point `at`, then continue from `to` (default `at`).

    After the switch, the head rises to `travel_z` (default: `lift` above `at`),
    moves over `to`, then descends, so set `travel_z` above anything in the way.

    Based on the stock profile's change_filament_gcode. The old tool is
    retracted; pass `unretract` when switching back to a tool that was retracted
    this way (ToolState tracks this).
    """
    if at.x is None or at.y is None or at.z is None:
        raise ValueError(f"tool_change needs a point with x, y and z: {at}")
    to = to or at
    if to.x is None or to.y is None or to.z is None:
        raise ValueError(f"tool_change needs a point with x, y and z: {to}")
    safe_z = max(at.z + lift, travel_z or 0)
    nozzle = s.filaments[tool].nozzle_temp
    return [
        fc.ManualGcode(
            text=f"G1 E-{TOOLCHANGE_RETRACT} F1800 ; retract before tool change"
        ),
        fc.Extruder(on=False),
        fc.Point(x=at.x, y=at.y, z=at.z + lift),
        fc.ManualGcode(
            text=f"""\
;===== tool change -> T{tool} =====
M109 S{nozzle} T{tool}
M400
T{tool}
SM_PRINT_PREEXTRUDE_FILAMENT INDEX={tool}
G90
G0 Z{safe_z:.4f} F8000
G0 X{at.x:.4f} Y{at.y:.4f} F8000 ; back over the part
;===== end tool change ====="""
        ),
        # Re-sync FullControl with where the head is, then travel over and down.
        fc.Point(x=at.x, y=at.y, z=safe_z),
        fc.Point(x=to.x, y=to.y, z=safe_z),
        fc.Point(x=to.x, y=to.y, z=to.z + lift),
        to.model_copy(),
        *(
            [fc.ManualGcode(text=f"G1 E{TOOLCHANGE_RETRACT} F1800 ; unretract")]
            if unretract
            else []
        ),
        fc.Extruder(on=True),
    ]


def travel(to: fc.Point, z: float) -> list:
    """Lift to `z`, move over `to`, and descend, without extruding."""
    return [
        fc.Extruder(on=False),
        fc.Point(z=z),
        fc.Point(x=to.x, y=to.y, z=z),
        to.model_copy(),
        fc.Extruder(on=True),
    ]


class ToolState:
    """Tracks the active tool and which tools are retracted from tool changes."""

    def __init__(self, s: Settings = DEFAULT, tool: int = 0):
        self.s = s
        self.current = tool
        self.retracted: set[int] = set()

    def change(
        self, tool: int, at: fc.Point, to: fc.Point, travel_z: float | None = None
    ) -> list:
        """Switch to `tool` (or just travel, if it's already active) and continue at `to`."""
        if tool == self.current:
            assert at.z is not None
            return travel(to, max(at.z + 1.5, travel_z or 0))
        steps = tool_change(
            tool,
            at,
            self.s,
            to=to,
            travel_z=travel_z,
            unretract=tool in self.retracted,
        )
        self.retracted.add(self.current)
        self.retracted.discard(tool)
        self.current = tool
        return steps


END_GCODE = """\
;===== U1 end =====
PRINT_END
"""


def gcode(
    steps: list,
    name: str,
    settings: Settings = DEFAULT,
    *,
    tool: int = 0,
    orca_compat: bool = True,
) -> Path:
    """Wrap design steps with U1 start/end G-code and save to tmp/<name>.gcode.

    `tool` is the starting tool. With orca_compat, add a header and config block
    so Orca's viewer previews tool changes and filament usage; the
    printer may also read these.
    """
    s = settings
    f = s.filaments[tool]
    first = next(p for p in steps if isinstance(p, fc.Point)).model_copy()
    all_steps = [
        fc.ManualGcode(text=orca.HEADER if orca_compat else ""),
        fc.ManualGcode(text=start_gcode(tool, f.nozzle_temp, f.bed_temp)),
        fc.Fan(speed_percent=s.fan_percent),
        # Travel (not extrude) from the purge line to the first point.
        fc.Extruder(on=False),
        fc.Point(x=PURGE_END[0], y=PURGE_END[1], z=2),
        fc.Point(x=first.x, y=first.y, z=2),
        first,
        fc.ManualGcode(
            text=f"; FEATURE: Outer wall\n; LINE_WIDTH: {s.line_width}\n; LAYER_HEIGHT: {s.layer_height}"
        ),
        fc.Extruder(on=True),
        *steps,
        fc.ManualGcode(text=END_GCODE),
    ]
    if orca_compat:
        all_steps.append(fc.ManualGcode(text=orca.config_block(s)))
    TMP.mkdir(exist_ok=True)
    out = TMP / name
    fc.transform(
        all_steps,
        "gcode",
        fc.GcodeControls(
            printer_name="custom",
            save_as=str(out),
            include_date=False,
            initialization_data={
                "relative_e": True,
                "primer": "no_primer",
                "extrusion_width": s.line_width,
                "extrusion_height": s.layer_height,
                "print_speed": s.print_speed,
                "travel_speed": s.travel_speed,
                "dia_feed": f.diameter,
                # Plain moves rather than G10/G11, which need Klipper firmware_retraction.
                "printer_command_list": {
                    "home": "G28 ; home axes",
                    "absolute_coords": "G90 ; absolute coordinates",
                    "relative_coords": "G91 ; relative coordinates",
                    "units_mm": "G21 ; set units to millimeters",
                    "retract": f"G1 E-{s.retraction} F1800 ; retract",
                    "unretract": f"G1 E{s.retraction} F1800 ; unretract",
                },
            },
        ),
        show_tips=False,
    )
    return out.with_suffix(".gcode")
