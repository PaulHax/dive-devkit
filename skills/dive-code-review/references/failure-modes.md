# Top 10 failure modes, frequency-ranked

What one-pass implementations got wrong most often on the reference feature. Each entry: the
pattern, a check that detects it, and the topic file with the full treatment.

Detect commands are worth running rather than eyeballing the diff — the parity and fixture misses
below were all found by a grep after a careful read had missed them. `$BASE` is whatever merge-base
you settled on.

---

## 1. Plan scaffolding fossilized in code

`Contract X-Y` taxonomies, `(FIX 1)`, `(FIX 3)`, `W-12 memory posture`, `(D2)`, workorder IDs,
finding numbers, test-name parentheticals. Four dedicated cleanup commits: `357bec9e`, `1d9b6686`,
`1c1dbad7`, `889ba328`.

> "these contract-whatever, these are leftover implementation details... clean out those contract labels"

```bash
git diff "$BASE"...HEAD | grep -inE 'contract [a-z0-9]+-[0-9]|\(fix ?[0-9]|w-[0-9]+|\(d[0-9]\)|workorder|finding #'
```

→ [comments-docs.md](comments-docs.md)

## 2. Comment flooding

Mechanics narration, multi-paragraph design essays, 11-line doc blocks on wire types. ~60 lines cut
from one composable in `1d9b6686`. "why not what" was repeated verbatim in three separate sessions.

Read check: every added comment line. Flag any that paraphrases the line below it, and any block
≥3 lines not stating an invariant.

→ [comments-docs.md](comments-docs.md)

## 3. Invented abstractions against repo convention

Exported constants for established literals, classifiers where a filename pointer suffices,
platform-split providers where the read paths are identical, trivial Maybe→array adapters with
trivia tests. `1d9b6686`, `889ba328`.

> "I don't get it, why do we need this classifier? We just need a pointer to the file name"
> "Do we really need this new provider?"

Read check: for each new exported symbol or module, check whether `origin/main` uses a plain literal
or an existing pattern for the same job.

→ [abstraction.md](abstraction.md)

## 4. Platform split leaking into shared surfaces

Multiple optional Api methods plus `runWeb`/`runDesktop` branches in shared code — or the desktop
mirror forgotten entirely. `dab55292` collapsed three optional methods into one (+306/−369).

> "what happesn in the desktop whichi has no server"

The desktop gap was not hypothetical: a folder-import classifier mis-parsed a sidecar as VIAME
detections and crashed `Track.fromJSON`.

```bash
grep -rnE 'runWeb|runDesktop' client/dive-common client/src
# plus: count new optional methods on the Api interface in apispec.ts
```

→ [parity.md](parity.md)

## 5. Over-built test infrastructure

46 conformance fixtures deleted in one commit (`d7f7074a`, 49 files changed) — an on-disk corpus
with runtime readdir discovery plus a guard test, for a single-implementation parser. Plus
mock-everywhere specs.

> "we intrduce many test fixture files. are they needed? can they be inlined in the tests?"

```bash
git diff --stat "$BASE"...HEAD | grep -iE 'fixture|testdata'
grep -rn 'readdirSync' client --include='*.spec.ts'
```

→ [tests-fixtures.md](tests-fixtures.md)

## 6. Speculative defensive code

10MB caps, hash-header promotion for inputs no fixture produces, dead pad loops, warnings-event
channels, precedence machinery, version fields. `fa302c5c`.

> "the 10 mb cap is wrong" — real AUV nav sidecars run 32–50 MB, and the desktop skip logged nothing
> "i don't have an exampel to support it, so maybe no"

Read check: every new limit, tolerance, or optional format branch in the diff. Demand the motivating
sample.

→ [abstraction.md](abstraction.md)

## 7. Lint/format non-conformance and diff churn

Double quotes in client TS, `eslint-disable` instead of conforming, unsorted imports, reformatting
untouched lines. One dedicated 14-file autofix commit (`49e2064a`); a 1-insertion/3-deletion commit
(`5ee46a0d`) existed solely to un-wrap an import back to upstream's formatting.

```bash
dive-devkit/tools/test.sh <wt> --lint
git diff "$BASE"...HEAD | grep -n 'eslint-disable'
diff <(git diff --numstat "$BASE"...HEAD) <(git diff -w --numstat "$BASE"...HEAD)   # differing lines = format-only hunks
```

→ [diff-hygiene.md](diff-hygiene.md)

## 8. Unfinished error paths

Spinners stuck on failure, busy flags reset only on success, silent degrade. Found within minutes of
live testing, every time.

> "there is an issue, if there is an error on upload of a file the uplaod spinner is stick"

`12be12a4`: `if (!error) $emit('update:uploading', false)` left `uploading=true` on every pending row,
with no way to recover but closing the dialog.

Read check: every busy flag set in the diff — does the throw path reset it?

→ [correctness.md](correctness.md)

## 9. Terminology drift

'telemetry' vs 'frame metadata', 'Meta Editor' vs 'Dataset Info', stale UI names surviving in error
messages and docs. `d8873447` (11 files), `964b6aa6`.

```bash
grep -rniE 'telemetry|meta editor' --exclude=package-lock.json client/ server/ docs/
```

Substitute the synonym list for the feature under review — old names, plan vocabulary, the branch
name.

→ [naming.md](naming.md)

## 10. Green gates treated as done

No live stack for manual verification, no Electron e2e (the `Track.fromJSON` crash slipped through),
the dive-devkit seeder left broken, no discoverable upload path in the actual UI (typed file pickers
silently blocked sidecars), docs asserting a stale contract.

> "you better start the stack so i can tesets"
> "fix devkit"

Check: does the branch or PR carry live-verification evidence? Do `dive-devkit/seed/` fixtures and
self-checks still match renamed conventions and endpoints?

→ [parity.md](parity.md), [tests-fixtures.md](tests-fixtures.md)

## 11. Type-level regressions the client gate cannot see

**The DIVE client has no typecheck step at all.** `client/package.json` ships `lint`,
`lint:templates`, `test`, and the two builds — no `tsc --noEmit`, no `vue-tsc`; Vite strips types
without checking them. `typescript` is pinned at `~4.3.5`, old enough that pointing it at the project
produces hundreds of parse errors inside `@types/node` before it reaches a single project file. A
deliberate `export const x: number = 'bad'` planted in `naming.ts` produced no output.

So "873 vitest tests and full eslint green" says nothing about types or exports. Restructuring an
`export {}` / `export type {}` block silently dropped `FrameMetadataRow`, `FrameMetadataTable`, and
`DelimitedTableDelimiter` while the whole gate stayed green.

```bash
# every symbol exported by a touched module vs. every symbol imported from it
git diff "$BASE"...HEAD -- '*.ts' | grep -n '^[-+].*export \(type \)\?{'
git grep -n "from '.*<module>'" client | grep -o '{[^}]*}'
```

Read check: any diff that moves, inlines, or collapses an export block gets a manual import-site
trace. Nothing automated is watching.

→ [tests-fixtures.md](tests-fixtures.md), [abstraction.md](abstraction.md)
