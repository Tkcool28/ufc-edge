# Features

UFC Edge treats FEATURES as a versioned semantic system layered on frozen canonical DATA.

## Start here

Read these in order:

1. `FEATURE_CONTRACT.md` — authoritative F00 semantics, PIT rules, denominators, missingness, orientation, and shared architecture.
2. `feature_catalog.yaml` — authoritative machine-readable feature definitions and materialization declarations.
3. `feature_governance.json` — durable feature IDs, lifecycle, semantic/methodology versions, implementation locations, and replacement history.
4. `FEATURE_GOVERNANCE.md` — contributor rules for adding, changing, renaming, deprecating, or sourcing features.
5. `FEATURE_REFERENCE.md` — generated human-readable inventory.
6. `feature_inventory.json` — generated machine-readable inventory.
7. `f02/README.md` — F02 deterministic historical predictor replay contract, reproduction, target separation, and artifact policy.

Current feature contract: **0.1.2-draft**.
Current governance version: **1.0.0**.

Verified governed baseline after PR #31:

- 60 durable feature concepts in the shared catalog;
- 24 active V1 concepts;
- 104 F01-selected values;
- 99 fighter-state/context values + 5 matchup-interaction values;
- 164 catalog-declared active variants when round-specific declarations are included.

F02 expands the literal governed F01 matchup surface across both oriented fighters: 99 fighter/context values per side plus 5 matchup interactions = **203 row-level predictor columns**. It does not create model-private feature definitions.

The 104 vs 164 counts are intentionally different. F00 declares possible round-specific variants; F01 currently emits the narrower reviewed 104-value surface.

## Authority map

| Concern | Authority |
| --- | --- |
| Meaning, formula, eligibility, units, missingness | `feature_catalog.yaml` |
| Stable identity, lifecycle, methodology version | `feature_governance.json` |
| Vocabulary and forbidden semantic aliases | `terminology.json` |
| Predictor/target leakage rules | `leakage_registry.yaml` |
| Source/derived/consumer lineage | `dependencies.json` |
| Known missing source requirements | `data_requirements.json` |
| Simulator suitability and blockers | `simulator_requirements.json` |
| Evolution/migration history | `migrations/feature_migrations.json` |
| Runtime feature implementation | `src/ufc_edge/features/` |
| F02 replay/target contract | `f02/README.md`, `f02/replay_contract_v1.json`, `f02/target_contract_v1.json` |
| F02 frozen replay identity | `f02/F02_PREDICTOR_REPLAY_V1_COMPLETE.json` |
| Deterministic generated feature reference | `FEATURE_REFERENCE.md`, `feature_inventory.json` |

No model may create a private semantic definition for a concept that belongs in this shared layer.

## Current elapsed-exposure policy

PR #30 migrated the contract to `0.1.2-draft`.

Elapsed-time-normalized historical features may use only `ruleset_registry_v1`, with fail-closed bout/round eligibility from:

- `provenance/rulesets/elapsed_exposure_ruleset_registry_v1.json`
- `src/ufc_edge/features/elapsed_exposure.py`

There is still **no universal five-minute fallback**.

The six restored V1 primitives are:

- `sig_strike_flow`
- `knockdown_rate`
- `takedown_pressure`
- `control_rate`
- `submission_attempt_rate`
- `reversal_rate`

Generic `fighter_round_stats.control_sec` remains generic control. It is not top-position, ground-position, back-control, or exact positional duration.

## F01 V1 materializer

F01 remains the reference point-in-time materializer and semantic authority used by replay.

Runtime entry point:

```text
python tools/features/materialize_v1.py --validate-bounded
```

Persisted manifests include durable feature IDs, semantic/methodology versions, governance hash, dependency/terminology hashes, DATA freeze, canonical manifest, ruleset registry, feature catalog/schema, code commit, materialized columns, and prediction cutoff.

## F02 historical predictor replay

F02 is the shared historical predictor surface for future model families. It replays canonical target fights in deterministic `event_date -> event_id -> fight_id` order, uses the target event date as the prediction cutoff, inherits F01's strict prior-date rule, and excludes all same-date history rather than guessing bout order.

Runtime entry points:

```text
PYTHONPATH=src python tools/features/replay_f02.py inspect
PYTHONPATH=src python tools/features/replay_f02.py equivalence --equivalence-targets 16
PYTHONPATH=src python tools/features/replay_f02.py bounded --output-dir /tmp/ufc-edge-f02-bounded --attach-targets
PYTHONPATH=src python tools/features/replay_f02.py full --output-dir /tmp/ufc-edge-f02-full --attach-targets --resume
```

The frozen V1 identity is `f02/F02_PREDICTOR_REPLAY_V1_COMPLETE.json`. Full Parquet matrices remain reproducible runtime artifacts and are not committed to git. Labels are attached only after the predictor artifact is frozen.

## Generated reference

Regenerate after an approved governance/catalog change:

```text
python tools/features/generate_feature_reference.py
```

CI verifies the generated views are current:

```text
python tools/features/generate_feature_reference.py --check
```

Do not hand-edit generated reference files.

## Known missing-data foundation

The explicit registry is `data_requirements.json`.

The highest-priority simulator blocker is exact positional duration. Current data provide:

- exact generic `control_sec`;
- coarse FightMetric whole-minute position/TIP buckets.

Neither is equivalent to exact top/bottom/back/clinch/ground duration. That distinction is enforced by terminology/governance tests.

`DR_EXACT_POSITIONAL_DURATION_V1` remains unresolved and does **not** block F02 predictor replay.

## Quarantined pre-F00 prior art

The following remain **INACTIVE / QUARANTINED PRIOR ART**:

- `feature_contract_v0.json`
- `family_a_striking_v0.json`
- legacy `build_*_v0.py`, `validate_*_v0.py`, and coverage scripts
- `features/v0/` generated matrices/manifests
- `features/provenance/` old feature-only runs/audits
- `features/workflows/archive/`

They are preserved for archaeology only. They are not semantic authorities and cannot feed new models unless a reviewed migration explicitly promotes a concept.

## Frozen DATA boundary

FEATURES consumes canonical DATA and its provenance contract. It does not bypass DATA by reading provider-specific raw layouts.

Non-negotiable rules include:

- missing is not zero;
- no future leakage;
- same-day chronology is not invented;
- FightMetric round 0 is not a real round;
- quantized position buckets are not exact duration;
- generic control is not positional control;
- mutable rankings/profiles are point-in-time observations;
- ambiguous identities remain quarantined;
- betting odds/ROI/CLV are outside the core feature contract.

F02 historical replay is now a separate governed artifact layer above F01. Model training, opponent-adjustment implementation, and simulator implementation remain later milestones.
