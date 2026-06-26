---
name: kiss-changelog
description: Use after a change lands — a feature, a fix, or any behavior change — to record what changed and why, so humans and future-you can follow the project's evolution without reading the diff. Use before declaring a unit of work done, not in a batch at the end.
---

# KISS — Changelog

A changelog is the project explaining its own history. Per-unit synopses keep a *file* legible
(`kiss-readable`); the changelog keeps the *project* legible over time. Write the entry when the cut
lands — not "later," because later it's reconstructed from memory and half of it is wrong.

## The ritual — when a cut lands

Before you call a unit of work done, add an entry:

- **What** changed — one line.
- **Why** — the reason, not just the mechanic.
- **Where** — the files touched.

Group under **Added / Changed / Fixed** (the Keep a Changelog convention).

## Two tiers — scale to the project

- **Simple project:** one `CHANGELOG.md`, entries under `## [Unreleased]`.
- **Shipping product:** an **internal** log (every change, never trimmed, never ships) plus a
  **public** log (a user-facing summary, per release). At release, move `[Unreleased]` into a
  versioned block and distill the public summary from it.

## Entry quality

- What **and why**, not just what. "Fixed double-count" < "Fixed double-count — totals summed the
  draft and final rows because both carried the same id."
- Keep noise out of the *public* log (whitespace, internal renames).
- **Never let it drift behind the code.** A changelog that lies is worse than none — update it as
  part of the cut, not as an afterthought.

## Why it's a measure-twice discipline

Writing the entry forces you to state, in one line, what you actually changed and why. That's a
final measurement: if you can't summarize the cut in a sentence, you probably did more than you were
asked to — go back and check the blast radius (`kiss-blast-radius`). The changelog isn't just
record-keeping; it's the receipt that proves the cut was intentional and scoped.
