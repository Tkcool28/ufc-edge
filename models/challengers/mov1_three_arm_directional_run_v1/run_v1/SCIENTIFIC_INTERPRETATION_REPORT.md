# MOV1 three-arm directional challenger V1 — scientific interpretation

| Arm | Conditional LL | Conditional Brier | ECE | Calibration intercept | Calibration slope | AUC | Composed LL | Composed Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.615366 | 0.213614 | 0.031387 | 0.010552 | 0.830658 | 0.663563 | 0.975754 | 0.586206 |
| B | 0.615496 | 0.213621 | 0.030891 | 0.008243 | 0.833447 | 0.663617 | 0.975819 | 0.586200 |
| C | 0.607777 | 0.210100 | 0.021438 | -0.037952 | 0.971148 | 0.678643 | 0.971987 | 0.584547 |

| Comparison | Classification | LL delta | Brier delta | Favorable years |
| --- | --- | --- | --- | --- |
| C-A | SUPPORTED_IMPROVEMENT | -0.007589 | -0.003514 | 8 |
| B-A | INCONCLUSIVE | 0.000130 | 0.000007 | 5 |
| C-B | SUPPORTED_IMPROVEMENT | -0.007719 | -0.003521 | 8 |

## Representation isolation: B versus A

INCONCLUSIVE. This tests only the appended submission cross-sum, under independently inner-selected regularization.

## Compact model: C versus A

SUPPORTED_IMPROVEMENT. The primary conclusion applies the frozen pooled/paired/Brier/annual and leave-one-year-out criteria.

## Compact versus augmented MIN: C versus B

SUPPORTED_IMPROVEMENT. Multiple representation choices change; no removed-feature causal attribution.

C-A: fight LL interval [-0.012874191500551064, -0.0023226695143039153]; event LL interval [-0.012643088392909198, -0.002576557959326584]; 8/9 favorable years; median annual delta -0.004842; leave-one-year-out deltas {'2018': -0.007942120049142593, '2019': -0.006767180492113781, '2020': -0.006600348402408885, '2021': -0.006577872682158726, '2022': -0.008335831827321677, '2023': -0.00894826029454393, '2024': -0.006959257684829278, '2025': -0.008305875234414081, '2026': -0.007903611169860719}. All unfavorable and partial2026 folds are retained.

B-A: fight LL interval [-0.0005531470204500954, 0.0008226101777543724]; event LL interval [-0.0005278672011185244, 0.0008236249025475184]; 5/9 favorable years; median annual delta -0.000000; leave-one-year-out deltas {'2018': 0.0002260335068959632, '2019': 0.00013092864433795356, '2020': -5.119300101905979e-05, '2021': 0.00022676928903022256, '2022': 1.1524024612029144e-05, '2023': 0.000270897943974531, '2024': 0.00017660147220047116, '2025': 3.721897132244484e-05, '2026': 0.00014247575655529658}. All unfavorable and partial2026 folds are retained.

C-B: fight LL interval [-0.013816453661075569, -0.0017236464716830914]; event LL interval [-0.013571875069738825, -0.0021340948993528036]; 8/9 favorable years; median annual delta -0.004266; leave-one-year-out deltas {'2018': -0.008168153556038556, '2019': -0.006898109136451734, '2020': -0.006549155401389825, '2021': -0.006804641971188948, '2022': -0.008347355851933705, '2023': -0.009219158238518462, '2024': -0.00713585915702975, '2025': -0.008343094205736526, '2026': -0.008046086926416016}. All unfavorable and partial2026 folds are retained.

## B3_TD_ACCESS_PLUS_SUB_PRESSURE

# B3_TD_ACCESS_PLUS_SUB_PRESSURE

| Arm | N | Actual SUB | Predicted SUB | Predicted KO | Abs gap | Log loss | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 224 | 0.540179 | 0.447894 | 0.552106 | 0.092285 | 0.702464 | 0.253128 |
| B | 224 | 0.540179 | 0.446069 | 0.553931 | 0.094110 | 0.703914 | 0.253679 |
| C | 224 | 0.540179 | 0.440088 | 0.559912 | 0.100091 | 0.702832 | 0.252792 |

Individual-fight losses are retained in FIGHT_LEVEL_EVIDENCE.csv.xz. Prediction quantiles/histograms, all annual and completeness strata are in PANEL_METRICS.json; paired annual deltas and both uncertainty variants are in PATHWAY_UNCERTAINTY.json. These overlapping, repeatedly inspected cells are developmental diagnostics.

C-A: INCONCLUSIVE. LL delta 0.000368; Brier delta -0.000336; fight LL interval [-0.017129926467803085, 0.01731837656365919]; event LL interval [-0.015110029014675426, 0.016025652833186122].

B-A: NOT_SUPPORTED. LL delta 0.001450; Brier delta 0.000551; fight LL interval [-0.0010044011741336923, 0.004062223508801249]; event LL interval [-0.0010051700982988325, 0.0040827405707374075].

C-B: INCONCLUSIVE. LL delta -0.001083; Brier delta -0.000887; fight LL interval [-0.01863043012788052, 0.015893296489711894]; event LL interval [-0.01660759136056302, 0.014487869670643236].

