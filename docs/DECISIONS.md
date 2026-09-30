# UFC EDGE — Architecture Decision Log

Status: **AUTHORITATIVE DECISION INDEX**

Short ADR-style records for decisions future agents should not rediscover.

## D001 — Canonical/provider boundary
**Decision:** provider-specific vocabulary stops at adapters/canonicalization. Downstream features/models consume governed canonical meanings.

## D002 — Static physical attributes may be backfilled under governed semantics
**Decision:** stable physical attributes may be recovered/backfilled when source semantics and identity are governed. This does not automatically make historical availability/missingness safe.

## D003 — Missingness requires independent point-in-time safety
**Decision:** missingness and data availability are predictive surfaces and must independently satisfy PIT safety. See `governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md`.

## D004 — Mutable acquisition is separated from deterministic consumption
**Decision:** live UFCStats or other mutable acquisition may be used only through controlled evidence capture; canonical/model builds consume pinned governed evidence.

## D005 — Preserve invalidated historical model evidence
**Decision:** do not delete original M1 or other important invalidated/superseded experiments. Label authority explicitly.

## D006 — F02 is shared infrastructure, not a model
**Decision:** F02 is deterministic historical replay/predictor infrastructure shared by model families.

## D007 — M0 remains the permanent small winner baseline
**Decision:** preserve M0 as a compact frozen empirical benchmark even when stronger models exist.

## D008 — Shared M1 feature representation changes require explicit authorization
**Decision:** corrective DATA work and repository cleanup do not silently prune/redesign/outcome-shop M1 features.

## D009 — Corrected M1 is formally frozen
**Decision:** PR #71 committed `models/m1/M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_CORRECTED_FROZEN.json`; corrected M1 is the authoritative frozen M1 V1 winner baseline. Original M1 performance remains historical/contaminated.

## D010 — Repository organization favors indexes over mass path churn
**Decision:** preserve stable code/artifact paths where relocation could break workflows, tests, historical references or provenance. Move only through a separately reviewed reference-complete migration.

## D011 — Validation Terrain V1 is permanent and model-independent
**Decision:** reuse the frozen assignment unchanged across model comparisons. Changed thresholds/sources require an explicit V2; model outcomes do not redefine V1 terrain.

## D012 — MOV0 V1 is a frozen STANDARD_FINISH model
**Decision:** the accepted PR #73 run establishes useful STANDARD_FINISH-vs-decision probability signal. MOV0-MIN establishes the central incremental signal; MOV0-FULL incremental gain beyond MIN is not established.

## D013 — Post-freeze diagnostics explain; they do not tune
**Decision:** PRs #111/#112/#113 may characterize calibration, terrain, feature behavior and archetypes using frozen evidence and explicitly guarded recovery mechanics. They do not authorize feature selection, threshold optimization, recalibration or retraining.

## D014 — Stale branches/PRs are not continuity authority
**Decision:** current status/index/freeze records outrank old draft PR descriptions, old branches and legacy handoffs. Superseded original-M1 PRs #61/#62 must not be revived as current M1 authority; paused market PRs #34/#60 require an explicit market-phase decision.
