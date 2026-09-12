# M0-MD0 Validation Report V0

**Status:** M0_MARKET_DIAGNOSTIC_V0_COMPLETE  
**Verdict:** **MARKET_COMPLEMENTARY**

## Frozen input

- M0 OOF rows: **5,626**
- M0 OOF logical SHA-256: `708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c`
- M0 probability unchanged: **YES**

## Market source

V0 uses the pinned public `theGholland/ufc-data_with_random_forests` historical listed-odds dataset, whose upstream market source is documented as `betmma.tips`. Line observation timing is not established, so these prices are **historical listed odds, timing unspecified** and are not called opening or closing lines. The market data remain diagnostic-only and outside canonical DATA.

- source file SHA-256: `064d0b7bd94dd894d675180e4ebf8860f1925ac0193f7bbd4c30041db92489bf`
- odds format: decimal
- raw implied probability: `1 / decimal_odds`
- de-vig: proportional normalization
- cross-book aggregation: not applicable; one listed source
- fixed blend: `0.5 * M0 + 0.5 * market`

## Matching

- M0 OOF rows: **5,626**
- matched rows: **3,363**
- matched share: **59.78%**
- matched range: **2015-01-03 through 2023-12-16**
- unmatched M0 rows: **2,263**
- ambiguous external-name rows rejected: **22**
- unresolved external-name rows rejected: **719**
- invalid-odds rows rejected: **53**
- conflicting duplicate groups: **0**

Matched rows by year:

| Year | Rows |
|---|---:|
| 2015 | 395 |
| 2016 | 418 |
| 2017 | 360 |
| 2018 | 365 |
| 2019 | 409 |
| 2020 | 296 |
| 2021 | 355 |
| 2022 | 395 |
| 2023 | 370 |

## Same-sample metrics

| Probability | Log loss | Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|
| 50/50 | 0.693147 | 0.250000 | 48.59% | 0.500000 |
| M0 | 0.666653 | 0.237065 | 59.29% | 0.629424 |
| Market | 0.616480 | 0.214158 | 65.33% | 0.717391 |
| Fixed 50/50 blend | 0.629057 | 0.219200 | 66.22% | 0.713072 |

Market ECE on the matched sample: **0.018633**.

The raw historical listed market is clearly stronger than M0 on this matched population. The fixed 50/50 blend improves materially on M0 but does **not** beat the market alone.

## Correlation and disagreement

- Pearson: **0.465742**
- Spearman: **0.455141**
- mean absolute probability difference: **0.130828**
- median absolute probability difference: **0.115837**

| Absolute difference | Rows |
|---|---:|
| <0.05 | 744 |
| 0.05–0.10 | 742 |
| 0.10–0.15 | 613 |
| >=0.15 | 1,264 |

These buckets are descriptive only. No outcome/profit analysis was performed by disagreement bucket.

## Incremental-information test

Expanding-year chronological evaluation scores **2,968** rows from **2016–2023** across **8** folds. The first matched year is training-only.

| Diagnostic model | Log loss | Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|
| Market-only calibration | 0.613272 | 0.212535 | 66.04% | 0.723909 |
| Market + M0 | **0.611564** | **0.211733** | **66.64%** | **0.725722** |

- folds where Market + M0 improves log loss: **6/8**
- folds where Market + M0 improves Brier: **6/8**
- folds where it improves both: **6/8**
- M0 logit coefficient mean: **0.371311**
- M0 coefficient range: **0.317975 to 0.445182**
- M0 coefficient sign: **positive 8/8, negative 0/8**

This is the key V0 result: although the market is substantially better than M0 alone, M0 contributes a small but chronologically stable positive increment after market probability is already known.

## Verdict

**MARKET_COMPLEMENTARY**

The market is stronger overall. M0 is not yet market-competitive on standalone probability quality, and the naive fixed blend does not beat market alone. However, the predeclared chronological orthogonality test improves aggregate log loss and Brier, improves both in 6/8 folds, and keeps the M0 term positive in all 8 folds. That is measurable independent information under V0.

## Reproducibility

- GitHub Actions run: `34681219952`
- runtime artifact ID: `10293394863`
- runtime artifact archive digest: `sha256:65107d3d9e6a9aceabf038fdc022da2bf81e706ce13b4c057668494ca27f26c4`
- diagnostic table rows: **3,363**
- diagnostic table logical SHA-256: `a9fe9c4d68876fff2b38b1d3ce99b9f4379797fb86477cf9253de966607b8a0e`

## Guardrails

**Was M0 changed, tuned, or retrained based on market results?** NO.

**Was ROI, bet-threshold, or profitable-bucket optimization performed?** NO.

**Was the market used only as a diagnostic benchmark?** YES.
