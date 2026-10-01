# MOV0 hierarchical / partial-pooling challenger V1

All 18 chronological fits passed preregistered convergence gates. First H1 repeat verified posterior and prediction equality. Frozen reference was read, never refit.

Contract commit: `30b14dc5b355e9356dbdd80c793ab6d6feedf861`.

## Aggregate

| Surface | Log loss | Brier | AUC | ECE | Cal intercept | Cal slope |
|---|---|---|---|---|---|---|
| H0 | 0.670238 | 0.238630 | 0.627456 | 0.032872 | 0.080259 | 0.832109 |
| H1 | 0.672588 | 0.239613 | 0.625387 | 0.038392 | 0.075880 | 0.763611 |
| H2 | 0.672584 | 0.239557 | 0.626464 | 0.036634 | 0.077436 | 0.758541 |

## Paired uncertainty

- H1_vs_H0: delta +0.002349; years better/worse/tied 2/7/0; fight CI [0.0012648673722293106, 0.0034461238789861054]; event CI [0.001321490958812046, 0.0034431726599451567].
- H2_vs_H0: delta +0.002346; years better/worse/tied 3/6/0; fight CI [0.0007057101486299672, 0.0039651214229155535]; event CI [0.0008206719105691663, 0.003984688914001882].
- H2_vs_H1: delta -0.000004; years better/worse/tied 5/4/0; fight CI [-0.0012083769594823425, 0.0012126245908498485]; event CI [-0.0012422546194738125, 0.0013158572212992518].

## Annual metrics

| Year | Surface | N | Log loss | Brier | AUC | ECE | Cal intercept | Cal slope |
|---|---|---|---|---|---|---|---|---|
| 2018 | H0 | 470 | 0.669133 | 0.237960 | 0.636377 | 0.048066 | 0.147999 | 0.854866 |
| 2019 | H0 | 507 | 0.661071 | 0.234022 | 0.639493 | 0.047785 | -0.122196 | 0.910486 |
| 2020 | H0 | 443 | 0.663498 | 0.235899 | 0.636934 | 0.059656 | 0.104311 | 0.891145 |
| 2021 | H0 | 492 | 0.695822 | 0.250465 | 0.577059 | 0.059175 | -0.000124 | 0.459251 |
| 2022 | H0 | 505 | 0.676156 | 0.241975 | 0.615191 | 0.074586 | 0.269409 | 0.888773 |
| 2023 | H0 | 505 | 0.676335 | 0.241473 | 0.620618 | 0.051738 | 0.121372 | 0.787624 |
| 2024 | H0 | 502 | 0.652875 | 0.230638 | 0.651687 | 0.029370 | -0.122197 | 1.050335 |
| 2025 | H0 | 504 | 0.664926 | 0.235592 | 0.648873 | 0.057962 | 0.130232 | 0.940164 |
| 2026 | H0 | 332 | 0.672925 | 0.240009 | 0.628709 | 0.073068 | 0.272371 | 0.885860 |
| 2018 | H1 | 470 | 0.679422 | 0.242274 | 0.624092 | 0.069910 | 0.132890 | 0.645525 |
| 2019 | H1 | 507 | 0.663649 | 0.235049 | 0.636905 | 0.040896 | -0.124945 | 0.795825 |
| 2020 | H1 | 443 | 0.665688 | 0.236832 | 0.634835 | 0.052160 | 0.096125 | 0.811517 |
| 2021 | H1 | 492 | 0.700078 | 0.252211 | 0.575388 | 0.066220 | -0.003436 | 0.416716 |
| 2022 | H1 | 505 | 0.677996 | 0.242869 | 0.612861 | 0.083502 | 0.267194 | 0.842499 |
| 2023 | H1 | 505 | 0.677190 | 0.241852 | 0.619967 | 0.052712 | 0.121007 | 0.762727 |
| 2024 | H1 | 502 | 0.652417 | 0.230401 | 0.652265 | 0.029109 | -0.121535 | 1.045708 |
| 2025 | H1 | 504 | 0.664083 | 0.235182 | 0.651392 | 0.048705 | 0.134888 | 0.949939 |
| 2026 | H1 | 332 | 0.673213 | 0.240152 | 0.627315 | 0.072684 | 0.268937 | 0.878702 |
| 2018 | H2 | 470 | 0.677245 | 0.241286 | 0.629854 | 0.071046 | 0.140066 | 0.666876 |
| 2019 | H2 | 507 | 0.662591 | 0.234490 | 0.639226 | 0.063214 | -0.119807 | 0.800056 |
| 2020 | H2 | 443 | 0.669017 | 0.238328 | 0.631125 | 0.049628 | 0.097246 | 0.769060 |
| 2021 | H2 | 492 | 0.702683 | 0.253224 | 0.573321 | 0.077427 | -0.008581 | 0.392732 |
| 2022 | H2 | 505 | 0.678564 | 0.243069 | 0.614908 | 0.082740 | 0.264552 | 0.824416 |
| 2023 | H2 | 505 | 0.677030 | 0.241830 | 0.620845 | 0.055607 | 0.123088 | 0.765916 |
| 2024 | H2 | 502 | 0.652703 | 0.230513 | 0.653487 | 0.029247 | -0.118078 | 1.041382 |
| 2025 | H2 | 504 | 0.662666 | 0.234432 | 0.656557 | 0.056150 | 0.139591 | 0.968406 |
| 2026 | H2 | 332 | 0.670661 | 0.238884 | 0.634577 | 0.074052 | 0.271966 | 0.900704 |

