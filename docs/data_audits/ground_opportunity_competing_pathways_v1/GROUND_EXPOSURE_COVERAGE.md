# Ground exposure coverage

**No broadly usable exact historical ground-exposure denominator is present.** Existing positional records are real, but incomplete and coarse. Do not confuse an observed positive bucket sum with a complete fighter career denominator.

All audit histories use event_date < target event date; the target and every same-date bout are excluded. Only pinned UFC history through 2026-08-15 is used. No prospective confirmation outcomes, model fitting, feature promotion or frozen-source edits occur. This is retrospective event-date governance: 2026 acquisition snapshots cannot prove what a provider published before every old fight. Preserve that publication-vintage limitation.

The modern population is the unchanged 5,658-fight PR #125 universe; its 4,260 outer-scored bouts and exact conditional training/scoring fight IDs are reused. Historical measurements retain earlier UFC bouts where available. Boundary rows describe unique fighters appearing in the frozen conditional training set at January 1. Training-prefight rows describe their original historical prediction dates, not values accumulated at the later boundary. Scoring rows include all eligible bouts, with 2026 truncated at the existing August 15 boundary. Division rows follow frozen target division, without inferring sex from unsupported metadata.

`career` here means available prior UFC history for the candidate measurement audit. `last5` means the last five prior UFC bouts, including measurement-missing bouts; tied dates crossing the boundary fail closed. This deliberately conservative coverage window is not an exact replay of F01's component-specific last5 eligible-observation selector. F01's available windows are inventoried separately and remain unchanged. Prior non-UFC outcome history cannot supply a UFC round-stat denominator. No prior UFC history is reported separately; it does not prove a professional debut. F01 likewise withholds automatic debut-prior substitution when debut/completeness is unproven.

A full-bout count requires all rounds 1..finish_round and nonmissing field values. Pair candidates sum only rounds with both measurements; conversion requires a complete attempted-submission bout before attaching the result. Ground-bucket pairs additionally require governed elapsed duration and a lower bound within that duration. Partial paired histories remain explicitly partial. `complete_history_pct` requires every prior UFC bout to have the relevant complete pair; observed-pair availability alone is insufficient. Zero denominator is distinct from missing history, and zero minute bucket means less than one minute under the contract, not necessarily no exposure. The contract's interval model is empirical evidence, not an independently published vendor unit guarantee.

Counts summed across target fighter states repeat a fighter's prior events at different prediction dates: columns explicitly say state-weighted. They are support distributions, not independent trial totals or confidence intervals. Bout-level records supply unique event counts; no statistical uncertainty calculation treats repeated fighter states as independent. Quantiles and missingness are descriptive; no style thresholds are chosen from outcomes.

## Every frozen outer training boundary

SUB / completed TD fallback, paired counts:

| outer_year | eligible_training_fights | eligible_prior_ufc_fights | unique_fighters | num_observed_states | den_observed_states | zero_den_pct_observed | den_p10 | den_p25 | den_p50 | den_p75 | den_p90 | complete_history_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | 707 | 4457 | 662 | 662 | 662 | 17.98 | 0.00 | 1.00 | 4.00 | 11.00 | 21.00 | 100.00 |
| 2019 | 948 | 4931 | 779 | 779 | 779 | 17.20 | 0.00 | 1.00 | 5.00 | 11.00 | 21.20 | 99.74 |
| 2020 | 1179 | 5443 | 883 | 883 | 883 | 17.21 | 0.00 | 1.00 | 4.00 | 11.00 | 21.00 | 99.77 |
| 2021 | 1399 | 5895 | 1007 | 1007 | 1007 | 19.86 | 0.00 | 1.00 | 4.00 | 11.00 | 21.00 | 99.80 |
| 2022 | 1638 | 6396 | 1111 | 1111 | 1111 | 18.63 | 0.00 | 1.00 | 4.00 | 11.00 | 22.00 | 99.82 |
| 2023 | 1906 | 6904 | 1205 | 1205 | 1205 | 17.76 | 0.00 | 1.00 | 5.00 | 11.00 | 22.00 | 99.83 |
| 2024 | 2164 | 7420 | 1313 | 1313 | 1313 | 17.52 | 0.00 | 1.00 | 5.00 | 11.00 | 22.00 | 99.85 |
| 2025 | 2387 | 7928 | 1400 | 1400 | 1400 | 16.64 | 0.00 | 1.00 | 5.00 | 12.00 | 23.00 | 99.86 |
| 2026 | 2639 | 8436 | 1505 | 1505 | 1505 | 17.01 | 0.00 | 1.00 | 5.00 | 12.00 | 23.00 | 99.87 |

