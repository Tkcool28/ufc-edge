# MOV0 PROBABILITY BUCKET CALIBRATION DIAGNOSTIC V1

Status: **MOV0_PROBABILITY_BUCKET_CALIBRATION_DIAGNOSTIC_V1_COMPLETE**

This is a post-freeze descriptive diagnostic only. No predictions were regenerated and MOV0 was not retrained, refit, recalibrated, or otherwise changed.

## 1. Authoritative source identity

- Run source HEAD: `dd4e7de7de4baa24090388fcf845c996564f2bf8`
- Workflow run: `35376956316`
- Artifact: `mov0-standard-finish-probability-v1`
- Artifact ID: `10561085362`
- Artifact SHA256: `03e8651b2e34c656daadb2d789ba0cbf298d0dcad14ec3a08bd5d0d6ce64e866`
- Frozen MOV0-MIN OOF SHA256: `786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57`
- Frozen MOV0-FULL OOF SHA256: `9d543356b157fefaabe27f7f4d1b5663536e4cf659fdf11fedd8531c4b13faa0`
- OOF rows per model: **4,260**
- OOF years: **2018–2026**

The downloaded ZIP SHA256 matched the authoritative Actions digest exactly. The embedded OOF files also matched the frozen manifest hashes exactly.

## 2. Fixed bucket definitions

The diagnostic used exactly these preregistered interpretation bins:

1. `< 0.30`
2. `0.30–<0.40`
3. `0.40–<0.50`
4. `0.50–<0.60`
5. `0.60–<0.70`
6. `>= 0.70`

No boundaries were changed after inspecting results.

Observed finish-rate uncertainty uses the **Wilson 95% binomial interval** throughout.

## 3. MOV0-MIN

| Bucket | N | Finish | Decision | Mean p(finish) | Observed finish | Gap: observed - mean p | Wilson 95% | Years |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| < 0.30 | 383 | 110 | 273 | 24.95% | 28.72% | +3.77 pp | 24.42–33.45% | 2018–2026 (9) |
| 0.30–<0.40 | 865 | 358 | 507 | 35.80% | 41.39% | +5.59 pp | 38.15–44.70% | 2018–2026 (9) |
| 0.40–<0.50 | 1,321 | 614 | 707 | 44.93% | 46.48% | +1.55 pp | 43.80–49.18% | 2018–2026 (9) |
| 0.50–<0.60 | 956 | 556 | 400 | 54.62% | 58.16% | +3.54 pp | 55.01–61.25% | 2018–2026 (9) |
| 0.60–<0.70 | 523 | 333 | 190 | 64.08% | 63.67% | -0.41 pp | 59.46–67.68% | 2018–2026 (9) |
| >= 0.70 | 212 | 144 | 68 | 75.48% | 67.92% | -7.55 pp | 61.37–73.84% | 2018–2026 (9) |

### MIN reading

Observed finish rate rises monotonically across all six bins:

**28.7% → 41.4% → 46.5% → 58.2% → 63.7% → 67.9%**

There are **no monotonicity violations**.

MIN is underconfident in the lower/middle bins, is nearly calibrated in `0.60–<0.70`, and becomes overconfident in the `>=0.70` bin. The highest-confidence bucket's mean prediction is 75.5%, but its observed finish rate is 67.9%.

The top bucket is nevertheless materially separated from the middle: observed finish rate is **+21.4 percentage points** versus `0.40–<0.50` and **+9.8 points** versus `0.50–<0.60`.

## 4. MOV0-FULL

| Bucket | N | Finish | Decision | Mean p(finish) | Observed finish | Gap: observed - mean p | Wilson 95% | Years |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| < 0.30 | 355 | 99 | 256 | 25.24% | 27.89% | +2.65 pp | 23.48–32.77% | 2018–2026 (9) |
| 0.30–<0.40 | 766 | 301 | 465 | 35.80% | 39.30% | +3.49 pp | 35.90–42.80% | 2018–2026 (9) |
| 0.40–<0.50 | 1,210 | 564 | 646 | 45.30% | 46.61% | +1.31 pp | 43.82–49.43% | 2018–2026 (9) |
| 0.50–<0.60 | 975 | 539 | 436 | 54.61% | 55.28% | +0.68 pp | 52.15–58.38% | 2018–2026 (9) |
| 0.60–<0.70 | 640 | 397 | 243 | 64.29% | 62.03% | -2.26 pp | 58.21–65.71% | 2018–2026 (9) |
| >= 0.70 | 314 | 215 | 99 | 75.84% | 68.47% | -7.37 pp | 63.14–73.36% | 2018–2026 (9) |

### FULL reading

Observed finish rate also rises monotonically across all six bins:

**27.9% → 39.3% → 46.6% → 55.3% → 62.0% → 68.5%**

There are **no monotonicity violations**.

FULL is closer to nominal calibration than MIN through much of the lower and middle range, especially `0.50–<0.60`, but it becomes overconfident in the upper range. Its `>=0.70` mean prediction is 75.8%, versus a 68.5% observed finish rate.

