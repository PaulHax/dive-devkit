# Tests & fixtures

## Inline typed case tables beat on-disk fixture corpora

An on-disk fixture survives only if a **second-language implementation consumes it**. Everything else
goes inline.

`d7f7074a` deleted 46 conformance fixtures across 49 files, keeping exactly one —
`source_names.expected.json` — because it is 'shared with the server harness so the mirrored
predicate cannot drift'.

> "we intrduce many test fixture files. are they needed? can they be inlined in the tests?"

Supporting rules: generate large or non-printable payloads in code (`'x'.repeat(131073)`, `\0`
escapes) rather than committing them; no runtime `readdir` discovery of cases; per-case extras go
through an optional `assertParsed?` hook, never `if (name === ...)` branches.

Note this **reversed** an earlier readdir + existsSync-guard design once the single-shared-parser
architecture settled. Re-check test infrastructure against the current architecture rather than
against what the plan said.

## Minimal mocking, few comments, only high-value assertions

'Carrying their weight' is the bar for tests and comments alike.

> "Can you massively simplify this test? I don't like the use of mocks everywhere... Just keep the really good assertions. Comments are out of control in this test too."
> "evaluate the tests... make sure they're carrying their weight"

## Regression tests drive public entry points

Assert observable behavior, never the internal field that was fixed. `563bc317`'s test runs
`createSoftClone` and then `load_frame_metadata_sources`; it never inspects `ForeignMediaIdMarker`.
`889ba328` replaced a wrapper-mechanics test with a classification-behavior test.

## Red-green with a blast-radius check

Failing regression test first, then the fix, then verify, then audit usages. Every bug discussed in
review gets a named test.

> "Okay, write the regression test, make sure it fails, then apply the fix, verify it passes... Look around and make sure this won't break anything else... check usage of foreign media ID"
> "do we have a test for that two csv case now?"

## Missing-test findings cite a production line

Anchor to the specific untested production `file:line` and the concrete regression risk — never a
generic coverage complaint.

## Girder model mocks patch EVERY importing module

The class is imported per-module, so `@patch('dive_server.crud_dataset.Folder')` **and**
`@patch('dive_server.crud.Folder')`, both wired to one `folders_by_id` dict. `563bc317`.

## Fixtures in-repo, media never in the source tree

Reviewer test bundles (media plus sidecar zip) live under `test-datasets/` with manifest provenance.

> "does this work involve using fixtur3es outside the dive repo?" (mid-run audit)
> "make or find a siingle fodler with the okeanos image set and put the fraem-metadata.csv... and zip it up"

## Alias/shared-state bugs need a state-returning mount helper

Mount helpers return `{vm, state}` so the test can mutate local state and assert the injected state
is unchanged. Extend the existing helper with a defaulted param rather than writing a second one —
Kitware/dive@966895a7 gave `mountImportAnnotations` an `annotationSet = ''` param, reused by every
existing test unchanged.

## What the default gate does not cover

`dive-devkit/tools/test.sh <wt>` runs server unit/lint/type plus client unit/lint/builds. It does
**not** cover: `pytest -m integration` (needs `GIRDER_API_KEY` and a live Girder), girder_worker task
execution (`extract_zip`, `convert_video`, `convert_images`), real browser upload flows, or Electron
IPC. Track "gates green, no live e2e" as a separate open item — green gates were repeatedly treated
as done, and the desktop `Track.fromJSON` crash slipped through exactly that gap.

---

Related: [failure-modes.md](failure-modes.md#5-over-built-test-infrastructure),
[parity.md](parity.md).
