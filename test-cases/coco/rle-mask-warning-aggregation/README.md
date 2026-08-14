# COCO RLE mask warning aggregation

## Contents

`rle-warning-fish.coco.json` and `rle-warning-shark.coco.json` each contain one valid bounding box
and one unsupported run-length encoded mask.

## Data invariant

Each file produces its own unsupported-mask condition. The files have different categories but the
same source image, so input order and repeated warning text remain observable.
