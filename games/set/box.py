"""Upright card box for SET: the 81 cards standing on end, with a lift-off lid
held on by magnets.

The box is python/designs/card_box.py's, which has how it's made and printed.
This file is what goes in it, its colors, and its art: three cards on the
front, and the logo in the lid's top.

Five colors, so the body and the lid print apart, each an object of its own:
the body in purple, white, green and red, the lid in lavender, purple and
white. The view is the box closed.

The logo's letters are each set alone, so nothing is lost to OCCT reading only
a font's `kern` table.
"""

from dataclasses import replace
from math import floor
from pathlib import Path

from build123d import (
    FontStyle,
    Kind,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    Shape,
    Sketch,
    SlotCenterToCenter,
    Text,
    import_svg,
    offset,
    scale,
)

from build.cad import Object, View, project, sketch
from designs.card_box import SETTINGS, Art, CardBox

# Contents

# Dimensions of the sleeved cards.
sleeve = (59.5, 91.0)
# Depth of the full deck.
deck = 50

# Colors

box_color = "purple"
lid_color = "lavender"
card_color = "white"

# Cards

# A card on the front: its width. Its length is as a real card's.
card_w = 19
card_r = 1.6
# Between cards.
card_gap = 2.5
# The row of them leans this far, counter-clockwise; their lines on the bed
# lean with them, to run along the cards.
cards_lean = 12
# The row's middle, as a share of the front's height below the seam. Low
# enough to keep the cards off the magnets' pockets, 10 mm under the seam,
# where the wall is too thin for an inlay.
cards_at = 0.43
# The symbols, as measured off a picture of the cards, in card widths: each
# one's size, along the card's width and across, and from one to the next.
diamond_size = (0.683, 0.354)
oval_size = (0.659, 0.311)
squiggle_size = (0.634, 0.323)
symbol_pitch = 0.442
# The line an open or shaded symbol is drawn in.
symbol_line = 0.8
# A shaded symbol's stripes: their width, and from one to the next.
shade = (0.45, 0.9)

# Logo

# Across the lid's top, all of it.
logo_w = 62
# What the letters are set in.
font = "TeX Gyre Termes"

plain = CardBox(sleeve=sleeve, stack=deck, color=box_color, lid_color=lid_color)

# The cards. Each is drawn upright at the origin, its symbols lying across it,
# one above the next.

card = (card_w, card_w * 89 / 57)


def diamond() -> Sketch:
    x, y = card_w * diamond_size[0] / 2, card_w * diamond_size[1] / 2
    return sketch(Sketch() + Polygon((-x, 0), (0, -y), (x, 0), (0, y), align=None))


def oval() -> Sketch:
    x, y = card_w * oval_size[0], card_w * oval_size[1]
    return sketch(Sketch() + SlotCenterToCenter(x - y, y))


def squiggle(open: bool = False) -> Sketch:
    """Traced from the same picture; open, its outline alone. Outlined before
    it's scaled, in the trace's own units, as OCCT can't offset the curves
    scale() leaves: its scale across and along differ by 0.3%."""
    shape = sketch(Sketch() + import_svg(Path(__file__).with_name("squiggle.svg")))
    size = shape.bounding_box().size
    sx = card_w * squiggle_size[0] / size.X
    sy = card_w * squiggle_size[1] / size.Y
    if open:
        shape = outline(shape, symbol_line * 2 / (sx + sy))
    # Scaled before it's moved: scale() goes wrong on a shape that has been.
    shape = scale(shape, (sx, sy, 1))
    return sketch(Pos(-shape.bounding_box().center()) * shape)


def outline(shape: Sketch, line: float = symbol_line) -> Sketch:
    """An open symbol: its outline alone, `line` wide. Its corners rounded
    inside, where the squiggle's traced curves meet, which OCCT can't
    mitre."""
    return sketch(shape - offset(shape, -line, kind=Kind.ARC))


def shaded(shape: Sketch) -> Sketch:
    """Its outline, and stripes across it, evenly either side of its middle."""
    n = floor(card[0] / 2 / shade[1])
    stripes = [
        Pos(k * shade[1], 0) * Rectangle(shade[0], card[0]) for k in range(-n, n + 1)
    ]
    return sketch(outline(shape) + (shape & (Sketch() + stripes)))


def symbols(n: int, shape: Sketch) -> Sketch:
    """n of a symbol, as they go on a card."""
    pitch = symbol_pitch * card_w
    return sketch(
        Sketch() + [Pos(0, (i - (n - 1) / 2) * pitch) * shape for i in range(n)]
    )


