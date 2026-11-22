# Models

This is my repo for primarily 3d models for 3d printing.

Models are drawn in Python with [build123d](https://github.com/gumyr/build123d)
(with heavy LLM assistance) and then generated to Orca projects that
pre-select important slicer options.

The generated files are not checked-in; you can create them with:

```bash
just generate path/to/file.py
```

this will generate files into `./gen/`.

Dependencies:

* With [nix](https://nixos.org/), just use `nix develop` or
  [`direnv`](https://direnv.net/)
* Without nix:
  - [`just`](https://just.systems/)
  - [`uv`](https://docs.astral.sh/uv/)
  - [`orca-slicer`](https://github.com/OrcaSlicer/OrcaSlicer/releases) at least
    version 2.5.0 in your PATH
  - `$ORCA_SOURCE` set to a checkout of
    [OrcaSlicer's source](https://github.com/OrcaSlicer/OrcaSlicer) at the same
    version as the binary.

If you'd like a nice command palette to explore multiple projects, run
`nix/f.sh`, or just `f` from a nix shell. This has more dependencies; they are
listed in `flake.nix`.

## G-code

The scripts in `gcode/` emit G-code directly, with the library in `python/lib`,
for interesting lattices. Not sure if it will work at all yet.

## License

Everything originating here, including anything generated from it, such as
Orca projects, G-code, or STL files, is licensed under any of

* Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE))
* MIT license ([LICENSE-MIT](LICENSE-MIT))
* CC BY 4.0 ([LICENSE-CC-BY](LICENSE-CC-BY))

at your option, except as noted below.

### Work by others

These files were created by other authors, or are adapted from their work.
They retain their license, as do any models created with them:

| Files | Work | License |
| --- | --- | --- |
| `games/feast-for-odin/card-trays/*.stl`, and `deck_tray()` in `games/feast-for-odin/insert.py`, which redraws them | [Remixed A Feast for Odin card trays](https://www.printables.com/model/1145265-remixed-a-feast-for-odin-card-trays) by DewLeen, a remix of A Feast for Odin (+exp) Organizer / Insert by RiftForge 3D. See [its README](games/feast-for-odin/card-trays/README.md). | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |
| `games/fox-in-the-forest/fox.svg` | [Fox](https://game-icons.net/1x1/caro-asercion/fox.html) by Caro Asercion, modified | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| `games/fox-in-the-forest/forest.svg` | [Forest entrance](https://game-icons.net/1x1/delapouite/forest-entrance.html) by Delapouite, modified | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| `games/fox-in-the-forest/logo.svg` | The title of The Fox in the Forest, traced from the Deluxe edition's box front. It belongs to the game's publishers, Renegade Game Studios and White Goblin Games. | Not licensed; all rights remain with its owners |
