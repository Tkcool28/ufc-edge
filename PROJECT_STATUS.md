# UFC EDGE — Project Status

Status: **AUTHORITATIVE**
Snapshot date: **2026-09-17**
Authoritative main before this freeze branch: `3ccf11d4f804f66845a385c0ce7013634e616d97`
Current phase: **corrected M1 foundation freeze before next model-development phase**

> Fresh sessions: read this file first, then `PROJECT_MAP.md`, `docs/MASTER_MILESTONES.md`, `docs/DECISIONS.md`, and `docs/MODELING_RESET_CHECKLIST.md`. Always verify current `main` before changing anything.

## Repository identity

Repository: `Tkcool28/ufc-edge`

PR #70 is merged and establishes the permanent model-independent Validation Terrain V1. Old draft PRs and old branches are historical evidence, not authority.

Historical/parallel draft PRs #34, #60, #61, and #62 predate the current authoritative corrected foundation and must not be reused as current authority without deliberate review.

## Authoritative DATA

Status: `RECENT_PHYSICAL_PROFILE_COMPLETE_FROM_GOVERNED_PRIMARY_SOURCES`.

Physical-profile recovery order:

`existing canonical/governed source -> UFC Official null-fill -> pinned live UFCStats recovery -> governed supplemental recovery -> null`

Network acquisition is separated from canonical consumption. Live UFCStats recovery is pinned as evidence before deterministic/offline canonical consumption. Repository-local nulls do **not** prove the live source is null.

The committed canonical tree remains rooted at `data/canonical/v0/`; the corrected physical-profile reconciliation/replay workflow constructs the corrected canonical package deterministically at runtime from governed evidence. See `data/README.md`, `data/supplemental/`, `data/raw/ufcstats_live_recovery/`, and the physical-profile reconciliation pipeline/workflows.

## Authoritative feature stack

### F00 — feature contract/governance

Purpose: feature definitions, semantics, versioning, provenance and safety rules.
Methodology: **frozen unless an explicit feature-contract migration is authorized**.
Entry points: `features/FEATURE_CONTRACT.md`, `features/FEATURE_GOVERNANCE.md`, `features/README.md`.

### F01 — point-in-time fighter state

Purpose: materialize fighter state as known strictly before a target fight.
Methodology: **frozen for the corrected physical-profile foundation**.
Entry points: `features/F01_MATERIALIZER.md`, F01 tests/builders referenced by `features/README.md`.

### F02 — historical predictor replay

Purpose: deterministic historical replay of F01 across canonical fights:

`canonical fight -> strict pre-fight cutoff -> F01 states -> deterministic matchup predictors -> predictor artifact -> labels attached afterward`

F02 is **not a model**. It is the shared predictor surface consumed by models.

Corrected authoritative F02 identities for corrected M1:

- predictor logical SHA256: `2d1a367416e105ed6fe546eb8590ae7b555dd044304ad0ba40c7945420599ba0`
- table SHA256: `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`

## Authoritative validation terrain

Status: **PERMANENT MODEL-INDEPENDENT VALIDATION TERRAIN V1**.

Rule:

> Same historical terrain, different model.

Entry point:

`governance/model_validation_bucket_v1/`

Key frozen identities:

- assignment logical SHA256: `a23b138ea103a751ae988cce5f90369b265547bfeec1c0e708484b4428015665`
- assignment physical SHA256: `8b59c09e103997e4c6d6311608620e7178962aac0cdf807dfa9d1740c7aa6d97`
- contract SHA256: `23bb56aa33116b126c73054396ad3a08c16d04481226985e246224d21b3f1aac`
- percentile-reference SHA256: `c5a54e23e61c5b59f6e7c44c4de2c19652bdd664733001b126cddd41d66f89aa`

V1 assignments and percentile references are immutable. Changed thresholds or sources require a deliberate V2.

## Authoritative models

### M0

Status: **PERMANENT FROZEN SMALL EMPIRICAL BASELINE**.

