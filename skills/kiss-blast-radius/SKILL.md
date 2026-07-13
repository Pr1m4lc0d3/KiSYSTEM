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

## Replacing a condition — the silent-deletion trap

Containment is not enough. You can stay perfectly inside your bounded unit, change exactly what you
were asked to, pass every test — **and still delete a rule.**

Because a condition often does **two jobs**: the one it says, and one nobody wrote down.

| The "ugly" line | What it *says* | What it was **also** doing |
|---|---|---|
| `ctrl is TemplateBase ? Roster.IsEnabled(id) : Settings.IsEnabled(id)` | pick the right store | **hiding licence-locked agents** — Roster didn't know them, so it returned `false` |
| the same line, elsewhere | pick the right store | **hiding the orchestrator** from the agent roster — same accident |

Both were replaced with a *correct*, cleaner, identity-based accessor. Both hidden rules evaporated:
unlicensed agents joined a paid council; the orchestrator appeared in the agent list, un-removable.
**Neither was caught by 700+ passing tests** — because the rule was never *tested*; it was never even
*intended*. It was a side-effect that load-bore.

> **Before you replace a condition, ask what it is *incidentally preventing*.**
> Not what it says — **what it stops from happening.** Then re-implement that rule **explicitly**, or you
> have just deleted it.

**How to actually check (tests will not tell you):**

1. **Enumerate what flows through it.** For each *kind* of input, what did the old branch answer, and what
   does the new one answer? Any input whose answer **flips** is a rule you are changing — name it out loud.
2. **Hunt the fail-open default.** Where does the *new* path send an input it doesn't recognise? If that
   fallback answers "yes" for unknowns (`unknown ⇒ allowed`), then **every routing mistake becomes a grant** —
   security, licensing, visibility. This is how both incidents above became *grants* rather than denials.
3. **A green suite is not evidence here.** The rule was accidental, so no test asserts it. Reason about the
   inputs, or verify at runtime.

**Corollary — a permissive default may be load-bearing.** If `unknown ⇒ true` is what makes new records
appear at all, **do not "fix" it to fail closed.** Fix the routing that wrongly reached it, and mark the
default as deliberate (see `kiss-coherence` → *Record the negative finding*).

## Why containment beats cleanup

Collateral damage is the most expensive kind: it breaks code that was already working and that no
one was watching. Containing the radius prevents it at the source — cheaper than any amount of
after-the-fact debugging.
