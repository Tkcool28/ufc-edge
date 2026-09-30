# UFC EDGE — Project Status

Status: **AUTHORITATIVE**  
Snapshot date: **2026-09-30**  
Authoritative main at audit start: `0618a21e21002be9999d34f6997be659ca8ff224`  
Current phase: **repository continuity refresh before next model-type authorization**

> Fresh sessions: read this file first, then `PROJECT_MAP.md`, `docs/MASTER_MILESTONES.md`, `docs/DECISIONS.md`, and `docs/MODELING_RESET_CHECKLIST.md`. Always verify current `main` before changing anything.

## Repository identity

Repository: `Tkcool28/ufc-edge`

The accepted foundation now includes corrected frozen M1, permanent Validation Terrain V1, frozen MOV0 STANDARD_FINISH V1, and three merged MOV0 post-freeze diagnostics.

Old draft PRs, old branches, root handoffs and runtime artifacts are not authority merely because they are detailed or newer-looking.

## Authoritative DATA / feature foundation

- DATA status: `RECENT_PHYSICAL_PROFILE_COMPLETE_FROM_GOVERNED_PRIMARY_SOURCES`.
- F00: frozen feature contract/governance.
- F01: frozen point-in-time fighter-state methodology.
- F02: frozen deterministic historical predictor replay, schema `1.0.1`; **not a model**.
- Corrected F02 logical SHA256: `2d1a367416e105ed6fe546eb8590ae7b555dd044304ad0ba40c7945420599ba0`.
- Corrected F02 table SHA256: `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`.

Physical-profile recovery remains governed and pinned before deterministic canonical/model consumption. Repository-local nulls do not prove a live source is null.

## Permanent Validation Terrain V1

Status: **FROZEN / MODEL-INDEPENDENT**.

Rule: **same historical terrain, different model.**

Entry point: `governance/model_validation_bucket_v1/`.

Key identities:

- assignment logical SHA256: `a23b138ea103a751ae988cce5f90369b265547bfeec1c0e708484b4428015665`
- assignment physical SHA256: `8b59c09e103997e4c6d6311608620e7178962aac0cdf807dfa9d1740c7aa6d97`
- contract SHA256: `23bb56aa33116b126c73054396ad3a08c16d04481226985e246224d21b3f1aac`
- percentile-reference SHA256: `c5a54e23e61c5b59f6e7c44c4de2c19652bdd664733001b126cddd41d66f89aa`

Changed thresholds/sources require a deliberate V2.

## Authoritative models

### M0

Status: **PERMANENT FROZEN SMALL EMPIRICAL WINNER BASELINE**.

Entry: `models/m0/`.

### M1 original

Status: **HISTORICAL — TEMPORALLY CONTAMINATED BY REACH-AVAILABILITY LEAKAGE**.

Primary confirmed leakage surface:

`pair::ctx__physical_size_profile__reach_cm::missing_diff`

The reach value itself was not the defect; historical availability/missingness carried future-derived information.

### M1 corrected

Status: **AUTHORITATIVE FROZEN M1 V1 WINNER BASELINE**.

Freeze marker:

`models/m1/M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_CORRECTED_FROZEN.json`

Key identities:

- corrected M1 prediction artifact/content SHA256: `5eaa09e82787cae0e3a198d31b0c19573557c94f0faf9302a582023c44a39b78`
- corrected M1 OOF logical SHA256: `7e6a08a6a4013630239986360654ad0963a1f242dae9acd7b172ee5a321384e6`

Aggregate metrics: log loss `0.649120128`, Brier `0.229025402`, accuracy `62.1045%`, ROC AUC `0.665905862`.

Provenance: PRs #65, #66, #67, #70 and formal freeze PR #71.

### MOV0 — STANDARD_FINISH probability

Status: **FROZEN FIRST RUN COMPLETE — CLEAR_SUCCESS**.

Purpose:

`P(STANDARD_FINISH)`, where STANDARD_FINISH = KO/TKO or submission rather than decision.

