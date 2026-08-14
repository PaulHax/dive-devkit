# Filtered export of raw confidence pairs

## Procedure

Create the baseline from `media/image-sequence`, `multipair.annotations.json`, and
`three-level-forest.config.json`. Change the checked type set, then export with Checked Types Only.

## Expected behavior

Export compares checked names with raw stored pair names. Checked raw pairs remain even when they
are not the resolved display type. Unchecked raw pairs are absent. Export filtering does not change
the stored tracks.
