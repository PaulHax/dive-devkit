# Server & Girder

## Each feature gets its own service module

Under `client/platform/web-girder/api`, re-exported through the barrel `index.ts`. Export only the
public entry point, as a single `export default`; helpers and response interfaces stay
module-private. `53136adf` moved 53 lines out of `dataset.service.ts` into `frameMetadata.service.ts`
exporting only `loadFrameMetadata`.

> "Does it make sense to extract this out of this huge dataset surface and put frame metadata in its own surface?"

## apispec.ts carries only cross-platform contract types

Single-platform response shapes live privately in that platform's service file. `dab55292` moved
`FrameMetadataSourceItem {itemId, name}` out, leaving only the platform-neutral
`FrameMetadataSourceText`.

## Resolve clones through crud.getCloneRoot()

Never the immediate source folder id. And any new sibling path must set **every** marker the
established path sets — `563bc317`: `_create_multicam_soft_clone` omitted the `ForeignMediaIdMarker`
that `_create_single_camera_soft_clone` set, so downstream `load_frame_metadata_sources` silently
failed.

Clone is a *soft* clone: read paths resolve through the indirection, so the write side that creates
it needs its own test coverage. Read-spec without write-coverage is a recurring plan defect.

## Classify uploads by the canonical extension lists

In `dive-common/constants`, parameterized by media type — never pass all filenames through.
`889ba328` added `mediaFileNamesForImport`; without it, sidecars and `tracks.csv` leaked into
`originalImageFiles`.

## Failed validation must not carry plausible partial classification

Blank `type` when `ok` is False, and test the blank. `889ba328` (`crud_dataset.py` +
`test_validate_files.py`).

## Know what process_items is

A convergence sweep for **ALL** writers — S3 assetstore imports, zip extraction, pipeline outputs,
API side-door — not browser-upload validation. Server-side classification is justified only by the
headless paths. Enumerate which deployment paths break before removing a server check.

> "what if we ripped out all the checks server side? would ingestion of preexsiting s3 imports in girder not work?"
> "why... that needs to be server side validated, would be better if we did a in TypeScript in client right."

## A marker cannot tell DIVE-stored artifacts from user files it merely discovered

Reusing the reserved-name resolver for a *supersede/delete* path is a data-loss bug: discovery
records what it finds in the same marker a deliberate upload sets, so the marker is not evidence of
ownership. The name is. `crud_dataset.py:1910`:

> Supersede cleanup removes only an attachment DIVE itself stored. A reserved-name file is the user's
> own folder content, uploaded with the media and merely discovered by resolution -- and
> process_items records what it discovers in this same marker, so the marker alone cannot tell the
> two apart. The name can: replacing the attachment shadows a reserved-name file, and deleting it
> would destroy a file the user uploaded.

For any replace/supersede path keyed on a marker, ask whether the marker can be true for something
the user put there — and plant a reserved-name file *without* going through the system's own write
path in the test.

## Refresh a folder document immediately before read-modify-write

Girder's `save()` is a **full-document replace**, so a folder loaded at request entry and saved later
silently reverts every key a background job wrote in between. `a895d278` moved
`crud.refresh_folder_document(folder)` to sit directly before the `meta` read in `set_metadata_file`:

> Girder's save is a full-document replace and async jobs (convert_video) write folder meta while
> callers hold this document, so refresh first or their keys (annotate, originalFps, ffprobe_info)
> are replaced with this stale in-memory copy.

The regression test simulates the concurrent write and asserts `annotate`/`originalFps` survive.

For any handler that reads a folder's `meta` to make a decision and later saves that same object,
name which job (`convert_video`, `convert_images`, postprocess) can touch it mid-request. Refresh, or
update the field atomically instead of saving the whole document.

## Survey existing ingestion mechanisms before inventing one

Match the established convention for dive-aware files (`viame.csv`, dive config).

> "What is the current convention for when the server or any code of the dive comes upon a bag of files?"
> "there are other ways to 'import' fiels or data into DIVE. consiter the others and comapre"

Map: `plans/metadata/ingestion/dive-ingestion-paths.md`.

## The upload choke point

POST `/dive_dataset/validate_files` is authoritative for what the client uploads — no selected file
may be silently discarded. Partition new file kinds there FIRST, before the generic csv/txt
classification. Client side: `client/platform/web-girder/uploadPackage.ts` and `views/Upload.vue`.

```bash
git grep -n "def validate_files" server/dive_server/
git grep -n "def _get_data_by_type\|def process_items" server/dive_server/crud_rpc.py
```

## Four server entrances, each patched separately

`crud_rpc.postprocess` (regex → jobs); `extract_zip` in `dive_tasks/tasks.py` (girder_worker);
assetstore fs/s3 imports in `dive_server/event.py` — which needs its own tests, and has both
`process_assetstore_import` and `process_dangling_annotation_files` paths; and
`views_rpc.batch_postprocess`.

## Import failure UX conventions

Unparseable files are removed plus a loud `RestException` carrying an actionable rename hint;
warnings (not errors) for stored-but-unsupported; conflicts rejected BEFORE touching any item so both
survive for the user to retry.

## Pydantic models

Named `BaseModel` subclasses and `Literal[...]` enums, never `Dict[str, Any]` or loose nested shapes.
`f3a39c50`: `Dict[str, Dict[str, List[List[float]]]]` → `Dict[str, PairHomography]`; `Dict[str, str]`
→ `Dict[str, CameraTransformType]` with a `Literal`.

## Celery task routing

Route to the queue whose workers ship the binary — VIAME tools live on `pipelines` (VIAME image)
workers, not `celery` — with a comment saying why. Kitware/dive@8b08c569:
'convert_cam_format.py lives on pipeline workers'.

## Export is a per-artifact decision across three zip streamers

`export_multicam_annotations_zipstream`, `_yield_single_dataset_export`,
`_yield_multicam_dataset_export` in `crud_dataset.py`. Media is included **by regex only**, so
non-media items are silently excluded unless handled. Calibration items are the include pattern
(`_yield_calibration_files`, `_clone_calibration_item`); frame metadata is the deliberate-exclude
example. State which one a new artifact is.

---

Related: [parity.md](parity.md), [data-path.md](data-path.md).
