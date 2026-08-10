# Comments & docs

## Comments state WHY, and paraphrase comments get deleted, not shortened

Why = the invariant, the ownership, the consequence of drift. `357bec9e` turned a score-mechanics
comment into a camera rationale. `5345de87` deleted block comments outright. `fa302c5c` deleted ~15
narration comments and kept exactly one: 'Empty header cells usually come from pandas indexes'.

> "comments should be for why not what"
> "Comments should say why they exist, not what they are"
> "telling me what the code is doing, not why"

The upstream idiom looks like `// Local copy (not an alias of the injected ref); '' means default.`
(Kitware/dive@966895a7) — one sentence, states the trap.

## Never reference the development process in shipped code

No workorder IDs, FIX-N tags, review-finding numbers, plan-step refs, invented cross-file tag
taxonomies. This was the single most repeated cleanup: `1d9b6686` (~60 lines: '(FIX 1)', '(FIX 3)',
'(W-12 memory posture)'), `357bec9e` (every 'Contract X-Y' tag plus ~20 test-name parentheticals),
`1c1dbad7` ('readtime deferred finding #8'), `889ba328` ('(D2)').

> "these contract-whatever, these are leftover implementation details... clean out those contract labels"

## Keep only genuinely invisible behavior, one sentence of consequence

Survivors from `d6622c04`: a BOM hidden inside `trim()`; Python `csv.field_size_limit` parity;
'uniq keeps first-occurrence order so folder precedence is preserved'; 'Last-wins on a
normalized-key collision'. Each names something you cannot see by reading the line.

## Docs update in the SAME commit as the contract

Stale examples or quoted hints are blockers, not follow-ups. `dab55292` rewrote the architecture
doc's read-path in-commit; `9445de0e` updated 3 docs alongside the predicate; `d7f7074a` corrected
'conformance corpus is the referee' → 'inline parser specs'. Upstream does the same
(Kitware/dive@3fa8c1d8 for the notes token) and goes further — Kitware/dive@5c5db03, where the
maintainer wrote the missing CLI docs himself, and Kitware/dive@966895a7, which fixed the stale
Node-18+ README line that the PR body had explicitly flagged as 'out of scope'.

## User docs = user-observable behavior only

No parsers, caches, or internals. No 'v1' framing or product rhetoric. No defensive negative-space
prose. Edge cases go in a terse **Limits** list. `c6c4de9c` deleted a 256-line architecture doc from
`docs/` and cut 'Slow-and-loud is acceptable', 'Non-goals in v1', and the rename-hint paragraphs.

> "it's far too detailed. Also, it includes implementation details like V1"

Architecture narrative belongs in `plans/`, outside the DIVE tree.

## One canonical page per fact

Siblings get 2–3 lines plus a link. `c6c4de9c` collapsed 76- and 92-line duplicates into pointers at
`Frame-Metadata.md`. Don't restructure mkdocs nav for one feature page — `a56ae00c` reverted the nav
change and used `not_in_nav: Frame-Metadata.md`.

## Type declarations get one-line doc comments

The return type is the doc. `1c1dbad7` cut 26 lines to 5 on `ResolvedFrameMetadata` /
`FrameMetadataSourcesResponse`. Behavior docs never live in `apispec.ts`.

> "The return type is enough doc. Make this design change now."

## Encode meaning in the type instead of a comment

`5345de87`: labeled tuple elements `[sourceName: string, rawText: string][]` replaced a comment
explaining what the positions meant.

## Docs reference stable UI surfaces, never internal section layout

`2cd3c7ff` reverted 'the Dataset Info section of the Dataset Info panel'. Don't sprinkle feature
mentions across existing pages.

> "avoid the little 'dataset Info section' addition sprkicled around and kee the old verbage to avoid thrashing"

## Mirrored-logic comments name the counterpart and the drift consequence

1–2 lines. `357bec9e` replaced a 7-line block listing truth-table paths and both harnesses with one
sentence: matching names are auto-read as frame metadata instead of imported as annotations. Never
enumerate the enforcement machinery.

## Comment thrash recurs at every restack — audit it mechanically each time

Long-lived stacks lose and re-lose prose. Across one feature: comments dropped and restored, trivial
one-line edits unrelated to the feature, and a docs bullet still describing an `'ambiguous'` state
after the code path was deleted.

> "there are a few comments we dropped form the code that we shoudl proably keep to avoid thrashing"
> "look through all the commits to undo trival 1 line changes that are unrealted to the feature at hand"

After every history rewrite, diff each tip against the true upstream base and flag any hunk whose
only content is a comment or prose edit disconnected from the code around it. This is a recurring
sweep, not a one-time check.

---

Related: [naming.md](naming.md), [parity.md](parity.md) for what mirrored logic is allowed at all.
