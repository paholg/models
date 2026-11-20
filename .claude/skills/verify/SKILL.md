---
name: verify
description: Lint code, and check model properties before committing.
---

## Lint

Run `just check` to lint code in the repo and get it passing.

Do your best to use proper types in Python for fixing type errors and not just
silence them.

## Slicer settings

For any edited project:

1. Ensure no slicer settings are being implicitly relied on (such as default
   layer height). Any such dependencies should be clearly set and documented.
2. Ensure that any slicer setting is truly needed: prefer to set in the part
   geometry wherever possible.
