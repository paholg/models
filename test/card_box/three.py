"""Three card boxes in one project, of three sizes, each with a dot on its front:
a test of python/designs/card_box.py's boxes side by side, each named, which
goes before its pieces' names.

Each box is an object, every panel outside down, on a plate of its own. The
view "assembly" is the three closed, side by side.
"""

from dataclasses import replace

from build123d import Circle, Pos

from build.cad import Object, Piece, project
from designs.card_box import SETTINGS, Art, CardBox

# Each one's name and deck.
decks = [("thin", 20), ("mid", 34), ("fat", 52)]

boxes = {
    name: CardBox(
        name=name,
        stack=deck + 2 * i,
        front=[Art("dot", "yellow", Pos(0, 30) * Circle(8 + 2 * i))],
    )
    for i, (name, deck) in enumerate(decks)
}


def assembly() -> list[Piece]:
    return [
        replace(p, shape=Pos(i * (box.size[0] + 20), 0, 0) * p.shape)
        for i, box in enumerate(boxes.values())
        for p in box.assembly()
    ]


project(
    __file__,
    objects={
        name: Object(box.panels, f"The {name} box's panels outside down")
        for name, box in boxes.items()
    },
    views={"assembly": Object(assembly, "The three closed, side by side")},
    orca=SETTINGS,
    plates=list(boxes),
)
