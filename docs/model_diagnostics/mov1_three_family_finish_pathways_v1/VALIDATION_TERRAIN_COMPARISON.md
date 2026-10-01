# Immutable Validation Terrain comparison

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

| Environment | All N | Finish N | Gate | Actual KO | Actual SUB | LINEAR_MIN | XGB | LGBM | CAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scheduled_duration_bucket::5_ROUND | 423 | 232 | NORMAL | 73.7% | 26.3% | 0.511026 | 0.524905 | 0.518367 | 0.520639 |
| title_status::NON_TITLE_BOUT | 4088 | 2024 | NORMAL | 64.2% | 35.8% | 0.617883 | 0.612129 | 0.613399 | 0.613138 |
| title_status::TITLE_BOUT | 172 | 91 | MODERATE_UNCERTAINTY | 68.1% | 31.9% | 0.559367 | 0.587049 | 0.578244 | 0.568328 |
| completeness_tier::HIGH_MISSINGNESS | 821 | 434 | NORMAL | 65.9% | 34.1% | 0.606838 | 0.619546 | 0.621695 | 0.614568 |
| completeness_tier::LOW_MISSINGNESS | 3439 | 1681 | NORMAL | 64.0% | 36.0% | 0.617567 | 0.608856 | 0.609354 | 0.610342 |
| striking_environment::STRIKE_LOW | 2332 | 1084 | NORMAL | 58.2% | 41.8% | 0.675904 | 0.660353 | 0.660528 | 0.666379 |
| striking_environment::STRIKE_ONE_SIDED | 939 | 509 | NORMAL | 72.9% | 27.1% | 0.523376 | 0.530540 | 0.531970 | 0.520097 |
| grappling_environment::GRAPPLE_ONE_SIDED | 873 | 447 | NORMAL | 53.9% | 46.1% | 0.681230 | 0.684436 | 0.678632 | 0.684068 |
| grappling_environment::GRAPPLE_TWO_SIDED | 122 | 76 | MODERATE_UNCERTAINTY | 47.4% | 52.6% | 0.738084 | 0.670925 | 0.681417 | 0.686466 |
| joint_mov_environment::STRIKE_LOW__GRAPPLE_LOW | 1546 | 690 | NORMAL | 62.5% | 37.5% | 0.662670 | 0.643925 | 0.645715 | 0.651696 |
| joint_mov_environment::STRIKE_LOW__GRAPPLE_ONE_SIDED | 676 | 326 | NORMAL | 51.8% | 48.2% | 0.687144 | 0.690687 | 0.685148 | 0.691035 |
| joint_mov_environment::STRIKE_LOW__GRAPPLE_TWO_SIDED | 110 | 68 | MODERATE_UNCERTAINTY | 45.6% | 54.4% | 0.756312 | 0.681632 | 0.692799 | 0.697172 |
| joint_mov_environment::STRIKE_ONE_SIDED__GRAPPLE_LOW | 747 | 393 | NORMAL | 77.1% | 22.9% | 0.484517 | 0.489999 | 0.494238 | 0.480020 |
| joint_mov_environment::STRIKE_ONE_SIDED__GRAPPLE_ONE_SIDED | 180 | 108 | NORMAL | 58.3% | 41.7% | 0.660352 | 0.674406 | 0.665369 | 0.660350 |
| joint_mov_environment::STRIKE_ONE_SIDED__GRAPPLE_TWO_SIDED | 12 | 8 | INSUFFICIENT | 62.5% | 37.5% | — | — | — | — |
| joint_mov_environment::STRIKE_TWO_SIDED__GRAPPLE_ONE_SIDED | 17 | 13 | INSUFFICIENT | 69.2% | 30.8% | — | — | — | — |

