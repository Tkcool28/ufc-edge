# B5 focused diagnostic

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

**B5_SUB_PRESSURE_VS_SUB_VULNERABILITY**: 355 finishes (NORMAL); observed KO 45.1%, SUB 54.9%. XGB: KO 53.3%, SUB 46.7%, gap +8.20 pp; LL delta -0.018359, Brier delta -0.008405; absolute mean gap narrows by 0.78 pp. LGBM: KO 53.1%, SUB 46.9%, gap +8.02 pp; LL delta -0.016468, Brier delta -0.007538; absolute mean gap narrows by 0.96 pp. CAT: KO 52.6%, SUB 47.4%, gap +7.53 pp; LL delta -0.019270, Brier delta -0.008752; absolute mean gap narrows by 1.45 pp.

XGB moves toward submission in 6/9 observed annual group means; loss improves in 6/8 years meeting the 25-finish reporting gate. Annual subgroup means and counts are retained for all nine years; unavailable gated losses are blank. Mean movement is not equivalent to stable loss improvement.

LGBM moves toward submission in 5/9 observed annual group means; loss improves in 5/8 years meeting the 25-finish reporting gate. Annual subgroup means and counts are retained for all nine years; unavailable gated losses are blank. Mean movement is not equivalent to stable loss improvement.

CAT moves toward submission in 7/9 observed annual group means; loss improves in 5/8 years meeting the 25-finish reporting gate. Annual subgroup means and counts are retained for all nine years; unavailable gated losses are blank. Mean movement is not equivalent to stable loss improvement.

| model | all_N | finish_N | actual_KO | mean_KO | mean_SUB | gap | log_loss | brier | ll_delta_MIN | brier_delta_MIN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LINEAR_MIN | 591 | 355 | 0.450704 | 0.540514 | 0.459486 | 0.089810 | 0.706751 | 0.256122 | 0.000000 | 0.000000 |
| XGB | 591 | 355 | 0.450704 | 0.532728 | 0.467272 | 0.082024 | 0.688393 | 0.247717 | -0.018359 | -0.008405 |
| LGBM | 591 | 355 | 0.450704 | 0.530900 | 0.469100 | 0.080196 | 0.690283 | 0.248584 | -0.016468 | -0.007538 |
| CAT | 591 | 355 | 0.450704 | 0.526043 | 0.473957 | 0.075339 | 0.687481 | 0.247370 | -0.019270 | -0.008752 |
| SELECT | 591 | 355 | 0.450704 | 0.525692 | 0.474308 | 0.074988 | 0.692813 | 0.249867 | -0.013938 | -0.006255 |

## All annual coverage

