# MOV0 STANDARD_FINISH PROBABILITY V1 — FIRST FROZEN RUN CLOSEOUT

Status: **MOV0_STANDARD_FINISH_PROBABILITY_V1_COMPLETE**

Classification: **CLEAR_SUCCESS**

## Repository / execution identity

- Branch: `feat/mov0-standard-finish-run-v1`
- Base main: `a796d594b1815b0313fcf795f5251554f42f531c`
- Successful frozen-run source HEAD: `dd4e7de7de4baa24090388fcf845c996564f2bf8`
- Draft PR: #73
- Workflow: `MOV0 Standard Finish Frozen Run V1`
- Successful workflow run: `35376956316`
- Evidence artifact: `mov0-standard-finish-probability-v1`
- Artifact ID: `10561085362`
- Artifact digest: `sha256:03e8651b2e34c656daadb2d789ba0cbf298d0dcad14ec3a08bd5d0d6ce64e866`
- Artifact manifest SHA256: `8e85abedab41b094157452a2c5f5da4324bf4395fded6ffa3db2085c28ac459a`

The complete evidence artifact contains execution config, fold manifest, preprocessing metadata, selected C values, four OOF prediction files, aggregate/fold metrics, calibration/reliability diagnostics, both bootstraps, Validation Terrain diagnostics, invariance proof, hashes, and the generated run report.

## Governed population

- Exact OOF N: **4,260**
- STANDARD_FINISH=1: **2,115**
- DECISION=0: **2,145**
- OOF prevalence: **0.4964788732**
- Outer years: **2018–2026**
- First outer training N: **1,398**
- No pre-2015 row was authorized or used.

## Aggregate metrics

| Surface | Log loss | Brier | ROC AUC | ECE | Cal intercept | Cal slope |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 0.693459672 | 0.250156237 | 0.477794 | 0.021381 | -0.024452 | -3.468885 |
| B1 | 0.683561010 | 0.245222955 | 0.580565 | 0.008041 | 0.004095 | 0.786153 |
| MOV0-MIN | 0.670238307 | 0.238630440 | 0.627456 | 0.032872 | 0.080259 | 0.832109 |
| MOV0-FULL | **0.669477686** | **0.238230638** | **0.627593** | 0.022844 | 0.013280 | 0.790084 |

MOV0-FULL improves log loss by **0.014083324** versus B1 overall. That improvement is favorable in every outer year.

## Primary comparison 1 — B1 vs B0

Aggregate candidate-minus-baseline log-loss delta: **-0.009898662**.

- Better / worse / tied years: **8 / 1 / 0**
- Median yearly delta: **-0.009788383**
- Strongest favorable year: **2019**, -0.021993700
- Strongest unfavorable year: **2021**, +0.003738907
- Strongest favorable year contribution to aggregate gain: **26.44%**

| Year | Delta |
|---:|---:|
| 2018 | -0.009788383 |
| 2019 | -0.021993700 |
| 2020 | -0.005289602 |
| 2021 | +0.003738907 |
| 2022 | -0.006476054 |
| 2023 | -0.003139332 |
| 2024 | -0.016112088 |
| 2025 | -0.014544169 |
| 2026 | -0.016984645 |

Bootstrap 95% intervals:

- Fight-level paired: **[-0.015440487, -0.004598372]**
- Event-cluster: **[-0.014804908, -0.004866054]**

Structural context therefore improves STANDARD_FINISH probability beyond training-history prevalence.

## Primary comparison 2 — MOV0-MIN vs B1

Aggregate candidate-minus-baseline log-loss delta: **-0.013322703**.

- Better / worse / tied years: **9 / 0 / 0**
- Median yearly delta: **-0.013689850**
- Strongest favorable year: **2024**, -0.024368859
- Least favorable year: **2021**, still favorable at -0.000886952
- Strongest favorable year contribution to aggregate gain: **21.55%**