## Terrain probability quality

| Dimension / label | N | H0 LL | H1 LL | H2 LL |
|---|---|---|---|---|
| experience_bucket / 0 | 821 | 0.685914 | 0.685567 | 0.684624 |
| experience_bucket / 11+ | 392 | 0.656541 | 0.659722 | 0.660083 |
| experience_bucket / 1–2 | 1169 | 0.675848 | 0.679026 | 0.678958 |
| experience_bucket / 3–5 | 989 | 0.660523 | 0.663190 | 0.665379 |
| experience_bucket / 6–10 | 889 | 0.665234 | 0.668264 | 0.666612 |
| layoff_bucket / 12–18 months | 473 | 0.675541 | 0.680543 | 0.680913 |
| layoff_bucket / 18+ months | 293 | 0.704548 | 0.709196 | 0.712915 |
| layoff_bucket / 6–12 months | 1712 | 0.658876 | 0.661091 | 0.662041 |
| layoff_bucket / < 6 months | 961 | 0.664017 | 0.666904 | 0.664685 |
| layoff_bucket / STRUCTURAL_NA_OR_UNKNOWN | 821 | 0.685914 | 0.685567 | 0.684624 |
| scheduled_duration_bucket / 3_ROUND | 3837 | 0.672112 | 0.673999 | 0.673905 |
| scheduled_duration_bucket / 5_ROUND | 423 | 0.653245 | 0.659783 | 0.660601 |
| title_status / NON_TITLE_BOUT | 4088 | 0.670094 | 0.672377 | 0.672354 |
| title_status / TITLE_BOUT | 172 | 0.673676 | 0.677589 | 0.678056 |
| weight_class / Bantamweight | 485 | 0.673488 | 0.674439 | 0.672486 |
| weight_class / Catch Weight | 59 | 0.686208 | 0.689672 | 0.691518 |
| weight_class / Featherweight | 498 | 0.694509 | 0.696286 | 0.695916 |
| weight_class / Flyweight | 248 | 0.696083 | 0.699976 | 0.700578 |
| weight_class / Heavyweight | 311 | 0.656784 | 0.657028 | 0.659281 |
| weight_class / Interim Bantamweight | 1 | N-only | N-only | N-only |
| weight_class / Interim Featherweight | 1 | N-only | N-only | N-only |
| weight_class / Interim Flyweight | 1 | N-only | N-only | N-only |
| weight_class / Interim Heavyweight | 4 | N-only | N-only | N-only |
| weight_class / Interim Lightweight | 3 | N-only | N-only | N-only |
| weight_class / Interim Middleweight | 1 | N-only | N-only | N-only |
| weight_class / Interim Welterweight | 1 | N-only | N-only | N-only |
| weight_class / Light Heavyweight | 319 | 0.660121 | 0.662068 | 0.663492 |
| weight_class / Lightweight | 571 | 0.670217 | 0.672723 | 0.672278 |
| weight_class / Middleweight | 474 | 0.676655 | 0.681067 | 0.678298 |
| weight_class / Road To UFC 1 Bantamweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Road To UFC 1 Featherweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Road To UFC 1 Lightweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Road to UFC 1 Flyweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Road to UFC 3 Bantamweight Tournament TitleBout | 1 | N-only | N-only | N-only |
| weight_class / Road to UFC 3 Flyweight Tournament TitleBout | 1 | N-only | N-only | N-only |
| weight_class / Road to UFC 3 Women's Strawweight Tournament TitleBout | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 27 Featherweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 27 Lightweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 28 Heavyweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 28 Women's Featherweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 32 Featherweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 32 Middleweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 33 Flyweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Ultimate Fighter 33 Welterweight Tournament | 1 | N-only | N-only | N-only |
| weight_class / Welterweight | 544 | 0.685387 | 0.687897 | 0.687870 |
| weight_class / Women's Bantamweight | 158 | 0.634751 | 0.631189 | 0.631448 |
| weight_class / Women's Featherweight | 26 | 0.653989 | 0.654209 | 0.655504 |
| weight_class / Women's Flyweight | 266 | 0.631606 | 0.634898 | 0.637289 |
| weight_class / Women's Strawweight | 274 | 0.634478 | 0.638885 | 0.641013 |
| completeness_tier / HIGH_MISSINGNESS | 821 | 0.685914 | 0.685567 | 0.684624 |
| completeness_tier / LOW_MISSINGNESS | 3439 | 0.666496 | 0.669489 | 0.669710 |
| striking_environment / STRIKE_LOW | 2332 | 0.665617 | 0.668600 | 0.668809 |
| striking_environment / STRIKE_ONE_SIDED | 939 | 0.671320 | 0.674332 | 0.674543 |
| striking_environment / STRIKE_TWO_SIDED | 168 | 0.651735 | 0.654770 | 0.655202 |
| striking_environment / UNASSIGNABLE_BY_CONTRACT | 821 | 0.685914 | 0.685567 | 0.684624 |
| grappling_environment / GRAPPLE_LOW | 2444 | 0.668205 | 0.671756 | 0.671784 |
| grappling_environment / GRAPPLE_ONE_SIDED | 873 | 0.657655 | 0.658437 | 0.659310 |
| grappling_environment / GRAPPLE_TWO_SIDED | 122 | 0.695520 | 0.703163 | 0.702572 |
| grappling_environment / UNASSIGNABLE_BY_CONTRACT | 821 | 0.685914 | 0.685567 | 0.684624 |
| joint_mov_environment / STRIKE_LOW__GRAPPLE_LOW | 1546 | 0.663194 | 0.666717 | 0.667056 |
| joint_mov_environment / STRIKE_LOW__GRAPPLE_ONE_SIDED | 676 | 0.665475 | 0.666372 | 0.666614 |
| joint_mov_environment / STRIKE_LOW__GRAPPLE_TWO_SIDED | 110 | 0.700550 | 0.708747 | 0.706931 |
| joint_mov_environment / STRIKE_ONE_SIDED__GRAPPLE_LOW | 747 | 0.680593 | 0.684280 | 0.683867 |
| joint_mov_environment / STRIKE_ONE_SIDED__GRAPPLE_ONE_SIDED | 180 | 0.634298 | 0.634536 | 0.636644 |
| joint_mov_environment / STRIKE_ONE_SIDED__GRAPPLE_TWO_SIDED | 12 | N-only | N-only | N-only |
| joint_mov_environment / STRIKE_TWO_SIDED__GRAPPLE_LOW | 151 | 0.658233 | 0.661385 | 0.660415 |
| joint_mov_environment / STRIKE_TWO_SIDED__GRAPPLE_ONE_SIDED | 17 | N-only | N-only | N-only |
| joint_mov_environment / UNASSIGNABLE_BY_CONTRACT | 821 | 0.685914 | 0.685567 | 0.684624 |

