# Type hierarchy seed data

Covers the `sefsc-seamap` and `hierarchical-classification` seed entries.

## Static data, not generated
`seed/seamap-taxonomy.json` (147 classes) and `seed/sefsc-seamap-hierarchy.json` are checked in.
They are derived from the public VIAME SEFSC-SEAMAP add-on by `tools/derive_seamap_taxonomy.py`,
which range-reads a 120 KB `train_info.json` out of a 2.4 GB archive without downloading it. Run
that by hand only when the add-on is republished — **the seeder never calls it**, so seeding stays
off that endpoint.

Parents come from the taxonomic codes in the class labels (genus zeroes the last two digits, family
the last four). Five digits crosses a level boundary and yields false parents —
`BODIANUSPULCHELLUS -> SCIAENIDAE`, a wrasse under a drum family. The model's own class graph ships
with every edge list empty, so there is no upstream hierarchy to copy.

## Malformed-hierarchy scenarios
DIVE validates the hierarchy on every write and rejects malformed ones, but returns stored metadata
verbatim on read so the viewer can report corruption. So a corrupt-state dataset must be planted
through Girder's generic metadata endpoint, which is what a seed entry's `plantTypeHierarchy` does
(the seeder then re-reads `dive_dataset/<id>` and fails if the malformed value did not survive).
Flip a seeded dataset to another payload without reseeding:
```bash
uv run --with girder-client --no-project python dive-devkit/tools/plant_type_hierarchy.py \
  <folderId> dive-devkit/.generated/hierarchical-classification/self-edge.config.json
```
The viewer then prompts `The saved type hierarchy is invalid: <reason>. …` on the next load.
Note DIVE only *marks* a dataset folder for deletion, so a deleted seed folder still blocks its
name until the cleanup task runs — rename it if you need to reseed the same name immediately.
