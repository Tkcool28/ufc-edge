# MOV1 conditional KO versus submission — first frozen run V1

**MOV1_KO_VS_SUBMISSION_GIVEN_FINISH_V1_COMPLETE**

MIN adds chronologically persistent conditional method signal beyond context and improves the composed three-way system. FULL’s extra surface is not supported over MIN. Calibration and submission-pathway limitations remain; no feature, fold or threshold was changed to address them.

## Identity and safety gates

Starting main `b6a644d9ef8d267f7d7da97f21e691f2bae99226`, exact current main after merged#118. Branch `feat/mov1-ko-vs-submission-run-v1`; draft [PR119](https://github.com/Tkcool28/ufc-edge/pull/119). Implementation freeze `31008e323d0ac579c8b93d810918c23ff15df5a1` was committed before historical fitting. The six source/test/workflow files are individually hashed in `IMPLEMENTATION_IDENTITY.json`. Contract manifest `9034e647bebaa7099f5358ed7a5db0e1bc515df1894db912274e5dae629cb714` verified with every listed artifact and foundation file. Corrected F02 physical `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`, logical `2d1a367416e105ed6fe546eb8590ae7b555dd044304ad0ba40c7945420599ba0`. Frozen MOV0-MIN OOF `786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57` consumed unchanged.

Exact modern population5,658 =1,812 KO +1,010 SUB +2,836 DEC, including45 decision draws. Conditional eligible finishes2,822. Outer2018–2026 scoring4,260, conditional evaluation2,115. Each surface has4,260 scores; the combined file has17,040 rows. Three-way systems likewise17,040 rows. Exclusions, categories, fold counts and ordered-ID identities match the pinned audit/contract. No decision or pre2015 fitting/preprocessing row. Existing governed F02 career states retain their existing strict-prior history, including earlier bouts.

All216 inner fits and27 outer fits converged; maximum56 solver iterations, zero solver warnings. Every fitted inner/outer model passes exact-side swap checks and asymmetric-null fixtures; maximum swap error0. Every scoring row is retained independent of outcome; removed/changed labels yield identical probabilities. All persisted predictions regenerate from saved records with max error0. Representative MIN2021 refit is identical float64 in the same environment. Composition sum error1.11e−16; conditional/composed paired loss identity error6.66e−16, no log-clipping exceptions. Immutable terrain joins one-to-one without rebuilding.

Pinned environment: Python3.12.14, NumPy1.26.4, pandas2.2.3, pyarrow17.0.0, scikit-learn1.5.2, SciPy1.14.1; numerical thread pools limited to1. Lock includes transitive packages/platform/BLAS records. pandas emits a forward-looking object-fill downcasting warning in preprocessing; behavior under the pinned version is unchanged and validated. No cross-platform bitwise reproducibility is claimed; independent CI regeneration uses contracted1e−12 tolerance.

## Frozen method and selection

C0 is prior-finish training KO prevalence; C1 has5 literal columns; MIN35; FULL55. Allowlists and transforms exactly match the contract. Shared pooled-pair median precedes mean/absolute difference; numeric scaling and category encoding train only on each finish history. L2 logistic, lbfgs, intercept, max_iter3000, tol1e−4, no classweights, seed17; inner concatenated log loss selects frozen C grid in order with1e−12 tie tolerance. No recalibration is applied.

| Year | C1 C | MIN C | FULL C |
|---|---|---|---|
| 2018 | 0.10 | 0.03 | 0.03 |
| 2019 | 1.00 | 0.03 | 0.03 |
| 2020 | 0.10 | 0.03 | 0.03 |
| 2021 | 0.10 | 0.03 | 0.03 |
| 2022 | 0.10 | 0.03 | 0.03 |
| 2023 | 0.10 | 0.03 | 0.03 |
| 2024 | 0.30 | 0.03 | 0.03 |
| 2025 | 0.30 | 0.03 | 0.10 |
| 2026 | 1.00 | 0.10 | 0.03 |

## Conditional evaluation: finishes only

Observed KO prevalence among2,115 OOF finishes64.35%.