## Fixed probability bands

| Band | Model | N | Mean prediction | Observed finish | Gap | Wilson95 | Years |
|---|---|---|---|---|---|---|---|
| <0.30 | H0 | 383 | 24.948% | 28.721% | +3.773% | [0.24418193741420688, 0.33445681424153906] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| <0.30 | H1 | 425 | 24.278% | 29.412% | +5.133% | [0.25279774253320814, 0.3391260409525428] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| <0.30 | H2 | 436 | 23.997% | 30.734% | +6.737% | [0.26587020653859894, 0.352173984997045] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.30–<0.40 | H0 | 865 | 35.797% | 41.387% | +5.590% | [0.38150172643846636, 0.44700553632240325] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.30–<0.40 | H1 | 876 | 35.581% | 41.210% | +5.629% | [0.37995834062693445, 0.4450101256165002] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.30–<0.40 | H2 | 871 | 35.641% | 40.528% | +4.887% | [0.37316203657675195, 0.43823236141803035] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.40–<0.50 | H0 | 1321 | 44.930% | 46.480% | +1.550% | [0.4380442845973879, 0.4917586368157268] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.40–<0.50 | H1 | 1259 | 44.949% | 47.021% | +2.073% | [0.44277709856658237, 0.49783302357017506] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.40–<0.50 | H2 | 1266 | 44.960% | 47.235% | +2.275% | [0.4449787725068234, 0.4998962356969494] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.50–<0.60 | H0 | 956 | 54.616% | 58.159% | +3.543% | [0.55005429411607, 0.612472546714153] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.50–<0.60 | H1 | 915 | 54.540% | 58.470% | +3.930% | [0.5524812042299514, 0.6162094861084426] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.50–<0.60 | H2 | 914 | 54.597% | 57.877% | +3.280% | [0.5465001776593157, 0.6103896627549767] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.60–<0.70 | H0 | 523 | 64.079% | 63.671% | -0.408% | [0.5946341865691152, 0.6767947179064318] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.60–<0.70 | H1 | 539 | 64.107% | 62.709% | -1.399% | [0.5854980796331523, 0.6668776329692495] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| 0.60–<0.70 | H2 | 510 | 64.208% | 63.922% | -0.286% | [0.596639606716647, 0.6797102236880482] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| >=0.70 | H0 | 212 | 75.479% | 67.925% | -7.554% | [0.6137032514205217, 0.738407044790622] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| >=0.70 | H1 | 246 | 75.945% | 66.667% | -9.278% | [0.6055945502839866, 0.7226135877370519] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |
| >=0.70 | H2 | 263 | 75.618% | 66.540% | -9.078% | [0.6063538083245764, 0.7196824844782607] | [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] |

