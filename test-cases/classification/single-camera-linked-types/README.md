# Single-camera classification with linked types

## Contents

`tracks.annotations.json` contains three tracks on eight frames. Each track stores confidence pairs
for a leaf type and its ancestors.

`type-hierarchy.config.json` contains three taxonomy branches and the track and detection attribute
definitions used by related fixtures.

## Data invariant

The stored pair order is intentional. Track 1 stores `fish` first but has
`juvenile-red-snapper` as its deepest passing type. Tracks 2 and 3 cover the tuna and dolphin
branches.
