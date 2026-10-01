# B3 focused diagnostic

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

**B3_TD_ACCESS_PLUS_SUB_PRESSURE**: 224 finishes (NORMAL); observed KO 46.0%, SUB 54.0%. XGB: KO 57.5%, SUB 42.5%, gap +11.50 pp; LL delta -0.010396, Brier delta -0.004135; absolute mean gap widens by 2.27 pp. LGBM: KO 57.1%, SUB 42.9%, gap +11.16 pp; LL delta -0.017031, Brier delta -0.007382; absolute mean gap widens by 1.93 pp. CAT: KO 57.2%, SUB 42.8%, gap +11.27 pp; LL delta -0.019306, Brier delta -0.008473; absolute mean gap widens by 2.04 pp.

XGB moves toward submission in 2/9 observed annual group means; loss improves in 3/6 years meeting the 25-finish reporting gate. Annual subgroup means and counts are retained for all nine years; unavailable gated losses are blank. Mean movement is not equivalent to stable loss improvement.

LGBM moves toward submission in 4/9 observed annual group means; loss improves in 4/6 years meeting the 25-finish reporting gate. Annual subgroup means and counts are retained for all nine years; unavailable gated losses are blank. Mean movement is not equivalent to stable loss improvement.

CAT moves toward submission in 2/9 observed annual group means; loss improves in 4/6 years meeting the 25-finish reporting gate. Annual subgroup means and counts are retained for all nine years; unavailable gated losses are blank. Mean movement is not equivalent to stable loss improvement.

| model | all_N | finish_N | actual_KO | mean_KO | mean_SUB | gap | log_loss | brier | ll_delta_MIN | brier_delta_MIN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LINEAR_MIN | 412 | 224 | 0.459821 | 0.552106 | 0.447894 | 0.092285 | 0.702464 | 0.253128 | 0.000000 | 0.000000 |
| XGB | 412 | 224 | 0.459821 | 0.574853 | 0.425147 | 0.115032 | 0.692068 | 0.248992 | -0.010396 | -0.004135 |
| LGBM | 412 | 224 | 0.459821 | 0.571403 | 0.428597 | 0.111581 | 0.685433 | 0.245746 | -0.017031 | -0.007382 |
| CAT | 412 | 224 | 0.459821 | 0.572499 | 0.427501 | 0.112678 | 0.683159 | 0.244654 | -0.019306 | -0.008473 |
| SELECT | 412 | 224 | 0.459821 | 0.568422 | 0.431578 | 0.108600 | 0.691117 | 0.247990 | -0.011348 | -0.005137 |

## All annual coverage

