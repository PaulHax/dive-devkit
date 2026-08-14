# DIVE classification test cases

This catalog defines deterministic inputs for DIVE classification behavior. Directory names
describe the input condition or the invariant under test.

## Media provenance

The generated JPEG images come from NOAA Okeanos Explorer EX1402 dive 11. Wikimedia Commons
distributes the source clip as CC0 1.0 public-domain media. All annotations and configuration files
are synthetic.

## Directory map

| Directory | Condition or invariant |
| --- | --- |
| `classification/single-camera-linked-types` | One camera imports and preserves valid hierarchy data. |
| `classification/multicamera-linked-types` | Matching camera tracks import and preserve equal hierarchy data. |
| `classification/sefsc-seamap-fish-taxonomy` | A public video imports 24 real tracks and the observed SEAMAP hierarchy. |
| `coco/rle-mask-warning-aggregation` | More than one COCO input produces an unsupported-mask warning. |
| `clone/single-camera-metadata-isolation` | A soft clone has metadata that is independent from its source. |
| `hierarchy/valid-three-level-forest` | A valid hierarchy resolves complete confidence vectors. |
| `hierarchy/invalid-configurations` | Invalid hierarchy shapes and edges are rejected. |
| `multicamera/divergent-classification-replicas` | Linked camera tracks start with different vectors. |
| `multicamera/disjoint-track-merge` | The merge target and source start in different cameras. |
| `kwcoco/exact-confidence-pairs-round-trip` | A valid DIVE extension preserves order, sparse membership, and zero values. |
| `kwcoco/empty-confidence-pairs-extension` | An empty DIVE extension falls back to standard KWCOCO fields. |
| `display/resolved-attribute-filters` | Type-specific attributes use the resolved display type. |
| `display/resolved-suppression-regions` | Suppression uses the resolved display type. |
| `export/raw-confidence-pair-filtering` | Filtered export operates on raw stored pair names. |

Set manifests under `sets/` select cases without changing the case directories. The hierarchical
classification set supplies the current archive selection.

The builder adds media and JSON inputs to the selected directory structure. Run it from the devkit
root:

```bash
python3 tools/build_test_case_archive.py \
  --manifest test-cases/sets/hierarchical-classification.json
```

The command creates `.generated/test-data/classification/` and
`.generated/test-data/classification.zip`. Both outputs are ignored by Git. `SHA256SUMS` covers
every file in the generated directory.
