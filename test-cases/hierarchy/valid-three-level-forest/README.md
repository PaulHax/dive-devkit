# Valid three-level type hierarchy

## Procedure

1. Create an image-sequence dataset from `media/image-sequence`.
2. Import `multipair.annotations.json`.
3. Import `three-level-forest.config.json` as DIVE Configuration JSON.
4. Leave all types checked and use the default threshold.

## Expected behavior

Track 1 displays `juvenile-red-snapper`. Track 2 displays `bluefin-tuna`. Track 3 displays
`bottlenose-dolphin`.

A `bluefin-tuna` threshold of `0.95` makes track 2 display `tuna`. A `tuna` threshold of `0.25` then
makes track 2 display `fish`. The stored confidence vector does not change.
