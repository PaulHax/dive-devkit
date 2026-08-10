# Plan omissions and what they cost

Ground truth: **implementers execute wrong instructions faithfully and will not question a stated
rationale.** Every item below is something a plan left open or got wrong, and the cleanup commits it
produced. The cost column is the point — these are not hypotheticals.

## Omissions, ranked by what they cost

| What the plan didn't say | What it cost |
|---|---|
| **Contract sign-off + blast radius** | The highest-risk contract (reserved filenames `*.meta.csv`) was replaced 2 days post-implementation: `9445de0e`, 22 files, +289/−207 — both predicates, all server tests, docs, the shared fixture — plus an escape-hatch follow-up branch. Name what a contract change touches and get sign-off *before* implementation. |
| **Glossary + verbatim UI strings** | Terminology purge `d8873447` (11 files) plus a doc re-purge `a56ae00c`; the desktop rename-hint was rewritten twice. Decide every error message, rename hint, panel label, and tooltip up front, verified against the current tree — "also, we renamed the fraem info panel to 'dataset info'". |
| **UI spec, or an explicit "do not polish" marker** | A ~6-line UI work item produced 6 cleanup commits: tooltip `420ad398`, collapsible sections `d60a923d`/`50e60cd0`, and a full decomposition `964b6aa6` (12 files, +958/−880; a 494-line SFC split into a component family). Either spec the panel or write "design-iteration expected — do not polish". |
| **Fixture-placement rule** | The workorder's "43 fixtures" corpus was inlined by `d7f7074a` (49 files, +255/−355): 46 testdata files deleted, leaving only the cross-language `source_names.expected.json`. Decide corpus-as-referee vs corpus-as-requirement; file-based fixtures only when >1 language consumes them. |
| **Per-ported-behavior justification** | Comment-header promotion survived only because the plan listed it and fixtures existed FOR it; deleted in `fa302c5c`. A fixture inherited from a prototype is not a requirement — re-justify each with "what real-world input motivates this?" |
| **Output rules (no plan vocabulary in code)** | "W-12 memory posture", "FIX 3", port-source references stripped across `1c1dbad7`, `1d9b6686`, `357bec9e`, `5345de87`. |
| **Naming-scope rule** | A feature-scoped name colonized unrelated files; `1d9b6686` restored the `'singleCam'` literals. Never introduce a feature-scoped name for a pre-existing app-wide literal. |
| **Perf-claim gate** | "keeps raw multi-MB text off the IPC wire" was never measured; `dab55292` unified the method and abandoned the optimization. Unmeasured perf rationales are rebuttable — symmetry wins unless proven otherwise. |
| **Docs deliverable spec** | A 256-line architecture doc landed in `docs/` and was deleted by `c6c4de9c` (+83/−410) → one 64-line user page, then pulled from nav via `not_in_nav` (`a56ae00c`). One short user page in `docs/`; architecture narrative stays in `plans/`; no mkdocs nav restructuring in a feature PR. |
| **Churn ground rule** | Import reflow `5ee46a0d`; doc rewording `2cd3c7ff`; lint autofixes separated into `49e2064a` (14 files). |
| **Write-side + failure-state acceptance** | Multicam smoke tests only covered directly-created datasets → `563bc317`. An invariant covered classification but not retry → `12be12a4`. |

## Failure modes to design against

| Mode | Evidence |
|---|---|
| Wrong instructions executed faithfully | Four plan instructions were later reverted outright — a feature-scoped key, keep-the-tag-comments, comment-header promotion, file-based corpus placement. All were implemented exactly as written. |
| Under-specified UI shipped verbatim | 6-line item → 6 cleanup commits. |
| Perf rationale unquestioned | The IPC claim above. |
| Read-spec without write-coverage | Clone-creation path untouched → `563bc317`. |
| Happy-path-only dialogs | `12be12a4` — busy flags reset only on success. |
| Stale terminology from plan or memory | "Telemetry"; "Frame Info panel" vs the renamed "Dataset Info". Verify component names against the current tree, not memory. |
| Prototype inertia via fixtures | "Keep whatever passes the corpus" preserved dead behavior, because fixtures existed for it (`fa302c5c`). |
| Wrong-worktree drift | ~1hr lost working in a superseded worktree whose conventions had diverged — "we should fix frame-metadata-sidecars thats the branch we should be working with. the readtime branch is out of date". Plus Electron singleton locks blocking launch across worktrees. |
| Silent delivery-shape drift | A planned prerequisite PR collapsed into the feature PR unannounced. |
| Invented conventions / speculative mechanisms | "I don't get it, why do we need this classifier?"; "Isn't that just a one-step thing?"; "Why not just use one, the first found one or something?" |

## Where the cleanup lands

Budget accordingly. Cleanup spanned 109 files (+2267/−2704, net −437). The implementation pass
touched 90 files; only **5** escaped cleanup entirely (`constants.ts`, `use/index.ts`,
`ipcService.ts`, `crud.py`, `dive_tasks/utils.py`).

Concentration: shared TS and Vue. The parser lost 154 net lines, one composable was rewritten twice,
the main SFC was decomposed — while **Python landed near-pure rename**.

## Standing rules worth stating explicitly

Because they were each violated at least once when left implicit:

- Comments describe current behavior only. Work-item IDs, fix numbers, port-source names, and
  "what we didn't do" narratives never appear in shipped files.
- Lines not semantically touched stay byte-identical to upstream — no import reflow, no doc
  rewording. Lint autofixes of pre-existing code go in a separate labeled commit.
- Build only the mechanisms the plan lists. A new classifier, multi-step API, or precedence layer
  enters only with a named use case written down. Every new public method names its calling workflow
  — a `replaceX`/`removeX` lifecycle pair went in on plausibility alone and the whole
  post-creation-edit feature (~12 files) was cut once asked: *"why do we need new API?"*, then *"how
  complext is that feature, mabye we hsould remove it?"*
- For every indirection read through, test the code that creates it.
- Enumerate error and interrupted states for every dialog flow touched.
- Simplification passes that cut user-visible functionality list the cuts with concrete examples and
  get sign-off first — "Let's clear with me the functionality that we're cutting first, though. Give
  me some simple examples."
- Name the canonical worktree and any known cross-worktree runtime hazards.

---

Related: [approach-evaluation.md](approach-evaluation.md),
[dive-code-review failure modes](../../dive-code-review/references/failure-modes.md).
