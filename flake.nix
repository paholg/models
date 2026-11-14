{
  description = "OpenSCAD models";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # OrcaSlicer's source, at the version of orca-slicer below: for looking up settings
    # and for its bundled profiles. Not built.
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

        # nixpkgs is still on 2.4.2, and building 2.5.0 from source needs new
        # dependencies that aren't packaged yet, so wrap the upstream AppImage.
        # Remove once nixpkgs ships 2.5.0; keep the version in step with orca-source.
        # https://github.com/NixOS/nixpkgs/issues/585538
        orca-slicer =
          let
            pname = "orca-slicer";
            version = "2.5.0";
            src = pkgs.fetchurl {
              url = "https://github.com/OrcaSlicer/OrcaSlicer/releases/download/v${version}/OrcaSlicer_Linux_AppImage_Ubuntu2404_V${version}.AppImage";
              hash = "sha256-0T6wqc1hjtCAq2uCxkwKYMRQGqyR6I1awsO1JvsUGnw=";
            };
            contents = pkgs.appimageTools.extract { inherit pname version src; };
          in
          pkgs.appimageTools.wrapType2 {
            inherit pname version src;
            extraPkgs = p: [
              p.webkitgtk_4_1
              p.libsoup_3
              p.glib-networking
              p.gst_all_1.gstreamer
              p.gst_all_1.gst-plugins-base
              p.gst_all_1.gst-plugins-good
              p.gst_all_1.gst-plugins-bad
            ];
            extraInstallCommands = ''
              install -Dm444 ${contents}/*.desktop -t $out/share/applications
              substituteInPlace $out/share/applications/*.desktop \
                --replace-fail "Exec=AppRun" "Exec=orca-slicer"
              cp -r ${contents}/usr/share/icons $out/share/
            '';
          };

        # A small TUI: pick a .scad file or a G-code script with fzf, then open,
        # generate, preview or upload it.
        f = pkgs.writeShellApplication {
          name = "f";
          runtimeInputs =
            with pkgs;
            [
              curl
              fd
              fzf
              git
              inotify-tools
              jq
              ncurses
              openscad-unstable
              prusa-slicer
              util-linux
              uv
              xdg-utils
            ]
            ++ [ orca-slicer ];
          text = builtins.readFile ./nix/f.sh;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages =
            with pkgs;
            [
              just
              openscad-lsp
              openscad-unstable
              prusa-slicer
              ruff
              ty
              typst
              unzip
              util-linux
              uv
              xdg-utils
            ]
            ++ [
              f
              orca-slicer
            ];

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
