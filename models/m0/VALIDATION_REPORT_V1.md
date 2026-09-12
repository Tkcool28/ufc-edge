# M0 Empirical UFC Winner Baseline V1 — Validation Report

**Status:** M0_EMPIRICAL_WINNER_BASELINE_V1_COMPLETE  
**Verdict:** **M0_SIGNAL_CONFIRMED**

## Dataset

- Frozen F02 rows: **9,252**
- UFC target rows: **8,769**
- UFC binary-eligible rows: **8,617**
- Primary modeling era: **2010-01-01 onward**
- Modeling-era rows: **7,367**
- Out-of-fold validation rows (2015–2026): **5,626**
- Overall UFC binary fighter_1 win rate: **49.24%**, consistent with no suspicious lexicographic orientation advantage.

The 2010 start was selected from counts and feature coverage before M0 performance was observed.

## Feature set

M0-C uses five governed durable concepts:

- `FS_PRIOR_FIGHT_COUNT_V1`
- `CTX_AGE_AT_FIGHT_V1`
- `CTX_LAYOFF_DAYS_V1`
- `FS_SIG_STRIKE_EFFICIENCY_V1`
- `FS_TAKEDOWN_CONVERSION_V1`

These map to 14 exact F02 fighter-side source columns. Each pair is transformed inside the training fold to an antisymmetric value difference plus an antisymmetric missingness difference. Imputation uses one pooled training-fold median per pair. Standardization is scale-only (`with_mean=false`) and training-fold-only. Logistic regression is fixed L2, `C=1.0`, `fit_intercept=false`.

No outcome-driven feature selection was performed.

## Aggregate metrics

| Baseline | Log loss | Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|
| 50/50 | 0.69315 | 0.25000 | 49.52% | 0.5000 |
| Empirical experience | 0.69489 | 0.25087 | 48.81% | 0.4947 |
| Regularized logistic | **0.66417** | **0.23589** | **59.44%** | **0.6348** |

The empirical experience-only baseline does **not** beat 50/50. The compact multivariable logistic model does, materially, on both primary probability metrics.

## Walk-forward folds

| Fold | Validation rows | Logistic log loss | Logistic Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|---:|
| 2015 | 464 | 0.67048 | 0.23903 | 56.25% | 0.6129 |
| 2016 | 479 | 0.66500 | 0.23641 | 59.29% | 0.6288 |
| 2017 | 444 | 0.66914 | 0.23825 | 59.68% | 0.6242 |
| 2018 | 469 | 0.66717 | 0.23734 | 59.06% | 0.6306 |
| 2019 | 503 | 0.68013 | 0.24321 | 57.26% | 0.6064 |
| 2020 | 440 | 0.66640 | 0.23692 | 59.77% | 0.6297 |
| 2021 | 490 | 0.66190 | 0.23480 | 59.39% | 0.6417 |
| 2022 | 503 | 0.65913 | 0.23336 | 61.03% | 0.6505 |
| 2023 | 500 | 0.65793 | 0.23313 | 60.40% | 0.6415 |
| 2024 | 504 | 0.66433 | 0.23636 | 57.94% | 0.6199 |
| 2025 | 501 | 0.65970 | 0.23331 | 60.88% | 0.6550 |
| 2026* | 329 | 0.64283 | 0.22586 | 63.53% | 0.6819 |

`* 2026 is partial through 2026-08-15 in the frozen F02 artifact.`

**All 12 folds improve both log loss and Brier versus 50/50.**

## Calibration

Overall ECE: **0.01465**.

| Probability bin | N | Mean predicted | Actual win rate |
|---|---:|---:|---:|
| 0.00–0.20 | 12 | 18.12% | 33.33% |
| 0.20–0.30 | 174 | 26.64% | 22.41% |
| 0.30–0.40 | 879 | 35.97% | 35.27% |
| 0.40–0.45 | 805 | 42.61% | 41.99% |
| 0.45–0.50 | 956 | 47.54% | 46.34% |
| 0.50–0.55 | 996 | 52.51% | 50.70% |
| 0.55–0.60 | 804 | 57.35% | 58.33% |
| 0.60–0.70 | 818 | 63.99% | 65.53% |
| 0.70–0.80 | 176 | 73.21% | 78.98% |
| 0.80–1.00 | 6 | 81.93% | 50.00% |

The central probability mass is well behaved for a first baseline. The extreme bins are too small for strong interpretation.

## Predefined slices

### History depth

| Slice | N | Log loss | Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|---:|
| Zero-history | 1,091 | 0.67166 | 0.23936 | 58.75% | 0.6190 |
| Sparse history | 1,578 | 0.65911 | 0.23358 | 60.20% | 0.6453 |
| Established history | 2,957 | 0.66410 | 0.23585 | 59.28% | 0.6357 |

Zero-history means no prior canonical history for at least one fighter; it is **not** called a professional debut.

### Fight length and title

Three-round fights: log loss 0.66396, Brier 0.23579, N=5,073.  
Five-round fights: log loss 0.66606, Brier 0.23680, N=553.  
Non-title: log loss 0.66429, Brier 0.23596, N=5,386.  
Title: log loss 0.66138, Brier 0.23445, N=240.

### Important weak slice

Light Heavyweight is materially weaker: **N=412, log loss 0.70117, Brier 0.25353, accuracy 52.43%, AUC 0.5459**. This does not invalidate the global M0 result, but it is a real diagnostic to preserve for later model work.

## Coefficient stability

Stable directions across all 12 folds:

- Age difference: negative in 12/12 folds — older relative age lowers fighter_1 probability.
- Prior-fight-count difference: positive in 12/12.
- Career significant-strike accuracy difference: positive in 12/12.
- Career significant-strike defense difference: positive in 12/12.
- Career takedown-defense difference: positive in 12/12.

Less stable / weak:

- Layoff difference: negative 8/12, positive 4/12.
- Career takedown-success difference: negative 9/12, positive 3/12, small mean magnitude.

These are diagnostics only; no feature was removed or retuned after observing them.

## Orientation sanity

Maximum fold swap-complement error: **2.22e-16**. The arbitrary fighter_1/fighter_2 presentation is therefore not acting as directional signal in M0-C.

## OOF artifact

- Rows: **5,626**
- Logical SHA-256: `708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c`
- Runtime artifact ID: `10292502486`
- Runtime ZIP SHA-256: `69e2a4db932ecbfd747a387b708d5107e3d682223d4f608b850a00a605af3be0`

The prediction parquet and temporary fold outputs are **not committed**.

## Verdict

**M0_SIGNAL_CONFIRMED**

The governed F02 representation contains real, chronologically forward UFC winner signal with a deliberately compact linear model. The gain is not dependent on one validation year: all 12 annual outer folds beat 50/50 on both primary metrics.

This earns the project the right to proceed to a stronger shared-feature model after independent review. It does **not** imply that M0 is a production model, that every weight class is equally modeled, or that sportsbook edge has been established.

## Limitations

- M0 is validation-only; no production model is created.
- M0 intentionally ignores most of the 200-predictor F02 surface.
- 2026 is a partial latest-year validation fold.
- The requested external-history target slice is not reconstructed because the F02 predictor table does not carry the needed row-level flag; rebuilding history semantics inside M0 would violate the F02-consumer boundary.
- Tiny extreme calibration bins are not interpretable.
- Light Heavyweight is a clear weak slice worth preserving for future diagnosis.
- No sportsbook/market comparison was performed.

## Self-review

**Did M0 remain simple enough that poor performance would be interpretable?**

**YES.**
