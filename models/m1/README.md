# M1 — Regularized Shared-Feature UFC Winner Model V1

M1 is the first broad, serious winner-probability model over the frozen governed F02 predictor replay.

## Boundary

- M0 remains permanently frozen and is consumed only as the comparison benchmark.
- F02 replay schema `1.0.1` is the sole predictor source.
- The model is developed market-blind: no historical odds, sportsbook probabilities, market residuals, ROI, or betting thresholds enter feature selection, preprocessing, model selection, or acceptance.
- This task contains only L2 and elastic-net logistic regression.

## Frozen feature surface

`feature_surface_v1.json` is frozen before outcome evaluation.

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

Development is 2015–2023. Confirmation is 2024, 2025, and 2026 partial. The procedure and numerical acceptance gates are frozen in committed JSON before confirmation is evaluated.

## Orientation contract

All model inputs are antisymmetric and the logistic model has no intercept. Therefore fighter swap must satisfy, to numerical precision:

`P(swapped) = 1 - P(original)`

Focused tests enforce the projection and probability complement contracts.

## Runtime outputs

Full OOF predictions, fold coefficients, ablations, and final validation results are GitHub Actions runtime artifacts and are not committed as large matrices/models.
