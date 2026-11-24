"""The Magic Octagon's coin, reeded but without the bumps, and gold on both
faces. Three of them, their marks black and a quarter turn apart: an arrow on
each face; an arrow on one and a line, an arrow without its head, on the other;
and one with nothing on it.

The halves glue as coin.py's do, and only go together one way. Each coin is an
object, and the plate is one of each; the view is the three put together.
"""

from build.cad import Object, View, project
from designs.coin import COIN_SETTINGS, HALF_COLORS, Coin, row

GOLD = HALF_COLORS[0]

MARKS = {
    "arrows": ("arrow", "arrow"),
    "line": ("arrow", "line"),
    "plain": ("", ""),
}

coins = {
    name: Coin("knurled", marks=marks, colors=(GOLD, GOLD), bumps=0)
    for name, marks in MARKS.items()
}


project(
    __file__,
    objects={
        name: Object(
            coin.pieces,
            "Both halves face down, and what's inlaid",
            settings=COIN_SETTINGS,
            skip_audit=[coin.in_joint],
        )
        for name, coin in coins.items()
    },
    views={"assembly": View(row, "Each coin, glued", list(coins))},
    plates=[list(coins)],
)
