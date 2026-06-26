---
name: kiss-modularity
description: Use when creating a file, deciding where new code belongs, or about to edit an existing file — to keep units cohesive and right-sized while guarding BOTH cliffs: files that grow into monoliths, and codebases that shatter into so many tiny files that the tree and the map become their own complexity. Covers one-concern-per-unit, sections-before-files, size tiers, real-bloat vs legitimate length, and a responsibility check.
---

# KISS — Modularity

Keep units bite-size and cohesive so a human — and the map — can navigate them. There are **two**
ways to fail here, not one: a file that grows into a monolith, and a codebase that shatters into so
many tiny files that the tree and the index become their own complexity. Modularity means steering
between both. Splitting is not automatically good; over-splitting is its own mess.

## One coherent concern per *unit* — and a unit is a section OR a file

The rule is **one coherent concern per unit**, not "one function per file." A concern can be large.
Modularity works at two levels:

- **Section** — a banner-labeled block inside a file (see `kiss-readable`): bounded, liftable, and
  indexed by the map. Modularity *without* a new file.
- **File** — a whole module.

**Reach for a section before a new file.** A section gives every benefit of a split — a named,
bounded, mappable, transplantable unit — at none of the cost: no extra file in the tree, no extra
thing to wire, no bigger map. Promote a section to its own file only when it **earns** it:

1. the file is genuinely **too big** (size tiers below), or
2. it holds genuinely **independent concerns** that change for different reasons, or
3. another module needs to **reuse** that section on its own.

If none of those is true, keep it a section. A file that exists only to hold one trivial thing used
in one place is **fragmentation, not modularity** — fold it back in.

## The two failure modes

| Failure | Looks like | Fix |
|---|---|---|
| **Monolith** | one file doing several things; 800+ lines | split a concern out (section → file) |
| **Fragmentation** | many 10–30 line files; ten files to follow one flow; a sprawling map | consolidate trivial files into sections of a cohesive module |

Minimize file count **subject to clarity**: the fewest files that each hold one clear concern — not
the most units you can manufacture.

## Size tiers (the too-big cliff; defaults — tune per repo)

| Lines | Tier | Action |
|---|---|---|
| ~300 | review | Pause: does this still have one coherent concern? |
| ~500 | extract | Pull a section out *before* adding more. |
| ~800 | hard stop | Do not add; split first. |

The tiers (a review point, an extract-first point, a line you don't cross) matter more than the
exact numbers.

## Bloat vs. legitimate length

Length is a proxy. A long file that does **one** thing and is cleanly **sectioned** is legitimate —
don't split it for the line count alone. A short file that tangles three concerns is the real
problem, even under budget. Size flags candidates; cohesion arbitrates.

## Responsibility check — before every edit

State the file's single concern in one sentence before editing. Can't? It's doing too much. But
before you split into a new *file*, ask whether a *section* would do — usually it will.

## Common mistakes

- **Over-splitting** — a file per function. Sections are cheaper, and the map stays smaller.
- **Splitting for line count alone** — size is a proxy, not the disease; mixed concerns are.
- **Keeping a one-function file used in one place** — fold it into its caller's module as a section.
- **Reading "one responsibility per file" as a mandate to atomize** — it means one *concern* per
  *unit*, and a section is a unit.