| Surface | N | Log loss | Brier | AUC | ECE | Cal. intercept | Cal. slope | Mean KO |
|---|---|---|---|---|---|---|---|---|
| C0 | 2115 | 0.651593 | 0.229507 | 0.484382 | 0.003085 | 2.626001 | -3.525772 | 64.0% |
| C1 | 2115 | 0.641605 | 0.224829 | 0.583088 | 0.023608 | 0.158982 | 0.759019 | 63.7% |
| MOV1_MIN | 2115 | 0.615366 | 0.213614 | 0.663563 | 0.031387 | 0.010552 | 0.830658 | 66.3% |
| MOV1_FULL | 2115 | 0.619689 | 0.215100 | 0.657846 | 0.035589 | 0.065031 | 0.758336 | 66.1% |

Conditional MIN−C1 is **CLEAR_SUCCESS**, with calibration caveats. Context−prevalence is smaller but supported. FULL−MIN is **CURRENT_SPECIFICATION_NOT_SUPPORTED**. Aggregate/year reliability, diagnostic intercept/slope and AUC are preserved, including undefined statuses. C0 yearly calibration slope is undefined because its probability is constant within a year; pooled negative slope reflects tiny across-era variation and should not be interpreted as a useful method coefficient.

## Complete three-way evaluation: all eligible bouts

F is frozen MOV0-MIN; KO=F×K, SUB=F×(1−K), DEC=1−F. No renormalization or replacement node.

| System | Conditional node | N | Multiclass log loss | Summed Brier |
|---|---|---|---|---|
| S0 | C0 | 4260 | 0.993740 | 0.594575 |
| S1 | C1 | 4260 | 0.988782 | 0.592501 |
| S2 | MIN | 4260 | 0.975754 | 0.586206 |
| S3 | FULL | 4260 | 0.977901 | 0.586869 |

Composed S2−S1 and S2−S0 are **CLEAR_SUCCESS**. FULL S3 remains better than S0 but is not supported as an increment over S2. The complete system is judged directly, including Brier and classwise reliability. With identical F, log-loss deltas are zero on decision rows and equal conditional deltas on finish rows before clipping; therefore these two log-loss assessments are not independent replications. Different conditional nodes can still worsen Brier/calibration.

| S2 class | Observed rate | Mean probability | ECE | Calibration intercept | Slope |
|---|---|---|---|---|---|
| DECISION | 50.4% | 52.7% | 0.032872 | -0.080259 | 0.832109 |
| KO_TKO | 31.9% | 31.5% | 0.017642 | -0.096482 | 0.835968 |
| SUBMISSION | 17.7% | 15.9% | 0.024725 | -0.131681 | 0.829915 |

S2 mean probabilities by actual class and all annual classwise reliability tables are in `three_way_metrics.json`. Decision mean52.68% versus actual50.35% is inherited from F. Submission mean15.86% versus actual17.70% is a remaining complete-system shortfall. KO mean31.47% versus31.95% is closer. S2 submission ECE worsens versus S1 despite better overall log loss/Brier; no posthoc repair was made.

## Annual persistence and paired uncertainty

| Year | C1−C0 | MIN−C1 | FULL−MIN | S1−S0 | S2−S1 | S3−S2 |
|---|---|---|---|---|---|---|
| 2018 | -0.026780 | -0.018687 | -0.001767 | -0.013732 | -0.009582 | -0.000906 |
| 2019 | 0.002949 | -0.033327 | 0.008506 | 0.001344 | -0.015184 | 0.003876 |
| 2020 | -0.010585 | -0.015883 | 0.012348 | -0.005257 | -0.007888 | 0.006132 |
| 2021 | 0.021279 | -0.024438 | 0.007378 | 0.010337 | -0.011871 | 0.003584 |
| 2022 | -0.013178 | -0.018552 | 0.000683 | -0.006994 | -0.009846 | 0.000363 |
| 2023 | -0.004520 | -0.027442 | -0.007287 | -0.002309 | -0.014020 | -0.003723 |
| 2024 | -0.019353 | -0.016387 | 0.004357 | -0.008597 | -0.007280 | 0.001935 |
| 2025 | -0.013091 | -0.037829 | 0.011543 | -0.006546 | -0.018915 | 0.005771 |
| 2026 | -0.031676 | -0.047646 | 0.005148 | -0.017460 | -0.026263 | 0.002837 |

