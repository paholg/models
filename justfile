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

# Clear gen/, then export each part a .scad file lists in its `// export:`
# line to gen/<stem>-<part>.3mf, one object per color. Save Orca projects made
# from them next to the .scad.
export file:
    find gen -mindepth 1 ! -name .keep -delete
    for p in $(sed -n 's|^// export:||p' {{file}}); do \
        openscad -q --enable=lazy-union -D "part=\"$p\"" -o "gen/{{file_stem(file)}}-$p.3mf" {{file}}; \
    done
