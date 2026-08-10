# Correctness edges

## Convention-match never closes an error-path verdict

New code that matches an established idiom is not thereby clean — the idiom may carry the same
latent bug. For every guarded window (lock acquire→release, busy flag set→reset, cache
invalidate→refill, id/token pre-committed before an await), name what can throw inside it and where
that failure surfaces to the user. If you cannot trace the throw path, report a question, not
"clean". **Read the guard's implementation, not just its call site.**

This is here because it failed in practice. An A/B skill trial (2026-07-17,
`frame-metadata-explicit-import`) produced two false "clean" verdicts by matching idiom:

1. The desktop meta-lock in `importFrameMetadataFile` was cleared because it "matches the
   saveMetadata idiom, no try/finally is pre-existing" — without reading `_acquireLock` (never saw
   `stale:5000`) or tracing what throws between acquire and release.
2. A `useFrameMetadata` invalidation watcher was cleared as "token-guarded", while the reject branch
   of the pre-committed-id refetch (new code) leaves the panel stuck with `ensure()` a permanent
   no-op. Confirmed defect.

The convention rule from [abstraction.md](abstraction.md) read in reverse — match ⇒ clean — collided
with the error-path rule below, and convention won without anyone noticing.

## Error paths reset EVERY busy flag the success path resets

Finally-shaped teardown, all flags enumerated, per-row **and** dialog-level. Never silent degrade on
a user-toggled feature. UI severity by recoverability: per-item = warning, infra = error.

`12be12a4`: `if (!error) $emit('update:uploading', false)` left `uploading=true` on all pending rows.
Found live within minutes:

> "there is an issue, if there is an error on upload of a file the uplaod spinner is stick"

Upstream removed a silent-degrade branch for the same reason (Kitware/dive@c2c1fa5d) — it 'made that
look like annotations simply weren't measuring'; the same dialog now transitions progress→error.

## Diff new sibling paths against the established path

Every marker or mode the old path handles, the new one must too. `563bc317`:
`_create_multicam_soft_clone` omitted the `ForeignMediaIdMarker` that `_create_single_camera_soft_clone`
set, and downstream `load_frame_metadata_sources` silently failed. Kitware/dive@ce82043c:
`editingType === 'Point'`-only checks silently broke Polygon multicam draw at two sites.

A lookup is a sibling path too. `e3aac380`: the assetstore video-sidecar match ran
`Folder().findOne({'parentId': …, 'name': video_stem})` with no type filter, so a same-named
**image-sequence** folder swallowed the match. The fix added `f'meta.{TypeMarker}': VideoType`. When
one query gains a discriminator, grep every other query on the same field pair and ask whether it
needs the same one.

## A bare `return` inside a classifier is usually a missing fallthrough

Same commit: when no video folder matched, the handler simply returned, silently dropping the file.
It now falls through to the plain annotation path —

> Parent is already typed and no VideoType child exists — not a video-paired layout. Fall through so
> csv/json can follow the plain annotation path (process_items / dangling) instead of being silently
> dropped.

For every early return in a multi-branch classifier, decide out loud: is this "no match, nothing to
do", or "no match on *this* sub-case, try the next path"? The two read identically in the diff.

## Never key removal on the identity of a rebuilt object

Browser folder selection flattens entries into **new** `File` objects, so identity-based removal of a
chosen attachment silently fails and same-named entries collide in the registry. The fix was unique
opaque keys with filename-based dedup. Grep new client code for `.find(x => x === fileRef)`,
`indexOf`, or `filter` keyed on a `File`/object reference instead of a stable string id.

## A derived child record must clear what it should not inherit

Per-camera exports built by copying the parent record inherited the shared locator, producing corrupt
archives from stale desktop paths. Copy-then-clear, and assert the absence in a test — a child that
happens to omit a field today will carry it the moment the parent grows one.

## One boolean, one reason to skip

An export gate named for parent **media** was also stripping the parent's attachment declaration, so
multicam archives shipped the file with no locator. If a flag gates more content than its name says,
split it. Grep every consumer of a boolean export/import gate before reusing it.

## Accept-and-store unsupported input with a loud stated reason

Never reject, never silently drop.

> "well, lets take the files and store them, but be clear we dont' supprot them yet"

→ 'frame metadata is not supported for this media type'. The same principle killed the 10MB silent
skip.

## Green-but-misleading tests must not sit

Fix the gap surgically now, or make the test honest. An open gap flagged during a run gets followed
up by name, with a traced blast radius and explicit options. `dc68c577` made the double-extension
media tests honest on both platforms.

## Async client flows — tick each

- gate work on the tracked in-flight promise, not a bare `!enabled` early-return
- set state flags BEFORE awaits ('Mark it BEFORE any waiting below', Kitware/dive@c2c1fa5d)
- a load that pre-commits its id/token before the await: **trace the REJECT branch** — does a failed
  refetch leave state that makes `ensure()`/reload a permanent no-op? (stuck error, no retry)
- serialize overlapping ops on a promise chain (`cliOpenChain = cliOpenChain.then(...)`,
  Kitware/dive@ef45393)
- AbortController per-request, aborted on unmount
- debounced work `.cancel()`ed
- `markRaw()` on DOM objects placed in reactive state (Kitware/dive@c4e15ffc)

## Vue navigation guards call next(false) on the reject branch

Accept-only `next()` leaves navigation in limbo when an unsaved-changes prompt is declined.
Kitware/dive@effeec5 fixed both `beforeRouteLeave` and `beforeRouteUpdate` in `ViewerLoader.vue`.

## Electron main-process / IPC, early lifecycle

Only when the diff touches it: queue plus an explicit renderer-ready handshake (renderer pulls, main
flushes); cover the no-window cases (create if `app.isReady()`, reset the ready-flag on window
close); renderer handlers need try/catch because services may not be attached yet; report headless
stalls on **both** `console.info` and an in-app dialog. Kitware/dive@ef45393 replaced a nullable slot
with `pendingCliOpens[]` + `cliRendererReady`; Kitware/dive@75d5b40 made `CliTranscodingNotice`
dual-channel — 'Prompt service not attached yet; console + Jobs page still cover it'.

## GeoJS layers and annotators

Only when the diff touches them:

- unlock `clampBoundsX`/`Y` + `clampZoom` before programmatic zoom/center snaps — otherwise they are
  silently rejected, and `LargeImageAnnotator` clamps by default
- `map.exit()` before re-init and in `clear()` — orphaned WebGL contexts cause context loss, and then
  redraw throws; wrap redraw/disable in try/catch
- one physical click can emit duplicate same-tick events across overlapping layers, and toggle
  handlers self-undo — use a handled-this-tick flag
- validate 'done' annotations for minimum vertex counts before committing

Kitware/dive@0edf8f53, @e2509a89, @c2c1fa5d, @ce82043c — all upstream fixups.

## Tolerate the reload window

Only when the diff touches multicam/stereo or dataset-switch paths: `aggregateController` returns a
no-op stub when `cameras` is empty (controllers clear before recreation and watchers throw) —
Kitware/dive@83b70d11. Per-dataset service state (caches, fps maps, calibration, dialogs) resets on
dataset-id change so one dataset's state cannot leak into the next — Kitware/dive@5e0203f0.

---

Related: [vue-ui.md](vue-ui.md) for Vue 2 reactivity traps, [parity.md](parity.md).
