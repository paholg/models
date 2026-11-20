"""The Magic Octagon's coin, with its arrows a quarter turn apart: one of each
shape, the octagon, the round coin and the reeded one, whose bumps are where
the octagon's vertices would be.

python/designs/coin.py has how it's made: two halves, printed face down, with
the arrows inlaid, which glue together only one way.

Each shape is an object, of both halves and their arrows; the plate is one of
each. The views are the three put together, and pulled apart.
"""

from build.cad import Object, project
from designs.coin import SHAPES, Coin, row

coins = {shape: Coin(shape) for shape in SHAPES}


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
    plates=[" ".join(SHAPES)],
)
