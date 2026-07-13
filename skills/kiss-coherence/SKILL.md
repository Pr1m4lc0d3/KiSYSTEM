---
name: kiss-coherence
description: Use when auditing or changing a system where the same concept is derived in more than one place - enforces one canonical accessor per concept ("one question, one answer"), catching cross-cutting duplication that file-size and modularity audits structurally cannot see.
---

# KISS — Coherence

**One question, one answer.** For every core concept the system reasons about, exactly **one** canonical
accessor derives it. Every other site delegates.

This is the dimension that `kiss-modularity` cannot cover, and the two are **orthogonal**:

| | asks | fails when |
|---|---|---|
| **modularity** | *Is each unit simple?* | one unit does too much (or too little) |
| **coherence** | *Does the system have ONE answer?* | N units each derive the same concept differently |

A codebase can score **perfectly** on size, cohesion, dead code and test coverage while N small, clean,
single-responsibility functions independently derive the **same concept** from **different stores** and
silently drift apart. Simplicity of the parts is **not** coherence of the whole.

> **Splitting can HIDE this.** If all the duplicated logic sits in one ugly god-object, the contradictory
> reads are adjacent and obvious. Dispersing the concept into tidy separate files removes the proximity
> that would have exposed the drift. Aggressive modularization makes each answerer *easier to read* and
> the *duplication harder to see*.

## The two failure modes

| Failure | Looks like | Fix |
|---|---|---|
| **Divergent duplication** | N implementations of one concept, reading different stores, drifting | extract ONE canonical accessor; delegate the rest |
| **Premature unification** | forcing genuinely different questions through one accessor because they look alike | keep them separate; document why |

Both are real. "All installed plugins (for load/unload)" and "council-eligible agents" *look* like the
same question and are not — collapsing them is its own bug. Coherence means one answer **per question**,
not one accessor for everything vaguely similar.

## The audit

**1. Name the core nouns.** 5–15 concepts the system reasons about — the things it answers questions
about. Phrase each as the user's question: *"which agents are installed?"*, *"is this enabled?"*,
*"what's the price?"*

**2. Grep by STORE, not by concept name.** ← *the whole trick.*
Searching for `roster` finds nothing useful. Searching for the **persistence** finds every answerer:
file globs (`*.bgplugin`), file names (`roster-state.json`, `specialists.json`), tables, registries,
singletons, env vars. **Any function that reads a primary store directly is a candidate answerer.**

**3. Count the answerers and the stores.**
- More than one answerer → duplication risk.
- More than one **store** backing one concept → it **will** drift. That alone is the red flag.

**4. Extract the canonical accessor.** Make it **pure over its store** (no app/UI/global state) if it must
cross an assembly, process, or language boundary — cross-boundary splits are a *primary cause* of
duplication, because the far side "can't reach" the original and re-implements it.

**5. Delegate every consumer.** Delete the duplicates. Consumers should shrink.

**6. Ratchet it.** Register the concept in a guard (pre-commit / test) keyed on the **store pattern**, with
an allow-list of permitted direct readers, each carrying a reason:
`CANONICAL` · `DIFFERENT CONCEPT (why)` · `DEBT (migrate to X)`.
A **new** direct reader fails the build. Anything you can't migrate today is recorded as explicit debt —
visible and tracked, not silently forgotten. Add a second check that fails if an allow-list entry goes
**stale**, so the debt list can't rot into a lie.

**7. Publish a concept index.** One entry per concept: question · canonical accessor · store · consumers ·
debt. This is a deliverable *alongside* the file map — the map says what's in each unit; the index says
which unit is the sole answerer.

## The reverse pass — orphaned data (do this too; it is half the audit)

The audit above runs **code → store**: *for this question, how many places in code answer it?* Run it
backwards as well:

> **store → code: does every record in the store still have an OWNER in the code?**

Same concept index, same stores, opposite direction — and it finds a completely different class of bug.
The forward pass finds **contradiction**. The reverse pass finds **residue**: entities deleted from code
whose data was left behind, still sitting in config, still shipping in the package, still being *read*.

For each concept in the index, take its **store** and enumerate the ids in it. Any id that no code path
can still own is an orphan. Then check the three places orphans hide that a source-tree grep will *not*
show you:

- **the deployed/output tree** (`bin/`, `dist/`, the install dir) — a non-clean build never deletes what
  source deleted, so the corpse is still in the artifact even when the repo is spotless
- **wildcard packaging globs** (`Content Include="Assets\**\*"`) — these **ship** anything left in the tree
- **config rows keyed by id** — a stale `"retired_thing": true` in an enabled-state store makes the app
  *behave* as though a deleted entity is still switched on

**Why every other guard misses it:** a dead-code sweep proves the *code* is gone. Size audits weigh files
that exist. Coverage measures executed lines. Not one of them looks at the **store**, so a 4 MB corpse
rides into production with a green board. See `kiss-blast-radius` → *the residue trap* for the deletion-side
discipline that prevents orphans in the first place.

