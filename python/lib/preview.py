"""Interactive 3D preview of FullControl design steps, rendered as tubes.

Previews the design itself, not the final G-code: no start sequence, purge
line, or tool-change macros.
"""

from pathlib import Path

import fullcontrol as fc

from . import TMP
from .settings import DEFAULT, Settings


def preview(steps: list, name: str, settings: Settings = DEFAULT) -> Path:
    """Write tmp/<name>.html. Tubes use each move's ExtrusionGeometry width/height."""
    fig = fc.transform(
        steps,
        "plot",
        fc.PlotControls(
            style="tube",
            tube_type="cylinders",
            tube_sides=8,
            return_fig=True,
            initialization_data={
                "extrusion_width": settings.line_width,
                "extrusion_height": settings.layer_height,
            },
        ),
        show_tips=False,
    )
    TMP.mkdir(exist_ok=True)
    out = TMP / f"{name}.html"
    fig.write_html(out)
    return out
