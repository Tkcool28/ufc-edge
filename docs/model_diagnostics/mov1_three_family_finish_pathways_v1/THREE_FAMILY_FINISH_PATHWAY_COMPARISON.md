# Three-family finish-pathway comparison

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

Probability table is mean P(KO/TKO | STANDARD_FINISH) over the same actual finishes. Submission is exactly 1−K. It is not P(FINISH), and decisions never count as conditional negatives.

## Conditional KO probability

| Environment | All N | Finish N | Gate | Actual KO | Actual SUB | LINEAR_MIN | XGB | LGBM | CAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.4% | 27.6% | 72.2% | 70.4% | 70.8% | 71.3% |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 88.6% | 11.4% | 82.1% | 76.3% | 76.8% | 77.1% |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 75.2% | 24.8% | 77.1% | 74.8% | 75.4% | 76.1% |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 49.7% | 50.3% | 56.7% | 57.6% | 57.7% | 57.4% |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 54.3% | 45.7% | 59.6% | 61.0% | 61.0% | 60.5% |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 46.0% | 54.0% | 55.2% | 57.5% | 57.1% | 57.2% |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 57.3% | 42.7% | 60.9% | 59.6% | 59.5% | 59.5% |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 45.1% | 54.9% | 54.1% | 53.3% | 53.1% | 52.6% |
| Heavyweight | 316 | 187 | NORMAL | 77.5% | 22.5% | 76.9% | 76.6% | 76.8% | 77.7% |
| Light Heavyweight | 319 | 205 | NORMAL | 74.1% | 25.9% | 74.7% | 73.1% | 73.5% | 74.0% |
| Flyweight | 252 | 121 | NORMAL | 52.1% | 47.9% | 56.0% | 57.4% | 57.8% | 58.4% |
| Women's Strawweight | 275 | 94 | MODERATE_UNCERTAINTY | 44.7% | 55.3% | 50.6% | 52.6% | 52.5% | 51.0% |
| Women's Flyweight | 266 | 95 | MODERATE_UNCERTAINTY | 46.3% | 53.7% | 49.8% | 54.0% | 53.4% | 51.7% |

## Individual-fight conditional log loss

| Environment | All N | Finish N | Gate | Actual KO | Actual SUB | LINEAR_MIN | XGB | LGBM | CAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.4% | 27.6% | 0.554185 | 0.549678 | 0.551361 | 0.553864 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 88.6% | 11.4% | 0.350820 | 0.357951 | 0.356008 | 0.376912 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 75.2% | 24.8% | 0.538524 | 0.528881 | 0.535453 | 0.539131 |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 49.7% | 50.3% | 0.691982 | 0.675047 | 0.670705 | 0.681974 |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 54.3% | 45.7% | 0.666875 | 0.650416 | 0.650582 | 0.652028 |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 46.0% | 54.0% | 0.702464 | 0.692068 | 0.685433 | 0.683159 |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 57.3% | 42.7% | 0.662289 | 0.651864 | 0.656548 | 0.658695 |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 45.1% | 54.9% | 0.706751 | 0.688393 | 0.690283 | 0.687481 |
| Heavyweight | 316 | 187 | NORMAL | 77.5% | 22.5% | 0.504301 | 0.490473 | 0.488332 | 0.494703 |
| Light Heavyweight | 319 | 205 | NORMAL | 74.1% | 25.9% | 0.555442 | 0.549355 | 0.556248 | 0.551027 |
| Flyweight | 252 | 121 | NORMAL | 52.1% | 47.9% | 0.643466 | 0.654030 | 0.664837 | 0.662539 |
| Women's Strawweight | 275 | 94 | MODERATE_UNCERTAINTY | 44.7% | 55.3% | 0.708423 | 0.706068 | 0.694157 | 0.719470 |
| Women's Flyweight | 266 | 95 | MODERATE_UNCERTAINTY | 46.3% | 53.7% | 0.691294 | 0.735787 | 0.737720 | 0.724300 |

## Individual-fight conditional Brier

| Environment | All N | Finish N | Gate | Actual KO | Actual SUB | LINEAR_MIN | XGB | LGBM | CAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.4% | 27.6% | 0.188115 | 0.184842 | 0.185538 | 0.186768 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 88.6% | 11.4% | 0.102845 | 0.102781 | 0.102222 | 0.111242 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 75.2% | 24.8% | 0.180135 | 0.175487 | 0.177918 | 0.178679 |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 49.7% | 50.3% | 0.247953 | 0.240678 | 0.238632 | 0.243527 |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 54.3% | 45.7% | 0.236756 | 0.229309 | 0.228912 | 0.229287 |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 46.0% | 54.0% | 0.253128 | 0.248992 | 0.245746 | 0.244654 |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 57.3% | 42.7% | 0.234661 | 0.230300 | 0.232343 | 0.233345 |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 45.1% | 54.9% | 0.256122 | 0.247717 | 0.248584 | 0.247370 |
| Heavyweight | 316 | 187 | NORMAL | 77.5% | 22.5% | 0.163812 | 0.158853 | 0.157760 | 0.159430 |
| Light Heavyweight | 319 | 205 | NORMAL | 74.1% | 25.9% | 0.188776 | 0.183956 | 0.186857 | 0.184557 |
| Flyweight | 252 | 121 | NORMAL | 52.1% | 47.9% | 0.225375 | 0.231338 | 0.236136 | 0.235143 |
| Women's Strawweight | 275 | 94 | MODERATE_UNCERTAINTY | 44.7% | 55.3% | 0.256677 | 0.256039 | 0.250730 | 0.262246 |
| Women's Flyweight | 266 | 95 | MODERATE_UNCERTAINTY | 46.3% | 53.7% | 0.248110 | 0.269495 | 0.269978 | 0.263790 |

Lower loss/Brier is better. Means and individual probability losses answer different questions; a closer mean does not guarantee lower individual loss. Complete gaps, deltas, sample gates and annual coverage are in the comparison CSVs.
