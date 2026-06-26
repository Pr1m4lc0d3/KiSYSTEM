---
name: kiss-plan
description: Use before writing code for any multi-step task, feature, or new project — orient inside the existing structure first, then turn the request into a short design doc with explicit modules, interfaces, and a verify-stepped build sequence. Use when a task is ambiguous, spans more than one file, or has more than one reasonable interpretation.
---

# KISS — Plan

**Never write a line until you understand the frame.** Conceptualize before you build. Most rework
comes from a design that was never written down, and most bloat from code written before checking
whether it already exists.

## Frame-first: the order that prevents the error

Before writing any code, in this order:

1. **Name the unit.** State exactly what function/section you are building or changing, in one
   sentence. If you can't, you don't understand it yet.
2. **Check the map for a twin or a relative.** Query `.kiss/inert.md` (see `kiss-map`):
   - **Twin** (a duplicate already exists) → reuse it. Do not write new code.
   - **Relative** (something related/adjacent exists) → extend or compose it, don't fork it.
   - Nothing → you're clear to create.
3. **Choose its shape.** Decide the bounded, labeled section it will live in (see `kiss-readable`)
   and which file it belongs to (see `kiss-modularity`).
4. **Find its slot.** Identify exactly where it plugs into the frame.
5. **Only now write** — the design doc first, then the code.

Steps 1–4 are the "measure twice." Step 5 is the "cut once."

## The design doc

Write a `design.md` (use `templates/design.md.template`). A map, not a manuscript. Four things:

1. **Goal** — done as a *verifiable* condition. Not "make it work" — "X returns Y for input Z; the
   failing test passes."
2. **Modules** — the units this breaks into. For each: what it does · how it's used · what it
   depends on. If you can't name a unit's single responsibility in one sentence, it isn't a unit.
3. **Interfaces** — how units talk. A consumer understands a unit without reading its internals; you
   change internals without breaking consumers.
4. **Build sequence** — ordered steps, each with a verify check:
   ```
   1. [step] → verify: [observable check]
   2. [step] → verify: [observable check]
   ```

## Surface ambiguity, don't paper over it

Multiple interpretations? **List them and ask** — never pick one silently. A simpler approach than
requested? Say so before building the complex one. Naming the confusion early is cheaper than
finding it in review.

## Strong vs weak goals

| Weak (needs babysitting) | Strong (loop independently) |
|---|---|
| "Add validation" | "Tests for invalid inputs pass" |
| "Fix the bug" | "A test reproducing it passes" |
| "Refactor X" | "Same tests pass before and after" |
