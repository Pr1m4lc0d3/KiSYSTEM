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

## The twin check by NAME is not enough — check by QUESTION

The symbol map answers *"does a function called X exist?"* It **cannot** answer *"has someone already
answered this question?"* — and that is where duplication actually comes from.

A real case: one system had **eight** implementations of *"which agents are installed?"*. They were named
`LoadSpecialists`, `Enumerate`, `ExecuteSpecialistList`, `BuildRosterExpandedContent`… **not one contained
the word the concept goes by.** Every twin-check passed. They drifted, and the app started telling its own
AI that agents which plainly existed did not exist.

**So the twin check has two halves:**

1. **By symbol** (this map) — "is there a function called X?"
2. **By question** — "does anything already answer *this concept*?"

**How to do the second one: grep by STORE, not by concept name.**
Searching for `roster` finds nothing useful. Searching for the **persistence** finds every answerer —
file globs (`*.bgplugin`), file names (`roster-state.json`), tables, registries, singletons, env vars.
**Any function that reads a primary store directly is already answering the question.**

> **Before you write code that derives a fact from a store, grep the store.** If something already reads
> it, you are about to write a duplicate — call it instead.

## Index concepts, not just symbols

The map says *what is in each unit*. It does not say *what canonical question each unit answers, and
whether it is the sole answerer*. Keep a companion **concept index** — one entry per core concept:

```
question · canonical accessor · store · consumers · debt
```

e.g. `which agents are installed? → AgentLibraryScanner.Scan() [canonical]; store: *.bgplugin/manifest.json;
consumers: specialist_list, CouncilAgentCatalog`

This is the artifact that makes the eighth duplicate impossible to write by accident: you look up the
**question**, find the owner, and call it. See `kiss-coherence` for the full audit and the pre-commit guard
that fails the build when a new site starts deriving a concept that already has an owner.

**Why the map alone cannot save you:** a symbol index is exact about *existence* and blind to *meaning*.
Two functions can be perfect twins in behaviour and share no token in their names. Concept duplication is
invisible to it by construction — which is why it needs its own index and its own guard.

## What this is (and isn't)

A **structural index** — exact, deterministic, tiny, dependency-free. It cannot hallucinate a match.
That is deliberately *not* vector/semantic RAG: embeddings are fuzzy and can return a confident-wrong
answer, the exact failure this exists to kill. A semantic layer over the synopses can be added later
for fuzzy "is there anything that *does* X?" queries — kept separate so it never drags heavy infra
into the common path.
