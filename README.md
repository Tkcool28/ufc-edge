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

## Current source candidate

Historical UFCStats scrape from `Greco1899/scrape_ufc_stats`, pinned before ingestion to an exact upstream commit. Raw files are preserved unchanged; all parsing and modeling decisions live downstream.

## Non-negotiable leakage rule

Every training feature for a fight must be computable using only information available strictly before that fight. Current/career aggregate fields may be retained for provenance or QA but must not enter historical training rows.

## Current objective

Freeze the canonical feature specification and prove the selected historical source supports its required raw fields before writing production prediction models.
