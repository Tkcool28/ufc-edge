# Earliest fold support

The 2018 outer boundary has **707 frozen conditional training fights and 662 unique training fighters**. Training states are from 2015–2017; they must not borrow the extra exposure those fighters accrued before January 2018. The 2018 outer scoring universe is **470 bouts / 940 oriented fighter states**.

| scope | candidate | fighter_states | missing_pair_pct | zero_den_pct_observed | den_p10 | den_p25 | den_p50 | den_p75 | den_p90 | complete_history_pct | no_prior_ufc_states |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_training_prefight | sub_per_td | 1414 | 12.73 | 20.02 | 0.00 | 1.00 | 5.00 | 10.00 | 21.00 | 87.27 | 180 |
| frozen_training_prefight | control_per_td | 1414 | 12.73 | 20.02 | 0.00 | 1.00 | 4.00 | 10.00 | 21.00 | 86.70 | 180 |
| frozen_training_prefight | sub_per_ground_bucket | 1414 | 26.80 | 14.78 | 0.00 | 2.00 | 6.00 | 10.00 | 16.00 | 17.75 | 180 |
| frozen_training_prefight | ground_strikes_per_ground_bucket | 1414 | 26.80 | 14.78 | 0.00 | 2.00 | 6.00 | 10.00 | 16.00 | 17.75 | 180 |
| frozen_training_prefight | sub_per_elapsed_min | 1414 | 12.73 | 0.00 | 12.02 | 21.67 | 47.00 | 93.17 | 156.38 | 85.64 | 180 |
| frozen_training_prefight | ground_strikes_per_elapsed_min | 1414 | 12.73 | 0.00 | 12.02 | 21.67 | 47.00 | 93.17 | 156.38 | 85.64 | 180 |
| frozen_training_prefight | sub_conversion | 1414 | 12.73 | 36.14 | 0.00 | 0.00 | 1.00 | 4.00 | 8.00 | 87.27 | 180 |
| frozen_training_prefight | sub_conversion_faced | 1414 | 12.73 | 38.17 | 0.00 | 0.00 | 1.00 | 3.00 | 6.00 | 87.27 | 180 |
| frozen_outer_scoring_prefight | sub_per_td | 940 | 12.77 | 15.37 | 0.00 | 1.00 | 5.00 | 12.00 | 23.00 | 87.23 | 120 |
| frozen_outer_scoring_prefight | control_per_td | 940 | 12.77 | 15.37 | 0.00 | 1.00 | 5.00 | 12.00 | 23.00 | 87.13 | 120 |
| frozen_outer_scoring_prefight | sub_per_ground_bucket | 940 | 21.06 | 11.86 | 0.00 | 3.00 | 7.00 | 14.00 | 24.00 | 23.19 | 120 |
| frozen_outer_scoring_prefight | ground_strikes_per_ground_bucket | 940 | 21.06 | 11.86 | 0.00 | 3.00 | 7.00 | 14.00 | 24.00 | 23.19 | 120 |
| frozen_outer_scoring_prefight | sub_per_elapsed_min | 940 | 12.77 | 0.00 | 15.00 | 27.94 | 60.00 | 109.00 | 168.34 | 86.49 | 120 |
| frozen_outer_scoring_prefight | ground_strikes_per_elapsed_min | 940 | 12.77 | 0.00 | 15.00 | 27.94 | 60.00 | 109.00 | 168.34 | 86.49 | 120 |
| frozen_outer_scoring_prefight | sub_conversion | 940 | 12.77 | 34.63 | 0.00 | 0.00 | 1.00 | 4.00 | 8.00 | 87.23 | 120 |
| frozen_outer_scoring_prefight | sub_conversion_faced | 940 | 12.77 | 37.80 | 0.00 | 0.00 | 1.00 | 3.00 | 6.00 | 87.23 | 120 |

## What survives

Recorded submission activity, completed/attempted TDs, ground significant-strike activity, generic CTRL and reversals have enough *measurement coverage* for conservative diagnostic count comparisons. This is not proof of predictive value or individual-fighter precision. SUB/TD and CTRL/TD require positive TD denominators, paired round coverage and regularization if ever used predictively. True grounded-minute rates fail semantic/coverage requirements; source buckets are not exact minutes and complete ground history at the earliest boundary is only 22.51% of training fighters.

Conversion support must be judged at the original 2015–2017 dates too. The attempt bins in `conversion_support_bins.csv` separately report training-prefight, scoring-prefight and unique boundary-fighter support; missing observations are separate from zero. Per-division and recent-window figures are in `fold_state_coverage.csv`, not pooled away.

No prior UFC history flags in the outer set cannot establish a professional debut. Outcome-only pre-UFC records exist but cannot fill missing submission-attempt or grounded-time histories. Entirely missing history and no completed TD exposure stay unavailable rather than becoming zeros.

All audit histories use event_date < target event date; the target and every same-date bout are excluded. Only pinned UFC history through 2026-08-15 is used. No prospective confirmation outcomes, model fitting, feature promotion or frozen-source edits occur. This is retrospective event-date governance: 2026 acquisition snapshots cannot prove what a provider published before every old fight. Preserve that publication-vintage limitation.

The modern population is the unchanged 5,658-fight PR #125 universe; its 4,260 outer-scored bouts and exact conditional training/scoring fight IDs are reused. Historical measurements retain earlier UFC bouts where available. Boundary rows describe unique fighters appearing in the frozen conditional training set at January 1. Training-prefight rows describe their original historical prediction dates, not values accumulated at the later boundary. Scoring rows include all eligible bouts, with 2026 truncated at the existing August 15 boundary. Division rows follow frozen target division, without inferring sex from unsupported metadata.

`career` here means available prior UFC history for the candidate measurement audit. `last5` means the last five prior UFC bouts, including measurement-missing bouts; tied dates crossing the boundary fail closed. This deliberately conservative coverage window is not an exact replay of F01's component-specific last5 eligible-observation selector. F01's available windows are inventoried separately and remain unchanged. Prior non-UFC outcome history cannot supply a UFC round-stat denominator. No prior UFC history is reported separately; it does not prove a professional debut. F01 likewise withholds automatic debut-prior substitution when debut/completeness is unproven.

A full-bout count requires all rounds 1..finish_round and nonmissing field values. Pair candidates sum only rounds with both measurements; conversion requires a complete attempted-submission bout before attaching the result. Ground-bucket pairs additionally require governed elapsed duration and a lower bound within that duration. Partial paired histories remain explicitly partial. `complete_history_pct` requires every prior UFC bout to have the relevant complete pair; observed-pair availability alone is insufficient. Zero denominator is distinct from missing history, and zero minute bucket means less than one minute under the contract, not necessarily no exposure. The contract's interval model is empirical evidence, not an independently published vendor unit guarantee.

Counts summed across target fighter states repeat a fighter's prior events at different prediction dates: columns explicitly say state-weighted. They are support distributions, not independent trial totals or confidence intervals. Bout-level records supply unique event counts; no statistical uncertainty calculation treats repeated fighter states as independent. Quantiles and missingness are descriptive; no style thresholds are chosen from outcomes.