def on_card(i: int, shape: Shape) -> Sketch:
    """Moved to card i's place, in a leaning row under the seam."""
    row = Pos(0, cards_at * plain.seam[0]) * Rot(0, 0, cards_lean)
    return sketch(row * Pos((i - 1) * (card[0] + card_gap), 0) * shape)


# The front, a layer at a time: the cards themselves, then what's on them. The
# open squiggle is the box showing through its card.
cards = sketch(
    Sketch()
    + [on_card(i, RectangleRounded(*card, card_r)) for i in range(3)]
    - on_card(2, squiggle(open=True))
)
diamonds = on_card(0, symbols(3, diamond()))
ovals = on_card(1, symbols(2, shaded(oval())))

# The logo: for each letter a white tile, edged in purple, in front of a purple
# one and one striped purple and white, each up and to the right of the last.

# A tile's side, with the row of them logo_w across.
tile = logo_w / (2 * 1.4 + 1.44)
tile_size = (tile, 0.88 * tile)
tile_pitch = 1.4 * tile
tile_edge = 0.06 * tile
# The tiles behind: how far each is from the front one.
tile_mid = (0.22 * tile, 0.16 * tile)
tile_far = (0.44 * tile, 0.3 * tile)
tile_stripes = 8


def square(grow: float = 0) -> Sketch:
    """A tile, grown by `grow`."""
    return sketch(
        Sketch() + Rectangle(tile_size[0] + 2 * grow, tile_size[1] + 2 * grow)
    )


def tile_at(i: int, shape: Shape) -> Sketch:
    """At letter i's place, the row centered."""
    return sketch(Pos((i - 1) * tile_pitch - tile_far[0] / 2, -tile_far[1] / 2) * shape)


def text(s: str, size: float, style: FontStyle) -> Sketch:
    """Centered as OpenSCAD set it: across by its advance, and up and down by
    its ink. `size` is OpenSCAD's, which is about 0.72 of the font's em."""
    t = Text(s, size / 0.72, font, font_style=style)
    return Pos(0, -t.bounding_box().center().Y) * t


def letter(i: int) -> Sketch:
    if i == 0:
        s = text("S", 1.12 * tile, FontStyle.BOLDITALIC)
        return Pos(-0.06 * tile, -0.13 * tile) * s
    return text("SET"[i], 0.58 * tile, FontStyle.BOLD)


def bars() -> Sketch:
    """The striped tile's."""
    pitch = tile_size[1] / tile_stripes
    return sketch(
        Sketch()
        + [
            Pos(0, -tile_size[1] / 2 + (k + 0.25) * pitch)
            * Rectangle(tile_size[0], pitch / 2)
            for k in range(tile_stripes)
        ]
    )


# The purple: the striped tiles' frames and bars, the middle tiles, and the
# front tiles' edges and letters, which the white covers but for its edge and
# letter.
logo_purple = sketch(
    Sketch()
    + [
        tile_at(i, part)
        for i in range(3)
        for part in [
            Pos(*tile_far) * (square() - square(-tile_edge) + bars()),
            Pos(*tile_mid) * square(),
            square(tile_edge),
            letter(i),
        ]
    ]
)
# The white: the front tiles, less their letters, and between the striped
# tiles' bars, where they show past the tiles in front of them: their own, and
# the next letter's.
fronts = Sketch() + [
    tile_at(i, part)
    for i in range(3)
    for part in [Pos(*tile_mid) * square(), square(tile_edge), letter(i)]
]
logo_white = sketch(
    Sketch()
    + [tile_at(i, square() - letter(i)) for i in range(3)]
    + (
        Sketch()
        + [tile_at(i, Pos(*tile_far) * (square(-tile_edge) - bars())) for i in range(3)]
        - fronts
    )
)

box = replace(
    plain,
    front=[
        Art("cards", card_color, cards, turn=cards_lean),
        Art("diamonds", "green", diamonds, turn=cards_lean),
        Art("ovals", "red", ovals, turn=cards_lean),
    ],
    top=[Art("logo", box_color, logo_purple), Art("logo white", "white", logo_white)],
)

project(
    __file__,
    objects={
        "body": Object(box.body, "The body's panels outside down, and the cards"),
        "lid": Object(box.lid, "The lid's panels outside down, and the logo"),
    },
    views={
        "assembly": View(
            lambda o: box.closed(o["body"] + o["lid"]), "Closed", ["body", "lid"]
        )
    },
    orca=SETTINGS,
    # Apart: five colors are more than the printer's four heads.
    plates=[["body"], ["lid"]],
)
