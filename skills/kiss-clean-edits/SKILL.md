---
name: kiss-clean-edits
description: "Use when adding or changing code in an existing file — a method, handler, case branch, property, or any member. Enforces three reflexes at the moment of the edit: state the host file's size before adding to it (extract-on-touch), make only changes that trace to the request (surgical edits), and write nothing speculative (YAGNI)."
---

# KISS — Clean Edits

Three reflexes that fire at the moment of an edit. They prevent the two commonest forms of
breakage: bloat-by-accretion and change-by-overreach.

## 1. Extract on touch — make file size visible *before* you add

Bloat accretes one reasonable append at a time, because at the moment you add a method the file's
existing size is off-screen. Put it on-screen:

**Before adding any member to an existing file, state its current line count.**

| File is... | Do |
|---|---|
| under the review tier | Append normally |
| past the **extract** tier | Extract first — new code goes in a new file/section, not appended |
| past the **hard stop** | New code goes in a new file; flag the host for splitting |

A *positive required step*, not a prohibition: you're not banned from large files, you're required
to look before you grow one. (Tiers: `kiss-modularity`. Where things live: `kiss-map`.)

### Dispatch chains are not an exemption

"It's one long `if`/`switch`, so a new branch has to live in the method" is a common false exit. The
**branch** stays in the method — its **body** does not. Extract the body into a new file/section,
leave a one-line call:

```
if (action == "summarize") return SummarizeRound(args);   // stays inline
// SummarizeRound lives in a new section/file — 40 lines out of the monolith
```

"The branch must be inline" is not "the logic must be inline." Claiming "no clean seam" when a
body-extraction is available does not satisfy this reflex.

## 2. Surgical edits — every changed line traces to the request

- Don't "improve" adjacent code, comments, or formatting you weren't asked to touch.
- Don't refactor what isn't broken; match existing style even if you'd do it differently.
- Remove only the imports/variables your *own* change orphaned; mention pre-existing dead code,
  don't delete it.
- The test: every changed line traces directly to the request. If you can't trace it, drop it.
  (This is the inner loop of `kiss-blast-radius`.)

## 3. YAGNI — write nothing speculative

- No features beyond what was asked; no abstraction for single-use code; no configurability nobody
  requested; no error handling for impossible states.
- If 200 lines could be 50, write the 50.
- Ask: "Would a senior engineer call this overcomplicated?" If yes, simplify before moving on.

## Why this form

The extract-on-touch reflex is built test-first: a baseline showed fresh agents grow an over-budget
file with **zero** awareness of its size — the failure is *omission*, not defiance. So the fix is a
required *measurement*, not a ban: a prohibition gets negotiated away ("my change is small and
correct"); a measurement can't ("did I state the line count before editing, or not?").