Observed monotonicity reversals: {'H0': [], 'H1': [], 'H2': []}.

## Exact PR #113 panel

| Archetype | N | Actual | H0 mean/gap | H1 mean/gap | H2 mean/gap |
|---|---|---|---|---|---|
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 59.895% | 55.675% / +4.220% | 55.696% / +4.199% | 55.449% / +4.447% |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 55.245% | 54.983% / +0.262% | 54.824% / +0.420% | 54.936% / +0.309% |
| A3_ACCURACY_VS_ABSORPTION | 973 | 47.996% | 47.932% / +0.064% | 47.740% / +0.256% | 47.635% / +0.361% |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 61.343% | 57.725% / +3.619% | 57.720% / +3.624% | 57.481% / +3.863% |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 53.172% | 48.367% / +4.805% | 48.233% / +4.939% | 48.091% / +5.081% |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 48.854% | 47.324% / +1.529% | 47.074% / +1.780% | 46.945% / +1.909% |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 54.369% | 51.344% / +3.025% | 51.229% / +3.140% | 51.245% / +3.124% |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 52.887% | 49.922% / +2.965% | 49.932% / +2.955% | 49.939% / +2.948% |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 60.068% | 53.495% / +6.572% | 53.625% / +6.443% | 53.668% / +6.399% |
| C1_DAMAGE_PLUS_SUBMISSION_ACCESS | 29 | 65.517% | 61.793% / +3.724% | 61.818% / +3.699% | 61.453% / +4.064% |
| C2_BOTH_HIGH_FINISH_HISTORY | 1483 | 55.698% | 53.968% / +1.729% | 53.946% / +1.751% | 53.891% / +1.807% |
| C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS | 417 | 55.635% | 59.352% / -3.717% | 59.910% / -4.274% | 59.829% / -4.193% |
| D1_LOW_DAMAGE_STRONG_DEFENSE | 74 | 27.027% | 31.179% / -4.152% | 30.132% / -3.105% | 29.598% / -2.571% |
| D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE | 499 | 44.489% | 42.951% / +1.538% | 42.637% / +1.852% | 42.428% / +2.060% |
| D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE | 124 | 31.452% | 42.997% / -11.545% | 42.365% / -10.914% | 42.375% / -10.923% |

## Limitations

Correlated repeated fighters/events, one preregistered prior specification, differing Bayesian global regularization from frozen ridge, normalized rare labels, incomplete 2026, posterior inference uncertainty, overlapping exploratory subgroup tests. Bootstrap intervals condition on fitted OOF predictions; they do not incorporate refit or model-selection uncertainty. Effects are conditional predictive associations; no causal or hazard interpretation. H1 vs H0 changes prior/inference and label pooling as well as hierarchical intercepts; H2 vs H1 isolates the added slope hierarchy more directly. All probabilities remain uncalibrated posterior predictive means; no outcome-selected recalibration.
