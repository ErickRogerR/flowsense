# Learning log

## Week 1 — Tooling and typing

**2026-09-26 — src layout**
Didn't understand why `import flowsense` failed until I realised the package
has to be installed for it to resolve. With a flat layout it works by accident
because the working directory is on `sys.path`. The src layout makes that
accident impossible.

**2026-09-26 — narrowing**
`if x is None: return ...` isn't just defensive style — it's what lets mypy
know the type is no longer optional on the next line. Removing the guard
produces an error, which is the whole point.

**Still fuzzy:** when to use `Protocol` vs an abstract base class.