The highest-confidence bucket is also materially separated from the middle: **+21.9 percentage points** versus `0.40–<0.50` and **+13.2 points** versus `0.50–<0.60`.

## 5. Side-by-side MIN vs FULL

| Bucket | MIN N | MIN mean p | MIN observed | MIN gap | FULL N | FULL mean p | FULL observed | FULL gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| < 0.30 | 383 | 24.95% | 28.72% | +3.77 pp | 355 | 25.24% | 27.89% | +2.65 pp |
| 0.30–<0.40 | 865 | 35.80% | 41.39% | +5.59 pp | 766 | 35.80% | 39.30% | +3.49 pp |
| 0.40–<0.50 | 1,321 | 44.93% | 46.48% | +1.55 pp | 1,210 | 45.30% | 46.61% | +1.31 pp |
| 0.50–<0.60 | 956 | 54.62% | 58.16% | +3.54 pp | 975 | 54.61% | 55.28% | +0.68 pp |
| 0.60–<0.70 | 523 | 64.08% | 63.67% | -0.41 pp | 640 | 64.29% | 62.03% | -2.26 pp |
| >= 0.70 | 212 | 75.48% | 67.92% | -7.55 pp | 314 | 75.84% | 68.47% | -7.37 pp |

Because MIN and FULL assign different fights to bins, differences in observed rates are descriptive and are not paired estimates of model superiority.

## 6. Confidence monotonicity

Both models display the desired qualitative confidence behavior: higher predicted-probability bins correspond to higher realized finish rates without a single reversal.

No monotonicity violation needs a small-N explanation because there are no violations.

The upper-confidence groups are meaningfully separated from the middle, but neither model's top bin reaches its nominal mean probability. Confidence ordering is therefore real, while top-end calibration remains imperfect.

## 7. Sample-size governance

Every one of the 12 model/bucket cells has **N >= 100** and therefore receives the project's **NORMAL** interpretation classification.

The smallest cells are:

- MIN `>=0.70`: N=212
- FULL `>=0.70`: N=314

Thus the high-confidence finding is not being driven by a formally thin or insufficient bucket.

No bins were merged or widened.

## 8. Year coverage / stability

Every fixed bucket for both models contains fights from **all nine OOF years, 2018 through 2026**.

No bucket is concentrated in one year, two years, or only the recent period.

For MIN, the largest single-year share of any bucket ranges from about **12.5% to 15.1%**. The `>=0.70` bucket's largest single-year contribution is 2020 with 32/212 fights (**15.1%**); 2024–2026 contribute 53/212 (**25.0%**).

For FULL, the largest single-year share ranges from about **12.4% to 14.1%**. The `>=0.70` bucket's largest single-year contribution is 41/314 (**13.1%**, tied in 2023 and 2024); 2024–2026 contribute 100/314 (**31.8%**).

This diagnostic therefore provides no evidence that the apparent confidence ordering is a narrow recent-era artifact.

## 9. Notable MIN/FULL differences

FULL behaves differently from MIN in allocation and calibration, but this diagnostic alone does not establish that FULL is better.

- FULL places **314** fights in `>=0.70` versus **212** for MIN.
- Despite the larger top bucket, observed finish rate is almost unchanged: **68.5% FULL vs 67.9% MIN**.
- Mean top-bin predictions are also similar: **75.8% FULL vs 75.5% MIN**.
- Therefore FULL creates a materially larger high-confidence population without demonstrating a materially higher realized finish rate there.
- FULL is descriptively closer to nominal calibration in the first four bins, especially `0.50–<0.60` (+0.68 pp gap vs MIN +3.54 pp).
- MIN is descriptively closer to nominal calibration in `0.60–<0.70` (-0.41 pp vs FULL -2.26 pp).
- In `>=0.70`, both are similarly overconfident by roughly **7.4–7.6 percentage points**.

These are descriptive bucket behaviors. They do not promote FULL over MIN or retire either model.

## 10. Final descriptive conclusion

MOV0 confidence behaves like **real confidence** in the most basic and important sense: realized finish rates increase steadily as model-assigned finish probability increases, for both MIN and FULL, across the full chronological OOF period.

The fixed-bin ordering is completely monotonic and all bins have normal sample size with representation across all nine OOF years.

At the same time, the probabilities are not perfectly calibrated. Both models underpredict finish frequency in much of the low/middle range and overpredict it in the highest-confidence bin. The `>=0.70` bucket is genuinely a higher-finish environment than the middle bins, but its realized finish rate is about **68%**, not the roughly **75–76%** mean probability assigned.

FULL does show different behavior from MIN: it assigns substantially more fights to the top bucket and is closer to calibration in several lower/middle bands. However, its expanded top bucket does not produce a materially higher observed finish rate than MIN's top bucket. That is descriptive evidence of different confidence allocation, not evidence that FULL should replace MIN.

No probability threshold was optimized.

No sportsbook prices were used.

No ROI or EV analysis was performed.

No recalibration was performed.

MOV1 was not started.

No model should be promoted or retired from this diagnostic alone.
