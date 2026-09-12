# M1 — Regularized Shared-Feature Winner Model V1 Validation Report

## Final status

**M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_COMPLETE**

**Verdict: M1_OUTPERFORMS_M0**

The broad, governed F02 predictor surface contains materially more chronologically stable winner signal than the compact frozen M0 baseline. M1 improved both primary metrics in aggregate and improved both log loss and Brier in **9 of 12** outer walk-forward folds.

This remains a model-quality result only. No odds, sportsbook, ROI, Kelly, price threshold, or market-target information entered M1.

## Authoritative evaluation

The accepted evaluation is GitHub Actions run **34718520686**, full-validation job **103620043254**, from accepted evaluation head:

`77ad61a954f3c845ba584cc55260c5e858436294`

The M1 feature/model/regularization methodology was already frozen at `c109fd01dbb9da05ce120aecc7907da46df87296` before any accepted performance result. A successful precursor performance-bearing run later occurred at `45f080dec8438d619d28a559d16f57fb6011ceca`; after that, only frozen-M0 row-key normalization and comparator/provenance documentation changed. M1 features, model family, C grid, nested selection rule, and validation population did not change.

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

M1 expected calibration error was **0.01809**, versus **0.01465** for frozen M0. So calibration-bin ECE became slightly worse even while the proper probability scores (log loss and Brier) improved materially.

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


## Outer-fold stability

| Fold | M0 log loss | M1 log loss | M0 Brier | M1 Brier | Primary-metric result |
| --- | ---: | ---: | ---: | ---: | --- |
| 2015 | 0.67048 | **0.59364** | 0.23903 | **0.20594** | both better |
| 2016 | 0.66500 | **0.62152** | 0.23641 | **0.21859** | both better |
| 2017 | 0.66914 | **0.63946** | 0.23825 | **0.22520** | both better |
| 2018 | 0.66717 | **0.64889** | 0.23734 | **0.22876** | both better |
| 2019 | 0.68013 | **0.66644** | 0.24321 | **0.23708** | both better |
| 2020 | **0.66640** | 0.66823 | **0.23692** | 0.23713 | both worse |
| 2021 | 0.66190 | **0.65785** | 0.23480 | **0.23268** | both better |
| 2022 | 0.65913 | **0.65651** | 0.23336 | **0.23252** | both better |
| 2023 | **0.65793** | 0.66165 | **0.23313** | 0.23450 | both worse |
| 2024 | 0.66433 | **0.63490** | 0.23636 | **0.22208** | both better |
| 2025 | **0.65970** | 0.66058 | 0.23331 | **0.22318** | mixed |
| 2026* | 0.64283 | **0.64223** | 0.22586 | **0.22477** | both better |

\* 2026 is partial in frozen F02.

The aggregate gain is therefore not universal. **2020 and 2023 are regressions on both primary metrics**, and **2025 is mixed**. The predeclared stability gate still passes because 9/12 folds improve both primary metrics.

## Predefined diagnostic weaknesses

### Light Heavyweight remains weak

Light Heavyweight improves versus M0 but remains close to an uninformative probability benchmark:

| Model | N | Log loss | Brier | Accuracy | AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen M0 | 412 | 0.70117 | 0.25353 | 52.43% | 0.5459 |
| M1 | 412 | **0.69489** | **0.25032** | **54.61%** | **0.5788** |

That is not a reason to retune M1 after the fact. It is a real slice-level failure point to carry forward.

### Missingness dependence needs later robustness work

The largest mean absolute coefficient across the 12 outer models is:

`pair::ctx__physical_size_profile__reach_cm::missing_diff`

Mean coefficient: **-0.6552**, negative in **12/12** folds.

This is not target leakage under the chronological, training-fold-local construction. But it does mean the model is using **data availability itself** as a strong predictor. That could encode real historical/roster structure, source coverage patterns, or both. Before any production promotion, this deserves a dedicated missingness/data-quality robustness audit rather than being silently treated as ordinary fight signal.

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


## Floating-point reproducibility note

A successful precursor full-validation run, **34718491353** at head `45f080dec8438d619d28a559d16f57fb6011ceca`, produced the same substantive result:

- log loss: 0.646334387319501
- Brier: 0.2269899882350201
- verdict: **M1_OUTPERFORMS_M0**
- OOF logical SHA-256: `9c367452cd494d9f46e9ff2215448a8b8510fdcec57dec2bdd60bf308c587e89`

The accepted run produced log loss 0.646334387315568 and Brier 0.226989988232787, but a different OOF logical SHA-256.

The differences are at floating-point noise scale (roughly 1e-11 or smaller in aggregate metrics), and M1 methodology did not change between these runs. Still, this means **bitwise raw-probability rerun determinism has not been demonstrated** for the hosted logistic solve. The authoritative identity is therefore the accepted Actions artifact and its frozen OOF hash, not an assertion that a future rerun must reproduce every floating-point bit.

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
- After the first successful performance-bearing run, only M0 comparator row-key/provenance handling changed; M1 feature/model/regularization methodology did not.
- Runtime parquet/model artifacts remain outside git.

## Conclusion

**M1 passes its truth test.** The broader governed feature representation adds independent chronological predictive value over frozen M0 when constrained by strong L2 regularization.

The correct frozen verdict is:

**M1_OUTPERFORMS_M0**
