# UFC EDGE — DATA

Status: **AUTHORITATIVE DATA NAVIGATION**

This directory contains source evidence and reproducible source-neutral DATA products. Current overall authority is summarized in `../PROJECT_STATUS.md`.

## `raw/`

Immutable/source-faithful snapshots and pinned acquisition evidence. Provider-specific names/formats are allowed here. Raw data are not automatically canonical, historically safe, or model-ready.

Recent UFCStats physical-profile recovery evidence is pinned under `raw/ufcstats_live_recovery/` where applicable.

## `canonical/`

Source-neutral UFC entities/histories satisfying canonical contracts under `../schemas/`.

At the repository-organization snapshot the committed canonical package remains under `canonical/v0/`. The corrected physical-profile reconciliation workflow builds the corrected canonical package deterministically at runtime from governed/pinned inputs; do not infer that absence of a committed `v1/` directory means the correction is unauthoritative.

## `supplemental/`

Governed recovery/enrichment evidence used to close gaps that cannot be justified from the existing canonical/source layer alone. Supplemental evidence must preserve source identity/provenance and does not bypass canonical semantics.

Current recent physical-profile status: `RECENT_PHYSICAL_PROFILE_COMPLETE_FROM_GOVERNED_PRIMARY_SOURCES`.

Recovery precedence:

`existing canonical/governed source -> UFC Official null-fill -> pinned live UFCStats recovery -> governed supplemental recovery -> null`

## `derived/`

Reproducible non-feature DATA products useful for QA/operations. This must not become a hidden feature layer.

## Critical live-source rule

**Repository-local missingness does not prove live-source missingness.** For unresolved recent UFCStats physical-profile gaps, the controlled recovery architecture may query live UFCStats separately.

Network acquisition and canonical consumption are intentionally separated:

- network state is mutable;
- acquisition may use live sources;
- acquired evidence is pinned/governed;
- canonical builds consume pinned evidence offline/deterministically.

Do not make canonical/model builds depend directly on an unpinned mutable website response.

## Navigation

- source locks/status/research conclusions -> `../provenance/`
- source/canonical contracts -> `../schemas/`
- acquisition/normalization/reconciliation -> `../pipelines/`
- feature definitions/replay -> `../features/`
- model contracts/results -> `../models/`
- current state -> `../PROJECT_STATUS.md`
