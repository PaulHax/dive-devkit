# Conventions & gates

## Check every new filename/format convention against what DIVE already emits

`.meta.txt` collided conceptually with the exported `meta.json` — noticed only in review:

> "Can you brainstorm some alternatives to this dot meta dot t x t? … confusing because we have this meta dot JSON output when we export"

For any data-format contract, check VIAME CSV / KWIVER precedent **first**. For style, survey the
tree rather than inventing:

> "I think we should just follow the naming style that you find in the way Dive deals with files. Does Dive in general ingest underscore or dashes?"
> "lets prefer kebab case in docs )but still support snake)"

Prefer derived defaults over config fields — "for abolsut etimestamps, we could jsut take the first
row timestamp as the start"; "frame wins".

## State what real invariant each inherited restriction proxies

For every pre-existing DIVE restriction or special case the feature touches, the plan either:

- relaxes the proxy and enforces the **real** invariant at the content-aware layer, or
- records the load-bearing justification for keeping it, and where docs should rank it (hard
  requirement vs fallback convention).

The legacy single-CSV rule turned out to be a proxy from before telemetry CSVs existed — one
annotation source, not one CSV.

> "we should alowo more than one CSV. why whould they not alow that?"
> "Should we remove this special case naming?"
> "So why is order important again... Why not just use one, the first found one or something?"

## Ground scope in real data, not imagination

> "i don't have an exampel to support it, so maybe no"

The 10MB cap was wrong because real AUV nav logs run 32–50 MB. New format leniency without a
motivating sample gets cut and a rejection test written instead. Reviewer test bundles live under
`test-datasets/` with manifest provenance, never in the source tree.

## Know what the default gate does NOT cover

`dive-devkit/tools/test.sh <wt>` runs server unit/lint plus client unit/lint/builds.

**Not covered — budget manual live-stack e2e for these:**

- `pytest -m integration` (needs `GIRDER_API_KEY` and a live Girder)
- girder_worker task execution: `extract_zip`, `convert_video`, `convert_images`
- real browser upload flows
- Electron IPC

Track "gates green, no live e2e" as a separate open item. Green gates were repeatedly treated as
done, and that gap is exactly where the desktop `Track.fromJSON` crash and the broken devkit seeder
lived.

Two more gate details that cost time:

- Pin conformance runs to the **deployed** runtime — the corpus was pinned to local py3.10 while
  `girder.Dockerfile` runs 3.11.
- Capture a baseline lint/test run first, then require zero NEW errors per work package, and halt on
  failure rather than accumulating.

## Manual-test steps enumerate every enablement condition

A disabled submit button strands the tester with no visible reason, and the blocker is usually a
pre-existing field the feature never touched — here, "Dataset name" sitting *below* the optional
metadata picker:

> "i think i did all that but begin import is still grayed out"

For any dialog with a gated action, list all its conditions, not just the new feature's.

## Counts in docs and PR messages are derived — recompute them at review time

Fixture counts, test counts, and directory tallies get copied between documents and go stale within
minutes of a fix. Re-derive from the tree or the gate output rather than trusting the previous
sentence.

> "i think we need to simplify our manual tests ... and proalby the pr mssages to go with ti."

## Planning docs outside the repo get no backup refs

Stacked-PR discipline protects `backup/*` refs inside the repo; a workspace-local file such as
`plans/…/stacked-pr-messages.md` is the only copy on disk and survived six history rewrites only by
hand. Before a destructive rewrite, identify which touched paths fall outside any git root and
snapshot them separately.

## Convention changes ripple into the devkit

Any convention or API change must update `dive-devkit/seed/` fixtures and self-checks, plus
`test-datasets/manifest.json`, in the same pass — then re-verify the seeder end to end. A sidecar
rename plus an endpoint removal broke it and the user had to catch it.

> "fix devkit"

---

Related: [ingestion.md](ingestion.md),
[dive-code-review tests & fixtures](../../dive-code-review/references/tests-fixtures.md).
