# Example: Kanban CLI — built under KiSYSTEM

A small terminal Kanban board, **built entirely under the KiSYSTEM discipline**, shipped as proof
of what that produces. There's no benchmark to take on faith here — just read it.

## Read it in this order (≈10 minutes)

1. **`design.md`** — written *before* any code: the goal as a verifiable condition, one
   responsibility per module, the interfaces, and a verify-stepped build sequence.
2. **`MAP.md`** — the generated index (`kiss-map`). Normally `.kiss/inert.md` and gitignored;
   committed here so you can see it. Every symbol with its file, line, and a one-line synopsis —
   the index reads like documentation because the code was written to explain itself.
3. **`CHANGELOG.md`** — what changed and why.
4. **`kanban/`** — six tiny, single-responsibility modules. Start with `board.py`: a module
   docstring that states what it does *and what it refuses to know*, banner-sectioned, a synopsis
   on every method, why-comments on the non-obvious calls.

## What to notice

- **Modularity** — `models` (the card) · `store` (JSON I/O) · `board` (rules) · `filters` ·
  `render` (display) · `cli` (wiring). No file mixes two concerns; largest is ~113 lines.
- **Self-documenting** — every non-trivial function carries a one-line *what + why*; comments
  explain *why*, never restate code.
- **Clean by KiSYSTEM's own tools** — `kiss-size-audit` reports 0 review/extract/hard-stop
  violations and no clutter.

## Run it

```
python -m kanban add "Write the spec" --label docs
python -m kanban move 1 doing
python -m kanban list
python -m kanban list --label docs
```

Pure Python 3 standard library — no dependencies.
