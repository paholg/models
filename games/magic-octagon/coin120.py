"""The Magic Octagon's coin with its arrows a third of a turn apart, not a
quarter. Two shapes: round; and round with a reeded edge, which has a bump
every 30 degrees, so that each arrow points at one.

The halves glue as coin.py's do, and only go together one way. Each shape is
an object, and the plate is one of each; the views are the two put together,
and pulled apart.
"""

from build.cad import Object, project
from designs.coin import Coin, row

coins = {
    shape: Coin(
        shape,
        angles=(0, 120),
        bumps=12,
        # coin.py's pin holes are 1.5 deep, which leaves little under an
        # arrow's inlay: here they are clear of both arrows.
        pin_a=90,
    )
    for shape in ("round", "knurled")
}


project(
    __file__,
    objects={
        shape: Object(coin.print, "Both halves face down, and their arrows")
        for shape, coin in coins.items()
    },
    views={
        "assembly": Object(lambda: row(coins), "Each shape, glued"),
        "exploded": Object(lambda: row(coins, 12), "Each shape, its halves apart"),
    },
    plates=[" ".join(coins)],
)
