# Abstraction & dead code

## Looks-dead may be load-bearing — check this before any deletion finding

Before reporting code as dead, or duplication as drift, enumerate every caller. Grep for it,
including **Python callers of TS-adjacent surfaces** such as `crud_rpc.py`. Then check whether tests
deliberately pin the duplication as an isolation boundary. Residual doubt → report a question, not a
deletion finding.

Both directions have burned real time:

> "the parser `Union[MediaKeyIndex, Mapping]` coercion branch is LOAD-BEARING (crud_rpc.py:790 still passes a raw dict) — do not delete it"

and a `/simplify` reuse attempt in `crud_rpc` broke 7 `process_items` mock-isolation tests and was
reverted — "inline duplication there is a deliberate test-isolation boundary".

## Challenge every abstraction the branch introduced

If it diverges from repo convention, back it out — even when it is genuinely better. `1d9b6686`
deleted `SingleCameraFrameMetadataKey` and reverted three files to the `'singleCam'` literal.

> "I guess if our frame metadata branch here introduced this concept, we should probably... back it out... use that plain string, because that's the convention right now"
> "I don't get it, why do we need this classifier? We just need a pointer to the file name"
> "Do we really need this new provider?"

## No speculative format support without a motivating sample

Reject it, and write the test that asserts rejection. `fa302c5c` deleted the hash-header-promotion
path and flipped its tests to `toBeNull()`.

> "i don't have an exampel to support it, so maybe no"
> "Let's clear with me the functionality that we're cutting first, though. Give me some simple examples."

Any new file-format or keying decision must cite a motivating sample — a `test-datasets/` path, or a
VIAME/KWIVER precedent file. Absent one, ask rather than assert.

## No invented defensive limits on user data

A silently-skipping cap is itself a defect.

> "the 10 mb cap is wrong"

Real AUV nav sidecars run 32–50 MB, and the desktop path skipped them while logging nothing. The
stance that replaced it: never silently drop a declared input.

## Delete dead defensive code the read site already covers

Unreachable fallbacks, trivial adapters, and their trivia tests. `fa302c5c` (a pad-short-rows loop
dead under `values[index] || ''`), `5c0ef6e7` (`.pop() ?? name` unreachable), `889ba328`
(a `getExplicitAnnotationFiles` Maybe→array helper inlined).

## Question inherited restrictions and every schema field

Demand the concrete use case. The legacy single-CSV rule turned out to be a proxy from before
telemetry CSVs existed — the fix was to relax the proxy and enforce the real invariant where content
is known.

> "we should alowo more than one CSV. why whould they not alow that?"
> "do we need the 'version' in frame metadata manifest?"
> "So why is order important again... Why not just use one, the first found one or something?"

## Verify compat shims against upstream before keeping them

`_is_stored_frame_metadata_json` looked like backward compatibility; it was added by the branch's own
`af9459c6` and absent upstream. Deleted, per the AGENTS.md no-shims rule.

> "the A5 thing, are we looging backwars cmpatabliy? or are we lossing somehting that was introduced on this branch?"

## Clean deletions are invisible to thrash sweeps — diff the symbol set

A remove-then-re-add audit only finds churn. Code the branch deleted outright and never restored
leaves no trace in that sweep: `_mark_metadata_file_item` and `MetadataFileMarker` disappeared from a
stacked PR undisclosed, and were safe only by luck (write-only, never read).

> "in PR 2, do we mention that we remove the marked itme for a reason."

For any rewrite touching pre-existing upstream code, diff the exported symbol set between the true
base and each tip, and require one line of justification per symbol that vanished.

## When a refactor orphans part of a return value, narrow and rename

`e53d44ba`: `splitCommentBlock` returning `{commentBlock, body}` became `dropLeadingCommentRows`
returning `string[][]`.

## Delete guards that only existed because of a bug

Even when removing them changes visible UI. Kitware/dive@966895a7 removed `v-if="currentSet !== ''"`,
which was only reachable via the aliasing bug being fixed.

## Remove parallel bookkeeping the primary structure encodes

`5345de87` deleted a `claimed` Set; the guard is `records[frame] !== undefined`.

---

Related: [data-path.md](data-path.md) for single-owner normalization,
[failure-modes.md](failure-modes.md#3-invented-abstractions-against-repo-convention).
