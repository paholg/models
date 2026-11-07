"""Print settings that vary per print: nozzle, filaments, layer height, speeds."""

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Filament:
    type: str = "PLA"
    nozzle_temp: int = 210
    bed_temp: int = 60
    density: float = 1.24  # g/cm³
    diameter: float = 1.75
    color: str = "#E0E0E0"


PLA = Filament()


@dataclass(frozen=True)
class Settings:
    nozzle_diameter: float = 0.4
    layer_height: float = 0.2
    line_width: float = 0.4
    print_speed: int = 1000  # mm/min
    travel_speed: int = 8000  # mm/min
    fan_percent: int = 100
    retraction: float = 1.5  # mm, for FullControl's retract/unretract commands
    # One per tool, T0..T3.
    filaments: tuple[Filament, ...] = field(
        default_factory=lambda: (
            PLA,
            replace(PLA, color="#3060C0"),
            replace(PLA, color="#C03030"),
            replace(PLA, color="#30A030"),
        )
    )


DEFAULT = Settings()
