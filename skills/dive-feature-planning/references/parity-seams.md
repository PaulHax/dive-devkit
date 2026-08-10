# Platform parity — the mirror tax

## Name which of the three homes each behavior lives in

| Home | Path | Exists |
|---|---|---|
| server Python | `server/dive_server` + `dive_utils` | once |
| desktop TS backend | `client/platform/desktop/backend` | once |
| shared TS | `client/dive-common` | once, used by both |

Format serializers exist **twice**: `server/dive_utils/serializers/{viame,kwcoco,dive,kpf}.py` vs
`client/platform/desktop/backend/serializers/{viame,coco,dive,kpf,nist}.ts`.

Count the mirror tax in the plan and drive it toward zero. The landed feature has exactly ONE
mirrored function — `server/dive_utils/frame_metadata.py` ↔ `client/dive-common/frameMetadata/naming.ts`
— pinned by a shared `source_names.expected.json` fixture, and the workorder said so explicitly:
'this is the only mirrored logic left in the whole feature'.

## Default placement is shared TS

Every piece of server-side Python logic in the plan must name the **headless path** that requires it:
assetstore/S3 import, zip extraction, side-door API, VIAME pipeline outputs — no client runs there.

Expect radical-removal probes, and answer them by enumerating which real paths break:

> "what if we ripped out all the checks server side?"
> "would be better if we did a in TypeScript in client right"
> "it would be great if that could be all done, like, pure TypeScript so the desktop app can use it cleanly"
> "We decided all parsing happens in TypeScript client-side."

## The apispec seam

`client/dive-common/apispec.ts` defines `interface Api`, provided/injected via `useApi`, and
implemented twice: web `client/platform/web-girder/api/*.service.ts`; desktop
`frontend/api.ts` → `ipcRenderer` → `backend/ipcService.ts` → `native/common.ts`.

Optional members are the convention for one-platform capabilities — but **exactly one method with
one response shape**. Several optional methods that shared code branches on (`runWeb`/`runDesktop`)
is the asymmetry smell that `dab55292` unified across 11 files (+306/−369). New feature APIs get
their own service module (`53136adf`).

## New client APIs: one call, complete payload, lazy

No list-then-fetch. Fetch lazily at the single consuming component — audit who actually consumes it
before designing its lifecycle. Prefer wire shapes identical on every fetch (report state, not
events) so no dedup machinery has to exist.

> "Isn't that just a one-step thing? And then the backend … just returns all of them"
> "sparse lookup at display time"

## Schema versioning is two-sided

`migrate()` in `server/dive_utils/serializers/dive.py` vs desktop `JsonMetaCurrentVersion`
(`client/platform/desktop/constants.ts`) plus `backend/native/migrations.ts`.

New persisted fields need a version bump or optional-with-default on **both**. Keep Girder
folder-metadata and desktop `meta.json` symmetric — and when they cannot be, name the asymmetry
rather than papering over it.

> "maybe we should introduce version one to the folder metadata for girder so that meta dot JSON is symmetric? … this is pointing at… some pain in the architecture… different ingestation paths, and then the two back ends?"

Counter-case: **an unshipped branch's own prior draft shape is not production data.** Do not write
migration or compatibility machinery for fields that have never been released.

> "do you think the migration is needed or simpfliygin or shoudl we keep exsiitng structure?"

## Desktop: size "user picked it" and "infer it from disk" separately

They are not one work item. The explicit-pick path is ~20 lines; the fallback that discovers the file
when nobody picked one runs ~200 lines across three consumers (`common.ts` folder scan, import,
archive) and is what makes a desktop PR balloon.

> "complexity with the desktop needing to discover files. I thought the user just pointed at the file directly, more or less."

Scope them as two line items and challenge the inferred half — do all three consumers need it?

## dive-common is node-free

Capabilities enter as props; actions leave as emitted events the platform loader binds. State the
node-free constraint at the module boundary of any file extracted into it.

## Three data stores, three merge semantics

Name which one the feature touches:

| Store | Semantics |
|---|---|
| annotations | additive/overwrite, plus annotation sets; `set` param threads through `views_annotation.py` |
| datasetInfo | per-key merge — implemented **separately** on both platforms (server `resolve_imported_dataset_info`, desktop explicit per-key merge after a lodash deep-merge) |
| frame metadata | read-only; never in annotation import/export |

---

Related: [ingestion.md](ingestion.md), [media-clone-export.md](media-clone-export.md).
