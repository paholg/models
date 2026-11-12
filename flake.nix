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

        # A small TUI: pick a .scad file with fzf, then open, generate or slice it.
        f = pkgs.writeShellApplication {
          name = "f";
          # orca-slicer comes from the system.
          runtimeInputs = with pkgs; [
            fd
            fzf
            git
            inotify-tools
            ncurses
            openscad-unstable
            util-linux
            uv
          ];
          text = builtins.readFile ./nix/f.sh;
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
              f
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
