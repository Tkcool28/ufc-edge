# UFC Edge

Shared, leakage-safe UFC data and feature foundation for multiple models.

## Design rule

This repository separates source data from normalized data, shared features, and model-specific artifacts. A model must never rewrite or redefine the canonical data layer for its own convenience.

## Data layers

- `data/raw/` — immutable, source-faithful snapshots. Never hand-edit.
- `data/canonical/` — normalized UFC entities and one-fighter-per-fight history derived from raw data.
- `data/features/shared/` — pre-fight features that are reusable across models and obey the locked feature contract.
- `data/features/model_specific/` — transformations or features used by only one model.
- `schemas/` — source mappings, canonical schemas, feature definitions, missing-data rules, denominators, windows, and leakage rules.
- `provenance/` — exact upstream source revisions and file manifests.
- `pipelines/` — deterministic ingestion, normalization, and feature-building code.
- `tests/` — source, canonical, and no-look-ahead data-quality gates.

## Historical source v1

Greco1899's UFCStats scrape is the first pinned historical source. The initial snapshot is commit `8e40eb945e1127bf0ef172ab211a34787948f312` from 2026-08-18 UTC and is stored unchanged under `data/raw/greco1899/8e40eb945e11/` after Git-blob verification.

The selected raw set is event details, fight details, fight results, round-level fight stats, fighter identity, and fighter tale-of-the-tape data. Source provenance and expected hashes live in `provenance/greco1899.lock.json`; the imported snapshot carries its own SHA-256 manifest.

## Non-negotiable leakage rule

Every training feature for a fight must be computable using only information available strictly before that fight. Observed results/statistics from the target fight may be labels or future history only; they cannot be predictors for that target row.

## Current objective

Freeze the canonical feature specification, normalize/replay the selected historical source without look-ahead, and identify any feature families that require a second source before writing production prediction models.
