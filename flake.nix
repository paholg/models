{
  description = "OpenSCAD models";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # OrcaSlicer's source, at the version of the system's orca-slicer: for looking up
    # settings and for its bundled profiles. Not built.
    orca-source = {
      url = "github:OrcaSlicer/OrcaSlicer/v2.5.0";
      flake = false;
    };
  };

  outputs =
    {
      flake-utils,
      nixpkgs,
      orca-source,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        # A small TUI: pick a .scad file or a G-code script with fzf, then open,
        # generate, preview or upload it.
        f = pkgs.writeShellApplication {
          name = "f";
          # orca-slicer comes from the system.
          runtimeInputs = with pkgs; [
            curl
            fd
            fzf
            git
            inotify-tools
            ncurses
            openscad-unstable
            prusa-slicer
            util-linux
            uv
            xdg-utils
          ];
          text = builtins.readFile ./nix/f.sh;
        };
      in
      {
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
            ++ [ f ];

          # src/libslic3r/PrintConfig.cpp defines every setting; resources/profiles holds
          # the presets Orca copies into ~/.config/OrcaSlicer/system.
          ORCA_SOURCE = orca-source;

          FONTCONFIG_FILE = pkgs.makeFontsConf {
            fontDirectories = [ pkgs.liberation_ttf ];
          };
        };
      }
    );
}
