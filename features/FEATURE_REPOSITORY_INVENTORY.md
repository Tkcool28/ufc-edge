# Feature Repository Inventory — Governance V1 + F02

Governance baseline main: `d57038afcd356db0b76d2ce88c54ab5d626a6095`
PR #30 merge commit: `d57038afcd356db0b76d2ce88c54ab5d626a6095`
F02 base main after PR #31: `a672ac2022c49aa70aecdda9727862cf0554b0d2`

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

## Historical replay authority

F02 is a separate artifact/orchestration layer above F01; it does not redefine feature semantics. Its reviewed row schema distinguishes 96 fighter-specific F01 values per side, three shared fight-context values represented once, and five matchup interactions, for 200 model-eligible predictors.

- handoff/reproduction: `f02/README.md`
- replay contract: `f02/replay_contract_v1.json`
- target contract: `f02/target_contract_v1.json`
- frozen replay identity: `f02/F02_PREDICTOR_REPLAY_V1_COMPLETE.json`

The runtime matrices themselves are reproducible Parquet artifacts and are not committed.

## Runtime implementation

- aggregations: `src/ufc_edge/features/aggregations.py`
- PIT history: `src/ufc_edge/features/history.py`
- state/matchup implementation: `src/ufc_edge/features/state.py`
- F01 materializer/provenance: `src/ufc_edge/features/materializer.py`
- verified elapsed exposure: `src/ufc_edge/features/elapsed_exposure.py`
- governance validation: `src/ufc_edge/features/governance.py`
- F02 replay/chunk/schema/target implementation: `src/ufc_edge/features/replay.py`

## Tools

- `tools/features/materialize_v1.py`
- `tools/features/audit_elapsed_exposure_v1.py`
- `tools/features/generate_feature_reference.py`
- `tools/features/replay_f02.py`

## Tests

Feature tests cover F00 contract, F01 materialization/target guards, elapsed exposure, governance semantic regressions, and F02 temporal leakage, orientation, target separation, determinism, schema, restartability, and reference/optimized equivalence.

## Workflows

The feature-specific CI surfaces are:

- F00 Feature Contract
- F01 V1 Materializer
- Elapsed Exposure Normalization V1
- Feature Governance V1
- F02 Historical Predictor Replay V1

F02 CI performs focused tests, reference/optimized equivalence, a deterministic bounded real replay, frozen DATA/H00/H01 guards, runtime-artifact hygiene, and the gated full historical replay used to produce the frozen runtime artifact.

## Provenance dependencies

Feature and replay interpretation depends on the frozen DATA identity, canonical manifest, feature governance, and elapsed ruleset registry. These remain separate authorities so DATA, feature semantics, and generated replay artifacts remain distinguishable.

## Artifact policy

Committed:

- contracts;
- implementation;
- tests/workflow;
- concise handoff;
- F02 frozen replay identity metadata.

Not committed:

- full predictor Parquet matrices;
- target/modeling Parquet tables;
- temporary runs;
- profiling/log output;
- feature stores or model outputs.

## Quarantined prior art

Legacy v0 builders, contracts, generated matrices, feature-only runs/provenance, and archived workflows remain preserved but explicitly non-authoritative.

They are not moved because their current quarantine is already clear and moving large historical artifacts would create churn without improving semantic safety.

## Disagreements found and resolved

1. The pre-governance feature README was stale after PR #30: it still named contract 0.1.1-draft and said no safe elapsed source existed. Governance V1 corrected it.
2. “104 active V1 names” is the F01 executable definition surface, not the full catalog expansion. F00 declares 164 active variants when round-specific declarations are included.
3. After F02 was implemented, the governance-era top-level index/inventory still described historical replay as future work. This inventory now records the F02 contracts, implementation, tests, workflow, and freeze identity without changing any F01 feature semantics.

No undocumented semantic disagreement was resolved by guesswork.
