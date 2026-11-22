"""The Magic Octagon's coin, with its arrows a quarter turn apart: one of each
shape, the octagon, the round coin and the reeded one, whose bumps are where
the octagon's vertices would be.

python/designs/coin.py has how it's made: two halves, printed face down, with
the arrows inlaid, which glue together only one way.

Each shape is an object, of both halves and their arrows; the plate is one of
each. The view is the three put together.
"""

from build.cad import Object, View, project
from designs.coin import SHAPES, Coin, row

coins = {shape: Coin(shape) for shape in SHAPES}


project(
    __file__,
    objects={
        shape: Object(coin.pieces, "Both halves face down, and their arrows")
        for shape, coin in coins.items()
    },
    views={"assembly": View(row, "Each shape, glued", list(coins))},
    plates=[list(SHAPES)],
)
