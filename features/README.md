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

Current feature contract: **0.1.2-draft**.
Current governance version: **1.0.0**.

Verified merged-main baseline after PR #30:

- 60 durable feature concepts in the shared catalog;
- 24 active V1 concepts;
- 104 F01-selected values;
- 99 fighter-state/context values + 5 matchup-interaction values;
- 164 catalog-declared active variants when round-specific declarations are included.

The last two counts are intentionally different. F00 declares possible round-specific variants; F01 currently emits the narrower reviewed 104-value surface.

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
| Runtime implementation | `src/ufc_edge/features/` |
| Deterministic generated reference | `FEATURE_REFERENCE.md`, `feature_inventory.json` |

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

F01 remains the reference point-in-time materializer.

Runtime entry point:

```text
python tools/features/materialize_v1.py --validate-bounded
```

Persisted manifests now include durable feature IDs, semantic/methodology versions, governance hash, dependency/terminology hashes, DATA freeze, canonical manifest, ruleset registry, feature catalog/schema, code commit, materialized columns, and prediction cutoff.

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

Historical replay, model training, opponent-adjustment implementation, and simulator implementation remain separate milestones.
