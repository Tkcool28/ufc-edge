# F01 — Point-in-Time Fighter State

Status: **AUTHORITATIVE LAYER GUIDE**

F01 materializes **fighter state as known before a target fight** under F00 feature semantics.

## Core rule

Only information available strictly before the target fight may contribute. Same-day chronology is not invented.

## Entry points

- contract/materializer documentation: `F01_MATERIALIZER.md`
- governed definitions: `FEATURE_CONTRACT.md`, `feature_catalog.yaml`, `feature_governance.json`
- implementation: `../src/ufc_edge/features/` and task-specific tools referenced by `README.md`
- tests: `../tests/features/`

## Methodology status

F01 methodology is frozen for the corrected physical-profile experiment. Corrected physical-profile DATA was propagated through the existing F01 methodology; the cleanup task does not modify logic.

## Downstream

F02 deterministically replays F01 across historical target fights to produce the shared predictor dataset.