Lower average KO alone does not establish correction. Coefficients and directional inputs are associative representations, not causal pathway/hazard estimates.


## B5_SUB_PRESSURE_VS_SUB_VULNERABILITY

# B5_SUB_PRESSURE_VS_SUB_VULNERABILITY

| Arm | N | Actual SUB | Predicted SUB | Predicted KO | Abs gap | Log loss | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 355 | 0.549296 | 0.459486 | 0.540514 | 0.089810 | 0.706751 | 0.256122 |
| B | 355 | 0.549296 | 0.462942 | 0.537058 | 0.086353 | 0.706938 | 0.256102 |
| C | 355 | 0.549296 | 0.480572 | 0.519428 | 0.068723 | 0.682100 | 0.244638 |

Individual-fight losses are retained in FIGHT_LEVEL_EVIDENCE.csv.xz. Prediction quantiles/histograms, all annual and completeness strata are in PANEL_METRICS.json; paired annual deltas and both uncertainty variants are in PATHWAY_UNCERTAINTY.json. These overlapping, repeatedly inspected cells are developmental diagnostics.

C-A: SUPPORTED_CELL_IMPROVEMENT. LL delta -0.024651; Brier delta -0.011484; fight LL interval [-0.041223030573647554, -0.008423554692381624]; event LL interval [-0.04189332812226898, -0.008209481368256699].

B-A: INCONCLUSIVE. LL delta 0.000187; Brier delta -0.000020; fight LL interval [-0.0018452723201269833, 0.002269068842126195]; event LL interval [-0.0019309322989877668, 0.002525809731798915].

C-B: SUPPORTED_CELL_IMPROVEMENT. LL delta -0.024838; Brier delta -0.011464; fight LL interval [-0.04127882323634402, -0.008665446103259594]; event LL interval [-0.04152570420373924, -0.008570965261389198].

Lower average KO alone does not establish correction. Coefficients and directional inputs are associative representations, not causal pathway/hazard estimates.


## Striking and division preservation

| Cell | Comparison | Status | LL delta | Brier delta |
| --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | C-A | RETAINED_SUPPORTED | -0.003948 | -0.002594 |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | B-A | RETAINED_SUPPORTED | 0.000105 | -0.000078 |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | C-B | RETAINED_SUPPORTED | -0.004053 | -0.002516 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | C-A | THIN_DESCRIPTIVE | -0.002077 | -0.001750 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | B-A | THIN_DESCRIPTIVE | 0.001646 | 0.000406 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | C-B | THIN_DESCRIPTIVE | -0.003723 | -0.002156 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | C-A | RETAINED_SUPPORTED | -0.002478 | -0.001802 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | B-A | RETAINED_SUPPORTED | 0.000116 | 0.000034 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | C-B | RETAINED_SUPPORTED | -0.002594 | -0.001836 |
| Heavyweight | C-A | UNCERTAIN | 0.000331 | -0.000429 |
| Heavyweight | B-A | RETAINED_SUPPORTED | 0.000270 | 0.000034 |
| Heavyweight | C-B | UNCERTAIN | 0.000060 | -0.000463 |
| Light Heavyweight | C-A | UNCERTAIN | -0.004852 | -0.003543 |
| Light Heavyweight | B-A | RETAINED_SUPPORTED | 0.001141 | 0.000381 |
| Light Heavyweight | C-B | RETAINED_SUPPORTED | -0.005993 | -0.003925 |

All13 governed division reports retain men/women Flyweight and women Strawweight separately. Detailed annual/terrain/archetype/completeness cells, including thin/empty/unknown samples and all15 archetypes, remain in the full tables. No probability shifts or feature changes follow from a preservation failure.

## Complete system

| Comparison | Classification | LL delta | Summed Brier delta |
| --- | --- | --- | --- |
| C-A | SUPPORTED_IMPROVEMENT | -0.003768 | -0.001659 |
| B-A | INCONCLUSIVE | 0.000065 | -0.000007 |
| C-B | SUPPORTED_IMPROVEMENT | -0.003832 | -0.001653 |

Decision probabilities are exactly unchanged. Conditional and composed LL differences are algebraically related; multiclass Brier and classwise calibration add distinct evidence.

## Forward confirmation and next milestone

Historical results remain developmental, motivated by repeatedly inspected samples. Conditional2026 fixed-model records are saved; independent confirmation requires prospective pre-event source/prediction snapshots and sealed outcomes under the existing protocol. No forward predictions or enrollment performed here. Forward complete-system enrollment remains BLOCKED_MISSING_FROZEN_MOV0_RECORD; no MOV0 retraining or replacement. The next scientific milestone is prospective confirmation of these frozen specifications, alongside separately authorized preservation-only MOV0 record recovery if composed confirmation is desired. If compact specification is not supported, retain the reference and treat alternatives as requiring a new preregistration rather than repairing C posthoc.

## Limitations

Paired bootstrap conditions on fixed fitted OOF predictions; event clustering does not eliminate repeat-fighter dependence or overlapping training. Sparse calibration/AUC/metrics are suppressed under frozen gates; archetype overlap and previous inspection limit group inference. Source exposure is not measured causal susceptibility. Coefficients are associations, not mechanistic/hazard estimates. No sportsbook/ROI/EV, simulator, recalibration or automatic model promotion.
