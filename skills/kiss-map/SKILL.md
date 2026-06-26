---
name: kiss-map
description: Use before editing or creating code, to find where something is, whether it exists at all, or whether a twin/duplicate already exists — cheaply and without guessing. Use instead of grepping or reading the whole codebase, and whenever you are tempted to assume a function's existence or location.
---

# KISS — Map

Finding things by reading the codebase is expensive and unreliable: a wide grep plus a long read
burns thousands of tokens, and a missed search invites a confident wrong guess. The map fixes both.
**Consult the map first; never guess about what exists.**

## The artifact: `.kiss/inert.md`

A single generated markdown file — the project's distilled source of truth for *what exists and
where*. One compact entry per symbol:

```
file · section · symbol · signature · line · one-line synopsis
```

It is **inert** (no runtime effect), **generated** (never hand-edited), **gitignored** (cannot ship,
cannot drift in history), and the agent's **first stop**.

## Discipline

- **Consult `.kiss/inert.md` first.** Before editing: look up the symbol → jump straight to
  `file:line`. Before creating: check for a **twin** (duplicate → reuse) or **relative** (related →
  extend/compose). This is the twin/relative check `kiss-plan` calls for.
- **Grep it, don't read it whole.** Look up the one entry you need; do not load the entire map. That
  keeps it cheap at any project size.
- **It is the source of truth for existence.** "I don't think that exists" → check the map, don't
  guess. If the map disagrees with reality, the map is **stale, not wrong** — regenerate it.
- **Regenerate when stale.** One pass, cheap. Do it after adding/removing/renaming symbols, or
  whenever in doubt. Never hand-patch the map.

## Generating

```
python tools/kiss/kiss-map-gen.py <repo-root>
```

Writes `.kiss/inert.md`. The generator harvests the banner **sections**, declaration **signatures**,
and per-unit **synopses** that `kiss-readable` puts in the code — so legible code is also reliably
mappable. Run it at kickoff and whenever the structure changes; wire it into a pre-commit hook for
a map that can't drift.

## What this is (and isn't)

A **structural index** — exact, deterministic, tiny, dependency-free. It cannot hallucinate a match.
That is deliberately *not* vector/semantic RAG: embeddings are fuzzy and can return a confident-wrong
answer, the exact failure this exists to kill. A semantic layer over the synopses can be added later
for fuzzy "is there anything that *does* X?" queries — kept separate so it never drags heavy infra
into the common path.
