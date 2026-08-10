---
name: dive-feature-planning
description: Catalog of the seams, hidden coupling, and plan-level omissions that have sunk DIVE features before, organized by surface. Use when designing or reviewing a DIVE feature that touches ingestion, export, per-frame data, media handling, schema/storage, or both platforms.
disable-model-invocation: false
---

# DIVE feature planning — the seams that bite

The frame-metadata feature was built **three times**. `frame-metadata-v1` and
`frame-metadata-readtime` both died on questions the ingestion and parity surveys below force up
front. `frame-metadata-sidecars` then shipped in one implementation pass (8 commits) — and still
needed 28 cleanup commits, nearly all traceable to something the plan under-specified or got wrong.
Four of its instructions were later outright reverted.

**This file is an index.** Read the surface files that match what the feature touches. Each lists
the seams on that surface, what went wrong at each, and where to look in the tree.

Nothing here prescribes how you plan, what documents to produce, or how to structure them — that is
yours. What is worth keeping is the list of things that turn out to be load-bearing and are easy to
miss.

## Surfaces

| Surface | Read when the feature touches | File |
|---|---|---|
| Ingestion | any new file kind, classification, or discovery mechanism | [ingestion.md](references/ingestion.md) |
| Platform parity | anything with both a server and a desktop story | [parity-seams.md](references/parity-seams.md) |
| Media types, clone, export | media handling, clones, multicam, what round-trips | [media-clone-export.md](references/media-clone-export.md) |
| Conventions & gates | new filenames/formats, or any "is it tested?" question | [conventions-and-gates.md](references/conventions-and-gates.md) |
| Approach evaluation | choosing between designs, or a branch that grew too big | [approach-evaluation.md](references/approach-evaluation.md) |
| Plan omissions | before handing a plan to an implementer | [plan-omissions.md](references/plan-omissions.md) |

## The one that killed two cuts

**Run the whole-ingestion-path survey before choosing any classification, flagging, or discovery
mechanism.** There are ~25 distinct ways data enters DIVE. Only the **filename** travels every path;
anything that persists a decision at import time structurally misses clone, side-door, and
assetstore arrivals.

That survey was run only in readtime round 2. Run first, it would have invalidated cuts 1 and 2
before a line was written. → [ingestion.md](references/ingestion.md)

## Two questions worth asking early

- **Does this need to be stored at all?** "Anything inferable is re-inferable, so there is no
  decision worth storing… a derived copy would only create a second thing that can disagree with the
  source." This single question killed cut 1. → [approach-evaluation.md](references/approach-evaluation.md)
- **What real invariant does this restriction proxy?** For every pre-existing DIVE restriction or
  special case the feature touches, either relax the proxy and enforce the real invariant where
  content is known, or record why it is load-bearing.
  → [conventions-and-gates.md](references/conventions-and-gates.md)

## Reading the evidence

Bare shas resolve in a `frame-metadata-sidecars` worktree. Symbol names are given with `git grep`
locators rather than line numbers, which rot. Quotes are verbatim from planning and review
transcripts, typos included.

Companion skill: [dive-code-review](../dive-code-review/SKILL.md) catalogs what goes wrong in the
code itself, once the plan is being executed.
