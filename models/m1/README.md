# M1 — Regularized Shared-Feature Winner Model V1

M1 is the next linear winner-probability benchmark after frozen M0. It tests whether the broader governed F02 feature surface materially improves out-of-sample UFC winner prediction without changing feature semantics or introducing market information.

## Fixed boundaries

- Consume frozen F02 1.0.1; do not rebuild historical features.
- Use the same UFC binary-winner population and 2010 modeling-era start as M0.
- Keep the annual 2015–2026 outer walk-forward unchanged.
- Model family is L2 logistic regression only.
- No random split, tree/boosting/ensemble/AutoML, opponent-adjustment work, simulator work, or outcome-driven feature selection.
- No sportsbook odds, market probabilities, ROI, Kelly, price thresholds, or market-diagnostic inputs.
- Runtime OOF predictions/models stay outside git.

## Broad shared-feature projection

F02 remains the authority for predictor eligibility through schema predictor=true.

M1 mechanically audits all 200 F02 predictors. The three shared fight-context predictors—scheduled rounds, title status, and weight class—remain diagnostic slice fields and are excluded from the model matrix because they do not provide a fighter-direction signal.

The remaining 197 source predictors are projected orientation-safely:

- 96 f1/f2 source pairs -> training-fold pooled-median value difference + missingness difference;
- four directional knockdown-matchup values -> two mirrored directional pairs, each projected to value difference + missingness difference;
- one already-oriented reach-difference matchup value -> direct antisymmetric value, with neutral-zero model-space imputation only when missing.

This yields 197 numeric model dimensions. Scaling is training-fold-only and scale-only (StandardScaler(with_mean=false)), and logistic regression uses no intercept. Swapping fighter presentation must negate the model input and produce complementary probability to numerical tolerance.

## Regularization

The only tuned quantity is L2 strength. The grid is frozen before M1 performance is observed:

C = [0.01, 0.1, 1.0, 10.0]

For each outer year, C is selected using only that outer training set with nested expanding chronological annual validation beginning in 2013. Selection uses pooled inner-OOF log loss; exact ties choose the smaller C.

## Frozen comparator

M1 loads the authoritative frozen M0 OOF artifact directly from Actions run 34676508116, artifact 10292502486 (ZIP SHA-256 69e2a4db932ecbfd747a387b708d5107e3d682223d4f608b850a00a605af3be0). Its M0 OOF logical SHA-256 must equal:

708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c

A mismatch is a hard failure rather than a new baseline. M0 probabilities are not numerically recomputed under a later dependency solve.

## Full validation

python tools/models/run_m1.py validate --f02-dir <f02-artifact-dir> --m0-dir <m0-artifact-dir> --output-dir <runtime-dir>

The full run writes m1_result.json, m1_oof_predictions.parquet, m1_coefficients.json, and m1_regularization_selection.json as runtime artifacts. Performance must not be used to revise the feature surface or C grid inside this task.
