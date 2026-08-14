# Multicamera merge with disjoint target and source tracks

## Condition

Port contains target track 4 at frame 0. Starboard contains source track 5 at frame 1. The other
camera does not initially contain the corresponding track.

## Procedure

Create a multicamera dataset from `media/multicamera`. Import the matching camera annotation files
and `three-level-forest.config.json`. Merge track 5 into track 4.

## Expected behavior

Track 4 exists in both cameras after the merge. Port keeps its frame-0 observation and
`camera = port-target`. Starboard keeps the former track-5 frame-1 observation and
`camera = starboard-source`. Both vectors contain `fish: 0.7` and `mammal: 0.8`. Track 5 is absent
after save and reload.
