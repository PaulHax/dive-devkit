---
name: dive-code-review
description: Catalog of the defects, drifts, and taste violations that real DIVE review cycles caught, organized by topic. Use when reviewing a DIVE branch, PR, or diff, or when writing DIVE code and you want to know what tends to go wrong in the area you are touching.
disable-model-invocation: true
---

# DIVE code review — what goes wrong, by topic

A catalog of issues that actually surfaced on DIVE: one one-pass implementation followed by 28
review-driven cleanup commits on PR Kitware/dive#1741; the four-PR frame-metadata stack
Kitware/dive#1806–#1809, where upstream pushed 15 corrective commits onto the branches and one
regression escaped to a follow-up PR; plus upstream commits on adjacent features (calibration,
SealTK import, CLI open, annotation sets). Every entry carries the commit or verbatim review quote it
came from, so you can check whether it still applies.

**This file is an index.** Read the topic files that match what the diff touches — each is a
self-contained checklist with the real failure behind it. Nothing here prescribes how to run the
review, how to rank findings, or what to write up; that is yours to decide.

## Start here

[failure-modes.md](references/failure-modes.md) — the things one-pass agent implementations got wrong
most often, with a grep or read check for each, ending with the one the gate structurally cannot
catch: **the DIVE client has no typecheck step**. If you only read one file, read that one.

## Topics

| Topic | Read when the diff touches | File |
|---|---|---|
| Failure modes | anything — the frequency-ranked hunt list | [failure-modes.md](references/failure-modes.md) |
| Naming & terminology | new names, a rename, file-format conventions | [naming.md](references/naming.md) |
| Comments & docs | added comments, `docs/`, mkdocs nav | [comments-docs.md](references/comments-docs.md) |
| Abstraction & dead code | new exports, helpers, limits, compat shims | [abstraction.md](references/abstraction.md) |
| Parsers & data path | parsing, caching, normalization, precedence | [data-path.md](references/data-path.md) |
| Desktop/web parity | apispec.ts, anything with a server and desktop story | [parity.md](references/parity.md) |
| Correctness edges | async, error paths, busy state, lifecycle | [correctness.md](references/correctness.md) |
| Vue & Vuetify | client components, panels, composables | [vue-ui.md](references/vue-ui.md) |
| Server & Girder | `server/`, `web-girder/api`, upload classification | [server-girder.md](references/server-girder.md) |
| Tests & fixtures | specs, fixture corpora, mocks | [tests-fixtures.md](references/tests-fixtures.md) |
| Diff hygiene | commit shape, formatting, scope | [diff-hygiene.md](references/diff-hygiene.md) |

## Two rules that override the rest

Both cost real time when they were violated in the opposite direction, so they are stated once here
rather than buried in a topic file:

- **Convention-match never closes an error-path verdict.** New code that matches an established
  idiom is not thereby clean — the idiom may carry the same latent bug. See
  [correctness.md](references/correctness.md).
- **Looks-dead may be load-bearing.** Before calling code dead or duplication drift, enumerate every
  caller, including Python callers of TS-adjacent surfaces. See
  [abstraction.md](references/abstraction.md).

## Reading the evidence

Bare shas (`d6622c04`) resolve in a `frame-metadata-sidecars` worktree; `git show <sha>`. Shas
written `Kitware/dive@<sha>` exist only on GitHub — `gh api repos/Kitware/dive/commits/<sha>`.
Everything was captured at branch commit `12be12a4` (2026-07-16); `file:line` references drift, so
re-locate with `git grep -n <symbol>` before trusting one. Quotes are verbatim from review
transcripts, typos included — they are quoted rather than paraphrased so you can judge tone and
intent yourself.

Two habits that make the rest usable: get the feature's canonical name from the **current tree's UI
label**, not from plans or memory or the branch name (names changed mid-branch twice), and confirm
the worktree under review is the canonical one for the feature — a superseded sibling carries
divergent conventions that poison every terminology check.
