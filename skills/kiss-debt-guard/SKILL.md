---
name: kiss-debt-guard
description: Use when a repo needs an enforceable size/debt control rather than advice — installs a light, dependency-free size-budget audit script plus a config, and points to heavier guards (dead-code, duplicate-surface, test-debt, dependency-risk, doc-drift) when a repo warrants them. Use during KISS kickoff, or when files keep drifting over budget despite good intentions.
---

# KISS — Debt Guard

Reflexes slip; a guard does not. This installs the smallest useful enforcement: a script that fails
when a file exceeds its size budget, so the discipline survives a tired afternoon.

## What it installs

Copy from `assets/` into the target repo (default `tools/kiss/`):

- `kiss-size-audit.py` — dependency-free (Python 3 stdlib) size-budget audit.
- `kiss-budget.config.json` — the repo's tiers, included file types, excluded paths, and waivers.

## Install workflow

1. Copy both files into `tools/kiss/`.
2. **Baseline, don't fantasize.** Run the audit and set tiers from the repo's real distribution;
   record genuine over-budget files as waivers with an expiry, rather than relaxing tiers to make
   the first run green.
3. Add a contract line to `CLAUDE.md`/`AGENTS.md`: *"Before adding code to a file, check its size
   against `tools/kiss/kiss-budget.config.json`; if over the extract tier, extract first."*
4. Wire it where it runs: a pre-commit hook, a CI step, or a documented manual run per milestone.

## Running

```
python tools/kiss/kiss-size-audit.py <repo-root>
```

Exit code is non-zero if any non-waived file exceeds the **hard-stop** tier — suitable for a hook or
CI gate. `--report` prints the full review/extract/hard-stop breakdown without failing.

## Bloat vs. length

The audit flags by line count, but line count is a *proxy*. A flagged file that has a single
responsibility and is cleanly sectioned (see `kiss-modularity`, `kiss-readable`) is legitimate —
waive it. A short file that tangles responsibilities is the real debt. The guard flags; the
comprehension test arbitrates.

## Waivers

A real exception goes in `waivers` with a reason **and an expiry date**. A waiver without an expiry
is just hidden debt. Never silently raise a tier to dodge a waiver.

## Systematic backup — via git, not clutter

Keeping a way back before a risky cut is a real duty — measure twice, cut once, *keep a rollback*.
Do it with **git**, never with copied folders.

Copied-folder backups — `project-backup/`, `*.bak`, `*.orig`, `module-old/`, `service copy.py` — are
**duplicate-surface bloat**: a grep now returns the stale copy alongside the real one, the copy
drifts from source, and nobody remembers which is canonical. It is exactly the clutter this guard
exists to catch.

- **Do:** commit before and after a unit; `git stash` or a throwaway branch before a risky cut; tag
  a checkpoint. Recoverability with zero clutter.
- **Don't:** copy files or folders as "backups" inside the tree. If you find such artifacts, delete
  them — git already remembers.

The audit enforces this: stray backup/copy artifacts are reported as **CLUTTER** so they can be
removed before they rot into the codebase.

## When to reach for heavier guards

This guard covers **size** only — the highest-leverage single axis. When the pain is elsewhere,
install a focused guard rather than reinventing it here:

| Symptom | Reach for |
|---|---|
| Unreachable/abandoned code lingering | a dead-code guard |
| Mirrored panels / old+new implementations patched in parallel | a duplicate-surface guard |
| Features shipping faster than tests | a test-debt guard |
| Fragile/obsolete dependencies | a dependency-risk guard |
| Docs that no longer match behavior | a doc-drift guard |

KISS ships the size guard and the pointers; bundling the whole family would be the bloat it exists
to prevent.