SUB / ground-bucket candidate (bucket units; **not SUB per grounded minute**):

| outer_year | unique_fighters | missing_pair_pct | zero_den_pct_observed | den_p10 | den_p25 | den_p50 | den_p75 | den_p90 | complete_history_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | 662 | 11.03 | 12.56 | 0.00 | 2.00 | 6.00 | 12.00 | 20.00 | 22.51 |
| 2019 | 779 | 9.50 | 12.20 | 0.00 | 2.00 | 6.00 | 13.00 | 22.00 | 25.03 |
| 2020 | 883 | 12.68 | 11.80 | 0.00 | 2.50 | 7.00 | 13.00 | 22.00 | 15.63 |
| 2021 | 1007 | 20.85 | 12.05 | 0.00 | 2.00 | 7.00 | 13.00 | 22.00 | 10.03 |
| 2022 | 1111 | 27.27 | 12.25 | 0.00 | 2.00 | 7.00 | 13.00 | 22.00 | 8.64 |
| 2023 | 1205 | 32.53 | 12.30 | 0.00 | 2.00 | 7.00 | 13.00 | 22.00 | 7.80 |
| 2024 | 1313 | 38.08 | 12.30 | 0.00 | 2.00 | 7.00 | 13.00 | 22.00 | 7.08 |
| 2025 | 1400 | 41.86 | 12.29 | 0.00 | 2.00 | 7.00 | 13.00 | 22.00 | 6.64 |
| 2026 | 1505 | 45.78 | 12.25 | 0.00 | 2.00 | 7.00 | 13.00 | 22.00 | 6.18 |

`boundary_coverage.csv` includes all eight denominator/support candidates, numerators and denominators, missingness, zero numerators/denominators and exposure quantiles. `fold_state_coverage.csv` adds original training-date and scoring-date support, career/recent windows and every division at every boundary. This prevents later boundary history from masquerading as early training support. `fold_field_support.csv` separately reports every raw count/position/control-allowed/SUB-finish field at all boundaries, original-date scopes, divisions and windows. `exact_ground_denominator_feasibility.csv` explicitly marks the unavailable true denominators at every boundary. `year_field_coverage.csv` counts observed measurements against expected fighter-round keys, including absent stat/position rows.

## Interval-quality safeguards

| field | lower_bound_exceeds_elapsed_rows | observed_bucket_rows | round_duration_eligible_rows | zero_bucket_rows |
| --- | --- | --- | --- | --- |
| ground | 6 | 10240 | 10232 | 5964 |
| ground_control | 2 | 23695 | 23651 | 18758 |
| standing | 8 | 23696 | 23652 | 2826 |
| back_control | 1 | 23714 | 23670 | 23190 |

Only positional pairs with a known elapsed duration and lower bound no greater than that duration enter bucket support. These additional conflicts are diagnostic exclusions, not modifications to the canonical source. An upper bucket bound must be intersected with round duration, never used as an exact observed number. A zero bucket can hide up to 59 seconds. SUB or ground-strike counts divided by the bucket integer have zero/quantization problems; exact candidate rates remain unavailable at **every** boundary.

Overall SUB.ATT counts are not phase-coded: standing/clinch attempts may be included. Even with exact ground seconds, overall SUB attempts / ground time would require an explicit proxy interpretation; a genuine ground-only activity rate needs phase-matched SUB attempts.

CTRL/TD can be formed on matched rounds but is generic control retention proxy, can include clinch/control entered without a TD, and cannot identify time per ground entry. Standups and reversals are real counts with uncertain opportunity conditioning; neither yields an escape probability. Ground-control buckets are not substitute ground exposure, especially for bottom-position submissions.