| Comparison | Delta LL | Better / worse years | Fight paired95 | Event paired95 | Verdict |
|---|---|---|---|---|---|
| C1_vs_C0 | -0.009988 | 7 / 2 | [-0.017802, -0.002235] | [-0.018284, -0.001428] | CLEAR_SUCCESS |
| MOV1_FULL_vs_MOV1_MIN | 0.004324 | 2 / 7 | [0.000201, 0.008622] | [0.000018, 0.008337] | CURRENT_SPECIFICATION_NOT_SUPPORTED |
| MOV1_MIN_vs_C1 | -0.026239 | 9 / 0 | [-0.037958, -0.013835] | [-0.037655, -0.014047] | CLEAR_SUCCESS |
| S1_vs_S0 | -0.004959 | 7 / 2 | [-0.008853, -0.000929] | [-0.009075, -0.000713] | CLEAR_SUCCESS |
| S2_vs_S0 | -0.017986 | 9 / 0 | [-0.024790, -0.011437] | [-0.024608, -0.011067] | CLEAR_SUCCESS |
| S2_vs_S1 | -0.013027 | 9 / 0 | [-0.018826, -0.007284] | [-0.018882, -0.006961] | CLEAR_SUCCESS |
| S3_vs_S0 | -0.015840 | 8 / 1 | [-0.022827, -0.008988] | [-0.022889, -0.008544] | CLEAR_SUCCESS |
| S3_vs_S2 | 0.002147 | 2 / 7 | [-0.000003, 0.004282] | [0.000009, 0.004172] | CURRENT_SPECIFICATION_NOT_SUPPORTED |

MIN’s best year accounts for17.18% of its net improvement over C1; no single era supplies the gain. S2’s strongest year supplies18.95% of improvement versus S0. Intervals use2,000 seed17 paired fight or event resamples, no model refitting. Event clustering does not remove repeat-fighter dependence or overlapping training-history dependence. Strongest-fold/dominance diagnostics and every annual delta are preserved; no p-value model-selection rules.

## Fixed probability buckets

| Frozen MIN bucket | N | Status | Mean predicted KO | Observed KO | Gap pp | Wilson95 |
|---|---|---|---|---|---|---|
| <0.30 | 32 | THIN_EXPLORATORY | 25.1% | 50.0% | -24.90 | [0.33630882869327483, 0.6636911713067252] |
| 0.30–<0.40 | 69 | MODERATE_UNCERTAINTY | 35.9% | 33.3% | 2.62 | [0.2335105070168671, 0.4507352457128168] |
| 0.40–<0.50 | 208 | NORMAL | 45.5% | 47.6% | -2.13 | [0.40914326914496396, 0.5436516178631351] |
| 0.50–<0.60 | 380 | NORMAL | 55.5% | 53.2% | 2.31 | [0.4813419457751135, 0.5811838691114206] |
| 0.60–<0.70 | 495 | NORMAL | 65.1% | 63.6% | 1.50 | [0.5930867995415912, 0.6775402656569431] |
| 0.70–<0.80 | 518 | NORMAL | 74.8% | 69.9% | 4.94 | [0.6579897929071928, 0.736766117183849] |
| >=0.80 | 413 | NORMAL | 85.8% | 83.3% | 2.50 | [0.7939194363709641, 0.8658038089559656] |

All four models’ buckets retain empty cells, Wilson95, year coverage, division shares and all15 archetype status composition. The all-eligible distribution view never counts decisions as non-KO conditional labels. No boundary is changed. The thin low tail merits caution rather than an optimized cutoff.

## All-division method composition