Contract: PR #72 / `models/mov0/`.  
Implementation + first frozen run: PR #73.  
Closeout: `MOV0_STANDARD_FINISH_PROBABILITY_V1_REPORT.md` and `MOV0_STANDARD_FINISH_PROBABILITY_V1_COMPLETE.json`.

OOF population: 4,260 fights, 2018–2026.

Key aggregate log loss:

- B0: `0.693459672`
- B1: `0.683561010`
- MOV0-MIN: `0.670238307`
- MOV0-FULL: `0.669477686`

The central accepted finding is that MOV0-MIN added chronologically persistent finish-vs-decision signal beyond B1 (9/9 favorable outer years; both preregistered bootstrap intervals favorable). MOV0-FULL's incremental gain beyond MIN was small/mixed and not established by its uncertainty intervals.

No sportsbook data, ROI/EV optimization, post-hoc feature changes, MOV1 or simulator work was part of MOV0 V1.

## Merged MOV0 post-freeze diagnostics

These explain the frozen MOV0 result; they do **not** redefine or retrain it.

- PR #111 — probability-bucket calibration diagnostic.
- PR #112 — confidence terrain + feature-behavior diagnostic, including guarded coefficient-recovery refit only to reproduce frozen OOF probabilities.
- PR #113 — conditional feature interaction + fight-archetype diagnostic. Durable evidence is under `docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/`.

Diagnostic runners live under `tools/diagnostics/`. Additional committed diagnostic evidence lives under `models/mov0/diagnostics/`.

## Permanent major findings

1. Static attribute backfill does **not** make historical missingness safe.
2. Missingness/data availability must independently satisfy point-in-time safety.
3. Original-M1 reach-availability missingness was temporally unsafe; original performance is historical only.
4. Invalidated/superseded evidence is preserved and labeled rather than erased.
5. Corrected M1 is the frozen clean winner baseline.
6. Validation Terrain V1 is immutable and model-independent.
7. MOV0 establishes useful finish-vs-decision probability signal, primarily through the MIN surface.
8. Broader MOV0-FULL incremental value beyond MIN is not established.
9. Post-freeze diagnostics are explanatory evidence, not permission to tune the frozen model.
10. Thin cells and high-missingness terrain remain sample-governed caution areas.

## Open / stale work inventory

Open PRs as of this snapshot:

- #34 — historical/paused M0 bare-bones market diagnostic.
- #60 — historical/paused M0 The Odds API replication diagnostic.
- #61 — superseded original-M1 implementation/performance draft.
- #62 — superseded broad original-M1 draft/methodology provenance.

Do not merge/revive #61 or #62 as current M1 work. Do not resume #34/#60 without a deliberate market-phase authorization.

Numerous merged historical branches remain. Branch pruning is a separate maintenance action and should only follow exact reachability/dependency checks.

## Repository organization rule

Current organization policy is **indexes first, minimal path churn**.

Legacy root handoffs/logs remain where they are because scripts, workflows, PR descriptions or old chats may refer to stable paths. Nothing should be moved solely for aesthetics. If relocation is worthwhile, first produce an exact reference map and migration plan, update all consumers atomically, run relevant tests/workflows, and only then review the move.

See `docs/REPOSITORY_CONTINUITY_AUDIT_2026-09-30.md`.

## Modeling reset / project objective

Living reference: `docs/MODELING_RESET_CHECKLIST.md`.

Long-term objective:

> Produce trustworthy, calibrated pre-fight probabilities that can eventually be compared honestly with sportsbook prices to make better UFC fight and method-of-victory betting decisions, including knowing when confidence should be reduced or a fight should be passed.

Predictive model construction remains separated from market/ROI evaluation until an explicitly authorized market phase.

## Next action

Finish/review this repository continuity refresh, then return to MASTER/PM to define the exact next modeling question.

No next model family is authorized by this cleanup itself. In particular, do not silently start M1B, MOV1, tree/boosted challengers, opponent adjustment, feature selection, recalibration, simulator work or market optimization merely because the repository is ready for another phase.