| Year | Delta |
|---:|---:|
| 2018 | -0.013999050 |
| 2019 | -0.011525283 |
| 2020 | -0.024336538 |
| 2021 | -0.000886952 |
| 2022 | -0.011198052 |
| 2023 | -0.013689850 |
| 2024 | -0.024368859 |
| 2025 | -0.013726139 |
| 2026 | -0.004201339 |

Bootstrap 95% intervals:

- Fight-level paired: **[-0.019028812, -0.007611108]**
- Event-cluster: **[-0.019575918, -0.006903322]**

This is the central positive result. The preregistered direct finish-pressure/vulnerability features add chronologically persistent probability signal beyond fight context.

## Primary comparison 3 — MOV0-FULL vs MOV0-MIN

Aggregate candidate-minus-baseline log-loss delta: **-0.000760621**.

- Better / worse / tied years: **6 / 3 / 0**
- Median yearly delta: **-0.003221915**
- Strongest favorable year: **2026**, -0.007149693
- Strongest unfavorable year: **2020**, +0.013154797
- Strongest favorable year contribution to aggregate gain: **93.94%**

| Year | Delta |
|---:|---:|
| 2018 | +0.002198029 |
| 2019 | -0.000737456 |
| 2020 | +0.013154797 |
| 2021 | -0.004187568 |
| 2022 | -0.004256582 |
| 2023 | -0.006027278 |
| 2024 | +0.003036203 |
| 2025 | -0.003221915 |
| 2026 | -0.007149693 |

Bootstrap 95% intervals:

- Fight-level paired: **[-0.003357997, +0.002058465]**
- Event-cluster: **[-0.003365894, +0.001701985]**

The broader preregistered style surface does **not** establish meaningful incremental signal beyond MOV0-MIN. Its gain is tiny, mixed through time, and both uncertainty intervals cross zero. This does not negate MOV0-MIN's clear improvement over B1.

## Selected C by outer year

| Year | B1 | MOV0-MIN | MOV0-FULL |
|---:|---:|---:|---:|
| 2018 | 1.00 | 0.03 | 0.03 |
| 2019 | 0.30 | 0.03 | 0.03 |
| 2020 | 0.10 | 0.03 | 0.03 |
| 2021 | 0.30 | 0.03 | 0.03 |
| 2022 | 0.03 | 0.03 | 0.03 |
| 2023 | 0.03 | 0.03 | 0.03 |
| 2024 | 0.03 | 0.03 | 0.03 |
| 2025 | 0.10 | 0.03 | 0.03 |
| 2026 | 1.00 | 0.03 | 0.03 |

MIN and FULL selected the strongest frozen regularization value, C=0.03, in every outer fold.

## Calibration

The probability gains are not calibration-perfect, but they remain usable and interpretable.

- B1: ECE 0.0080, intercept 0.0041, slope 0.7862.
- MOV0-MIN: ECE 0.0329, intercept 0.0803, slope 0.8321.
- MOV0-FULL: ECE 0.0228, intercept 0.0133, slope 0.7901.

MOV0-FULL recovers much of MIN's aggregate calibration deterioration while retaining the log-loss/Brier gain. Brier improves materially from B1 (0.245223) to MIN (0.238630) and FULL (0.238231). FULL yearly ECE ranges from approximately 0.0335 to 0.0646, so calibration should remain an explicit watch item in future work rather than being treated as solved.

No post-hoc recalibration was performed.

## Validation Terrain V1

Terrain was joined by `fight_id` from the immutable frozen assignment; it was not regenerated.

Required watchpoints, B1 -> MOV0-FULL log loss:

- HIGH_MISSINGNESS (N=821): **0.683444 -> 0.682302**
- 3_ROUND (N=3,837): **0.683537 -> 0.670984**
- 5_ROUND (N=423): **0.683775 -> 0.655818**
- STRIKE_TWO_SIDED (N=168): **0.695282 -> 0.655236**
- GRAPPLE_TWO_SIDED (N=122): **0.706257 -> 0.685376**