| Division | All N | Finish N | Finish status | Actual KO \| finish | C1 mean K | MIN mean K | FULL mean K |
|---|---|---|---|---|---|---|---|
| Flyweight | 252 | 121 | NORMAL | 52.1% | 53.5% | 56.0% | 55.5% |
| Bantamweight | 488 | 213 | NORMAL | 61.5% | 59.4% | 64.7% | 65.0% |
| Featherweight | 502 | 239 | NORMAL | 66.5% | 63.6% | 65.5% | 65.7% |
| Lightweight | 576 | 311 | NORMAL | 66.6% | 64.1% | 66.8% | 67.0% |
| Welterweight | 546 | 283 | NORMAL | 67.8% | 66.5% | 69.3% | 69.2% |
| Middleweight | 476 | 270 | NORMAL | 65.9% | 68.9% | 68.9% | 68.2% |
| Light Heavyweight | 319 | 205 | NORMAL | 74.1% | 70.5% | 74.7% | 73.5% |
| Heavyweight | 316 | 187 | NORMAL | 77.5% | 75.7% | 76.9% | 75.8% |
| Women's Strawweight | 275 | 94 | MODERATE_UNCERTAINTY | 44.7% | 44.0% | 50.6% | 51.0% |
| Women's Flyweight | 266 | 95 | MODERATE_UNCERTAINTY | 46.3% | 49.3% | 49.8% | 51.6% |
| Women's Bantamweight | 158 | 56 | MODERATE_UNCERTAINTY | 51.8% | 56.9% | 58.0% | 56.2% |
| Women's Featherweight | 27 | 12 | INSUFFICIENT | 50.0% | 63.3% | 58.0% | 56.3% |
| Catch Weight | 59 | 29 | THIN_EXPLORATORY | 44.8% | 60.3% | 65.5% | 65.6% |

HW/LHW are KO-heavy without hard-coded historical rates. Flyweight remains relatively balanced; C1 is closer to its actual split than MIN. Women’s Strawweight/Flyweight have moderate conditional samples; MIN understates submission enrichment, particularly Strawweight. Women’s Featherweight is insufficient and Catch Weight thin. Complete division/round/era/reference tables are retained, with immutable audit rates used as descriptive context rather than claimed predictive truth.

## Archetypes and pathway behavior

| Archetype | All N | Finish N | Finish status | Actual KO \| finish | C1 mean K | MIN mean K | FULL mean K |
|---|---|---|---|---|---|---|---|
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.4% | 67.0% | 72.2% | 71.7% |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 88.6% | 69.1% | 82.1% | 81.8% |
| A3_ACCURACY_VS_ABSORPTION | 973 | 467 | NORMAL | 64.5% | 64.0% | 69.0% | 68.9% |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 75.2% | 70.1% | 77.1% | 76.6% |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 49.7% | 63.1% | 56.7% | 56.5% |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 54.3% | 64.1% | 59.6% | 59.5% |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 46.0% | 64.7% | 55.2% | 54.9% |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 57.3% | 62.8% | 60.9% | 60.6% |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 45.1% | 61.9% | 54.1% | 53.7% |
| C1_DAMAGE_PLUS_SUBMISSION_ACCESS | 29 | 19 | INSUFFICIENT | 42.1% | 66.7% | 67.3% | 68.8% |
| C2_BOTH_HIGH_FINISH_HISTORY | 1483 | 826 | NORMAL | 66.8% | 67.8% | 68.8% | 68.7% |
| C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS | 417 | 232 | NORMAL | 73.7% | 74.8% | 76.2% | 75.7% |
| D1_LOW_DAMAGE_STRONG_DEFENSE | 74 | 20 | INSUFFICIENT | 45.0% | 55.5% | 55.3% | 58.4% |
| D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE | 499 | 222 | NORMAL | 81.5% | 65.9% | 78.1% | 78.0% |
| D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE | 124 | 39 | THIN_EXPLORATORY | 74.4% | 65.7% | 74.5% | 75.9% |

A1/A4 exhibit useful KO-specific shifts beyond C1. A2 is coherent with moderate uncertainty. B1/B2/B3/B5 move toward submission, but MIN remains too KO-heavy; B3/B5 miss about9 conditional percentage points. See `PATHWAY_DECOMPOSITION_REPORT.md` for F/K/composed probabilities and actual three-way rates. Known-state formulas and frozen thresholds remain unchanged; the contract’s PR117 explicit unknown-status handling is retained and its historical flag differences disclosed. Thin/insufficient conditional cells are not interpreted strongly.

## Terrain and coefficient diagnostics

S2−S1 is favorable in43 of47 NORMAL terrain rows across declared dimensions, including all three predictive eras, three/five rounds, title/non-title and strike/grapple states. These rows overlap and are not independent successes. Exceptions include experience1–2 (N1,169, delta+0.003415), raw women’s Strawweight (N274,+0.009586), women’s Bantamweight (N158,+0.004755), and STRIKE_LOW__GRAPPLE_LOW (N1,546,+0.005174). No cell was used to alter fitting. Empty/thin cells and all division×archetype statuses remain visible.

