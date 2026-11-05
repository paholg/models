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
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            openscad-lsp
            openscad-unstable
            unzip
          ];

          FONTCONFIG_FILE = pkgs.makeFontsConf {
            fontDirectories = [ pkgs.liberation_ttf ];
          };
        };
      }
    );
}
