# M1 — Regularized Shared-Feature UFC Winner Model V1

Status: **AUTHORITATIVE METHODOLOGY; CORRECTED BASELINE READY FOR FORMAL FREEZE**

M1 is the broad regularized winner-probability model over the governed F02 predictor replay. Current project authority is summarized in `../../PROJECT_STATUS.md`.

## Methodology boundary

- F02 replay schema `1.0.1` is the predictor source.
- M1 is market-blind: no odds, sportsbook probabilities, ROI, Kelly or betting thresholds enter training/model selection.
- Frozen surface projects the 200 F02 predictor columns into 197 governed numeric dimensions.
- Fighter-side features are paired antisymmetrically; model has no intercept; fighter swap must satisfy `P(swapped) = 1 - P(original)` to numerical precision.
- Outer validation is chronological 2015–2026 with chronological inner selection over the predeclared L2/elastic-net grid.
- Feature surface, preprocessing, fold plan, grid, selection rule, seed/solver configuration were held fixed for the corrected physical-profile rerun.

Detailed contracts remain in `feature_surface_v1.json`, `model_contract_v1.json`, `validation_plan_v1.json`, and `acceptance_gates_v1.json`.

## Current authoritative clean baseline

The corrected physical-profile DATA rerun is the current clean M1 performance estimate.

| Metric | Corrected M1 |
|---|---:|
| Log loss | `0.649120128` |
| Brier | `0.229025402` |
| Accuracy | `62.1045%` |
| ROC AUC | `0.665905862` |

2026 partial (`N=329`): log loss `0.630602667`, Brier `0.220613882`, accuracy `63.22%`, ROC AUC `0.695153533`.

Status: **AUTHORITATIVE M1 BASELINE — READY FOR FORMAL FREEZE**.

The repository-organization inventory found no committed corrected-M1 completion/freeze marker equivalent to the established model-freeze convention. Do not silently manufacture one here. Current machine/status label: `CORRECTED_M1_READY_FOR_FREEZE_MARKER`.

## Historical original M1

Status: **HISTORICAL — TEMPORALLY CONTAMINATED BY REACH-AVAILABILITY LEAKAGE**.

The original validation remains important audit evidence, but is not authoritative for current M1 performance. The primary confirmed leakage surface was:

`pair::ctx__physical_size_profile__reach_cm::missing_diff`

The reach measurement itself was not the defect. Historical present/missing availability encoded future UFC career persistence/profile completeness.

Permanent rule: missingness/data availability must independently satisfy point-in-time safety even when a static attribute value can be safely backfilled.

Evidence/governance:

- PR #65 — corrected physical-profile F01/F02 rebuild + exact frozen M1 rerun;
- PR #66 — physical-profile correction diagnostic;
- PR #67 — full missingness temporal-leakage audit + governance;
- `../../governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md`.

## Runtime outputs

Large OOF predictions, coefficients, ablations and comparison matrices remain GitHub Actions runtime artifacts rather than committed large files. Preserve historical artifacts; their status determines authority.

## What is not M1 authority

M1B, tree/boosted challengers, opponent-adjusted models, feature-pruned variants and market/betting models are separate future work and are not started or made authoritative by repository cleanup.
