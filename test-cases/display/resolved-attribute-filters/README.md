# Attribute filters on resolved types

## Procedure

Create the baseline from `media/image-sequence`, `multipair.annotations.json`, and
`three-level-forest.config.json`. Add a track attribute filter and a detection attribute filter for
`juvenile-red-snapper`.

## Expected behavior

`LeafTrackMarker = juvenile-track` retains track 1. `LeafDetectionMarker = juvenile-detection` also
retains track 1. Changing either filter type to raw ancestor `fish` excludes track 1 while the leaf
is the resolved display type.
