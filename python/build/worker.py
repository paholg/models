"""What the server that cad.py's workers fork from loads: build123d, once for
them all. A worker runs the project file again, which has already said what it
says in the project's own process: so it says nothing until it draws."""

import os
import sys
import warnings

from . import cad

cad.given = {}
# The warnings a worker gives as it draws: those it would have.
heard = list(warnings.filters)
warnings.simplefilter("ignore")
sys.stdout = open(os.devnull, "w")  # noqa: SIM115  # for as long as the server runs
