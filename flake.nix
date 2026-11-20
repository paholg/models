{
  description = "OpenSCAD and build123d models";

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
            version = "2.5.1";
            src = pkgs.fetchurl {
              url = "https://github.com/OrcaSlicer/OrcaSlicer/releases/download/v${version}/OrcaSlicer_Linux_AppImage_Ubuntu2404_V${version}.AppImage";
              hash = "sha256-BzuBBckoNWFB2w3bzoi4HVLHqeJEL5uq4KkInIn/BOs=";
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

        # Every font a model names: Liberation Sans is also OpenSCAD's default.
        fonts = [
          pkgs.liberation_ttf
          pkgs.gyre-fonts
        ];

        # Include native dependencies for build123d with uv.
        uv = pkgs.symlinkJoin {
          name = "uv";
          paths = [ pkgs.uv ];
          nativeBuildInputs = [ pkgs.makeWrapper ];
          postBuild = ''
            wrapProgram $out/bin/uv --prefix LD_LIBRARY_PATH : ${
              pkgs.lib.makeLibraryPath (
                with pkgs;
                [
                  expat
                  libGL
                  libx11
                  stdenv.cc.cc.lib
                  zlib
                ]
              )
            }
          '';
        };

        # A small TUI: pick a .scad file, a build123d model or a G-code script
        # with fzf, then open, generate, preview or upload it.
        f = pkgs.writeShellApplication {
          name = "f";
          runtimeInputs =
            with pkgs;
            [
              curl
              fd
              freecad
              fzf
              git
              inotify-tools
              jq
              ncurses
              openscad-unstable
              prusa-slicer
              util-linux
              xdg-utils
            ]
            ++ [
              orca-slicer
              uv
            ];
          text = builtins.readFile ./nix/f.sh;
        };

        # `just diff`, from anywhere in the repo: what the working tree's changes
        # since a commit do to each part (see python/diff.py).
        scadiff = pkgs.writeShellApplication {
          name = "scadiff";
          runtimeInputs =
            with pkgs;
            [
              git
              gnutar
              openscad-unstable
            ]
            ++ [ uv ];
          text = ''
            cd "$(git rev-parse --show-toplevel)"
            exec uv --project python run python/diff.py "$@"
          '';
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages =
            with pkgs;
            [
              freecad
              just
              openscad-lsp
              openscad-unstable
              prusa-slicer
              ruff
              tombi
              ty
              typst
              unzip
              util-linux
              xdg-utils
            ]
            ++ [
              f
              orca-slicer
              scadiff
              uv
            ];

          # src/libslic3r/PrintConfig.cpp defines every setting; resources/profiles holds
          # the presets Orca copies into ~/.config/OrcaSlicer/system.
          ORCA_SOURCE = orca-source;

          FONTCONFIG_FILE = pkgs.makeFontsConf { fontDirectories = fonts; };
          # For build123d, whose fontconfig is older than the system's and warns at
          # every line of its config files: only the fonts. python/build/cad.py.
          CAD_FONTCONFIG_FILE = pkgs.writeText "cad-fonts.conf" ''
            <?xml version="1.0"?>
            <!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
            <fontconfig>
              ${pkgs.lib.concatMapStrings (font: "<dir>${font}</dir>") fonts}
              <cachedir prefix="xdg">fontconfig-cad</cachedir>
            </fontconfig>
          '';
        };
      }
    );
}
