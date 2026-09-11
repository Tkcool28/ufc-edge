# Feature Repository Inventory — Governance V1

Baseline main: `d57038afcd356db0b76d2ce88c54ab5d626a6095`  
PR #30 merge commit: `d57038afcd356db0b76d2ce88c54ab5d626a6095`

This is the human-readable repository-surface inventory paired with `repository_inventory.json`.

## Authoritative semantic contract

- `FEATURE_CONTRACT.md`
- `feature_catalog.yaml`
- `feature_schema.json`
- `leakage_registry.yaml`
- `src/ufc_edge/features/contract.py`

## Governance authority

- `feature_governance.json`
- `terminology.json`
- `dependencies.json`
- `data_requirements.json`
- `simulator_requirements.json`
- `migrations/feature_migrations.json`
- `FEATURE_GOVERNANCE.md`

## Runtime implementation

- aggregations: `src/ufc_edge/features/aggregations.py`
- PIT history: `src/ufc_edge/features/history.py`
- state/matchup implementation: `src/ufc_edge/features/state.py`
- materializer/provenance: `src/ufc_edge/features/materializer.py`
- verified elapsed exposure: `src/ufc_edge/features/elapsed_exposure.py`
- governance validation: `src/ufc_edge/features/governance.py`

## Tools

- `tools/features/materialize_v1.py`
- `tools/features/audit_elapsed_exposure_v1.py`
- `tools/features/generate_feature_reference.py`

## Tests

Feature tests cover F00 contract, F01 materialization/target guards, elapsed exposure, and governance semantic regressions.

## Workflows

The current feature-specific CI surfaces are F00 contract validation, F01 materializer validation, elapsed-exposure validation, and governance V1 validation.

## Provenance dependencies

Feature interpretation depends on the frozen DATA identity, canonical manifest, and elapsed ruleset registry. These remain outside the feature-definition files so DATA and interpretation layers remain distinguishable.

## Quarantined prior art

Legacy v0 builders, contracts, generated matrices, feature-only runs/provenance, and archived workflows remain preserved but explicitly non-authoritative.

They are not moved in this milestone because their current quarantine is already clear and moving large historical artifacts would create churn without improving semantic safety.

## Disagreements found and resolved

1. The pre-task feature README was stale after PR #30: it still named contract 0.1.1-draft and said no safe elapsed source existed. It is corrected in this branch.
2. “104 active V1 names” is the F01 executable surface, not the full catalog expansion. F00 declares 164 active variants when round-specific declarations are included. Governance now records both numbers explicitly.

No undocumented semantic disagreement was resolved by guesswork.
