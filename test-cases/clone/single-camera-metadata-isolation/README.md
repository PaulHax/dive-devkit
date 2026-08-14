# Single-camera soft-clone metadata isolation

## Condition

A source dataset has nested metadata and a type hierarchy. DIVE creates a single-camera soft clone
from that source.

## Procedure

1. Create an image-sequence dataset from `media/image-sequence`.
2. Import `source.annotations.json` and `source.config.json`.
3. Create a single-camera soft clone.
4. Import `clone-replacement.config.json` into the clone.
5. Reopen the source dataset.

## Expected behavior

The source keeps its original hierarchy. Source and clone metadata are independent objects. A
nested change in one object does not change the other object.

Stored data supplies a user-level smoke test. The exact object-identity check uses the
`createSoftClone` server entry point because the user interface does not expose both live Girder
folder objects.
