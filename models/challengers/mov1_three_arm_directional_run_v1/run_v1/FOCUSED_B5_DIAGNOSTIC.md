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
