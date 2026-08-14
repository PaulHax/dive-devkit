# Invalid type hierarchy configurations

## Contents

The directory contains one configuration for each rejected shape: a cycle, a non-object value, an
empty child, an empty parent, a non-string parent, and a self-edge.

## Data invariant

Each file isolates one normalization failure. Supported DIVE write paths reject these values before
storage; `plant_type_hierarchy.py` remains available for corrupt-at-rest scenarios.
