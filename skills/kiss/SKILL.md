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
| **Does this concept already have an OWNER?** (grep the **store**, not the name) | **`kiss-coherence`** |
| **About to hardcode a visual constant** (font size, color, spacing, radius)? **Does a design token already own that value?** | **`kiss-coherence`** → *design values* |
| Do I understand the frame and the slot it goes in? | `kiss-plan` |
| Is the change scoped to one bounded unit? | `kiss-blast-radius` |
| **If replacing a condition — what is it *incidentally* preventing?** | **`kiss-blast-radius`** |
| **If DELETING an entity — what is its full footprint?** (assets, config rows, data dirs, build output) | **`kiss-blast-radius`** → *residue trap* |
| Is the host file within its size budget? | `kiss-clean-edits` (extract-on-touch) |
| **Then cut — once, deliberately.** | the edit |
| Did it land clean — nothing else touched? | `kiss-blast-radius` verify |

If you can't answer a measurement, you have not measured twice. Stop and measure.

**The two measurements people skip, and what they cost:**

- **Skipping the concept check** is how one system ended up with **eight** implementations of *"which
  agents are installed?"* — each named differently, each locally clean, every twin-check passing. They
  drifted until the app told its own AI that agents which plainly existed did not exist. A symbol map
  cannot catch this; only grepping the **store** can.
- **Skipping the incidental-prevention check** is how a *correct*, cleaner refactor **silently deleted a
  licence gate** and, separately, un-hid an object that was never meant to be listed. Both passed 700+
  tests, because the rule they destroyed was never tested — it was never even *intended*.

## Kickoff — when starting a project or sizable feature

1. **Plan into the frame** → `kiss-plan` produces a `design.md` (modules, interfaces, verify-stepped
   build sequence) before code.
2. **Build the map** → `kiss-map` generates `.kiss/inert.md`, the cheap source-of-truth index the
   agent consults first.
3. **Set the budget** → `kiss-modularity` records the size/responsibility tiers.
4. **Arm the guards** → `kiss-debt-guard` installs the size audit + config; `kiss-coherence` installs the
   concept guard (fails the build when a second site starts deriving a concept that already has an owner)
   and seeds a **concept index** — `question · canonical accessor · store · consumers`.
5. **Establish the design system** → one source for the **visual constants** the UI reasons about — a type
   scale, a spacing scale, a color palette, radii — defined in a token file and documented in **`DESIGN.md`**
   (the scale, the rungs, the rationale). This is a coherence store like any other: register the token file
   with `kiss-coherence` so a hardcoded literal that duplicates a token's value is caught as divergent
   duplication. **Adopt it from the first line — no component hardcodes a value a token owns.** A token
   layer with near-zero adoption is *worse* than none: it reads as a design system but every value is
   answered in N hardcoded places, so the app cannot be retuned from one file and every screen is hand-
   fixed forever. `DESIGN.md` is a living deliverable — when the scale gains a rung, it is recorded there.

Kickoff **writes into the repo**: `design.md`, `DESIGN.md` + its token file, `.kiss/inert.md` (gitignored),
a budget/guard config, and a short KISS contract merged into `CLAUDE.md`/`AGENTS.md`. That makes KISS a
base, not advice.

## Routing — during ongoing work

| Moment | Skill |
|---|---|
| Starting a multi-step task or feature | `kiss-plan` |
| Finding where something is / whether it exists / has a twin | `kiss-map` |
| Writing or laying out code so it reads and lifts cleanly | `kiss-readable` |
| Creating a file / deciding where code belongs | `kiss-modularity` |
| Editing existing code without harming its neighbors | `kiss-blast-radius` |
| The same concept is derived in more than one place / auditing an existing codebase | `kiss-coherence` |
| About to hardcode a visual constant (size, color, spacing) a token could own / a token layer exists but nothing uses it | `kiss-coherence` (design values) |
| Adding or changing code (a method, branch, member) | `kiss-clean-edits` |
| A repo needs enforceable size/debt control | `kiss-debt-guard` |

## Retrofit — applying KISS to a codebase that was NOT built with it

Kickoff assumes greenfield: prevent at the wellspring. Most real work is the opposite — an existing
codebase, written without KISS, that you are now cleaning. **The hazards invert.**

In greenfield you are stopping bad code from being written. In a retrofit **the bad code is already load-
bearing**, and your clean-up is the most dangerous thing in the repo.

**Retrofit order (do not reorder — later steps are riskier):**

1. **Measure, don't touch.** File sizes, concept duplication (grep by store), dead code, doc drift. Produce
   the numbers before producing a diff. A guard that only inspects *changed* files says nothing about the
   codebase — run it over the whole tree.
2. **Guards before cleanup.** Install the ratchets *first* (`kiss-debt-guard`, `kiss-coherence`), with the
   existing violations recorded as tracked debt. This stops the bleeding while you work, and every
   subsequent step is verified as it lands.
3. **Consolidate concepts** (`kiss-coherence`) — this finds *live product bugs*, not just ugly code. It is
   the highest-value pass in a retrofit and the one no size audit can do for you.
4. **Sweep dead DATA, not just dead code** (`kiss-coherence` → *the reverse pass*). Run each store
   **backwards**: does every record still have an owner in code? Dead-code sweeps prove the *code* is gone
   and say **nothing** about the avatars, config rows, vaults and build artifacts it left behind — which a
   wildcard packaging glob will cheerfully **ship**. Check the *deployed* tree, not just the repo.
5. **Split by byte-motion** — pure moves, no logic changes. Cheap and safe.
6. **Refactor logic last.** Highest risk, lowest urgency. Often correctly deferred forever.

**The retrofit-specific traps — all three cost real regressions:**

- **Deliberate behaviour that looks like a bug.** Old code is full of odd-looking constructs that are
  load-bearing. A permissive default (`unknown ⇒ enabled`) may be the only reason new records appear at
  all. **Investigate before "correcting", and when you conclude it's intentional, WRITE THAT AT THE SITE**
  (`kiss-coherence` → *Record the negative finding*) — or you, or the next agent, will re-litigate it and
  eventually "fix" it into a real bug.
- **Conditions that enforce a rule by accident.** See `kiss-blast-radius` → *the silent-deletion trap*.
  Consolidation deletes conditions; some were doing a second, unwritten job. **A green test suite does not
  protect you** — the rule was never tested because it was never intended.
- **Tests prove structure, not behaviour.** In a retrofit the suite was written against the *old* shape. It
  will happily stay green while you change what the product does. Verify at runtime, on the actual surface.

**And the finding worth carrying into every retrofit:** code can be *locally* immaculate — small files,
clean names, one responsibility each — and *globally* incoherent, with one concept answered eight different
ways. Size audits score that codebase as excellent. Only a coherence pass sees it.

## The model underneath

Every unit of code is a **block**: bounded, labeled, self-documenting, reusable, slotted into a
known frame — the way a modular installer or a reusable UI panel is built. The plugin is the frame;
each skill is a block. KISS keeps everything bite-size, human-legible, and easy to transplant —
enforced by discipline, not by template files.
