# Flowsense

Python engineering practice repo — typing, project structure, tooling and testing.
Built while moving from 7 years of enterprise RPA into Python and AI engineering.

## What's here

- `src/flowsense/types_practice.py` — worked examples of `Literal`, `TypeVar`,
  `Protocol`, `TypedDict` + `Unpack`, and explicit `None` handling, all passing
  `mypy --strict`.
- `tests/` — pytest suite covering the public API.

## Stack

Python 3.12 · uv · ruff · mypy (strict) · pytest · pre-commit

## Running it

```bash
uv sync --all-extras
uv run ruff check .
uv run mypy
uv run pytest
```

## Notes

`src/` layout is deliberate: it forces tests to run against the installed
package rather than the working directory, so packaging mistakes surface
locally instead of at install time.
