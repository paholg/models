{
  description = "build123d models";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # OrcaSlicer's source, at the version of orca-slicer below: for looking up settings
    # and for its bundled profiles. Not built.
    orca-source = {
      url = "github:OrcaSlicer/OrcaSlicer/ced396fedc05842467f147ec67e926e4eb577faf";
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

        # nixpkgs is still on 2.4.2, and building 2.5 from source needs new
        # dependencies that aren't packaged yet, so wrap the upstream AppImage.
        # https://github.com/NixOS/nixpkgs/issues/585538
        #
        # A nightly, for its Snapmaker U1 filament sync: it matches a spool's
        # sub-type (Matte, Silk, SnapSpeed) to a preset, which no release does
        # yet (OrcaSlicer#16300). Go back to a release once one has it; keep
        # orca-source at the commit this was built from.
        #
        # The nightly's URL serves each night's build in turn, so this hash
        # holds only while this AppImage stays in the store: the dev shell
        # keeps it there (see ORCA_APPIMAGE), for direnv's GC root to hold.
        orca-appimage = pkgs.fetchurl {
          url = "https://github.com/OrcaSlicer/OrcaSlicer/releases/download/nightly-builds/OrcaSlicer_Linux_AppImage_Ubuntu2404_nightly.AppImage";
          hash = "sha256-8gyOVzht9r0O/9OqQqE87UnoLObaRBegGvnkqxVdxY8=";
        };
        orca-slicer =
          let
            pname = "orca-slicer";
            version = "2.6.0-dev-ced396f";
            src = orca-appimage;
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

        # Every font a model names.
        fonts = [
          pkgs.liberation_ttf
          pkgs.gyre-fonts
          pkgs.orbitron
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

        # A small TUI: pick a build123d model or a G-code script
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

      in
      {
        devShells.default = pkgs.mkShell {
          packages =
            with pkgs;
            [
              freecad
              # Turns the SVGs `just shots` draws into PNGs.
              imagemagick
              just
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
              uv
            ];

          # src/libslic3r/PrintConfig.cpp defines every setting; resources/profiles holds
          # the presets Orca copies into ~/.config/OrcaSlicer/system.
          ORCA_SOURCE = orca-source;
          # Unused, but keeps the downloaded AppImage alive alongside the shell, so a
          # rebuild of orca-slicer (after a nixpkgs update, say) needn't fetch it again
          # from a URL that has since moved on.
          ORCA_APPIMAGE = orca-appimage;

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
