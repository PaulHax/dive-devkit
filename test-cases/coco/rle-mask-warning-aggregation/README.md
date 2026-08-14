# COCO RLE mask warning aggregation

## Condition

`rle-warning-fish.coco.json` and `rle-warning-shark.coco.json` each contain one valid box and one
unsupported run-length encoded mask.

## Procedure

1. Use `media/image-sequence` as the image sequence.
2. Call the Desktop `ingestDataFiles` entry point with both COCO paths in the primary input list.
3. Inspect the returned warnings.

## Expected behavior

The result contains two warnings in input order. An empty warning list from a later input does not
remove an earlier warning. Equal warning strings remain separate entries.

DIVE has no direct multi-file Electron dialog for this entry point. The exact executable check is
the warning-preservation case in `common.spec.ts`.