M0 uses a small governed five-concept subset of F02 and remains the comparison/reference baseline. See `models/m0/README.md` and its committed completion/validation records.

### M1 — original historical model

Status: **HISTORICAL — TEMPORALLY CONTAMINATED BY REACH-AVAILABILITY LEAKAGE**.

The original M1 result is preserved for audit history, but its performance is not the authoritative performance estimate. The primary confirmed leakage surface was:

`pair::ctx__physical_size_profile__reach_cm::missing_diff`

The reach value itself was not the defect. Historical present/missing availability encoded future UFC career persistence/profile completeness.

### M1 — corrected physical-profile baseline

Status: **AUTHORITATIVE FROZEN M1 V1 BASELINE**.

Formal freeze marker:

`models/m1/M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_CORRECTED_FROZEN.json`

Corrected M1 prediction artifact/content SHA256:

`5eaa09e82787cae0e3a198d31b0c19573557c94f0faf9302a582023c44a39b78`

Formal corrected-M1 OOF logical SHA256:

`7e6a08a6a4013630239986360654ad0963a1f242dae9acd7b172ee5a321384e6`

Corrected aggregate metrics:

| Metric | Corrected M1 |
|---|---:|
| Log loss | `0.649120128` |
| Brier | `0.229025402` |
| Accuracy | `62.1045%` |
| ROC AUC | `0.665905862` |

2026 partial (`N=329`):

| Metric | Corrected M1 |
|---|---:|
| Log loss | `0.630602667` |
| Brier | `0.220613882` |
| Accuracy | `63.22%` |
| ROC AUC | `0.695153533` |

Calibration benchmarks:

- Validation Terrain V1 pick-confidence ECE (confidence-bin weighted absolute pick-calibration gap): `0.013465680`
- corrected-rerun probability-bin ECE: `0.015328076`
- calibration slope: `1.059266713`
- calibration intercept: `-0.020275341`
- governed calibration report SHA256: `1fcf0898321fc30d57cc5e5743231cbbf82b323567e30c7ec75177dfb6d35ccb`

Provenance:

- PR #65 — controlled corrected physical-profile rerun
- PR #66 — correction diagnostic
- PR #67 — missingness temporal-safety audit
- PR #70 — permanent validation terrain and corrected-M1 calibration diagnostic

## Permanent major findings

1. Static attribute backfill does **not** make historical missingness safe.
2. Missingness/data availability must be audited independently for point-in-time safety.
3. `pair::ctx__physical_size_profile__reach_cm::missing_diff` was the primary confirmed original-M1 leakage surface.
4. Invalidated historical evidence is preserved, labeled, and never silently deleted.
5. Corrected M1 probabilities are broadly well calibrated overall.
6. `GRAPPLE_TWO_SIDED` is a named corrected-M1 diagnostic stress-test, not an isolated model-selection target.
7. High-missingness fights remain a harder population.
8. Thin validation cells remain sample-governed and must not drive conclusions.

Active missingness rule:

`governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md`

## Modeling reset / project objective

Living reference:

`docs/MODELING_RESET_CHECKLIST.md`

This document is intentionally revisable. It exists to prevent model proliferation from becoming the project objective.

Long-term project objective:

> Produce trustworthy, calibrated pre-fight probabilities that can eventually be compared honestly with sportsbook prices to make better UFC fight and method-of-victory betting decisions, including knowing when confidence should be reduced or a fight should be passed.

Predictive model construction remains separated from market/ROI evaluation until an explicitly authorized market phase.

## Open/deferred work

Not automatically authorized by this freeze:

- M1B;
- tree/boosted challengers;
- opponent adjustment;
- feature pruning/selection;
- new feature families;
- betting simulation or market integration.

## Next approved action

Return to MASTER/PM for explicit next-model planning using corrected M1 and Validation Terrain V1 as the frozen foundation.

Do not begin M1B or another challenger merely because the foundation is frozen. First define the exact question the next model is intended to answer and how success will be judged on the permanent terrain.
