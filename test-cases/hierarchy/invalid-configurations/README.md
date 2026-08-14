# Invalid type hierarchy configurations

## Inputs

The files cover a cycle, a non-object value, an empty child, an empty parent, a non-string parent,
and a self-edge.

## Expected behavior

A normal configuration import rejects each file without changing the stored hierarchy. Testing a
corrupt value that is already at rest requires `plant_type_hierarchy.py`, because supported DIVE
write paths reject these values before storage.
