# Lint, check the formatting of, and type-check the Python in python/ and gcode/.
check:
    ruff check python gcode
    ruff format --check python gcode
    # By way of uv, to make the environment ty.toml points at.
    uv --project python run ty check

up:
    nix flake update
    uv --project python lock --upgrade

python *args:
    uv --project python run {{args}}

# Run a design script, then open the G-code and HTML preview it writes.
preview file:
    #!/usr/bin/env bash
    set -euo pipefail
    out=$(uv --project python run {{file}})
    echo "$out"
    while read -r f; do
        case "$f" in
            *.gcode) setsid prusa-gcodeviewer "$f" >/dev/null 2>&1 & ;;
            *.html) xdg-open "$f" >/dev/null 2>&1 & ;;
        esac
    done <<< "$out"

# Export each part a .scad file lists in its `// export:` line to gen/<dir>/<stem>-<part>.3mf,
# where <dir> is the file's directory in this repo: an Orca project with one part per color, which
# applies and shows the settings on the file's `// orca:` line (see python/generate.py).
generate file:
    uv --project python run python/generate.py {{file}}

# Slice one of those projects with Orca's CLI, to tmp/slice/<project>.gcode, for checking what a
# print comes out as. Takes --machine, --process and --filament preset names (see python/slice.py).
[positional-arguments]
slice project *args:
    @uv --project python run python/slice.py "$@"
