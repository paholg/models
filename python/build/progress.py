"""A progress bar for generating, on the terminal's last line, below the log.

Generating is a known list of stages: each object is drawn, assembled by Orca
and written, each view written, and the plates written. Whatever does one says
so with `stage()`, and whoever knows how many there will be with `expect()`.
Off a terminal, or outside `shown()`, both do nothing.
"""

import contextlib
import shutil
import sys
import threading
from collections.abc import Generator
from typing import TextIO

WIDTH = 20  # of the bar itself, in cells


class Bar:
    """Stands in for stdout, keeping the bar under whatever is printed."""

    def __init__(self, out: TextIO) -> None:
        self.out = out
        self.lock = threading.RLock()
        self.total = 0
        self.done = 0
        self.running: list[str] = []
        self.pending = ""  # a line printed only in part, held back until it ends
        self.drawn = False

    def write(self, text: str) -> int:
        with self.lock:
            lines, _, self.pending = (self.pending + text).rpartition("\n")
            if lines:
                self.clear()
                self.out.write(lines + "\n")
                self.draw()
        return len(text)

    def flush(self) -> None:
        self.out.flush()

    def isatty(self) -> bool:
        return self.out.isatty()

    def clear(self) -> None:
        if self.drawn:
            self.out.write("\r\033[K")
            self.drawn = False

    def draw(self) -> None:
        with self.lock:
            self.clear()
            filled = WIDTH * self.done // self.total if self.total else 0
            line = (
                f"\033[1m{self.done}/{self.total}\033[0m "
                f"\033[32m{'━' * filled}\033[2m{'━' * (WIDTH - filled)}\033[0m "
            )
            # Cut to the terminal's width: a line that wraps can't be cleared.
            room = shutil.get_terminal_size().columns - len(
                f"{self.done}/{self.total} {'━' * WIDTH} "
            )
            what = ", ".join(self.running) or ("" if self.done else "starting")
            if len(what) > room:
                what = what[: max(room - 1, 0)] + "…"
            self.out.write(line + what)
            self.out.flush()
            self.drawn = True


bar: Bar | None = None


@contextlib.contextmanager
def shown() -> Generator[None]:
    """Show the bar while generating, if stdout is a terminal."""
    global bar
    if not sys.stdout.isatty():
        yield
        return
    out, err = sys.stdout, sys.stderr
    bar = sys.stdout = sys.stderr = Bar(out)
    bar.draw()
    try:
        yield
    finally:
        with bar.lock:
            if bar.pending:
                bar.write("\n")
            bar.clear()
            bar.flush()
        sys.stdout, sys.stderr, bar = out, err, None


def expect(n: int) -> None:
    """Count `n` stages more to come."""
    if bar is not None:
        with bar.lock:
            bar.total += n
            bar.draw()


def start(what: str) -> None:
    """Start a stage, shown by `what` while it runs: "drawing lid", say."""
    if bar is not None:
        with bar.lock:
            bar.running.append(what)
            bar.draw()


def finish(what: str) -> None:
    """Finish the stage `start()` was given `what` for."""
    if bar is not None:
        with bar.lock:
            bar.running.remove(what)
            bar.done += 1
            bar.draw()


@contextlib.contextmanager
def stage(what: str) -> Generator[None]:
    """Do a stage, between `start()` and `finish()`."""
    start(what)
    try:
        yield
    finally:
        finish(what)
