"""Run a project file, as `python -m build.generate FILE [ARGS...]`, the way it
runs itself, but with its workers' server already starting.

The server loads build123d before it forks the first worker (see
cad.workers()), and so does the project, each in about 1.5 s. Run as a script,
the project loads it first and only then starts the server, which loads it
again: here the server starts first, so that the two load at once.

Only the standard library is imported here, so as not to hold up the server.
"""

import multiprocessing
import os
import runpy
import sys
from multiprocessing import forkserver
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python -m build.generate FILE [ARGS...]")
    file = sys.argv[1]
    # Below what's in use, so that drawing on every core doesn't bog it down:
    # the workers and Orca, started from here, are as nice.
    os.nice(10)
    # What cad.workers() asks for: the server is the same one, already running.
    context = multiprocessing.get_context("forkserver")
    context.set_forkserver_preload([f"{__package__}.worker"])
    forkserver.ensure_running()
    # As though it were run itself: its arguments, and its folder first on
    # the path, for what it imports from beside it. runpy makes it __main__
    # while it runs, which is the file each worker runs again.
    sys.argv = sys.argv[1:]
    sys.path.insert(0, str(Path(file).resolve().parent))
    runpy.run_path(file, run_name="__main__")


if __name__ == "__main__":
    main()
