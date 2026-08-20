# Data Directory

This directory contains source data and reproducible source-neutral data products. Feature definitions and model code live at the repository root, not inside `data/`.

## `raw/`

Immutable source snapshots exactly as acquired. Each provider gets one namespace; each changing source gets a pinned revision or timestamped snapshot. Source-specific layout rules live in `raw/README.md`.

Raw provider names and formats are allowed here. Nothing in `raw/` is assumed to be canonical, historically safe, or model-ready.

## `canonical/`

Source-neutral UFC entities and histories that satisfy `schemas/canonical_data_contract_v0.*`.

A canonical field has one repository-wide meaning regardless of source. Provider adapters may map different source fields into that concept, but downstream consumers never redefine it.

Current data-phase rule: **do not promote a raw observation merely because it downloaded successfully.** Identity, units, null semantics, duplicates/conflicts, temporal meaning, and provenance must pass the canonicalization gates first.

## `derived/`

Reserved for reproducible non-feature data products built from canonical data when they are useful for operations or QA—for example compact snapshots, crosswalk exports, or coverage tables.

`derived/` must not become a hidden feature layer. Predictive feature definitions/builders belong in top-level `features/` during the later feature phase.

## Navigation rule

Raw and canonical data live here; explanations generally do not.

- source locks/status/research conclusions -> `../provenance/`
- data contracts and source-adapter rules -> `../schemas/`
- acquisition/normalization/audit code -> `../pipelines/`
- machine diagnostics -> `../provenance/runs/`
- later feature code/definitions -> `../features/`
- later model code -> `../models/`

Do not create additional nested documentation trees under `data/`.
