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
              ruff
              ty
              unzip
              uv
            ]
            ++ [
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
