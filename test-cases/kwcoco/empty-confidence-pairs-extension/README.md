# Empty DIVE confidence-pairs extension

## Contents

`empty-confidence-pairs.kwcoco.json` declares the DIVE confidence-pairs extension, but its
annotation contains an empty `dive_confidence_pairs` array. Standard `prob`, `category_id`, and
`score` fields remain populated.

## Data invariant

The standard probability vector maps to `shark: 0.8` and `fish: 0.2` on track 7. The empty exact
extension is malformed without making the annotation unusable.
