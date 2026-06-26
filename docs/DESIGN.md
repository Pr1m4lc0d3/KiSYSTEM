# KiSYSTEM — Design

> This document exists because KiSYSTEM practices what it preaches: **conceptualize first, then
> build.** It is the design doc for the plugin itself — written the way `kiss-plan` says to write one.

## Purpose

KiSYSTEM is a clean-code discipline you turn on at the **base** of a project — before much code exists —
so the project *starts* clean and *stays* clean. Its one principle is the carpenter's rule:

> **Measure twice, cut once.** Prevention at the wellspring is cheaper than any cleanup.

Guards catch errors downstream. KiSYSTEM prevents them at the source: every cut (line written, edited,
or deleted) is preceded by a measurement, made once, then confirmed clean.

## Two failures it exists to kill

1. **"I can't read AI code."** Code that doesn't explain itself takes humans out of the loop.
2. **"AI breaks my working code."** Refactors that overreach damage neighbors that were fine.

The first is answered by self-documenting, labeled, modular sections; the second by blast-radius
containment. Both are forms of measuring before cutting.

## Architecture

One plugin, a thin base skill that orchestrates seven focused, independently-usable skills.

| Skill | Single responsibility |
|---|---|
| `kiss` | Measure-twice-cut-once spine: kickoff + the pre-cut gate + routing. |
| `kiss-plan` | Orient in the frame, then a `design.md`: name the unit, check the map for a twin/relative, choose its shape, find its slot — before code. |
| `kiss-map` | The cheap source-of-truth index `.kiss/inert.md`: what exists, where, and whether it has a twin. |
| `kiss-readable` | Bounded labeled sections (index + seam + firewall), per-unit synopses, why-comments, intention-revealing naming. |
| `kiss-modularity` | One concern per unit, sections before files, size tiers (guards monoliths *and* over-fragmentation), responsibility check. |
| `kiss-blast-radius` | Keep a change inside its bounded unit; verify the neighbors are untouched. |
| `kiss-clean-edits` | Edit-time reflexes: extract-on-touch, surgical edits, YAGNI. |
| `kiss-debt-guard` | A light, dependency-free size audit + config; a menu of heavier guards. |

Each skill is small enough to read in one sitting and usable alone. The base composes them; it does
not absorb them — a system that preaches modularity must be modular itself.

## The "from the base" workflow

**Kickoff** (invoke `kiss` when starting): plan → `design.md`; generate `.kiss/inert.md`; set the
size budget; arm the guard; write a short KiSYSTEM contract into `CLAUDE.md`/`AGENTS.md`. The project
now *starts* with a design, a map, a budget, and a guard.

**Ongoing**, every cut passes the gate: *map* says what exists → *plan* says you understand the
frame → write it as a labeled, self-documenting, reusable section → *blast-radius* keeps the change
contained → *size* stays under budget → confirm it landed clean.

## Lineage: the block model, generalized

KiSYSTEM generalizes a proven modular-installer model (bounded "blocks" with a one-line synopsis, slotted
into an orchestrated frame, never duplicated, regenerated on change) and a reusable-UI-panel model
(one unit built well, adapted across many interfaces). That discipline is normally enforced by
physical template files; KiSYSTEM enforces the same thing through **skills** — language-agnostic, no
template files. A code section is a block; its banner is its label and its seam; `inert.md` is the
chain map; the blast radius is its conductor isolation.

## Provenance

The clean-edit reflexes are built test-first. The core `extract-on-touch` rule has a documented
baseline (fresh agents grew an over-budget file with zero size-awareness — an *omission*, not
defiance), a fix (a required measurement, which can't be negotiated away the way a prohibition can),
and a hardening pass (closing the "it's a dispatch chain, no seam" loophole). KiSYSTEM holds that
standard: guidance is validated against real agent behavior, not asserted.

## Defaults (tunable)

Size tiers, shipped as documented defaults a repo overrides: **review** ~300 · **extract** ~500 ·
**hard-stop** ~800. The tiers (a review point, an extract-first point, a line you don't cross) matter
more than the exact numbers.
