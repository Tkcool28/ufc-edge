# M1 — Regularized Shared-Feature UFC Winner Model V1

M1 is the first broad, serious winner-probability model over the governed F02 predictor replay.

## Current authority

The **original historical M1 result is not authoritative** because historical reach present/missing availability encoded future UFC career persistence/profile completeness.

The authoritative M1 baseline is the controlled **corrected physical-profile rerun using unchanged M1 V1 methodology**.

Formal freeze marker:

`models/m1/M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_CORRECTED_FROZEN.json`

Corrected M1 prediction artifact/content SHA256:

`5eaa09e82787cae0e3a198d31b0c19573557c94f0faf9302a582023c44a39b78`

Formal corrected-M1 OOF logical SHA256:

`7e6a08a6a4013630239986360654ad0963a1f242dae9acd7b172ee5a321384e6`

Corrected aggregate metrics:

- log loss: `0.649120128`
- Brier: `0.229025402`
- accuracy: `62.1045%`
- ROC AUC: `0.665905862`

The permanent model-independent comparison surface is Validation Terrain V1 under:

`governance/model_validation_bucket_v1/`

Future winner-model challengers must compare against corrected M1 on the same frozen V1 terrain where applicable. Future MOV models must use the same permanent V1 environments where applicable, but must be compared with an appropriate frozen MOV baseline once one exists; KO/TKO, submission, and decision probabilities are not directly benchmarked against M1 winner probabilities.

For project-level model-development discipline and the long-term betting objective, see:

`docs/MODELING_RESET_CHECKLIST.md`

## Boundary

- M0 remains permanently frozen and is consumed only as the comparison benchmark.
- Corrected F02 is the authoritative predictor source for the frozen corrected M1 record.
- The model is developed market-blind: no historical odds, sportsbook probabilities, market residuals, ROI, or betting thresholds enter feature selection, preprocessing, model selection, or acceptance.
- M1 contains only L2 and elastic-net logistic regression.
- The corrected rerun did not change M1 methodology.

## Frozen feature surface

`feature_surface_v1.json` was frozen before outcome evaluation.

It discovers the 200 F02 predictors from schema metadata (`predictor == true`) and projects them as follows:

- 192 fighter-side columns -> 96 semantic pairs.
- Each fighter pair emits an imputed signed value difference and a missingness difference.
- Four directional knockdown matchup columns -> two signed pair differences plus two missingness differences.
- `mx__reach_difference_cm` remains a signed antisymmetric value with zero imputation.
- `scheduled_rounds`, `ctx__title_bout`, and `ctx__weight_class` are symmetric context and remain diagnostic-only.

Final M1 V1 dimension: **197**.

## Chronological selection

For each outer year 2015–2026:

1. outer training contains only earlier fights;
2. the two immediately preceding calendar years are used as chronological inner validation folds;
3. only inner chronological log loss selects among the frozen L2 / elastic-net grid;
4. preprocessing is fit inside each training period;
5. the winning regularization specification is refit on all permitted outer history;
6. the outer year is predicted once.

Development is 2015–2023. Confirmation is 2024, 2025, and 2026 partial. The procedure and numerical acceptance gates were frozen in committed JSON before confirmation was evaluated.

## Orientation contract

All model inputs are antisymmetric and the logistic model has no intercept. Therefore fighter swap must satisfy, to numerical precision:

`P(swapped) = 1 - P(original)`

Focused tests enforce the projection and probability complement contracts.

## Corrected-M1 provenance

- PR #65 — corrected physical-profile F01/F02 rebuild + exact frozen-M1 rerun
- PR #66 — read-only correction diagnostic
- PR #67 — missingness temporal-leakage audit and governance
- PR #70 — permanent model-independent validation terrain + corrected-M1 calibration diagnostic

The confirmed original-M1 leakage surface was:

`pair::ctx__physical_size_profile__reach_cm::missing_diff`

The underlying static reach value was not itself the defect. The unsafe historical availability state was the defect.

## Runtime outputs

Full OOF predictions, fold coefficients, ablations, and large validation results are GitHub Actions runtime artifacts rather than committed model matrices. Durable hashes and authoritative identities are pinned in the corrected-M1 freeze marker and validation-terrain manifests.
