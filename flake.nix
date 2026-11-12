{
  description = "OpenSCAD models";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { flake-utils, nixpkgs, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        snapmaker-orca = pkgs.callPackage ./nix/snapmaker-orca.nix { };

        # Pick a .scad file with fzf and open it in OpenSCAD, detached.
        scad = pkgs.writeShellApplication {
          name = "scad";
          runtimeInputs = with pkgs; [
            fd
            fzf
            git
            openscad-unstable
            util-linux
          ];
          text = ''
            cd "$(git rev-parse --show-toplevel)"
            files="$(fd --extension scad | sort)"
            # Show path components as aligned columns, without the suffix;
            # the real path rides along in a hidden first field.
            rows="$(echo "$files" | sed 's/\.scad$//' | column -t -s/ -o '  ')"
            # Only as wide as the longest row (plus fzf's gutter).
            width="$(($(echo "$rows" | wc -L) + 4))"
            cols="$(stty size </dev/tty | cut -d' ' -f2)"
            margin="$((cols > width ? cols - width : 0))"
            file="$(
              paste <(echo "$files") <(echo "$rows") |
                fzf --delimiter '\t' --with-nth 2 --height '~40%' --reverse \
                  --margin "0,$margin,0,0" --query "$*" --select-1 |
                cut -f1
            )"

            setsid --fork openscad "$file" >/dev/null 2>&1 </dev/null
          '';
        };
      in
      {
        packages = pkgs.lib.optionalAttrs (system == "x86_64-linux") {
          snapmaker-orca = pkgs.callPackage ./nix/snapmaker-orca.nix { };
        };

        devShells.default = pkgs.mkShell {
          packages =
            with pkgs;
            [
              openscad-lsp
              openscad-unstable
              prusa-slicer
              ruff
              ty
              unzip
              uv
            ]
            ++ [
              scad
              snapmaker-orca
            ];

          SNAPMAKER_ORCA_PROFILES = snapmaker-orca.profiles;

          FONTCONFIG_FILE = pkgs.makeFontsConf {
            fontDirectories = [ pkgs.liberation_ttf ];
          };
        };
      }
    );
}
