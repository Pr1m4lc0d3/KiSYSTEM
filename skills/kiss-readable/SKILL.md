---
name: kiss-readable
description: Use when writing or laying out code so a human and an AI can read it, navigate it, and lift pieces out of it cleanly. Covers bounded labeled sections, intent-summaries on non-trivial functions, why-comments on complex logic, and intention-revealing naming. Use whenever code is non-obvious or a file holds more than one section of related logic.
---

# KISS — Readable

Code that explains itself keeps humans in the loop — they can debug and trust AI-written code
without reverse-engineering it. The same structure that makes code legible makes it modular and
mappable. **Write so the next reader (human or AI) never has to guess.**

## Bounded, labeled sections — one technique, three payoffs

Separate each cohesive group of code with an **inert banner comment**:

```
// ───────────────────────── Recruitment ─────────────────────────
```

That one cheap line pays off three ways:

1. **Index** — the file can be scanned like a document; the section is a heading.
2. **Seam** — the section is a bounded, liftable unit. You can transplant, prune, or reuse it
   cleanly, because the boundary is already drawn.
3. **Firewall** — a change stays inside its section; an edit doesn't bleed into neighbors (see
   `kiss-blast-radius`).

These banners are also what `kiss-map`'s generator harvests into `.kiss/inert.md`. Labeling a
section makes it readable, liftable, *and* findable at once.

## Synopsis per non-trivial unit

Above each non-trivial function/section, one line of **what it does and why** — a synopsis, the way
a modular block carries a one-line description. A reader (or the map) should grasp a unit's purpose
without reading its body.

```
// Promotes the tournament winner to the canonical id, carrying its persona and vault.
```

## Why-comments, not what-comments

Comment the **non-obvious**: the surprising branch, the workaround and the reason for it, the
constraint that isn't visible in the code. Explain **why**, not what.

Anti-patterns — these are noise, not documentation:

- Restating the code (`i++  // increment i`).
- Stale comments that no longer match the code (worse than none — delete or fix on sight).
- A paragraph where a better name would do.

## Naming as documentation

- Intention-revealing names: a reader infers purpose from the name alone.
- **Name files/partials by feature** so the file tree is itself an index
  (`auth.session.ts`, `panel.providers.cs`). A good tree needs no map to navigate.