| year | model | finish_N | finish_gate | actual_KO | mean_KO | log_loss | ll_delta_MIN | brier_delta_MIN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | LINEAR_MIN | 58 | MODERATE_UNCERTAINTY | 0.465517 | 0.546168 | 0.676380 | 0.000000 | 0.000000 |
| 2019 | LINEAR_MIN | 41 | THIN_EXPLORATORY | 0.487805 | 0.552249 | 0.736307 | 0.000000 | 0.000000 |
| 2020 | LINEAR_MIN | 41 | THIN_EXPLORATORY | 0.439024 | 0.520229 | 0.841359 | 0.000000 | 0.000000 |
| 2021 | LINEAR_MIN | 43 | THIN_EXPLORATORY | 0.465116 | 0.547700 | 0.728184 | 0.000000 | 0.000000 |
| 2022 | LINEAR_MIN | 35 | THIN_EXPLORATORY | 0.485714 | 0.523250 | 0.694018 | 0.000000 | 0.000000 |
| 2023 | LINEAR_MIN | 45 | THIN_EXPLORATORY | 0.422222 | 0.524839 | 0.685376 | 0.000000 | 0.000000 |
| 2024 | LINEAR_MIN | 36 | THIN_EXPLORATORY | 0.472222 | 0.566188 | 0.682772 | 0.000000 | 0.000000 |
| 2025 | LINEAR_MIN | 40 | THIN_EXPLORATORY | 0.425000 | 0.548366 | 0.648281 | 0.000000 | 0.000000 |
| 2026 | LINEAR_MIN | 16 | INSUFFICIENT | 0.312500 | 0.527076 | — | — | — |
| 2018 | XGB | 58 | MODERATE_UNCERTAINTY | 0.465517 | 0.522675 | 0.675354 | -0.001026 | 0.000268 |
| 2019 | XGB | 41 | THIN_EXPLORATORY | 0.487805 | 0.520349 | 0.686209 | -0.050098 | -0.023085 |
| 2020 | XGB | 41 | THIN_EXPLORATORY | 0.439024 | 0.522674 | 0.737049 | -0.104311 | -0.047659 |
| 2021 | XGB | 43 | THIN_EXPLORATORY | 0.465116 | 0.547450 | 0.713188 | -0.014996 | -0.006779 |
| 2022 | XGB | 35 | THIN_EXPLORATORY | 0.485714 | 0.541422 | 0.690689 | -0.003328 | 0.000026 |
| 2023 | XGB | 45 | THIN_EXPLORATORY | 0.422222 | 0.530814 | 0.690231 | 0.004855 | 0.001086 |
| 2024 | XGB | 36 | THIN_EXPLORATORY | 0.472222 | 0.552586 | 0.681019 | -0.001753 | -0.002034 |
| 2025 | XGB | 40 | THIN_EXPLORATORY | 0.425000 | 0.536693 | 0.656230 | 0.007949 | 0.003976 |
| 2026 | XGB | 16 | INSUFFICIENT | 0.312500 | 0.518866 | — | — | — |
| 2018 | LGBM | 58 | MODERATE_UNCERTAINTY | 0.465517 | 0.517766 | 0.659553 | -0.016827 | -0.007141 |
| 2019 | LGBM | 41 | THIN_EXPLORATORY | 0.487805 | 0.523884 | 0.668842 | -0.067465 | -0.031552 |
| 2020 | LGBM | 41 | THIN_EXPLORATORY | 0.439024 | 0.505922 | 0.756002 | -0.085358 | -0.039471 |
| 2021 | LGBM | 43 | THIN_EXPLORATORY | 0.465116 | 0.549846 | 0.713137 | -0.015047 | -0.006861 |
| 2022 | LGBM | 35 | THIN_EXPLORATORY | 0.485714 | 0.545677 | 0.691315 | -0.002702 | 0.000326 |
| 2023 | LGBM | 45 | THIN_EXPLORATORY | 0.422222 | 0.529216 | 0.697006 | 0.011630 | 0.004577 |
| 2024 | LGBM | 36 | THIN_EXPLORATORY | 0.472222 | 0.544773 | 0.702750 | 0.019978 | 0.008741 |
| 2025 | LGBM | 40 | THIN_EXPLORATORY | 0.425000 | 0.549388 | 0.671161 | 0.022879 | 0.011323 |
| 2026 | LGBM | 16 | INSUFFICIENT | 0.312500 | 0.504567 | — | — | — |
| 2018 | CAT | 58 | MODERATE_UNCERTAINTY | 0.465517 | 0.521180 | 0.661266 | -0.015114 | -0.006422 |
| 2019 | CAT | 41 | THIN_EXPLORATORY | 0.487805 | 0.544776 | 0.685925 | -0.050382 | -0.023795 |
| 2020 | CAT | 41 | THIN_EXPLORATORY | 0.439024 | 0.494292 | 0.744849 | -0.096510 | -0.044551 |
| 2021 | CAT | 43 | THIN_EXPLORATORY | 0.465116 | 0.514606 | 0.709560 | -0.018624 | -0.008695 |
| 2022 | CAT | 35 | THIN_EXPLORATORY | 0.485714 | 0.525954 | 0.669394 | -0.024624 | -0.010431 |
| 2023 | CAT | 45 | THIN_EXPLORATORY | 0.422222 | 0.515985 | 0.694927 | 0.009551 | 0.003926 |
| 2024 | CAT | 36 | THIN_EXPLORATORY | 0.472222 | 0.548162 | 0.689337 | 0.006564 | 0.002820 |
| 2025 | CAT | 40 | THIN_EXPLORATORY | 0.425000 | 0.553141 | 0.683213 | 0.034932 | 0.017283 |
| 2026 | CAT | 16 | INSUFFICIENT | 0.312500 | 0.518745 | — | — | — |
| 2018 | SELECT | 58 | MODERATE_UNCERTAINTY | 0.465517 | 0.522675 | 0.675354 | -0.001026 | 0.000268 |
| 2019 | SELECT | 41 | THIN_EXPLORATORY | 0.487805 | 0.520349 | 0.686209 | -0.050098 | -0.023085 |
| 2020 | SELECT | 41 | THIN_EXPLORATORY | 0.439024 | 0.505922 | 0.756002 | -0.085358 | -0.039471 |
| 2021 | SELECT | 43 | THIN_EXPLORATORY | 0.465116 | 0.514606 | 0.709560 | -0.018624 | -0.008695 |
| 2022 | SELECT | 35 | THIN_EXPLORATORY | 0.485714 | 0.545677 | 0.691315 | -0.002702 | 0.000326 |
| 2023 | SELECT | 45 | THIN_EXPLORATORY | 0.422222 | 0.515985 | 0.694927 | 0.009551 | 0.003926 |
| 2024 | SELECT | 36 | THIN_EXPLORATORY | 0.472222 | 0.548162 | 0.689337 | 0.006564 | 0.002820 |
| 2025 | SELECT | 40 | THIN_EXPLORATORY | 0.425000 | 0.549388 | 0.671161 | 0.022879 | 0.011323 |
| 2026 | SELECT | 16 | INSUFFICIENT | 0.312500 | 0.504567 | — | — | — |

## Descriptive paired intervals

| model | metric | N | event_N | delta | fight_paired_95 | event_paired_95 |
| --- | --- | --- | --- | --- | --- | --- |
| XGB | log_loss | 355 | 225 | -0.018359 | [-0.04168654370371603, 0.005383128336511213] | [-0.04274018853790275, 0.0036869928176987738] |
| XGB | brier | 355 | 225 | -0.008405 | [-0.018783766524871005, 0.002479127683522919] | [-0.01903052630200537, 0.0013732539043489053] |
| LGBM | log_loss | 355 | 225 | -0.016468 | [-0.038774238085615455, 0.006379793863891318] | [-0.03870996585711311, 0.005365466455321802] |
| LGBM | brier | 355 | 225 | -0.007538 | [-0.01758195761414838, 0.002702399218591829] | [-0.017574368058610942, 0.0022075383487415645] |
| CAT | log_loss | 355 | 225 | -0.019270 | [-0.041076291088412424, 0.003452573120230001] | [-0.0424280070602303, 0.0029135700428084394] |
| CAT | brier | 355 | 225 | -0.008752 | [-0.01874461392273556, 0.0014167912578043863] | [-0.01934858354613591, 0.0011397097748933127] |

Representative examples are chosen from predictions alone, with successful and unsuccessful shifts visible. See `REPRESENTATIVE_FIGHT_DISAGREEMENTS.csv` and the complete primary-cell fight-level differences.
