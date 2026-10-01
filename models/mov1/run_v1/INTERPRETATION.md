# Separate frozen-run conclusions

Conditional MIN beyond C1: **CLEAR_SUCCESS**. Delta log loss −0.026239,9/9 favorable years, both paired95 intervals favorable, Brier/AUC improved. Calibration is imperfect: slope0.831, mean KO66.3% versus64.3%, ECE3.14%, grappling and women’s subgroup gaps. Do not equate predictive improvement with perfect calibration.

Composed S2 beyond S1/S0: **CLEAR_SUCCESS**. Multiclass log loss0.975754 and Brier0.586206, improvements across9/9 years with favorable uncertainty. KO reliability improves versus context, but submission ECE rises from0.00731 (S1) to0.02472 (S2). Decision predictions remain unchanged and overpredict prevalence by2.32 percentage points. This is improvement of the complete system with disclosed classwise tradeoffs, not universal calibration success.

Context vs prevalence: **CLEAR_SUCCESS**, smaller/mixed-year benefit (7/9 favorable), both intervals favorable and Brier improved; overdispersed C1 calibration is a limitation. C0’s near-zero coarse ECE reflects very little resolution, not an ability to discriminate individual methods. C0 pooled calibration slope is unstable/negative across nearly constant fold prevalences; per-year slope is undefined by constant prediction.

FULL vs MIN: **CURRENT_SPECIFICATION_NOT_SUPPORTED** as an incremental surface. Conditional delta+0.004324 with7/9 worse years; both conditional intervals positive. Composed delta+0.002147 with7/9 worse and Brier worse; fight interval barely crosses zero, while event interval is slightly positive. FULL’s calibration slope/ECE are worse than MIN. FULL still beats S0/S1 overall. This conclusion does not delete any FULL feature, tune the experiment or reject every future broader model.

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

Classifications are narrative applications of the frozen evidence dimensions, not new numeric acceptance gates or automatic promotion. Conditional and composed log-loss evidence are mathematically related with a shared F node; classwise reliability and multiclass Brier supply distinct checks. Bootstrap intervals condition on these fitted OOF predictions, retain training overlap and repeated-fighter dependence, and are not simultaneous subgroup tests.
