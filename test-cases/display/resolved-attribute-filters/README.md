# Attribute filters on resolved types

## Contents

The fixture contains the three-track hierarchy baseline. Track 1 has
`LeafTrackMarker = juvenile-track`, and each of its detections has
`LeafDetectionMarker = juvenile-detection`.

## Data invariant

Track 1 stores `fish` first but resolves to `juvenile-red-snapper` with the default checked types
and thresholds. The two markers make track-level and detection-level filtering distinguishable.