| Environment | All N | Finish N | Gate | Actual KO | Actual SUB | LINEAR_MIN | XGB | LGBM | CAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scheduled_duration_bucket::5_ROUND | 423 | 232 | NORMAL | 73.7% | 26.3% | 76.2% | 72.1% | 72.4% | 73.1% |
| title_status::NON_TITLE_BOUT | 4088 | 2024 | NORMAL | 64.2% | 35.8% | 66.1% | 65.1% | 65.2% | 65.6% |
| title_status::TITLE_BOUT | 172 | 91 | MODERATE_UNCERTAINTY | 68.1% | 31.9% | 71.6% | 69.3% | 69.4% | 70.1% |
| completeness_tier::HIGH_MISSINGNESS | 821 | 434 | NORMAL | 65.9% | 34.1% | 63.9% | 62.7% | 62.6% | 63.2% |
| completeness_tier::LOW_MISSINGNESS | 3439 | 1681 | NORMAL | 64.0% | 36.0% | 66.9% | 66.0% | 66.1% | 66.5% |
| striking_environment::STRIKE_LOW | 2332 | 1084 | NORMAL | 58.2% | 41.8% | 62.5% | 62.6% | 62.6% | 62.8% |
| striking_environment::STRIKE_ONE_SIDED | 939 | 509 | NORMAL | 72.9% | 27.1% | 73.7% | 71.4% | 71.9% | 72.4% |
| grappling_environment::GRAPPLE_ONE_SIDED | 873 | 447 | NORMAL | 53.9% | 46.1% | 58.4% | 58.3% | 57.9% | 58.1% |
| grappling_environment::GRAPPLE_TWO_SIDED | 122 | 76 | MODERATE_UNCERTAINTY | 47.4% | 52.6% | 49.2% | 53.8% | 54.3% | 52.6% |
| joint_mov_environment::STRIKE_LOW__GRAPPLE_LOW | 1546 | 690 | NORMAL | 62.5% | 37.5% | 67.1% | 66.5% | 66.7% | 67.1% |
| joint_mov_environment::STRIKE_LOW__GRAPPLE_ONE_SIDED | 676 | 326 | NORMAL | 51.8% | 48.2% | 55.8% | 56.4% | 55.9% | 56.1% |
| joint_mov_environment::STRIKE_LOW__GRAPPLE_TWO_SIDED | 110 | 68 | MODERATE_UNCERTAINTY | 45.6% | 54.4% | 47.8% | 52.6% | 53.1% | 51.0% |
| joint_mov_environment::STRIKE_ONE_SIDED__GRAPPLE_LOW | 747 | 393 | NORMAL | 77.1% | 22.9% | 76.5% | 73.8% | 74.4% | 75.1% |
| joint_mov_environment::STRIKE_ONE_SIDED__GRAPPLE_ONE_SIDED | 180 | 108 | NORMAL | 58.3% | 41.7% | 64.1% | 62.9% | 62.9% | 62.8% |
| joint_mov_environment::STRIKE_ONE_SIDED__GRAPPLE_TWO_SIDED | 12 | 8 | INSUFFICIENT | 62.5% | 37.5% | 61.4% | 64.1% | 65.0% | 66.0% |
| joint_mov_environment::STRIKE_TWO_SIDED__GRAPPLE_ONE_SIDED | 17 | 13 | INSUFFICIENT | 69.2% | 30.8% | 74.8% | 66.9% | 66.8% | 66.7% |

All experience, layoff, duration/rounds, title, weight, completeness, striking, grappling, joint and fixed era cells are retained in CSV, with complete annual tables. GRAPPLE_TWO_SIDED has 76 finishes and STRIKE_LOW×GRAPPLE_TWO_SIDED 68: moderate, overlapping samples. They cannot be counted as independent confirmations. Unknown states are retained, never reconstructed as LOW.

**striking_environment::STRIKE_LOW**: 1084 finishes (NORMAL); observed KO 58.2%, SUB 41.8%. XGB: KO 62.6%, SUB 37.4%, gap +4.37 pp; LL delta -0.015551, Brier delta -0.006252; absolute mean gap widens by 0.12 pp. LGBM: KO 62.6%, SUB 37.4%, gap +4.35 pp; LL delta -0.015377, Brier delta -0.006287; absolute mean gap widens by 0.09 pp. CAT: KO 62.8%, SUB 37.2%, gap +4.55 pp; LL delta -0.009525, Brier delta -0.004134; absolute mean gap widens by 0.30 pp.

**striking_environment::STRIKE_ONE_SIDED**: 509 finishes (NORMAL); observed KO 72.9%, SUB 27.1%. XGB: KO 71.4%, SUB 28.6%, gap -1.54 pp; LL delta +0.007164, Brier delta +0.002567; absolute mean gap widens by 0.75 pp. LGBM: KO 71.9%, SUB 28.1%, gap -1.04 pp; LL delta +0.008594, Brier delta +0.002769; absolute mean gap widens by 0.25 pp. CAT: KO 72.4%, SUB 27.6%, gap -0.51 pp; LL delta -0.003279, Brier delta -0.001805; absolute mean gap narrows by 0.28 pp.

**grappling_environment::GRAPPLE_ONE_SIDED**: 447 finishes (NORMAL); observed KO 53.9%, SUB 46.1%. XGB: KO 58.3%, SUB 41.7%, gap +4.34 pp; LL delta +0.003206, Brier delta +0.001833; absolute mean gap narrows by 0.11 pp. LGBM: KO 57.9%, SUB 42.1%, gap +3.97 pp; LL delta -0.002597, Brier delta -0.000997; absolute mean gap narrows by 0.48 pp. CAT: KO 58.1%, SUB 41.9%, gap +4.15 pp; LL delta +0.002838, Brier delta +0.001479; absolute mean gap narrows by 0.31 pp.

**grappling_environment::GRAPPLE_TWO_SIDED**: 76 finishes (MODERATE_UNCERTAINTY); observed KO 47.4%, SUB 52.6%. XGB: KO 53.8%, SUB 46.2%, gap +6.48 pp; LL delta -0.067159, Brier delta -0.028758; absolute mean gap widens by 4.63 pp. LGBM: KO 54.3%, SUB 45.7%, gap +6.98 pp; LL delta -0.056667, Brier delta -0.024821; absolute mean gap widens by 5.13 pp. CAT: KO 52.6%, SUB 47.4%, gap +5.21 pp; LL delta -0.051618, Brier delta -0.021767; absolute mean gap widens by 3.36 pp.
