# Multicamera classification with linked types

## Condition

Port and starboard contain the same three logical tracks. Both camera files have equal geometry and
equal confidence values.

## Procedure

1. Create a multicamera image-sequence dataset from `media/multicamera`.
2. Import `port.annotations.json` into port and `starboard.annotations.json` into starboard.
3. Import `type-hierarchy.config.json` as DIVE Configuration JSON.
4. Switch between both cameras, play all frames, and reload the dataset.
5. Export the multicamera annotations.

## Expected behavior

The dataset opens without an import, hierarchy, or camera-divergence warning. Each camera has the
same three linked tracks on all eight frames. Both cameras display `juvenile-red-snapper`,
`bluefin-tuna`, and `bottlenose-dolphin`. Reload and export preserve equal confidence pairs in both
camera files.
