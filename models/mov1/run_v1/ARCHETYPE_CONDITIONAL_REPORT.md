# Exact frozen archetype conditional evaluation

All15 #113 known-state formulas and thresholds are unchanged. The merged contract uses PR117’s pinned MATCH/NO_MATCH/UNASSIGNABLE memberships, which retain unknown qualifications rather than treating missing as LOW or no-match. This disclosed unknown-negation handling differs from certain historical flags; no definition or threshold is refitted here. Archetypes overlap and are evaluation references only. The CSV includes all three statuses, year counts, division composition and uncertainty intervals.

| Archetype | All N | Finish N | Finish status | Actual KO \| finish | C1 mean K | MIN mean K | FULL mean K |
|---|---|---|---|---|---|---|---|
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.4% | 67.0% | 72.2% | 71.7% |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 88.6% | 69.1% | 82.1% | 81.8% |
| A3_ACCURACY_VS_ABSORPTION | 973 | 467 | NORMAL | 64.5% | 64.0% | 69.0% | 68.9% |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 75.2% | 70.1% | 77.1% | 76.6% |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 49.7% | 63.1% | 56.7% | 56.5% |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 54.3% | 64.1% | 59.6% | 59.5% |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 46.0% | 64.7% | 55.2% | 54.9% |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 57.3% | 62.8% | 60.9% | 60.6% |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 45.1% | 61.9% | 54.1% | 53.7% |
| C1_DAMAGE_PLUS_SUBMISSION_ACCESS | 29 | 19 | INSUFFICIENT | 42.1% | 66.7% | 67.3% | 68.8% |
| C2_BOTH_HIGH_FINISH_HISTORY | 1483 | 826 | NORMAL | 66.8% | 67.8% | 68.8% | 68.7% |
| C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS | 417 | 232 | NORMAL | 73.7% | 74.8% | 76.2% | 75.7% |
| D1_LOW_DAMAGE_STRONG_DEFENSE | 74 | 20 | INSUFFICIENT | 45.0% | 55.5% | 55.3% | 58.4% |
| D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE | 499 | 222 | NORMAL | 81.5% | 65.9% | 78.1% | 78.0% |
| D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE | 124 | 39 | THIN_EXPLORATORY | 74.4% | 65.7% | 74.5% | 75.9% |

A1 MIN72.2% KO versus actual72.4%; A4 MIN77.1% versus75.2%. Their shifts beyond C1 are coherent and method-specific. A2 MIN82.1% versus88.6% is directionally coherent but has79 finishes and MODERATE_UNCERTAINTY.

B1 MIN56.7% versus49.7%; B2 MIN59.6% versus54.3%; B3 MIN55.2% versus46.0%; B5 MIN54.1% versus45.1%. Each moves down from C1, but remains too KO-heavy. Grappling pathway separation is useful and incomplete. B3/B5 submission enrichment is understated by about9 conditional percentage points; FULL does not resolve it. A3 also overpredicts KO (69.0% versus64.5%). C1 mixed-damage/access and D1 survival archetypes have fewer than25 finishes; D3 has39 and is thin. No strong conditional claim is made for them.
