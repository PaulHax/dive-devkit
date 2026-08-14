# Divergent multicamera classification replicas

## Condition

Port and starboard contain linked tracks with the same IDs and geometry. Track 2 stores
`bluefin-tuna: 0.9` on port and `bluefin-tuna: 0.35` on starboard.

## Expected behavior

Dataset load reports one bounded divergence warning. Logical-track reads use the first configured
camera. Canvas display can differ by camera. A classification edit synchronizes independent vectors
to both replicas. Save and reload preserve the synchronized result.