Coefficient histories support the broad direct pathways: MIN KO win/KD created/KD allowed means positive9/9; SUB win/attempts and TD success/pressure means negative9/9. Loss-history and some residual division signs are unstable. Context-only division signs align with the audit; after state adjustment the residual HW term need not be positive for HW predictions to remain KO-heavy. FULL’s declared redundant KD subspace further limits attribution. No causal-importance or feature-selection claim.

## Explicit answers to the twelve interpretation questions

1. **Context alone?** Yes: conditional delta−0.009988,7/9 favorable, both paired intervals favorable, with overdispersion and some yearly losses.
2. **MIN beyond context?** Yes:−0.026239,9/9 favorable, better Brier/AUC and both intervals favorable. CLEAR_SUCCESS with stated calibration limitations.
3. **FULL beyond MIN?** No supported incremental value: conditional+0.004324,7/9 worse, composed+0.002147 and Brier worse. CURRENT_SPECIFICATION_NOT_SUPPORTED for this addition.
4. **Calibrated?** Imperfect: MIN slope0.831 and ECE3.14%, mean KO1.97 percentage points too high; some reliable high-probability grouping but tail/subgroup gaps. No calibration wrapper or claim of universal calibration.
5. **Heavyweight?** Yes: MIN76.9% conditional KO versus77.5% observed; LHW74.7% versus74.1%.
6. **Flyweight balanced?** Relatively: MIN56.0% versus52.1%; much less UFC-wide KO-heavy, although C1 at53.5% is closer.
7. **Striking archetypes toward KO?** Yes for A1/A4; A2 directionally with moderate uncertainty. A3 is less well matched.
8. **Grappling toward submission?** Yes relative to context, incompletely. B3/B5 still roughly9 conditional points too KO-heavy and have important composed submission deficits.
9. **Persistence?** MIN improves all nine years and all three fixed predictive eras; strongest year contributes17.18%, not a single-era artifact.
10. **Complete-system improvement?** Yes for S2 vs S0/S1 in multiclass log loss/Brier,9/9 years and favorable paired uncertainty. Submission class reliability does not uniformly improve.
11. **Largest remaining node errors?** Frozen F contributes0.670238 of S2 log loss versus0.305516 weighted conditional-method contribution and overpredicts decision rate by2.32 points. This suggests a substantial finish/survival limitation in several pathways. Raw entropy/loss terms are different targets, so they do not prove which node has the largest reducible error; K’s submission gaps also remain material.
12. **Useful for a future simulator?** Retain the two-node predictive reference architecture, especially MIN; no causal hazard/transition interpretation or simulator implementation follows. Structural coherence and predictive gains coexist with unresolved calibration.

## Boundaries, evidence and closeout

2026 ends at the frozen August15 snapshot and is partial. Historical evolution, repeated fighters, selection of finish-only training targets, limited rare-division/archetype samples and F-node errors constrain interpretation. Career states are existing PIT histories, not truncated/rebuilt at2015. These are probabilities for a conditional target scored at pre-fight states, not empirical labels for hypothetical decision-fight finish methods. Descriptive cross-tabs are overlapping and not causal or multiplicity-controlled hypothesis tests. FULL multicollinearity is disclosed.

All29 requested artifact families are persisted, including fitted JSON records, every score table, fold/preprocessing/solver/swap provenance, calibration/uncertainty/bucket/division/archetype/terrain/coefficient reports, three-way probabilities, pathway/simulator reports and completion marker. `EVIDENCE_MANIFEST.json` hashes every evidence file except itself; the final handoff records its digest. `RUN_MANIFEST.json` pins the implementation and immutable inputs. Runtime validation precedes all interpretation. Five independent synthetic tests pass. CI independently regenerates the complete predictions within1e−12.

No DATA/F02/MOV0/terrain/archetype/audit/contract changes, odds/ROI/EV, new predictors, new hierarchy or nonlinear model, posthoc recalibration or simulator code. No merge. Stop after reporting.
