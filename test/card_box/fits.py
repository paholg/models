"""The fits of python/designs/card_box.py's boxes, to try before printing one:
"seam" is the front wall across the seam, for the key's fit, and "magnets" a
strip of magnet pockets, each at three fits. Both print on one plate.

They're a box's as it comes, so they hold for any box that leaves its walls,
key and magnets alone.
"""

from build.cad import Object, project
from designs.card_box import BED_GAP, SETTINGS, CardBox

box = CardBox()

project(
    __file__,
    objects={
        "seam": Object(box.seam_test, "The front wall across the seam, at three fits"),
        "magnets": Object(box.magnet_test, "Magnet pockets at three crushes"),
    },
    orca=SETTINGS,
    plates=[["seam", "magnets"]],
    # Room for their ears.
    plate_gap=BED_GAP,
)
