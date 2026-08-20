# Raw Data

Raw data is immutable and source-faithful.

## Rules

- Never hand-edit a raw source file.
- Never overwrite an existing snapshot when upstream changes; create a new snapshot keyed by the new pinned commit.
- Every imported file must be verified against its source identity and listed in a manifest.
- Raw files may contain post-fight information. They are **not** model features until transformed through the canonical and feature layers with no-look-ahead enforcement.

## Greco1899 layout

Pinned Greco UFCStats snapshots live at:

`data/raw/greco1899/<source-commit-prefix>/`

The active source revision and expected Git blob SHAs are in `provenance/greco1899.lock.json`.