> **A concept index that records the store is what makes this pass possible.** That is a second reason to
> keep it — not just "who answers?" but "who is still *in* there?"

## AI-native rule (do not skip)

> **When a MODEL reads system state, enumerate every surface it can read and prove they agree.**

Code consumers fail **loudly** — a stale schema throws. **Model consumers fail *plausibly*.** An LLM
reading a stale surface does not crash: it reasons impeccably from bad data and proposes something
reasonable-sounding. So the bug presents as *"the agent is being difficult"* instead of a stack trace,
and it is brutal to chase — fix one surface and the model simply consults a different, still-stale one
and contradicts you.

Enumerate every surface the model reads — **system prompt, tool outputs, injected context, RAG** — and
assert one agent set / one answer across all of them. Also check the model actually *has* the tool: if
tools are retrieval-trimmed to a topK, anything the model needs on *every* turn must be **pinned**, or it
vanishes on off-topic queries and the model will confidently tell you the capability doesn't exist.

## Consolidation is not free (learn this before you delete a line)

Unifying duplicated logic **deletes conditions**. Some of those conditions were doing a second job nobody
wrote down — they were **incidentally enforcing** a rule. Delete them and the rule silently vanishes.

Two real cases, one afternoon, same mechanism:

| The "ugly" code | What it *said* | What it was **also** doing |
|---|---|---|
| `ctrl is SpecialistTemplateBase ? Roster.IsEnabled(id) : Settings.IsEnabled(id)` | pick the right store | **hiding licence-locked agents** (Roster didn't know them → `false`) |
| the same line, elsewhere | pick the right store | **hiding the orchestrator** from the agent roster (same accident) |

Both were replaced with a clean identity-based accessor. Both rules evaporated. Unlicensed agents joined a
council; the orchestrator appeared in the agent list, un-removable. **Neither was caught by 700+ tests.**

> **Before you replace a condition, ask: what is this *incidentally* preventing?**
> Not what it says — what it **stops from happening**. Then re-implement that rule **explicitly**, or you have
> just deleted it.

**Fail-open defaults turn every such accident into a grant.** A lookup that answers `true` for an id it has
never seen (`unknown ⇒ allowed`) means *any* newly-broken routing GRANTS access rather than denying it. Find
these first — they convert your refactor's mistakes into security and licensing holes. If a permissive
default is load-bearing (e.g. new records must default to "on"), **do not flip it** — fix the routing that
reached it, and mark the default as deliberate (below).

## Record the negative finding (mandatory)

Investigations that end in *"actually, this is correct"* **must leave a marker at the site.** Otherwise the
next person — human or AI — repeats the entire investigation, reaches the same suspicion, and "fixes" it into
a bug.

This is Chesterton's Fence with the reasoning **nailed to the fence**.

**When you conclude a suspicious construct is intentional, write at the site:**

1. **The behaviour** — plainly ("an unknown id returns `true`").
2. **DELIBERATE — DO NOT 'FIX'** — say it loudly enough to stop a skim-reader.
3. **Why it is load-bearing** — what breaks if you "correct" it. Be concrete.
4. **The wrong conclusion you almost drew** — name it, so the next investigator recognises their own thought
   and stops.
5. **The safe path**, if it ever *should* change — in order, with what must land first.

A "no bug here" finding that isn't written down **is not a finding**. It is work you will pay for again — and
next time it may be paid in a regression rather than in time.

> Symptom you are missing these: you keep "discovering" the same suspicious code, or you find yourself saying
> *"I was wrong, it's intentional"* more than once about anything. Each of those is a marker you failed to leave.

## Debugging signal

When a consumer insists something "doesn't exist" that you can see on disk:

1. **Do not fix the first surface you find.** Ask: *"how many places answer this question, and do they
   agree?"* — before touching anything.
2. **Trace the surface the consumer actually reads**, not the one you assume. Take its words literally:
   *"the roster in my system prompt"* → the prompt builder. *"the roster shows 15 built-ins"* → the
   `roster_list` tool. Each phrase names a **different** surface.
3. Fixing surfaces one at a time as the consumer exposes them is the failure loop. Unify first.

## Red flags

- Two functions in different assemblies/processes doing "the same scan" — the far one re-implemented it.
- A concept whose truth lives in 2+ persistent stores.
- A comment saying *"mirrors X"* / *"keep in sync with Y"* — that is an unenforced invariant. Enforce it
  or extract it.
- A consumer that "should" see something and doesn't.
- Any hand-maintained duplicate. (`SpecialistToolPolicy`'s own header says two copies drifted and
  tool-starved every agent — the same disease, already diagnosed once and not generalized.)

## Common mistakes

- **Auditing size instead of coherence.** They're orthogonal; passing one says nothing about the other.
- **Comparing outputs instead of removing the duplication.** A parity test over two hand-written
  implementations pins agreement *today* without preventing divergence *tomorrow*. Extract, then pin.
- **Unifying concepts that merely look alike** (premature unification).
- **Guarding without an allow-list** — real different-concept readers exist; force them to justify
  themselves rather than banning the pattern outright.