Important unfavorable NORMAL-size terrain cells for FULL vs B1:

- 18+ month layoff (N=293): **+0.005654** log-loss regression
- Light Heavyweight (N=319): **+0.005279**
- Heavyweight (N=311): **+0.001843**
- Flyweight (N=248): **+0.000706**

Catch Weight (N=59, MODERATE_UNCERTAINTY) regresses by +0.001136.

These weaknesses are real and must remain visible. They do not dominate the aggregate result, and the main finish-oriented watchpoints are favorable.

## Fighter-order invariance proof

Maximum absolute prediction difference after swapping Fighter 1 and Fighter 2:

- B1: **0.0** in every outer year
- MOV0-MIN: **0.0** in every outer year
- MOV0-FULL: **0.0** in every outer year

Required tolerance was `atol=1e-12, rtol=0`.

## Deterministic evidence hashes

- B0 OOF: `5e202ff96ffb7a9c8038e7344f7b1f0e1632ee82c57f4c1091f5ea89819331f2`
- B1 OOF: `6f2f082e276f69a7cac8e527d7a9697f8e5d4b83931717aefc3e8c84e2f127a6`
- MOV0-MIN OOF: `786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57`
- MOV0-FULL OOF: `9d543356b157fefaabe27f7f4d1b5663536e4cf659fdf11fedd8531c4b13faa0`
- Aggregate metrics: `497831871b179f31ad7d0944fd09064ab35e3ece752227a48d39870fdbebccf4`
- Comparisons: `cf36c084f7db87ca52c43054fc2206fdd1062bd9725f687ca84f2f826df0e459`
- Bootstrap report: `4b2ba2a455604af0267c5f04b240cf94b6eabc88237a9bc9425f4f1e74136ca4`
- Calibration/reliability: `5a7db6840a29cf0955c9cabf779db6a3f77e69db66dda19a6602fad28c5c1ac6`
- Validation Terrain report: `d1678cce8ff11bcabadaaf3ca991fa75962f6730c93ef2105144f343f313b404`
- Fighter-order invariance: `1537cca1194405454af321cc48d50d69fc2bb6d7c10f5985983ee084e9672147`

## Mechanical execution caveats

Two pre-closeout mechanical issues were corrected without changing MOV0 methodology:

1. The initial workflow passed escaped GitHub expressions to `actions/download-artifact`, producing a Bad credentials error before training began.
2. The next execution generated OOF predictions but stopped during terrain validation because the loader compared the checked-in compressed `.csv.gz` bytes against the frozen decompressed CSV physical hash. The permanent terrain documentation explicitly distinguishes those hashes. The loader was corrected to validate both the compressed SHA256 and the decompressed physical SHA256.
3. `set -euo pipefail` was added to the execution step so a Python failure piped through `tee` cannot be reported as success.

No feature, target, fold, preprocessing, model-family, C-grid, metric, terrain assignment, or acceptance rule was changed. The final successful run is the authoritative evidence package.

## Result classification

**CLEAR_SUCCESS**

Reason: MOV0-MIN establishes useful incremental STANDARD_FINISH probability signal beyond B1 with unusually strong chronological persistence (9/9 favorable years), concordant Brier improvement, and both paired uncertainty diagnostics wholly favorable. MOV0-FULL remains better than B1 overall and in every OOF year, with acceptable aggregate calibration, although its incremental contribution beyond MIN is not established.

This result means the frozen MOV0 specification established useful finish-vs-decision probability signal. It does **not** establish that every preregistered FULL feature family is useful, and it does not authorize MOV1, sportsbook analysis, ROI/EV work, post-hoc tuning, or recalibration.

## MASTER/PM recommendation

Review and freeze the completed MOV0 V1 result as **CLEAR_SUCCESS**, with MOV0-MIN identified as the component that established the signal and MOV0-FULL's incremental result recorded as inconclusive. Do not merge this PR until MASTER/PM has reviewed the evidence package.
