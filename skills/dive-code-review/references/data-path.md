# Parsers & data path

## One owning function per normalization/precedence invariant

A second identical implementation is a drift bug — extract it and name the owner in its doc comment.
`d6622c04` folded `buildMediaKeyIndex` and `normalizeMediaKeys` into `indexFromEntries`, documented
as 'the single owner of the normalize + collision rule... so the two can never drift'.

Subject to the load-bearing check in [abstraction.md](abstraction.md) — some duplication is a
deliberate test-isolation boundary.

## Check existing utilities before hand-rolling; extract generic mechanics; add no dependency

`d6622c04` used lodash `uniq` in place of a 13-line Set loop. `31ce6f46` extracted
`csvTokenizer.ts` exporting exactly one function and one type.

> "Seems like a lot of work in a file just to load some CSVs... Does dive not have like good utilities for that already?"
> "isolate into a separate file the CSV tokenizer... Let's not introduce a new dependency right now."

## One round-trip, lazy at the point of use, sparse at display time

Flag any new client flow that needs more than one API round-trip to render one panel, and any loop
that materializes per-frame records for all frames before display time.

> "Isn't that just a one-step thing?... Why doesn't it just include the item text at that point"
> "We can just do that when they're needed, and it can be one call... the only place we're using it right now is for the dataset info panel"
> "sparse lookup at display time"

## On data conflict, show something

Deterministic winner plus one non-repeating notice — never blank. Prefer wire shapes that are
identical on every fetch: **report state, not events**, so no dedup machinery has to exist.

> "well, better to show someting rather than nothing? right?"
> "is impimentinc C5 not to crayz? is there a simpliccation we shoudl consiter?"

The over-built warnings-event channel was simplified to `sources: string[]` per camera.

## Scope caches to the operation; dedupe by caching the Promise

Cache the in-flight Promise, not the resolved value. `d6622c04` replaced a composable-lifetime raw-text
Map with manual eviction by a pass-local `Map<string, Promise<string>>` — 'released when this map
goes out of scope'.

## Functional selection over imperative bookkeeping

`fa302c5c`: argmax via `{item, score}[].reduce`; `join` computed once at the single call site instead
of threading `threadedJoin ?? selectJoinColumn(...)` through return types. Never thread optional
precomputed results through a signature.

## Filename predicates split both separators and test the basename

And harden parsed records against prototype pollution. `9445de0e` split on both `/` and `\` in TS and
Python, with path-bearing fixture cases `left/x` and `right\x`.

> "The `proto.csv` case must yield an own-property record."

`fa302c5c` added `nullPrototypeRecord` / `projectRecord` helpers.

## Test every filename predicate against embedded dots

Real DIVE media is timestamp-named: `20171027.214830.208.029135.png`. `98348745` fixed web
image-sequence upload silently hiding those files, adding `getImageSequenceFileAccept()` so the
picker lists dotted extensions alongside MIME types —

> Extensions + MIME: some Linux pickers miss multi-dot PNGs when only MIME is listed.

— and clearing `accept` entirely in directory mode for the same reason. Any `input.accept`, suffix
regex, or extension check in the diff gets a fixture with ≥2 embedded dots before it is called clean.
A predicate that only ever saw `name.ext` has not been tested.

## Use DIVE's own ordinal before reconstructing identity from filenames

If the system already knows the entity's index, join on it. An ordered media list already gives
`array index → DIVE frame number`; a source-counter heuristic parsed out of filenames was
reconstructing what was authoritative two lines away.

> "does not dive have some understanding of the frame ordering when it imports a image list dataset? why don't we use the 'frame' column in the metadata to match the frame that Dive understands and avoid doing speical matching on file names again. dive already has understnaidng of frame number"

## Prefer first-match rules to scoring

Ranking machinery must earn its place on real data. Column scoring was cut for a leftmost-match rule
after the real fixture corpus showed ranking never changed the outcome; `join.ts` went 306 → 271
lines with no corpus regression.

> "instead of this scoring stuff can we cut the semantics? ... maybe we can just pick the first column that matches some simple rules instead of ranking columns against each other"

## Ordering assertions in specs are executable statements of intent

Before touching any precedence or tie-break, read the spec that pins the current order **and its
comment**. `join.spec.ts:101` — 'keeps filename precedence for a VIAME-shaped source with a different
frame field' — encodes that a VIAME `frame` column is a VIAME index, not a DIVE frame. The obvious
simplification (literal `frame` beats filename) would have inverted it and marked those tables
invalid.

## A success flag beside a sentinel field is a discriminated union waiting to happen

`{ok, message, type: DatasetType | ''}` became `{ok: true, type} | {ok: false, type?: undefined}`.
Flag any new response shape carrying a boolean plus a field that is sometimes `''`, `-1`, or an
unused `null` for the same fact.

> "can this not be emtry string? can we make emtpy dataset type? is that a thing? how to simplify this"
> "also, is ok field sstill needed?"

## Ground format and keying decisions in precedent and real samples

Prefer derived defaults over config fields.

> "KWIVER or VIAMI may have approaches to this already... check the incoming Viami.csv"
> "check out our other input exampels in .../auv-nav-telemetry-samples/source and help me decided"
> "for abolsut etimestamps, we could jsut take the first row timestamp as the start"
> "frame wins"

Filename↔frame matching is extension-stripped **stem value-match**, never row order — reuse
`crud.valid_image_names_dict`, the desktop splitExt map, or the dive-common resolver.

---

Related: [abstraction.md](abstraction.md), [parity.md](parity.md) — the parser lives on exactly one
side of the platform boundary.
