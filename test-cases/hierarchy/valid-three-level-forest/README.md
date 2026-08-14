# Valid three-level type hierarchy

## Contents

`multipair.annotations.json` contains three tracks with full confidence vectors.
`three-level-forest.config.json` contains fish, tuna, and dolphin branches with up to three levels.

## Data invariant

Track 2 stores `bluefin-tuna: 0.9`, `tuna: 0.2`, and `fish: 0.8`. Those non-monotone values support
leaf, parent, and root resolution without changing the stored vector.
