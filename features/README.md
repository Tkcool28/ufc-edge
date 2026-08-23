# Features

> **STATUS: INACTIVE / QUARANTINED AFTER DATA-PHASE BOUNDARY CORRECTION.**
>
> The files under `features/` were created after `DATA_PHASE_COMPLETE.md` even though the originating chat was intended to perform DATA acquisition/foundation work only. They are preserved here so no work is lost, but **feature engineering is stopped**. Nothing in this directory is part of the frozen DATA baseline, and no feature workflow is active under `.github/workflows/`.

DATA closed successfully at `DATA_PHASE_COMPLETE.md`; the exact immutable input baseline is frozen in `provenance/data_phase_freeze_v0.json`.

All accidental feature-specific code, outputs, audits, run logs, contracts, and archived workflow definitions are intentionally contained under this `features/` tree. The global `data/`, `schemas/`, `pipelines/`, `src/ufc_edge/data/`, and `provenance/` namespaces remain the DATA foundation.

## If/when FEATURES is deliberately resumed

Feature definitions and builders must consume only canonical DATA-phase outputs. They must remain leakage-safe, preserve missingness, and fail closed when chronology or identity is ambiguous. Models may choose among shared features, but may not silently redefine a shared field or feature for their own convenience.

### Phase rules

- Verify the frozen DATA baseline before every shared feature build.
- Historical state for a target fight uses only information strictly available before the target cutoff.
- Do not infer same-day tournament fight order when canonical chronology does not prove it.
- Missing is not zero. Rate features retain/document their numerator and denominator or exposure.
- `RAW_QA_ONLY` sources do not feed shared predictive features.
- Sportsbook prices are not inputs to the independent core fighter-state/model feature set.
- No model training begins until the shared fighter-state and matchup feature contracts validate.

### Preserved accidental build order/design

1. **Fighter state primitives v0** — canonical observed history, career/recent-3/recent-5/calendar-EWM windows, exact lineage and missing-safe domain exposures.
2. **Feature Family A — Striking environment** — pace, creation and prevention.
3. **Feature Family B — Wrestling environment** — creation and prevention.
4. **Feature Family C — Submission environment** — creation and prevention.
5. **Feature Family D — Durability**.
6. **Feature Family E — Cardio / persistence** with round-specific behavior.
7. **Feature Family F — Finish profile**, including explosive vs pressure/cumulative finishing indicators.
8. **Feature Family G — Context**.
9. **Opponent adjustment** — phase-specific performance relative to opponent expectation.
10. **Matchup interaction engine** — explicit KO, submission, decision and environment-control interactions.

Only after an explicit decision to reopen FEATURES should this work continue.

## Current preserved feature artifacts

- `features/feature_contract_v0.json`
- `features/family_a_striking_v0.json`
- `features/build_fighter_state_primitives_v0.py`
- `features/validate_fighter_state_primitives_v0.py`
- `features/build_striking_environment_v0.py`
- `features/validate_striking_environment_v0.py`
- `features/audit_striking_environment_coverage_v0.py`
- `features/v0/` — materialized accidental feature outputs and manifests
- `features/provenance/` — feature-only audits and run logs
- `features/workflows/archive/` — disabled copies of the former GitHub Actions workflows

These artifacts are **not raw data, not canonical DATA tables, and not part of the DATA freeze**.
