# Retrofit case study — applying KiSYSTEM to a live, AI-built application

> **This is the honest version.** It records what the discipline found, what it was worth, what it cost —
> including two regressions the cleanup itself caused, and five times the agent doing the work was simply
> wrong. It was written by that agent. Numbers are measured, not estimated.

**Subject:** [Deliberon](https://github.com/Pr1m4lc0d3/deliberon-releases) — a WPF/.NET 8 multi-agent AI desktop
application, ~127,000 lines of C#, being prepared for release.
**Condition:** The codebase was **not** built under KiSYSTEM. Roughly 127k lines already existed, written
across many AI sessions without the discipline. This was a **retrofit**, performed on a live product days
before shipping — the hardest case, and the most common one.
**Author's note:** Written by the agent that did the work, including the parts where it was wrong. Numbers
are measured, not estimated. Where the work caused damage, the damage is recorded.

---

## The verdict, up front

**Four defects were found that would otherwise have shipped to paying customers:**

| Found | Would have shipped as |
|---|---|
| The orchestrator AI could not see agents that existed on disk | An AI that "argues with you," denies your agents exist, and creates **duplicate ghost records** of them |
| **~48 abilities silently dead** (two drifted tool lists) | Documented features that simply do nothing — including the AI's own persona-switch and session-resume |
| **A licence bypass** | Unentitled users receiving paid features **for free** |
| A whole feature **100% blank in production** | A headline feature that displays nothing, with no error, for every user |

**None of them threw an exception. None of them failed a test.** 711 tests passed the entire time.
They were invisible to size audits, dead-code sweeps, doc-drift reconciliation and test-coverage analysis.
**Every single one of them was found by asking one question: "how many places answer this, and do they
agree?"**

**Yes — KISS can be retrofitted onto a codebase that was never built with it, and the payoff is not
cosmetic. It is shipped bugs prevented.** The size work made the code *readable*. The coherence work made
the product *correct*.

## The headline finding

> **Code can be locally immaculate — small files, clean names, one responsibility each — and globally
> incoherent, with a single concept answered eight different ways.**
>
> **A size audit scores that codebase as excellent. Only a coherence pass sees it.**

That sentence is the whole testimony. Everything below is evidence for it.

---

## 1. What the size discipline achieved (and where it stopped)

The anti-bloat pass was real and it worked. Measured against the previous release:

| | Previous release | After the retrofit |
|---|---|---|
| `.cs` files ≥ **1,200 lines** | **11** | **0** |
| `.cs` files ≥ 800 lines | 33 | **1** |
| `.cs` files ≥ 500 lines | 61 | **5** |
| average lines / `.cs` file | 210 | **169** |
| test methods | 313 | **535** |
| `.cs` lines total | 120,965 | 126,763 |

Eleven god-files to zero. That is not cosmetic — those files were where nobody could see what was happening.

**Note the last row honestly: the codebase grew ~5%.** Dead code was deleted (~1,600 lines in one sweep),
but features shipped during the same period, and splitting 575 files into 747 adds real boilerplate
(usings + namespace per new file). *Retrofitting KISS does not necessarily shrink a codebase. It changes
its shape.* Anyone promising shrinkage is selling something.

**And here is the ceiling:** after all of that, the product was still broken in ways the size audit was
structurally incapable of detecting. Every file was clean. The system was not.

---

## 2. What coherence found — and every one of these was a live product bug

The coherence pass asks one question: **for each concept the system reasons about, how many places
independently derive it, and do they agree?**

The method is one trick: **grep by STORE, not by concept name.** Searching for `roster` finds nothing.
Searching for the *persistence* — `*.bgplugin`, `roster-state.json`, `specialists.json` — finds every
answerer.

### 2.1 "Which agents are installed?" — **eight** answers

Eight independent implementations, reading four different stores. They drifted. Consequences in the
shipping product:

- The orchestrator AI **could not see agents that plainly existed on disk**, and proposed **recruiting
  duplicates** of them — which is precisely the ghost-record corruption the delete logic exists to prevent.
- The UI and the AI disagreed about which agents existed.

Not one of the eight was named for the concept (`LoadSpecialists`, `Enumerate`, `ExecuteSpecialistList`,
`BuildRosterExpandedContent`…). **A symbol-based "does a twin exist?" check passes cleanly while you write
the eighth duplicate.** That is why coherence needs its own index and its own guard.

**Why eight?** Not stupidity. One was *structurally forced* — a separate process that cannot reference the
main assembly, so it re-implemented the scan. Three were asking genuinely *different* questions and only
looked like duplicates. The rest were: *needed the list, wrote six lines, moved on.* **With no canonical
accessor to call and no index saying one should exist, a six-line scan gets rewritten by everyone who needs
it.** A human does this too. An AI does it faster and more times.

### 2.2 "Which tools may the orchestrator use?" — **two** hand-maintained copies, drifted

A tool only reaches the AI if it is in **both** the server list (what gets *served*) and the client list
(what gets *shown*). Two separate lists. Nobody kept them in sync.

**~48 abilities silently did not work:**
- **19** served but never shown — including a persona-switch tool **the AI's own instructions told it to
  call**.
- **24** shown but never served — including a session-resume tool **documented in its own operating
  pipeline**.
- **5** were ghosts — names of tools that had never existed.

The worst case: a duty pipeline *declared* a required tool, and an entire pinning mechanism existed to
protect that tool from being trimmed — **but the server never served it, so the pin protected nothing.**
The model, denied a capability its instructions promised, did the only thing it could: **it improvised.**

> **A model denied its tools does not error. It negotiates with you.** That is why this was invisible for
> months.

The codebase's own comment had already warned *"do not reintroduce a copy"* — about a **different** list.
The lesson was learned once and not generalised.

### 2.3 "Is this agent enabled?" — **three** stores, and the rule hand-inlined at five sites

The rule for *which store owns which agent* was copy-pasted as a ternary keyed on a **class type** — a proxy
that had silently stopped being true.

### 2.4 A licence bypass

An entitlement gate was being evaluated against a **licence-filtered** list, so an unentitled item looked
like "not one of ours," fell through to a permissive fallback, and was **granted**. Revenue leak, found and
closed before money was flowing.

### 2.5 A feature that was 100% dead in production

The community gallery displayed **nothing**, while the server was healthy and returning 33 records. Cause:
**one** record contained an empty-string date. The client deserialised the payload *as a list, in one call*,
so a single malformed row threw — and a **bare `catch`** returned an empty array. **One bad record silently
erased the entire feature**, and swallowed the reason.

> **Same disease as everything else here: nothing threw. Everything lied.**

---

## 3. The pattern across every single finding

| Bug | Exception thrown? | What the user saw |
|---|---|---|
| Orchestrator can't see agents | no | "the AI is being difficult" |
| 48 broken tools | no | "the AI improvises" |
| Licence bypass | no | unlicensed features working |
| Gallery empty | no | "the gallery is broken?" |
| Dead-looking UI control | no | "this button does nothing" |

**Zero exceptions. Zero test failures. Zero crashes.**

This is the defining property of failures in AI-integrated systems, and it deserves its own rule:

> **Code consumers fail loudly — a stale contract throws.**
> **Model consumers fail *plausibly*.** An LLM reading a stale surface does not crash. It reasons
> impeccably from bad data and proposes something reasonable-sounding.
>
> So the bug presents as *"the agent is being difficult"* rather than a stack trace — and it is brutal to
> chase, because fixing one surface just makes the model consult a different, still-stale one and contradict
> you.

**Wherever a model reads system state through multiple surfaces — system prompt, tool output, injected
context, RAG — those surfaces must be *proven* consistent.** The model silently picks a winner.

---

## 4. What the retrofit cost

This is the section most case studies omit.

**Two regressions were introduced by the cleanup itself.** Both by the same mechanism:

> A consolidation refactor **deletes conditions**. Some of those conditions were doing a **second job nobody
> wrote down** — enforcing a rule *by accident*.

- An "ugly" type-check was *incidentally* hiding licence-locked items. Replaced with a correct, cleaner,
  identity-based accessor → **the licence gate silently vanished** and unlicensed agents joined a paid
  session.
- The same line elsewhere was *incidentally* hiding the orchestrator from the agent roster. Same fix, same
  evaporation → it appeared in the user's agent list, un-removable.

**Neither was caught by 700+ passing tests** — because the rule they destroyed was never tested. It was never
even *intended*.

And a **fail-open default** (`unknown ⇒ enabled`) converted both accidents from *denials* into *grants*.
That default turned out to be **load-bearing** — it is the only reason a newly created record appears at all
— so "fixing" it would have broken creation. It was correctly left alone and **marked as deliberate**.

**The agent (me) also mis-diagnosed five things**, each time building a confident narrative on a code comment
or a plausible inference, and each time corrected by the human looking at the actual screen. The pattern was
consistent and worth naming:

> **When I measured, I was reliable. When I narrated, I overreached.**
>
> Every hard number held up. Every *story* told around the numbers was inflated.

---

## 5. The rules that came out of it

All four are now enforced in the method, not left to memory:

1. **One question, one answer.** For every concept, exactly one canonical accessor. Find the duplicates by
   **grepping the store, not the name**. Guard it in pre-commit so a new answerer fails the build.
2. **Consolidation is not free.** Before replacing a condition, ask what it is **incidentally preventing** —
   not what it says, but what it *stops from happening*. **A green test suite is not evidence here.**
3. **Record the negative finding.** When you investigate something suspicious and conclude *"actually, this
   is correct"* — **write that at the site**, with the wrong conclusion you almost drew. Otherwise the next
   person repeats the entire investigation and eventually "fixes" it into a bug. *A "no bug here" finding
   that isn't written down is not a finding.*
4. **Model consumers fail plausibly.** Prove every surface an AI reads is consistent.

---

## 6. Verdict

**Was the retrofit worth doing mid-project, days before release?** Unambiguously yes — but **not** for the
reason we expected.

The size work was valuable and visible: 11 god-files to zero. But **it found no bugs.** It made the code
*readable*.

**The coherence pass found the actual product defects** — an AI that couldn't see its own agents, 48 dead
abilities, a licence bypass, a feature that was 100% blank in production. Every one of them was invisible to
size, dead-code, doc-drift, and test-coverage audits. Every one of them would have shipped.

And the uncomfortable conclusion, which is the most interesting thing here:

> **The incoherence was likely an artefact of AI authorship.**
>
> Many sessions, each locally reasonable, none holding the whole system in view. A single human architect
> carrying the design in their head would probably not have written eight scanners — **because they would
> remember writing the first one.**
>
> AI writes code that is *locally cleaner* than most human code — smaller files, better comments, enforced
> guards — and *globally more incoherent*.

**That is a new failure mode, it is specific to how AI builds software, and size-based clean-code discipline
cannot see it.** Coherence is the dimension that was missing. It exists now because this project needed it.

---

## 7. What to expect when you retrofit KISS onto an existing codebase

If you are about to do this to a real, messy, already-shipping product, here is what actually happens —
in the order it happens.

**You will find that the size problem is the easy half.** Splitting god-files is mechanical, safe, and
satisfying. It will also find you **zero bugs**. Do it, but do not mistake it for the win.

**You will find concept duplication you did not believe was there.** Not two copies — *many*. Expect the
duplicates to have **completely different names**, to live in different assemblies, and to have each been a
locally sensible decision at the time. Expect at least one to have been **structurally forced** (a process
or assembly boundary that made calling the original impossible), and expect a few that only *look* like
duplicates but are genuinely answering a different question — **collapsing those is its own bug.**

**You will find that the duplicates have drifted, and that the drift is already costing you.** This is the
part people do not anticipate. Duplication is not merely ugly — **it is a live defect that is already in
production.** In this project every fragmented concept had already produced a user-facing failure.

**You will find that the failures are silent.** No stack traces. No red tests. The system runs. It simply
does the wrong thing, quietly. If AI reads any of this state, it will not crash — it will *improvise*,
and the bug will present as "the AI is being weird."

**Your cleanup will break things.** Accept this in advance and plan for it. Old code contains conditions
that enforce rules *by accident*; a correct, cleaner replacement deletes those rules silently, and **your
test suite will not tell you**, because nobody ever tested a rule nobody intended. Budget for regressions,
verify at runtime on the real surface, and treat every permissive default (`unknown ⇒ allowed`) as a
loaded weapon.

**You will keep "discovering" the same suspicious code.** Old codebases are full of constructs that look
wrong and are load-bearing. If you investigate one, conclude it is deliberate, and move on **without
writing that down at the site**, you *will* re-litigate it — and eventually "fix" it into a real bug.
Ask us how we know.

**Sequence that actually works:**

1. **Measure the whole tree first.** Numbers before diffs.
2. **Install the guards before the cleanup** — with existing violations recorded as tracked debt. This
   stops the bleeding while you work.
3. **Consolidate concepts.** ← *this is where the bugs are*
4. **Split files by pure byte-motion.** Safe, cheap.
5. **Refactor logic last, or never.** Highest risk, lowest urgency.

**What it will not do:** it will not shrink your codebase. Dead code comes out, but features go in and
splitting adds boilerplate. **Retrofitting KISS changes a codebase's shape, not its size.**

