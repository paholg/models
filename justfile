up:
    nix run nixpkgs#nix-update -- --flake snapmaker-orca
    nix flake update
    uv --project python lock --upgrade

python *args:
    uv --project python run {{args}}
