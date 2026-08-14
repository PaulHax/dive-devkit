# Suppression regions on resolved types

## Condition

Track 1 fully covers track 2 on every frame. Track 1 stores `fish` first, but normally resolves to
`juvenile-red-snapper`.

## Expected behavior

A `fish` suppression region does not activate while track 1 resolves to the leaf. Unchecking
`juvenile-red-snapper` and `red-snapper` makes track 1 resolve to `fish`. Track 2 then disappears
from the canvas, list, and counts without a reload. Rechecking both types restores track 2.
