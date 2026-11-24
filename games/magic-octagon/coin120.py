"""The Magic Octagon's coin with its arrows a third of a turn apart, not a
quarter. Two shapes: round; and round with a reeded edge, which has a bump
every 30 degrees, so that each arrow points at one.

The halves glue as coin.py's do, and only go together one way. Each shape is
an object, and the plate is one of each; the view is the two put together.
"""

from build.cad import Object, View, project
from designs.coin import COIN_SETTINGS, Coin, row

coins = {
    shape: Coin(shape, angles=(0, 120), bumps=12) for shape in ("round", "knurled")
}


project(
    __file__,
    objects={
        shape: Object(
            coin.pieces,
            "Both halves face down, and their arrows",
            settings=COIN_SETTINGS,
            skip_audit=[coin.in_joint],
        )
        for shape, coin in coins.items()
    },
    views={"assembly": View(row, "Each shape, glued", list(coins))},
    plates=[list(coins)],
)
