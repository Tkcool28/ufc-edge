# Two-node pathway decomposition — frozen MOV0-MIN + MOV1-MIN

These are means of individual composed probabilities; mean(F×K) is not replaced by mean(F)×mean(K). K_all describes the score available for every pre-fight state; K_finish is restricted to actual finishes for calibration comparison. Actual three-way rates use all bouts. See the complete archetype CSV for all four systems/statuses and weight-class cross-tabs.

| Archetype | All / finish N | F all | K all | K finish | Pred KO | Pred SUB | Pred DEC | Actual KO | Actual SUB | Actual DEC |
|---|---|---|---|---|---|---|---|---|---|---|
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 / 457 | 55.7% | 71.9% | 72.2% | 40.3% | 15.4% | 44.3% | 43.4% | 16.5% | 40.1% |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 / 79 | 55.0% | 81.5% | 82.1% | 44.8% | 10.2% | 45.0% | 49.0% | 6.3% | 44.8% |
| A3_ACCURACY_VS_ABSORPTION | 973 / 467 | 47.9% | 68.3% | 69.0% | 33.3% | 14.7% | 52.1% | 30.9% | 17.1% | 52.0% |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 / 484 | 57.7% | 76.9% | 77.1% | 44.3% | 13.4% | 42.3% | 46.1% | 15.2% | 38.7% |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 / 352 | 48.4% | 56.4% | 56.7% | 27.5% | 20.9% | 51.6% | 26.4% | 26.7% | 46.8% |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 / 341 | 47.3% | 58.2% | 59.6% | 27.9% | 19.4% | 52.7% | 26.5% | 22.3% | 51.1% |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 / 224 | 51.3% | 53.9% | 55.2% | 28.3% | 23.1% | 48.7% | 25.0% | 29.4% | 45.6% |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 / 861 | 49.9% | 60.2% | 60.9% | 30.4% | 19.5% | 50.1% | 30.3% | 22.6% | 47.1% |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 / 355 | 53.5% | 53.4% | 54.1% | 28.9% | 24.6% | 46.5% | 27.1% | 33.0% | 39.9% |
| C1_DAMAGE_PLUS_SUBMISSION_ACCESS | 29 / 19 | 61.8% | 66.0% | 67.3% | 40.7% | 21.1% | 38.2% | 27.6% | 37.9% | 34.5% |
| C2_BOTH_HIGH_FINISH_HISTORY | 1483 / 826 | 54.0% | 67.9% | 68.8% | 37.1% | 16.9% | 46.0% | 37.2% | 18.5% | 44.3% |
| C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS | 417 / 232 | 59.4% | 75.0% | 76.2% | 44.9% | 14.4% | 40.6% | 41.0% | 14.6% | 44.4% |
| D1_LOW_DAMAGE_STRONG_DEFENSE | 74 / 20 | 31.2% | 56.5% | 55.3% | 17.7% | 13.5% | 68.8% | 12.2% | 14.9% | 73.0% |
| D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE | 499 / 222 | 43.0% | 76.4% | 78.1% | 33.8% | 9.2% | 57.0% | 36.3% | 8.2% | 55.5% |
| D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE | 124 / 39 | 43.0% | 74.3% | 74.5% | 32.4% | 10.6% | 57.0% | 23.4% | 8.1% | 68.5% |

The two-node architecture distinguishes recognizable damage and grappling paths. A1/A4 receive substantial KO concentration, while B3/B5 receive more submission probability than their context-only systems. D2 illustrates why low grappling pressure can imply a KO-heavy split among the fights that do finish, even when total finish probability is lower.

It does not perfectly reproduce these environments. B3 predicts SUB23.1% versus actual29.4%; B5 predicts SUB24.6% versus33.0%. Frozen F understates total finish in both, and K also understates submission conditional on finish. A1 predicts DEC44.3% versus40.1%; A4 predicts DEC42.3% versus38.7%, limiting composed KO probability despite useful K. C3 five-round finish-pressure predicts KO44.9% versus41.0% and DEC40.6% versus44.4%: not every error is a missing KO pathway.

D1 has74 total bouts and20 finishes; its conditional pathway is insufficient. D3 has39 finishes; conditional interpretation is thin. Mixed damage/access C1 has19 finishes. The table preserves counts and descriptive means without treating these as established performance relationships.

No probability, archetype rate or coefficient is a causal hazard, action probability or round transition. The same F node gives identical DEC probabilities in S0–S3. Improvements in conditional/composed log loss are algebraically linked, while multiclass Brier and reliability add distinct assessment.
