"""Upright card box for The Fox in the Forest Deluxe: the 61 standard-size cards
in sleeves, standing on end, with the score tracker (score.py) behind them, and
a lift-off lid held on by magnets.

The box is python/designs/card_box.py's, which has how it's made and printed.
This file is what goes in it, its colors, and its art: the fox in the body's
front, the forest entrance in its back, and the title in the lid's top, all in
yellow.

"panels" is the whole box, every panel outside down. "seam" and "magnets" are
its tests, to try the key's and the magnets' fits before printing a box. The
views are the box closed, open, and pulled apart.
"""

from dataclasses import replace
from pathlib import Path

from build123d import Pos, Sketch, import_svg, scale

from build.cad import Object, project, sketch
from designs.card_box import SETTINGS, Art, CardBox

# Contents

# Dragon Shield Matte standard sleeve, outside, at its largest: width, length.
sleeve = (66.5, 92.5)
# 61 sleeved cards, as they stand in a printed box: they filled a 47 mm cavity,
# a little loose. (Counted up at ~0.61 mm a card they'd be 37.5.)
deck = 46.5
# The score tracker, rupees and all (score.py: top_h + rupee_lift + rupee_t).
tracker = 9.2

# Colors

box_color = "forestgreen"
art_color = "yellow"

# Fox

# Its silhouette, in the body's front, below the seam: its height, and its
# middle's height on the front.
fox_h = 50
fox_z = 30
# Its outline's center, right of the front's: the fox's weight is ~0.9 mm left
# of its outline's center, and it looked left of center in print.
fox_x = 1

# Forest

# The forest entrance, in the body's back, stretched to fill it up to the seam,
# with this left clear around it, to the back's edges and the seam; 0 is full
# bleed.
forest_margin = 2

# Logo

# The title traced from the Deluxe box's front, in the lid's top.
logo_w = 60


def svg(name: str, w: float = 0, h: float = 0) -> Sketch:
    """An SVG beside this file, centered on the origin, scaled to w across and h
    high: given one alone, it keeps its proportions."""
    shape = Sketch() + import_svg(Path(__file__).with_name(name))
    size = shape.bounding_box().size
    sx = w / size.X if w else h / size.Y
    sy = h / size.Y if h else sx
    # Scaled before it's moved: scale() goes wrong on a shape that has been.
    shape = scale(shape, (sx, sy, 1))
    return sketch(Pos(-shape.bounding_box().center()) * shape)


plain = CardBox(sleeve=sleeve, stack=deck + tracker, color=box_color)
seam_back = plain.seam[1]

fox = Pos(fox_x, fox_z) * svg("fox.svg", h=fox_h)
forest = Pos(0, seam_back / 2) * svg(
    "forest.svg", plain.size[0] - 2 * forest_margin, seam_back - 2 * forest_margin
)
logo = svg("logo.svg", w=logo_w)

box = replace(
    plain,
    front=[Art("fox", art_color, fox, pattern="octagramspiral")],
    back=[Art("forest", art_color, forest, pattern="archimedeanchords")],
    top=[Art("logo", art_color, logo)],
)

project(
    __file__,
    objects={
        "panels": Object(box.panels, "Every panel outside down, and the art"),
        "seam": Object(box.seam_test, "The front wall across the seam, at three fits"),
        "magnets": Object(box.magnet_test, "Magnet pockets at three crushes"),
    },
    views={
        "assembly": Object(box.assembly, "Closed"),
        "open": Object(lambda: box.assembly(lift=40), "The lid lifted off"),
        "exploded": Object(
            lambda: box.assembly(lift=36, explode=12), "The panels pulled apart"
        ),
    },
    orca=SETTINGS,
    # The tests together, before the box.
    plates=["seam magnets", "panels"],
)
