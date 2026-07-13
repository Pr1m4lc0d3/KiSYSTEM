# The coherence guard

**One question, one answer.** A pre-commit guard that fails the build when a *second* site starts deriving a
concept that already has a canonical owner.

## Why this exists

A size/bloat audit asks *"is each unit simple?"*. This asks *"does the system have **one answer**?"* They are
**orthogonal** — a codebase can score perfectly on file size, cohesion, dead code and coverage while N small,
clean, single-responsibility functions independently derive the same concept from different stores and
silently drift apart.

Worse: **splitting hides it.** In one ugly god-file the contradictory reads sit next to each other and are
obvious. Disperse them into tidy separate files and each becomes *easier to read* and the drift becomes
*invisible*.

## Install

1. Copy `coherence.config.json` and `run_coherence_audit.ps1` into `tools/coherence/` in your repo.
2. Edit the config: delete the example, add **your** concepts.
3. Wire it into your pre-commit hook, next to your size guard:

```sh
$PS_RUN tools/anti-bloat/run_anti_bloat_audit.ps1 -Staged || exit 1
$PS_RUN tools/coherence/run_coherence_audit.ps1   -Staged || exit 1
```

Run `-Staged` in the hook; run it with no flag to audit the whole tree.

## How to fill in the config

**Name your concepts as QUESTIONS** — *"which items are installed?"*, *"is this enabled?"*, *"what's the
price?"*

**Then find the answerers by grepping the STORE, not the concept name.** This is the whole trick.
Searching for `roster` finds nothing. Searching for the *persistence* — `*.plugin`, `roster-state.json`, a
table name, a singleton — finds **every** function that derives the concept, no matter what it is called.
Duplicates almost never share a name; that is exactly why a symbol-based "twin check" misses them.

**Every entry in `allowed` needs a reason**, and there are only three legitimate kinds:

- `CANONICAL` — the single source of truth.
- `DIFFERENT CONCEPT (why)` — it genuinely answers another question. Real, and **collapsing it would be its
  own bug** (*premature unification*).
- `DEBT (migrate to X)` — you cannot fix it today. Recorded, visible, tracked — not forgotten.

A **new** direct reader that is not on the list **fails the build**, forcing the author to either call the
canonical accessor or consciously record new debt.

## Two rules that come with it

- **Consolidation is not free.** A condition often does two jobs: the one it states, and one nobody wrote
  down. Replacing it with something cleaner and *correct* can silently delete a rule — and **your test suite
  will not tell you**, because the rule was never tested; it was never even intended.
- **Record the negative finding.** If you investigate something suspicious and conclude *"actually, this is
  correct"* — **write that at the site**, with the wrong conclusion you almost drew. Otherwise the next person
  repeats the investigation and eventually "fixes" it into a bug.

See [`skills/kiss-coherence`](../../skills/kiss-coherence) for the full audit method, and
[`docs/RETROFIT-CASE-STUDY.md`](../../docs/RETROFIT-CASE-STUDY.md) for what it found in a real 127k-line
application (spoiler: an AI that couldn't see its own data, ~48 dead abilities, a licence bypass, and a
feature that was 100% blank in production — none of which threw an exception or failed a test).