| year | model | finish_N | finish_gate | actual_KO | mean_KO | log_loss | ll_delta_MIN | brier_delta_MIN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | LINEAR_MIN | 28 | THIN_EXPLORATORY | 0.464286 | 0.548318 | 0.629473 | 0.000000 | 0.000000 |
| 2019 | LINEAR_MIN | 21 | INSUFFICIENT | 0.571429 | 0.525302 | — | — | — |
| 2020 | LINEAR_MIN | 18 | INSUFFICIENT | 0.500000 | 0.526188 | — | — | — |
| 2021 | LINEAR_MIN | 29 | THIN_EXPLORATORY | 0.413793 | 0.557294 | 0.741516 | 0.000000 | 0.000000 |
| 2022 | LINEAR_MIN | 32 | THIN_EXPLORATORY | 0.468750 | 0.548772 | 0.714117 | 0.000000 | 0.000000 |
| 2023 | LINEAR_MIN | 31 | THIN_EXPLORATORY | 0.419355 | 0.555231 | 0.650340 | 0.000000 | 0.000000 |
| 2024 | LINEAR_MIN | 25 | THIN_EXPLORATORY | 0.440000 | 0.610040 | 0.761343 | 0.000000 | 0.000000 |
| 2025 | LINEAR_MIN | 27 | THIN_EXPLORATORY | 0.444444 | 0.542907 | 0.730502 | 0.000000 | 0.000000 |
| 2026 | LINEAR_MIN | 13 | INSUFFICIENT | 0.461538 | 0.536328 | — | — | — |
| 2018 | XGB | 28 | THIN_EXPLORATORY | 0.464286 | 0.530629 | 0.685952 | 0.056479 | 0.026086 |
| 2019 | XGB | 21 | INSUFFICIENT | 0.571429 | 0.505542 | — | — | — |
| 2020 | XGB | 18 | INSUFFICIENT | 0.500000 | 0.572588 | — | — | — |
| 2021 | XGB | 29 | THIN_EXPLORATORY | 0.413793 | 0.598560 | 0.724207 | -0.017309 | -0.006637 |
| 2022 | XGB | 32 | THIN_EXPLORATORY | 0.468750 | 0.582941 | 0.714351 | 0.000234 | 0.001173 |
| 2023 | XGB | 31 | THIN_EXPLORATORY | 0.419355 | 0.609238 | 0.657174 | 0.006834 | 0.004392 |
| 2024 | XGB | 25 | THIN_EXPLORATORY | 0.440000 | 0.610763 | 0.730448 | -0.030896 | -0.009118 |
| 2025 | XGB | 27 | THIN_EXPLORATORY | 0.444444 | 0.574205 | 0.685920 | -0.044582 | -0.022418 |
| 2026 | XGB | 13 | INSUFFICIENT | 0.461538 | 0.562705 | — | — | — |
| 2018 | LGBM | 28 | THIN_EXPLORATORY | 0.464286 | 0.512665 | 0.653284 | 0.023811 | 0.010529 |
| 2019 | LGBM | 21 | INSUFFICIENT | 0.571429 | 0.517397 | — | — | — |
| 2020 | LGBM | 18 | INSUFFICIENT | 0.500000 | 0.567033 | — | — | — |
| 2021 | LGBM | 29 | THIN_EXPLORATORY | 0.413793 | 0.597421 | 0.724402 | -0.017114 | -0.006938 |
| 2022 | LGBM | 32 | THIN_EXPLORATORY | 0.468750 | 0.587253 | 0.703665 | -0.010452 | -0.004256 |
| 2023 | LGBM | 31 | THIN_EXPLORATORY | 0.419355 | 0.605593 | 0.658290 | 0.007950 | 0.004811 |
| 2024 | LGBM | 25 | THIN_EXPLORATORY | 0.440000 | 0.602490 | 0.708930 | -0.052413 | -0.018934 |
| 2025 | LGBM | 27 | THIN_EXPLORATORY | 0.444444 | 0.581785 | 0.693188 | -0.037314 | -0.018986 |
| 2026 | LGBM | 13 | INSUFFICIENT | 0.461538 | 0.531273 | — | — | — |
| 2018 | CAT | 28 | THIN_EXPLORATORY | 0.464286 | 0.528507 | 0.636990 | 0.007518 | 0.003095 |
| 2019 | CAT | 21 | INSUFFICIENT | 0.571429 | 0.540611 | — | — | — |
| 2020 | CAT | 18 | INSUFFICIENT | 0.500000 | 0.557396 | — | — | — |
| 2021 | CAT | 29 | THIN_EXPLORATORY | 0.413793 | 0.562961 | 0.707947 | -0.033568 | -0.014911 |
| 2022 | CAT | 32 | THIN_EXPLORATORY | 0.468750 | 0.577900 | 0.676728 | -0.037389 | -0.015691 |
| 2023 | CAT | 31 | THIN_EXPLORATORY | 0.419355 | 0.609304 | 0.666640 | 0.016300 | 0.008553 |
| 2024 | CAT | 25 | THIN_EXPLORATORY | 0.440000 | 0.600990 | 0.726490 | -0.034853 | -0.013828 |
| 2025 | CAT | 27 | THIN_EXPLORATORY | 0.444444 | 0.592315 | 0.713715 | -0.016787 | -0.008925 |
| 2026 | CAT | 13 | INSUFFICIENT | 0.461538 | 0.563950 | — | — | — |
| 2018 | SELECT | 28 | THIN_EXPLORATORY | 0.464286 | 0.530629 | 0.685952 | 0.056479 | 0.026086 |
| 2019 | SELECT | 21 | INSUFFICIENT | 0.571429 | 0.505542 | — | — | — |
| 2020 | SELECT | 18 | INSUFFICIENT | 0.500000 | 0.567033 | — | — | — |
| 2021 | SELECT | 29 | THIN_EXPLORATORY | 0.413793 | 0.562961 | 0.707947 | -0.033568 | -0.014911 |
| 2022 | SELECT | 32 | THIN_EXPLORATORY | 0.468750 | 0.587253 | 0.703665 | -0.010452 | -0.004256 |
| 2023 | SELECT | 31 | THIN_EXPLORATORY | 0.419355 | 0.609304 | 0.666640 | 0.016300 | 0.008553 |
| 2024 | SELECT | 25 | THIN_EXPLORATORY | 0.440000 | 0.600990 | 0.726490 | -0.034853 | -0.013828 |
| 2025 | SELECT | 27 | THIN_EXPLORATORY | 0.444444 | 0.581785 | 0.693188 | -0.037314 | -0.018986 |
| 2026 | SELECT | 13 | INSUFFICIENT | 0.461538 | 0.531273 | — | — | — |

## Descriptive paired intervals

| model | metric | N | event_N | delta | fight_paired_95 | event_paired_95 |
| --- | --- | --- | --- | --- | --- | --- |
| XGB | log_loss | 224 | 168 | -0.010396 | [-0.03930296091055062, 0.017787141435671564] | [-0.03865378197013157, 0.01639884395991253] |
| XGB | brier | 224 | 168 | -0.004135 | [-0.017276782964591435, 0.008869884749229562] | [-0.017220098603976233, 0.00802954394727505] |
| LGBM | log_loss | 224 | 168 | -0.017031 | [-0.04571989522738265, 0.011803945779312966] | [-0.045198377532387826, 0.008905977537310567] |
| LGBM | brier | 224 | 168 | -0.007382 | [-0.020469888058241167, 0.005671681757429449] | [-0.02040451804641552, 0.004154941248563417] |
| CAT | log_loss | 224 | 168 | -0.019306 | [-0.047709525051699606, 0.008869951250724007] | [-0.04643123815872292, 0.006148377503444738] |
| CAT | brier | 224 | 168 | -0.008473 | [-0.02115755799631612, 0.00444963361180189] | [-0.020633078118557045, 0.0033425616716869335] |

Representative examples are chosen from predictions alone, with successful and unsuccessful shifts visible. See `REPRESENTATIVE_FIGHT_DISAGREEMENTS.csv` and the complete primary-cell fight-level differences.
