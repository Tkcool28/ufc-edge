# M1 — Regularized Shared-Feature Winner Model V1 Validation Report

## Final status

**M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_COMPLETE**

**Verdict: M1_OUTPERFORMS_M0**

The broad, governed F02 predictor surface contains materially more chronologically stable winner signal than the compact frozen M0 baseline. M1 improved both primary metrics in aggregate and improved both log loss and Brier in **9 of 12** outer walk-forward folds.

This remains a model-quality result only. No odds, sportsbook, ROI, Kelly, price threshold, or market-target information entered M1.

## Authoritative evaluation

The accepted evaluation is GitHub Actions run **34718520686**, full-validation job **103620043254**, from pre-performance head:

`77ad61a954f3c845ba584cc55260c5e858436294`

Runtime artifact:

- name: `m1-regularized-shared-feature-winner-v1`
- artifact ID: `10305672641`
- ZIP SHA-256: `00fde41cff76fbc05aad8f6715babcea358636c4fe0e3267e34ff065748e33f8`
- runtime files: `m1_result.json`, `m1_oof_predictions.parquet`, `m1_coefficients.json`, and `m1_regularization_selection.json`

The M1 OOF logical SHA-256 is:

`d91ebe07db9569c8f47081ea78d1ed58d028bd2ba0df6ead51ba6ab73182447d`

## Aggregate result

| Metric | 50/50 | Frozen M0 | M1 | M1 vs M0 |
| --- | ---: | ---: | ---: | ---: |
| Log loss | 0.693147 | 0.664170 | **0.646334** | **-0.017836** |
| Brier | 0.250000 | 0.235893 | **0.226990** | **-0.008903** |
| Accuracy | 49.52% | 59.44% | **61.89%** | **+2.45 pp** |
| ROC AUC | 0.500000 | 0.634833 | **0.672769** | **+0.037936** |

M1 expected calibration error was **0.01809**.

The hard fighter-swap geometry check remained exact to numerical tolerance: maximum fold error was **2.22e-16**.

## Feature surface

F02 exposes 200 governed predictors. M1 mechanically audits that frozen schema rather than hand-selecting winners after seeing outcomes.

Three shared fight-context values remain diagnostic-only:

- scheduled rounds;
- title-bout status;
- weight class.

The model therefore consumes 197 source predictors:

- 96 mirrored fighter-side source pairs;
- two mirrored directional knockdown-interaction pairs;
- one already-oriented reach-difference value.

These become 197 antisymmetric numeric dimensions after fold-local preprocessing.

No fighter IDs, target fields, provenance identifiers, sportsbook fields, market probabilities, or post-fight information enter the matrix.

## Regularization result

The predeclared L2 grid was:

`C = [0.01, 0.1, 1.0, 10.0]`

Each outer fold selected C using only its training history through nested expanding chronological validation. Pooled inner-OOF log loss was the selection metric.

Selected values:

- **C=0.01 in 11 of 12 outer folds**
- **C=0.1 in 2016**
- C=1.0 and C=10.0 were never selected

That is useful evidence in its own right: the broader F02 surface adds signal, but it also needs strong shrinkage. The improvement is not evidence that every raw feature deserves a large coefficient; it is evidence that the shared governed surface, when strongly regularized, beats the compact baseline.

## Frozen M0 comparator incident

The first full M1 workflow, run **34718232000**, is not an accepted performance run.

The initial harness attempted to regenerate M0 raw probabilities with the unchanged M0 algorithm and then verify the frozen OOF hash. That guard failed:

- regenerated hash: `da240d23f271da550f4397e4c3c43159ed5d396d5e53886ac5217996d45649b0`
- frozen M0 hash: `708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c`

The correct response was **not** to weaken the hash or silently replace the frozen baseline. Raw floating-point model output can move under a later numerical/dependency solve even when the high-level algorithm is unchanged.

Before accepting any M1 result, the M1 comparator contract was changed to consume the authoritative M0 Actions artifact directly:

- M0 run: **34676508116**
- M0 artifact: **10292502486**
- M0 artifact ZIP SHA-256: `69e2a4db932ecbfd747a387b708d5107e3d682223d4f608b850a00a605af3be0`
- M0 OOF logical SHA-256: `708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c`

The successful M1 evaluation then loaded that artifact, verified its hash, aligned exact fight rows, and compared M1 against those frozen probabilities.

## Interpretation

M0 already established that the governed UFC representation contained real winner signal. M1 answers the next question: whether expanding from the compact M0 subset to the broad governed F02 surface helps under strict chronology and regularization.

It does.

The improvement is large enough to be meaningful rather than a rounding artifact:

- log loss improves by about **0.01784**;
- Brier improves by about **0.00890**;
- AUC rises by about **0.038**;
- accuracy rises by about **2.45 percentage points**;
- both primary metrics improve in **75% of outer folds**.

The result also remains weaker than a claim of betting edge. M1 has not been optimized against prices, and it has not seen the market. The next market comparison, when authorized, should treat the market as an external benchmark rather than feed it back into M1 training.

## Boundaries preserved

- F00/F01/F02 semantics were not changed.
- M0 was not changed.
- Frozen DATA was not changed.
- PR #34 and PR #60 market-diagnostic work was not modified.
- No sportsbook or market fields were used.
- No nonlinear challenger was introduced.
- No post-result feature pruning or C-grid expansion was performed.
- Runtime parquet/model artifacts remain outside git.

## Conclusion

**M1 passes its truth test.** The broader governed feature representation adds independent chronological predictive value over frozen M0 when constrained by strong L2 regularization.

The correct frozen verdict is:

**M1_OUTPERFORMS_M0**
