"""Draw a build123d project as one tree of the repo has it, for diff.py.

Usage:
  diff_draw.py TREE FILE            print the names of FILE's objects
  diff_draw.py TREE FILE OBJECT OUT write OBJECT's pieces to OUT, as BREP files
                                    and pieces.json, their names in order

TREE is a checkout of the repo, the working tree or one diff.py extracted, and
FILE a project in it. What the project imports from python/ comes from TREE's,
not this one's, and `project()` only keeps what it's given: so an old commit's
project draws as it did then, though its cad.py can't do this itself.
"""

import json
import runpy
import sys
from collections.abc import Mapping
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    tree, file, *rest = (Path(a) for a in sys.argv[1:])
    python = (tree / "python").resolve()
    # Only TREE's python/: not this script's directory, nor the one uv's
    # environment points at, which are the working tree's.
    sys.path[:] = [str(python)] + [p for p in sys.path if Path(p).resolve() != HERE]

    from build import cad

    given: dict[str, cad.Object] = {}

    # Its signature, though only `objects` matters.
    def project(
        file: str,
        objects: Mapping[str, cad.Object],
        orca: Mapping[str, object] | None = None,
        plates: list[str] | None = None,
        views: Mapping[str, cad.Object] | None = None,
    ) -> None:
        given.update(objects)

    vars(cad)["project"] = project
    runpy.run_path(str(tree / file), run_name="__main__")

    match rest:
        case []:
            print("\n".join(given))
        case [name, out]:
            from build123d import export_brep

            out.mkdir(parents=True, exist_ok=True)
            obj = given[str(name)]
            drawn = obj.draw()
            pieces = drawn if isinstance(drawn, list) else [cad.Piece(drawn, str(name))]
            for i, piece in enumerate(pieces):
                export_brep(piece.shape, out / f"{i}.brep")
            names = [p.name for p in pieces]
            (out / "pieces.json").write_text(json.dumps(names))
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
