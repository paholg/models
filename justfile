# Lint, check the formatting of, and type-check the Python in python/ and gcode/.
check:
    ruff check python gcode
    ruff format --check python gcode
    # By way of uv, to make the environment ty.toml points at.
    uv --project python run ty check
    tombi lint --error-on-warnings

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

# Write each object of a build123d project to gen/<dir>/<stem>-<object>.3mf, where <dir> is the
# file's directory in this repo: an Orca project that applies and shows the settings the file asks
# for, and one of its plates (see python/build/build.py and python/build/cad.py).
generate file:
    uv --project python run "{{file}}"

# Write an object of a build123d project to tmp/view/<stem>-<object>.step and open it in FreeCAD.
view file object:
    uv --project python run "{{file}}" --view "{{object}}"
    setsid freecad "tmp/view/$(basename "{{file}}" .py)-{{object}}.step" >/dev/null 2>&1 &

# Open FreeCAD on what the working tree's changes since a commit (HEAD by default) do to each
# piece of each project they reach, or of the projects named: green for what they add, red for
# what they remove, clear gray for what stays (see python/diff.py).
[positional-arguments]
diff *args:
    @uv --project python run python/diff.py "$@"

# Slice one of those projects with Orca's CLI, to tmp/slice/<project>.gcode, for checking what a
# print comes out as. Takes --machine, --process and --filament preset names (see python/slice.py).
[positional-arguments]
slice project *args:
    @uv --project python run python/slice.py "$@"
