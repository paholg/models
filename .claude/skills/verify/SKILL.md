---
name: verify
description: Check this repo's Python (python/ and gcode/) with ruff and ty. Use after changing any Python here, and before committing it.
---

Run `just check` from the repo root. It runs, in order:

- `ruff check python gcode`
- `ruff format --check python gcode`
- `ty check`, by way of uv, which makes the environment `ty.toml` points at

It passes when all three do. Fix what it reports and run it again until it is
clean: `ruff check --fix` and `ruff format` fix most of ruff's findings on their
own; ty's take a change to the code.

This checks the Python only. A change to what `python/generate.py` writes also
wants a project generated and sliced (`just generate`, then `just slice`), to
see it in the G-code.
