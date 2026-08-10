# Naming & terminology

## One feature = one term, everywhere

Code, comments, test names, fixture keys, error strings, docs. **The UI label is canonical** — read
it off the current tree, not the plan or the branch name.

`d8873447` swept telemetry→frame-metadata across 11 files, including the fixture key
`fmGateTelemetryOnly`→`fmGateFrameMetadataOnly` and error strings. `964b6aa6` renamed
`DatasetMetaEditorDialog`→`DatasetInfoFieldDialog` and "No dataset metadata"→"No dataset info".
`a56ae00c` caught the docs.

> "look for all mentions of telememty, and see if 'frame metadata' is more acurate"
> "also, we renamed the fraem info panel to 'dataset info'"

Names changed mid-branch twice. Verify against the tree, not memory.

## A rename is total or not done

Sweep types, fields, params, destructuring, exports, spec keys, and comments in one commit.
`37a84e9f` (5 files, +124/−112). A renamed type still carrying an old-word field —
`frameByKey` under `FrameAlignmentIndex` — is worse than no rename at all, because it reads as
deliberate.

## Pin the taxonomy before the sweep, not after

A contested name is not settled by renaming to the first alternative. `3ad7c69b` swept
`meta`→`config` across 75 files (+729/−644): `DatasetMeta`→`DatasetConfig`, `loadMetadata`→
`loadConfig`, desktop `meta.json`→`config.json`. Review rejected the target word outright:

> "config is pretty generic sounding to.  When i think config, i think its somethign that can be resued acrosss "datasets".  what is the file exactly?  its a representation of the dataset and its file assotations and state"

`547810e3` then split it three ways — `Metadata` (frame-level passthrough), `dataset.json` (desktop
project state), `config.json` (portable types/colors/confidence) — rewriting `JsonConfigFileName`→
`DatasetFileName`, `configFileAbsPath`→`datasetFileAbsPath`, and every error string
(`'missing configuration json file'`→`'missing dataset json file'`). Two large mechanical commits
where one would have done.

Before a rename crossing ~20 files, enumerate every related-but-distinct kind the word currently
covers and get the whole taxonomy agreed. Generic words — `config`, `data`, `meta`, `info` — need
this most, because they read as correct for all of them.

## A total sweep can still land the wrong word

Total ≠ correct. `1815b22b` ('fix so function names match the filetype being uploaded') undid part of
the sweep above: `uploadConfigFileItem`→`uploadMetadataFileItem`, `setDatasetConfigdataFile`→
`setDatasetMetadataFile`. Those functions POST the frame-**metadata** attachment; they became
`config` only because they contained the old word.

Tell: a doc comment or route that still says the other word. `uploadConfigFileItem` sat above a
`/metadata_file` route and a comment reading 'Upload an optional per-dataset metadata file'. After
any mechanical rename, re-read each renamed symbol against its own body.

## A legacy-name fallback must own every reference, not just the read

When a rename ships with back-compat, route locks, existence checks, and delete paths through the
resolver too. `3ad7c69b` migrated desktop `meta.json`→`dataset.json` with a read fallback, but
`saveConfig` still locked and read the canonical *new* path — ENOENT on every legacy project. Fixed
post-merge in Kitware/dive@607c6634:

> Locking dataset.json directly fails with ENOENT on legacy projects that still only have meta.json,
> and migrate-on-save below may remove the legacy file while the lock is held.

It passed review because the desktop spec corpus is almost entirely legacy `meta.json` fixtures — the
fallback looked well covered while the lock path had no test at all. Grep every use of the new
filename constant; each hit that is not the resolver is a candidate.

## Name for domain role, not mechanism or payload

`37a84e9f`: 'alignment keys', not 'media keys' or `indexFromEntries`. `e53d44ba`: `rowHasContent`
guards a `row`; `inQuotedField` not `inQuotes`; `scanDelimitedRows` scans chars. `fa302c5c`:
`fieldStart`→`atFieldStart`.

Flags and functions use vocabulary already in scope.

## Special files: exact reserved-basename allowlist

Never a suffix regex that lays claim to user filenames. `9445de0e` replaced a suffix regex with a
4-entry basename `Set`, mirrored in TS and Python plus the shared fixture, and replaced the docs
example.

> "Can you brainstorm some alternatives to this dot meta dot t x t? ... confusing because we have this meta dot JSON output when we export"
> "lets require the frame metadata file be frame-metadata.txt or frame_metadata.csv"

Vet any new convention against artifacts DIVE already emits.

## Derive conventions from the codebase, not from examples or invention

> "I think we should just follow the naming style that you find in the way Dive deals with files. Does Dive in general ingest underscore or dashes?"
> "lets prefer kebab case in docs )but still support snake)"

## Check upstream `main` before standardizing vocabulary

A cleanup rename can move the branch *away* from house style. A `sidecar`→`attachment` pass was
aborted mid-flight once `git log` showed `sidecar` is upstream's own word — `cliImport.ts`, the
desktop README, and four docs already say "pipeline metadata sidecar". Nine committed
`file`→`attachment` swaps had to be reverted as residue.

> "this reads like a dev justifcation chagne comment. also, shoudl we avoid the code thrash sher"

Grep `origin/main`, not the feature branch, for the term you plan to replace. If upstream uses it,
keep it.

## Established names beat naming-purity arguments

When unifying an API across platforms, keep the name already in use.

> "What's overloaded about that name? We're already using it for desktop."

## Check a new control against the labels already in its dialog

Confusability is a review finding even when the neighbour is untouched pre-existing code. A
frame-metadata filename-join control landed beside a pre-existing SealTK 'filename' frame-index
checkbox (`a152dc3a`), and neither the user nor the agent could tell them apart from the labels:

> "whats up with the 'filename' frame index checkbox?"
> "is this a frame metadata thing or prexisting?"

If two controls in one dialog share vocabulary, the labels have to disambiguate — a tooltip does not.

## User-facing hints state the exact filename

Never the naming rule. Tests assert the literal string. `9445de0e`/`d8873447` put
'rename it to frame-metadata.csv' in both `common.ts` and `crud_rpc.py`.

## Negative-case fixtures carry realistic unrelated names

`d8873447`: a file that is *not* frame metadata, named `telemetry.csv`, reads as the very thing it
is supposed to test against. `nav.csv` doesn't.

## Don't call data types or fixtures 'contracts'

`357bec9e`: `segmentation.ts`/`stereo.ts` headers became 'types shared between X and Y';
`ContractSource`→`ExpectedSource`, `loadContract`→`loadExpectedFixture`.

---

Related: [comments-docs.md](comments-docs.md) for terminology in docs,
[failure-modes.md](failure-modes.md#9-terminology-drift) for the drift grep.
