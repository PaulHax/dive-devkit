# Empty DIVE confidence-pairs extension

## Condition

`empty-confidence-pairs.kwcoco.json` declares the DIVE confidence-pairs extension, but its
annotation contains an empty `dive_confidence_pairs` array. Standard `prob`, `category_id`, and
`score` fields remain usable.

## Expected behavior

DIVE reports one bounded malformed-extension warning. It creates track 7 from the `prob` fallback
with `shark: 0.8` and `fish: 0.2`. It does not create an empty classification.

Run the import on Web and Desktop.
