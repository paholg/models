# Lint, check the formatting of, and type-check the repo's Python: the projects,
# python/ and gcode/.
check:
    ruff check
    ruff format --check
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
# for, and one of its plates (see python/build/build.py and python/build/cad.py). Or, with the
# names of objects and views, just theirs, leaving the rest as it is: a view named takes the
# objects it uses that aren't as they were last drawn. By way of python/build/generate.py, which
# starts the workers' server before the file loads build123d.
generate file *names:
    uv --project python run python -m build.generate "{{file}}" {{names}}

# Write an object of a build123d project to tmp/view/<stem>-<object>.step and open it in FreeCAD.
view file object:
    uv --project python run "{{file}}" --view "{{object}}"
    setsid freecad "tmp/view/$(basename "{{file}}" .py)-{{object}}.step" nix/fit.FCMacro >/dev/null 2>&1 &

# Look a project's objects, or those named, over for edges left sharp and for slivers where
# cuts meet, and fail if there are any (see python/build/audit.py).
audit file *objects:
    uv --project python run "{{file}}" --audit {{objects}}

# Write line drawings of an object or view to tmp/shots/<stem>-<object>-*.png: from all round,
# or close up at each X,Y,Z given, or, with `audit`, at each spot its audit finds.
shots file object *where:
    uv --project python run "{{file}}" --shots "{{object}}" {{where}}

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

# Check that the printer's loaded filaments and Spoolman agree, so Orca's filament sync picks the
# right presets (see python/spools.py).
spools:
    @uv --project python run python/spools.py
