---
name: kiss-blast-radius
description: Use before editing, refactoring, moving, or deleting existing code — to keep the change contained to its bounded unit and prevent collateral damage to surrounding services and functions. Use whenever a change touches a file other code depends on, or whenever a refactor could ripple beyond the thing you were asked to change.
---

# KISS — Blast Radius

The most-voiced fear about AI coding: it "helpfully" rewrites the code around your change and breaks
things that worked. This skill answers it. **A change must stay inside its boundary; the surrounding
services and functions are off-limits unless the task explicitly includes them.**

## Before the cut — contain it

1. **Identify the bounded unit** you are allowed to touch — the labeled section / function / module
   the task is about. Use `kiss-map` (`.kiss/inert.md`) to see exactly what that unit is and what
   references it.
2. **Map the radius.** What depends on this unit? A change to a shared interface has a large radius;
   a change inside one section's body has a small one. Prefer the smallest-radius change that
   solves the problem.
3. **Draw the line.** Everything outside the unit is off-limits. You are not refactoring the
   neighbors, renaming their variables, or "improving" them — even if they look improvable.

## The cut — once, surgically

- Every changed line traces to the request (see `kiss-clean-edits`). If you can't trace it, don't
  cut it.
- Prefer extracting a section's body over rewriting in place (the labeled boundary from
  `kiss-readable` is your firewall — keep the cut on one side of it).
- Make the change **once**, deliberately. Thrashing — edit, undo, re-edit across files — widens the
  radius and is how surrounding code gets damaged.

## After the cut — verify non-interference

A change isn't done because it's written; it's done when you've shown it didn't break the neighbors:

- **Scope the diff** — every changed file/line should be inside the intended unit. A surprise file
  in the diff is a blast-radius leak; investigate it.
- **Build / run the affected tests** — confirm the neighbors still pass, not just your unit.
- **Re-check the map** — symbols you didn't intend to touch should be unchanged.

State the evidence, don't assert success. "Diff is confined to `payments/`, build is green, the
auth tests still pass" — not "should be fine."

## Why containment beats cleanup

Collateral damage is the most expensive kind: it breaks code that was already working and that no
one was watching. Containing the radius prevents it at the source — cheaper than any amount of
after-the-fact debugging.
