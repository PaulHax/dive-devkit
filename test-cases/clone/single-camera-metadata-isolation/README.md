# Single-camera soft-clone metadata isolation

## Contents

`source.annotations.json` contains the three-track single-camera baseline. `source.config.json`
contains its hierarchy and nested configuration data. `clone-replacement.config.json` contains a
smaller replacement hierarchy.

## Data invariant

The source and replacement configurations differ below the top metadata object. This makes a
shared nested object distinguishable from an independent metadata copy.
