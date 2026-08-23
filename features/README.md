# Features

The FEATURES phase is now deliberately open.

## Authoritative F00 contract

F00 defines architecture and validation only. It does **not** materialize production feature matrices or train models.

Authoritative F00 files:

- `features/FEATURE_CONTRACT.md` — human-readable architecture and self-review
- `features/feature_catalog.yaml` — shared feature concepts, variants, targets, windows and policies
- `features/feature_schema.json` — machine schema/enums for the catalog
- `features/leakage_registry.yaml` — explicit predictor/target and point-in-time leakage rules
- `src/ufc_edge/features/contract.py` — lightweight fail-closed loader/validator
- `tests/features/test_feature_contract.py` — contract tests

Feature contract version: `0.1.0-draft`.

The future shared feature flow is:

```text
frozen canonical DATA
→ point-in-time fighter state
→ deterministic matchup join
→ matchup interactions/context
→ model-selected catalog subset
→ targets attached only in training tables
```

Normal feature inputs are `data/canonical/v0/` plus the frozen DATA semantic/provenance contract needed to interpret those tables. Feature code does not read provider-specific raw layouts. Sportsbook odds and betting-performance fields are not core feature inputs.

## Quarantined pre-F00 prior art

Everything listed below predates the deliberate F00 architecture task and remains **INACTIVE / QUARANTINED PRIOR ART**. It is preserved so work is not lost, but it is not authoritative and may not be consumed by new feature materializers unless a later reviewed task explicitly migrates a concept into the F00 contract.

- `features/feature_contract_v0.json`
- `features/family_a_striking_v0.json`
- `features/build_fighter_state_primitives_v0.py`
- `features/validate_fighter_state_primitives_v0.py`
- `features/build_striking_environment_v0.py`
- `features/validate_striking_environment_v0.py`
- `features/audit_striking_environment_coverage_v0.py`
- `features/v0/` — accidental materialized outputs/manifests
- `features/provenance/` — accidental feature-only audits/run logs
- `features/workflows/archive/` — disabled copies of former feature workflows

The old files do not define current naming, window, denominator, shrinkage, orientation, or model-consumption policy. Where old ideas remain useful, they are restated explicitly in the new F00 contract.

## Frozen DATA boundary

DATA closed at `DATA_PHASE_COMPLETE.md`; the immutable baseline is `provenance/data_phase_freeze_v0.json`.

F00 inherits these non-negotiable rules:

- missing is not zero;
- no future leakage;
- display-name-only identity is not trusted;
- FightMetric `round=0` is not a real round;
- FightMetric position/TIP values retain quantized bucket semantics and are never fabricated as exact seconds;
- exact `control_sec` is authoritative where canonical and is not synonymous with ground time;
- rankings and mutable profiles are point-in-time observations;
- no canonical judge-round score history currently exists;
- exact knockdown recovery, finish-after-knockdown sequences, exact ground/standing minutes and exact state-transition chronology are not directly observed;
- weigh-in annotations are used only when their semantics are source-explicit;
- ambiguous identities remain quarantined.

## Feature-phase rules

- Concepts come before materialized columns.
- Fighter state remains opponent-independent; matchup interactions are separate.
- All predictive concepts declare an information cutoff.
- Every rate declares numerator/denominator semantics and zero/missing behavior.
- Recent/EWMA/round variants are opt-in, not automatically multiplied across the catalog.
- Small-sample shrinkage preserves the distinction between a true debutant and missing historical coverage.
- Historical opponent adjustment must use the opponent's strictly pre-contest state; future opponent career information is forbidden.
- Model subsets are selected with consumer/status tags from one shared catalog; models may not silently redefine shared features.
- `RAW_QA_ONLY` sources and `data/raw/` do not feed predictive features.
- Betting odds, implied probabilities, line movement, ROI and CLV are outside the core feature contract.

No production feature materialization or modeling should begin until F00 is reviewed and the next FEATURES task is explicitly authorized.
