# Ingestion — the axis that killed two cuts

~25 distinct ways data enters DIVE: zip upload, assetstore no-copy import, clone, side-door API,
desktop folder import, pipeline output, batch postprocess, and more. Map:
`plans/metadata/ingestion/dive-ingestion-paths.md`.

**Only the filename travels every path.** Any mechanism that persists a decision at import time —
a marker, a classification, a manifest written during upload — structurally misses clone, side-door,
and assetstore arrivals. Two feature cuts died on this before the survey was run.

> "Only the filename covers all paths without per-path wiring"
> "there are other ways to 'import' fiels or data into DIVE. consiter the others and comapre"

Below are the choke points a new file kind must be handled at. Each was patched separately in the
landed feature; missing any one produces a path where the file is silently eaten or silently
dropped.

## 1. Web upload pre-classification

POST `/dive_dataset/validate_files` is authoritative for what the client uploads — **no selected file
may be silently discarded**. Partition new file kinds there FIRST, ahead of the generic csv/txt
classification, or they trip it.

```bash
git grep -n "def validate_files" server/dive_server/
```

Client side: `client/platform/web-girder/uploadPackage.ts` (`buildValidatedUploadPackage`) and
`views/Upload.vue`.

Failed validation must return a blank `type` — a plausible partial classification on a failure
response is worse than none.

### The file picker is part of that choke point

If the server is authoritative for what gets uploaded, the client `accept` list must be a **superset**
of what the server will classify — otherwise the picker settles a file's fate before the server ever
sees it, and the ignored-file list the user was promised comes back empty:

> "i don't see the 'inogred' list when i use 'add image sequence' on okeanos-upload-authority-ignore"

`client/platform/web-girder/utils.ts` now unions the annotation and metadata extension lists, with the
reason recorded in place — 'Filtering one out here would settle its fate before the server ever
classified it.' Directory mode clears `accept` entirely. Any PR whose thesis is "the server decides"
must be read against every `accept`/extension gate on the client path.

## 2. Server import funnels

```bash
git grep -n "def _get_data_by_type\|def process_items" server/dive_server/crud_rpc.py
```

- `_get_data_by_type` — per-file sniff, `FileType` enum in `dive_server/crud.py`.
- `process_items` — the postprocess sweep, oldest-first, with a `ProcessedMarker` exclusion.

A new file kind decides here between two outcomes: import and move to auxiliary, **or** mark
processed and leave in place. Frame metadata takes the second: 'never import it as annotations, move
it, or remove it'.

`process_items` is a convergence sweep for **all** writers — S3 imports, zip extraction, pipeline
outputs, the API side door. It is not browser-upload validation, and removing a check there because
"the client already validates" breaks every headless path. Enumerate which ones before proposing it.

## 3. Four server entrances, patched separately

| Entrance | Where |
|---|---|
| `crud_rpc.postprocess` | zipRegex / videoRegex / imageRegex → jobs |
| `extract_zip` | `dive_tasks/tasks.py`, girder_worker; MultiCamJsonFileName roots, zip-bomb checks |
| assetstore fs/s3 import | `dive_server/event.py` — `process_assetstore_import` **and** `process_dangling_annotation_files`; needs its own tests (`test_event_frame_metadata.py`) |
| `views_rpc.batch_postprocess` | batch path |

## 4. Desktop import is a full parallel second implementation

In `client/platform/desktop/backend/native/common.ts`:

- `beginMediaImport` — media sniff
- `findTrackandMetaFileinFolder` — **auto-discovers sibling files**; a new sidecar kind must be
  filtered OUT here or it gets eaten as annotations
- `_ingestFilePath` — the per-file gate, called by `ingestDataFiles`

```bash
git grep -n "_ingestFilePath\|findTrackandMetaFileinFolder" client/platform/desktop/backend/native/common.ts
```

Every web/server classification rule needs a mirrored gate here. When this was missed, the desktop
classifier read a sidecar as VIAME detections and crashed `Track.fromJSON` on `id:null` — a defect no
unit gate caught.

## Grep `main` for any new directive or field name before locking it in

A rebase stalled at commit 47/60 on a real collision: the branch's frame-metadata sidecar and a
newly-merged generic pipeline attachment both used `# Metadata File:` in `.pipe` headers, meaning
different things. `git grep` the exact token against current `main` while the name is still cheap to
change.

## Import failure UX conventions

- Unparseable files are removed, plus a loud `RestException` carrying an actionable rename hint.
- Stored-but-unsupported gets a **warning**, not an error.
- Conflicts are rejected BEFORE touching any item, so both survive for the user to retry.
- Re-check side-door arrivals in `process_items` even when `validate_files` already blocks them.

Product stance for unsupported input: store it and say so loudly.

> "well, lets take the files and store them, but be clear we dont' supprot them yet"
> "slow-and-loud is acceptable, silent loss is not"

The same principle killed a 10MB cap that silently skipped real AUV nav logs running 32–50 MB.

---

Related: [parity-seams.md](parity-seams.md), [media-clone-export.md](media-clone-export.md).
