# Media types, clone, multicam, export

## Branch on the 4-way media-type axis explicitly

`ImageSequenceType` / `VideoType` / `LargeImageType` / `MultiType`.

Supporting a subset is fine — but enforce the limit **at the endpoint** AND document it in a docs
"Limits" section. Silence on a media type is a defect, not a deferral.

Type-specific traps:

- `image_map` (stem→frame index) exists **only** for image sequences.
- Desktop `validImageNamesMap` throws on duplicate stems.
- Videos trigger transcoding on a worker; the media type changes what "upload finished" means.

## Filename↔frame matching is stem value-match, never row order

Extension-stripped stem, matched by value. Reuse what exists: `crud.valid_image_names_dict`, the
desktop splitExt map, or the dive-common resolver. Never positional, never row-order — a plan that
assumes row order will pass its own fixtures and fail on real data.

## Clone is a SOFT clone — plan the WRITE side

Read paths resolve through `crud.getCloneRoot`. That is the easy half. The half that gets missed is
the **write** side that creates the indirection:

- `createSoftClone`
- `_create_multicam_soft_clone`

The multicam variant never set the `ForeignMediaIdMarker` that the single-camera path set, so
downstream `load_frame_metadata_sources` silently failed. Fixed only in `563bc317`, at the very end
of cleanup, because the plan specified read precedence and never mentioned clone creation.

**Rule: for every indirection you read through, test the code that creates it.**

## Export is a per-artifact decision across three zip streamers

```bash
git grep -n "def _yield_\|def export_multicam" server/dive_server/crud_dataset.py
```

- `export_multicam_annotations_zipstream`
- `_yield_single_dataset_export`
- `_yield_multicam_dataset_export`

Media is included **by regex only**, so non-media items are silently excluded unless someone handles
them. For each artifact the feature adds, state whether it round-trips:

- **Includes** — copy the calibration-item pattern: `_yield_calibration_files`,
  `_clone_calibration_item`.
- **Deliberately does not** — frame metadata is the worked example; write down that it is deliberate,
  or the next reader will file it as a bug.

---

Related: [ingestion.md](ingestion.md), [parity-seams.md](parity-seams.md).
