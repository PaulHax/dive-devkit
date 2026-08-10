# Diff hygiene & commit granularity

## Never reformat a line your change doesn't semantically alter

No formatting-only hunks on a feature branch — restore upstream's exact formatting so the files diff
clean. `5ee46a0d` is a 1-insertion/3-deletion commit whose entire purpose was un-wrapping a
`Viewer.vue` import back to upstream's single line.

> "can we avcoid this change on this branch its just formating"

```bash
diff <(git diff --numstat "$BASE"...HEAD) <(git diff -w --numstat "$BASE"...HEAD)
```

Differing lines mean format-only hunks are in the diff.

## Scope fence

Touch only files relevant to the branch's concern. Codebase-wide 'consistency' refactors are out of
bounds *even when the rename is correct*.

> "hold up, this is chaning code thorughout the code base eh? i don't want to do that, lets jsut touch code relevent to dataset info and frame metadata work"

## One fix, one UX decision

The scope fence also applies inside a relevant file. `98348745` was titled as a filename-filtering
fix but, in the same commit, switched web image-sequence upload from multi-file select to
`webkitdirectory`, matching desktop. `efd8fc98` reverted exactly that half:

> Reverting a change I made to web/girder where I swapped the image-sequence to using the
> openDirectory like on desktop instead of the classic multiFile select on web... I decided this PR
> wasn't meant for this change so I'll hold off for another PR in the future to do that.

Read a narrow fix's diff against its own title: does it also change an interaction mode, a picker
type, or a default? If so it is a separate proposal, so it can be accepted or dropped without
re-opening the bug fix.

## Run the autoformatters before declaring done

Never `eslint-disable` when conforming is trivial; single-export modules use `export default`.
`49e2064a` was a dedicated 14-file 'ESLint autofix' commit — quotes, isort, black wrapping, and
removing a disable by converting to a default export.

> "can we avoid this and jsut default exprot the frucntio"

Upstream needed three separate lint commits on contributor work (Kitware/dive@1cce3796
prefer-destructuring, `7bcfe84b`, Kitware/dive@61b010e9; `826bfe09` split combined type imports), so
this is a real reviewer cost, not a nit.

## Mechanical changes get their own commit, named by mechanism

Renames are single-purpose and separable. `49e2064a` was isolated from all behavior commits;
`9445de0e` + `37a84e9f` + `d8873447` landed a convention change, a concept rename, and a synonym
sweep as three independently reviewable commits.

## Surgical within a commit, complete within a PR

A bug-fix diff is the defect plus its regression test, adjacent typos left alone — `12be12a4` is 8+/2−
and leaves the misspelled `pendingUplodsCopy` untouched; `563bc317` is a 2-line fix plus one test.

But under maintainer review, one-line adjacent defects **in the same file** get fixed in the PR rather
than deferred. Kitware/dive@966895a7 fixed the `currentSet` bug that the PR body had deliberately
deferred, plus a stale README line — punting one-line fixes reads as noise.

## Conflict resolution by file list drops cross-file companions

`git checkout <sha> -- <paths>` resolves the paths you name and silently reverts the other half of a
coupled change. `Upload.vue` came back destructuring `{ files, replaced }` from a
`multicamFileRegistry.ts` that still returned a bare `File[]` — `TypeError: Cannot read properties of
undefined (reading 'map')` at runtime, past every gate. It surfaced only because the user asked for a
sweep:

> "Can you take a look at the stacked commits and PRs and make sure there are not more thrashing and miss oriding of code changes like the uplaod.vue problme we just fixed."

After any path-scoped checkout, re-grep the symbols the restored file imports and confirm their
definers were resolved the same way.

## Rebasing a stack after upstream renames is not mechanical

Report the judgment calls; "clean rebase" is almost always false. Restacking onto a merged bottom PR
required adapting the whole stack from the branch's `Metadata`/`Meta` vocabulary to the merged
`Config` API, and archive handling from `meta.json` to `config.json` — while a *second* rename sent
the same old `meta.json` to `dataset.json` for a different concept. Two renames of one filename,
trivially conflated.

> "Was it a straightforward rebase, no funny, like, things to review or decisions that you made which might need my oversight?"

List every renamed symbol touched during the rebase and confirm each resolution picked the new name
consistently rather than a mix.

## Say where a stacked PR's own fix actually landed

When PR N's defect is fixed in PR N+1 (because the intermediate state would not build otherwise),
put a one-line disclosure in PR N's message. Verify placement per-symbol with `git log -S <symbol>`
rather than restating an earlier summary — an unverified claim about which PR carries which fix was
wrong the first time it was made.

## Commit and push are different words

Fixes to code introduced by an unmerged PR autosquash into the owning commit and force-push with
`--force-with-lease`; plain appends get a plain push. 'commit' never implies push, and never implies
opening a PR.

> Jul 16: "commit push" — then, when the agent inferred more: "you only said commit"

One commit per work package or logical fix, imperative subject.

## Bug-fix commit messages narrate symptom and recovery

User-visible symptom and how the user recovers — not code mechanics. `12be12a4`: 'the progress
spinner spun forever and row controls stayed disabled, with no way to recover besides closing the
dialog... so the rows can be removed or retried'.

---

Related: [comments-docs.md](comments-docs.md) for what must not survive into shipped files.
