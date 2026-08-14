# Exact DIVE KWCOCO confidence-pair round trip

## Condition

Track 17 has two annotations. The last frame contains the exact ordered vector `shark: 0.8`,
`fish: 0`, and `rock: 0.2`. The standard `prob` vector has different membership. The `shark`
category names `fish` as its direct parent.

## Procedure

1. Create an image-sequence dataset from `media/image-sequence/`.
2. Import `exact-confidence-pairs.kwcoco.json`.
3. Inspect track 17 and the type hierarchy.
4. Export the dataset as KWCOCO.
5. Import the export into another dataset that uses the same images.
6. Run the procedure on Web and Desktop, then exchange one export between the two platforms.

## Expected behavior

The import does not report a confidence-pair warning. Track 17 uses the last-frame exact vector in
its original order, including `fish: 0`. The hierarchy contains `shark: fish`. Each export and
reimport preserves the track ID, hierarchy edge, pair order, sparse membership, and explicit zero.
