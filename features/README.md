# Features

The **FEATURES phase is active**. DATA closed successfully at `DATA_PHASE_COMPLETE.md`; the exact input baseline is frozen in `provenance/data_phase_freeze_v0.json`.

Feature definitions and builders consume only canonical DATA-phase outputs. They must remain leakage-safe, preserve missingness, and fail closed when chronology or identity is ambiguous. Models may choose among shared features, but may not silently redefine a shared field or feature for their own convenience.

## Phase rules

- Verify the frozen DATA baseline before every shared feature build.
- Historical state for a target fight uses only information strictly available before the target cutoff.
- Do not infer same-day tournament fight order when canonical chronology does not prove it.
- Missing is not zero. Rate features retain/document their numerator and denominator or exposure.
- `RAW_QA_ONLY` sources do not feed shared predictive features.
- Sportsbook prices are not inputs to the independent core fighter-state/model feature set.
- No model training begins until the shared fighter-state and matchup feature contracts validate.

## Build order

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

Only after those shared features have chronological validation should the project move to the historical baseline and simple predictive Model 1.

## Current contract

`features/feature_contract_v0.json` is the machine-readable authority for the first fighter-state build. `features/v0/manifest.json` will bind materialized feature files back to the exact DATA freeze.
