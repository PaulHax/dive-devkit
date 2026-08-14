# Disjoint multicamera tracks

## Contents

Port contains track 4 at frame 0 with `camera = port-target`. Starboard contains track 5 at frame 1
with `camera = starboard-source`. The other camera does not contain the corresponding track.

## Data invariant

Track 4 stores `fish: 0.7`, and track 5 stores `mammal: 0.8`. The observations and attributes are
camera-local, while the two confidence vectors are complementary.
