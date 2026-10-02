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
