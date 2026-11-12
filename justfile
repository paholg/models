up:
    nix run nixpkgs#nix-update -- --flake snapmaker-orca
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

# Clear ~/3d-project-generated, then export each part a .scad file lists in its `// export:`
# line to ~/3d-project-generated/<stem>-<part>.3mf, an Orca project with one part per color, which
# applies and shows the settings on the file's `// orca:` line (see python/generate.py).
generate file:
    rm -rf ~/3d-project-generated
    mkdir ~/3d-project-generated
    uv --project python run python/generate.py {{file}} ~/3d-project-generated
