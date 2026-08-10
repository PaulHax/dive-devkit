# Desktop/web parity

DIVE ships two backends. Every behavior needs an explicit answer on both, and the gap is where
defects live.

## One Api method, one response shape

A platform difference never surfaces as several optional `apispec.ts` methods that shared code
branches on. Absorb the difference inside each platform's implementation.

`dab55292`: three optional methods plus `runWeb`/`runDesktop` branches collapsed into one
`loadFrameMetadata?`; the web service chains listing+download internally. 11 files, +306/−369, ~63
net lines deleted.

> "could we collapse load frame metadata into one function here that's shared between desktop and web?... Same like API signature at least?"

## Shared computation runs on exactly ONE side

The TS client parses; Python never does — even at the cost of a per-platform optimization, and
delete the comments that justified the optimization along with it. `dab55292` moved desktop
resolution into the renderer for both platforms, deliberately paying the IPC cost: 'Neither platform
parses the sidecar'.

> "including the one parser in Typscript"
> "We decided all parsing happens in TypeScript client-side."

A perf rationale for the split is rebuttable if unmeasured — the IPC-wire claim that justified the
original design was never measured, and `dab55292` abandoned it.

## The only acceptable mirror is a tiny predicate pinned by a shared truth table

And when it changes, both languages plus the fixture land in the SAME commit. `9445de0e` changed
`naming.ts`, `frame_metadata.py`, `source_names.expected.json`, and both test suites together.
`d7f7074a` deleted 46 fixtures and deliberately retained exactly that one shared file.

When client and server genuinely must both parse a format, each parser carries a cross-reference doc
comment naming its counterpart — Kitware/dive@f42122ad:
'Mirrors server/dive_utils/calibration_format.py:parse_stereo_calibration_json'.

## dive-common is node-free and platform-agnostic

Capabilities enter as props; actions leave as emitted events the platform loader binds. State the
node-free constraint at the module boundary of any extracted file (`31ce6f46` moved that comment to
the top of `csvTokenizer.ts`). Never reach for Electron or IPC from dive-common — `c96182cc` has
`EditorMenu` emitting `open-external-link` with the desktop `ViewerLoader` binding `openLink`.

## Standing question: what happens on desktop, which has no server?

A feature on one platform is incomplete until mirrored.

> "what happesn in the desktop whichi has no server"
> "What is the mirror of this uploading for the desktop app? Do we face the same issues? Is there a way to unify?"
> "How does the Desktop, Electron deployment, validate, creating new datasets?"

Upstream practice matches: Kitware/dive@c8f5db9d / @4cf64780 mirrored calibration import/export to
web; Kitware/dive@91ead189 / @76842b69 moved batch multicam into dive-common behind
platform-agnostic function props.

## Media-type coverage is per-consumer, not per-feature

Inside one platform there is a second parity axis: `ImageSequenceType` / `VideoType` /
`LargeImageType` / `MultiType`. "Same as image-sequence" means every consumer, not the producer you
edited. `e40d6117` populated `data.filenames` in `LargeImageAnnotator.vue` at three lifecycle
points — and changed nothing visible, because the panel still gated on `mediaKind === 'image-sequence'`
plus a `frameMetadataUnsupported` computed. It took a second fix in a different file and a different
PR of the stack to open that gate:

> the panel gated on `mediaKind === 'image-sequence'` and a `frameMetadataUnsupported` computed, so
> your `filenames` change had no visible effect

Grep every conditional keyed on media type across the consumer components, not just the producer.
Unit tests that mock the gate cannot see this class of miss — it needs the live panel.

## Unit gates do not catch desktop import bugs

When the diff touches desktop import or ingest paths, the absence of a live Electron e2e is itself
worth flagging. The classifier that mis-parsed a sidecar as VIAME detections produced:

```
Viewer.vue:1070 TypeError: Cannot read properties of null (reading 'toString')
  at Track.fromJSON (track.ts:671)
```

Related desktop hazards: failed imports leave partial dirs under `~/VIAME_DATA/DIVE_Projects` that
break both open and delete; stale Electron singleton locks across worktrees block launch entirely
('Another instance is already running'); renderer errors appear only in DevTools, never in the
main-process log.

## Keep Girder folder-metadata and desktop meta.json symmetric

Flag any Girder folder-metadata field added without the matching desktop `meta.json` field. Schema
versioning is two-sided: `migrate()` in `dive_utils/serializers/dive.py` vs desktop
`JsonMetaCurrentVersion` + `backend/native/migrations.ts`. Name the asymmetry as architectural pain
rather than papering over it.

> "maybe we should introduce version one to the folder metadata for girder so that meta dot JSON is symmetric? ... this is pointing at... some pain in the architecture... different ingestation paths, and then the two back ends?"

## Convention changes must update the devkit in the same pass

`dive-devkit/seed/` fixtures and self-checks, and `test-datasets/manifest.json`, then re-verify the
seeder end to end. A sidecar rename plus an endpoint removal broke the seeder and the user had to
catch it.

> "fix devkit"

---

Related: [server-girder.md](server-girder.md), [correctness.md](correctness.md).
