---
name: kiss
description: Use at the base of a project — when starting a new project, a sizable feature, or a fresh module, before much code exists — to set it up to stay clean, and as the entry point to the KISS discipline (plan, map, readable sections, modularity, blast-radius, debt). Use whenever you want clean-code structure established from the start rather than bolted on later.
---

# KISS

**Measure twice, cut once.** Every cut — every line written, edited, or deleted — is preceded by a
measurement. Measure, cut once, confirm the cut landed clean. Most bloat and breakage is cheapest
to prevent at the wellspring, *before* the cut exists; guards catch errors downstream, KISS
prevents them at the source.

This is the **front door**. It does three things: holds the measure-twice discipline, runs a
one-time **kickoff** that makes a project start clean, and **routes** to the focused KISS skills.

## The pre-cut gate — before any write, edit, or delete

The two measurements already live in the focused skills. This gate just makes sure they happened
before you cut:

| Measure (before the cut) | Skill |
|---|---|
| Does it already exist / where is it / does it have a twin? | `kiss-map` — consult `.kiss/inert.md` |
| Do I understand the frame and the slot it goes in? | `kiss-plan` |
| Is the change scoped to one bounded unit? | `kiss-blast-radius` |
| Is the host file within its size budget? | `kiss-clean-edits` (extract-on-touch) |
| **Then cut — once, deliberately.** | the edit |
| Did it land clean — nothing else touched? | `kiss-blast-radius` verify |

If you can't answer a measurement, you have not measured twice. Stop and measure.

## Kickoff — when starting a project or sizable feature

1. **Plan into the frame** → `kiss-plan` produces a `design.md` (modules, interfaces, verify-stepped
   build sequence) before code.
2. **Build the map** → `kiss-map` generates `.kiss/inert.md`, the cheap source-of-truth index the
   agent consults first.
3. **Set the budget** → `kiss-modularity` records the size/responsibility tiers.
4. **Arm the guard** → `kiss-debt-guard` installs the size audit + config.

Kickoff **writes into the repo**: `design.md`, `.kiss/inert.md` (gitignored), a budget/guard config,
and a short KISS contract merged into `CLAUDE.md`/`AGENTS.md`. That makes KISS a base, not advice.

## Routing — during ongoing work

| Moment | Skill |
|---|---|
| Starting a multi-step task or feature | `kiss-plan` |
| Finding where something is / whether it exists / has a twin | `kiss-map` |
| Writing or laying out code so it reads and lifts cleanly | `kiss-readable` |
| Creating a file / deciding where code belongs | `kiss-modularity` |
| Editing existing code without harming its neighbors | `kiss-blast-radius` |
| Adding or changing code (a method, branch, member) | `kiss-clean-edits` |
| A repo needs enforceable size/debt control | `kiss-debt-guard` |

## The model underneath

Every unit of code is a **block**: bounded, labeled, self-documenting, reusable, slotted into a
known frame — the way a modular installer or a reusable UI panel is built. The plugin is the frame;
each skill is a block. KISS keeps everything bite-size, human-legible, and easy to transplant —
enforced by discipline, not by template files.
