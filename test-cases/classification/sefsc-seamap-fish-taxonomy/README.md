# SEFSC-SEAMAP fish taxonomy

## Condition

This case contains a public 25.4-second video and its 24 real FishTrack23 tracks. The annotations
contain 983 detections across eight observed species. `config.json` contains the six direct parent
edges that apply to those annotation labels.

`seamap-taxonomy.reference.json` records the full source catalog: 147 classes and 73 derived direct
parent edges. It is a provenance reference, not the configuration file for these annotation labels.

## Procedure

1. Create a video dataset from `SEFSC-SEAMAP-761901231-Cam2.mp4` at 5 FPS.
2. Wait for video processing to finish.
3. Import `annotations.viame.csv`.
4. Import `config.json` as DIVE Configuration JSON.
5. Open the dataset and inspect the tracks and Type List.
6. Save and reload the dataset.

Verify: The dataset contains 24 tracks. It uses all eight observed species. The hierarchy includes
`seriola_rivoliana` → `seriola` → `carangidae`, and the same hierarchy remains after reload.

See `ATTRIBUTION.md` for the source, license, and publication citation.
