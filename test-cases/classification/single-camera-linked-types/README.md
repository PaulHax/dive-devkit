# Single-camera classification with linked types

## Condition

One image sequence has three tracks. Each track has confidence values for a leaf type and its parent
types in a valid hierarchy.

## Procedure

1. Create an image-sequence dataset from `media/image-sequence`.
2. Import `tracks.annotations.json`.
3. Import `type-hierarchy.config.json` as DIVE Configuration JSON.
4. Open the dataset, play all frames, and reload the dataset.
5. Export the annotations as DIVE JSON.

## Expected behavior

The dataset opens without an import or hierarchy warning. It has three tracks on all eight frames.
The displayed types are `juvenile-red-snapper`, `bluefin-tuna`, and `bottlenose-dolphin`. Reload and
export preserve each stored confidence pair.
