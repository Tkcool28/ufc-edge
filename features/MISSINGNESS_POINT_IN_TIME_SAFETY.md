# Missingness Point-in-Time Safety

Status: additive governance rule for UFC EDGE feature/model review.

## Rule

**Missingness and data availability must be audited independently for point-in-time safety.**

A feature value can be historically valid while the fact that the value is present or absent in a reconstructed dataset can still depend on information that accumulated after the prediction cutoff.

The following assumption is prohibited:

> Static attribute backfill means missingness is safe.

Static attributes may be backfilled when their semantic contract permits it, but the historical availability state must be evaluated separately.

## Known reference case: physical-profile reach

The corrected physical-profile M1 diagnostic established that historical reach missingness encoded future UFC career persistence/profile completeness. In the exact 2015-2018 correction-specific subset, the reach-known side won 94.6% of fights and had more future UFC fights in 93.7% of cases, while actual completed reach advantage did not explain the effect.

The underlying reach measurement was not the leakage surface. The historical present/missing state was.

## Required review for every new or materially changed feature family

Review both the feature value and its availability state.

1. State the exact information cutoff for the value.
2. State what causes the value to be missing, unavailable, ineligible, or unsupported.
3. Determine whether present/missing status can depend on later profile enrichment, future roster persistence, later source coverage, identity reconciliation, or any other post-cutoff process.
4. If the model receives missingness explicitly or implicitly, measure its target association separately from the value.
5. Compare suspicious availability states against pre-fight career/support facts and future career facts.
6. Check era concentration. Sparse historical-source eras require special scrutiny.
7. Where values can be completed without changing their historical semantics, test whether the completed value itself explains the target separation.
8. Preserve a point-in-time-safe negative control so the diagnostic does not mistake legitimate prior-history support for leakage.
9. Document source mechanism and provenance requirements.
10. Do not repair or remove a feature inside a leakage audit unless a separate repair task explicitly authorizes it.

## Leakage classifications

- `POINT_IN_TIME_SAFE`: no evidence that the modeled availability state materially depends on future information, with implementation/provenance consistent with the prediction cutoff.
- `POTENTIAL_TEMPORAL_LEAKAGE`: suspicious future association or source-coverage behavior exists but evidence is not decisive.
- `CONFIRMED_TEMPORAL_LEAKAGE`: the availability/missingness state demonstrably encodes information unavailable at the prediction cutoff.
- `NOT_A_MISSINGNESS_FEATURE`: initially flagged surface does not actually represent availability/missingness.

## Support counts are not automatically leakage

Counts of prior UFC fights, prior observed rounds, or prior attempts can be legitimate predictors when they are computed strictly from evidence available before the target fight. Future-career association alone is not sufficient to classify a feature as leakage. The implementation and time boundary must be part of the judgment.

## Review trigger

This check is required before freezing a new model baseline whenever the modeled surface introduces or materially changes:

- explicit missingness flags;
- imputation plus missingness indicators;
- source-availability indicators;
- profile-completeness indicators;
- support/sample counts;
- source-dependent eligibility;
- identity/source fallback indicators;
- reconstructed historical metadata whose completeness can improve later.

The audit evidence must be reproducible from frozen artifacts and must not mutate the model or data being audited.
