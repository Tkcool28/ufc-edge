# Submission conversion support

**Recorded SUB finish / recorded SUB attempts is not yet a defensible fighter-level conversion probability.** It combines bout results with provider-coded attempt counts and does not supply an event-linked success/failure trial definition.

Across historical UFC bouts through the existing boundary: **1704 submission wins**, **1697 with complete attempt observations**, **11 wins despite zero recorded SUB attempts**, and **7 wins with incomplete/missing attempts**. Raw recorded attempts total **6547**. These are broader historical-support counts, not the modern conditional training outcome counts and not newly scored evaluation results.

The zero-attempt finish cases make a literal event-level Bernoulli conversion interpretation invalid without a separately reviewed semantic correction. Do not add an attempt automatically for a successful finish: that would modify measurement definitions. Zero-success histories with observed attempts remain distinct from zero attempts and missing attempts.

## Earliest and latest support bins

| outer_year | scope | field | support_bin | states | total_states | pct |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | frozen_training_prefight | submission_attempts | missing | 180 | 1414 | 12.73 |
| 2018 | frozen_training_prefight | submission_attempts | 0 | 446 | 1414 | 31.54 |
| 2018 | frozen_training_prefight | submission_attempts | 1 | 180 | 1414 | 12.73 |
| 2018 | frozen_training_prefight | submission_attempts | 2-4 | 316 | 1414 | 22.35 |
| 2018 | frozen_training_prefight | submission_attempts | 5-9 | 190 | 1414 | 13.44 |
| 2018 | frozen_training_prefight | submission_attempts | 10+ | 102 | 1414 | 7.21 |
| 2018 | frozen_training_prefight | submission_attempts_faced | missing | 180 | 1414 | 12.73 |
| 2018 | frozen_training_prefight | submission_attempts_faced | 0 | 471 | 1414 | 33.31 |
| 2018 | frozen_training_prefight | submission_attempts_faced | 1 | 218 | 1414 | 15.42 |
| 2018 | frozen_training_prefight | submission_attempts_faced | 2-4 | 328 | 1414 | 23.20 |
| 2018 | frozen_training_prefight | submission_attempts_faced | 5-9 | 158 | 1414 | 11.17 |
| 2018 | frozen_training_prefight | submission_attempts_faced | 10+ | 59 | 1414 | 4.17 |
| 2018 | training_fighters_at_boundary | submission_attempts | missing | 0 | 662 | 0.00 |
| 2018 | training_fighters_at_boundary | submission_attempts | 0 | 244 | 662 | 36.86 |
| 2018 | training_fighters_at_boundary | submission_attempts | 1 | 110 | 662 | 16.62 |
| 2018 | training_fighters_at_boundary | submission_attempts | 2-4 | 165 | 662 | 24.92 |
| 2018 | training_fighters_at_boundary | submission_attempts | 5-9 | 96 | 662 | 14.50 |
| 2018 | training_fighters_at_boundary | submission_attempts | 10+ | 47 | 662 | 7.10 |
| 2018 | training_fighters_at_boundary | submission_attempts_faced | missing | 0 | 662 | 0.00 |
| 2018 | training_fighters_at_boundary | submission_attempts_faced | 0 | 201 | 662 | 30.36 |
| 2018 | training_fighters_at_boundary | submission_attempts_faced | 1 | 147 | 662 | 22.21 |
| 2018 | training_fighters_at_boundary | submission_attempts_faced | 2-4 | 193 | 662 | 29.15 |
| 2018 | training_fighters_at_boundary | submission_attempts_faced | 5-9 | 84 | 662 | 12.69 |
| 2018 | training_fighters_at_boundary | submission_attempts_faced | 10+ | 37 | 662 | 5.59 |
| 2026 | frozen_training_prefight | submission_attempts | missing | 642 | 5278 | 12.16 |
| 2026 | frozen_training_prefight | submission_attempts | 0 | 1667 | 5278 | 31.58 |
| 2026 | frozen_training_prefight | submission_attempts | 1 | 746 | 5278 | 14.13 |
| 2026 | frozen_training_prefight | submission_attempts | 2-4 | 1143 | 5278 | 21.66 |
| 2026 | frozen_training_prefight | submission_attempts | 5-9 | 708 | 5278 | 13.41 |
| 2026 | frozen_training_prefight | submission_attempts | 10+ | 372 | 5278 | 7.05 |
| 2026 | frozen_training_prefight | submission_attempts_faced | missing | 642 | 5278 | 12.16 |
| 2026 | frozen_training_prefight | submission_attempts_faced | 0 | 1761 | 5278 | 33.36 |
| 2026 | frozen_training_prefight | submission_attempts_faced | 1 | 938 | 5278 | 17.77 |
| 2026 | frozen_training_prefight | submission_attempts_faced | 2-4 | 1182 | 5278 | 22.39 |
| 2026 | frozen_training_prefight | submission_attempts_faced | 5-9 | 544 | 5278 | 10.31 |
| 2026 | frozen_training_prefight | submission_attempts_faced | 10+ | 211 | 5278 | 4.00 |
| 2026 | training_fighters_at_boundary | submission_attempts | missing | 0 | 1505 | 0.00 |
| 2026 | training_fighters_at_boundary | submission_attempts | 0 | 560 | 1505 | 37.21 |
| 2026 | training_fighters_at_boundary | submission_attempts | 1 | 272 | 1505 | 18.07 |
| 2026 | training_fighters_at_boundary | submission_attempts | 2-4 | 343 | 1505 | 22.79 |
| 2026 | training_fighters_at_boundary | submission_attempts | 5-9 | 219 | 1505 | 14.55 |
| 2026 | training_fighters_at_boundary | submission_attempts | 10+ | 111 | 1505 | 7.38 |
| 2026 | training_fighters_at_boundary | submission_attempts_faced | missing | 0 | 1505 | 0.00 |
| 2026 | training_fighters_at_boundary | submission_attempts_faced | 0 | 413 | 1505 | 27.44 |
| 2026 | training_fighters_at_boundary | submission_attempts_faced | 1 | 322 | 1505 | 21.40 |
| 2026 | training_fighters_at_boundary | submission_attempts_faced | 2-4 | 478 | 1505 | 31.76 |
| 2026 | training_fighters_at_boundary | submission_attempts_faced | 5-9 | 219 | 1505 | 14.55 |
| 2026 | training_fighters_at_boundary | submission_attempts_faced | 10+ | 73 | 1505 | 4.85 |

Complete 2018–2026 tables include 0, 1, 2–4, 5–9 and 10+ attempt/faced bins, separate missingness, and SUB wins/losses at original training and scoring dates. Full tables: `conversion_support_bins.csv`. Bout pairing and preserved counts: `bout_measurements.csv.gz`; measurement conflicts: `CONVERSION_MEASUREMENT_CHECK.json`.

A future conversion experiment must first settle whether a finish implies an observed successful attempt and whether failed attempts share a consistent event definition. Then a prior-only hierarchical/shrunk count model with support and uncertainty would be required; an unregularized raw ratio is not a production recommendation. No shrinkage hyperparameter is selected or estimated here. Many fighters have fewer than five prior attempts, so any future individual conversion estimate would often be prior-dominated. Submission attempts faced also confound opponent access and activity; they do not independently measure defensive skill.

All audit histories use event_date < target event date; the target and every same-date bout are excluded. Only pinned UFC history through 2026-08-15 is used. No prospective confirmation outcomes, model fitting, feature promotion or frozen-source edits occur. This is retrospective event-date governance: 2026 acquisition snapshots cannot prove what a provider published before every old fight. Preserve that publication-vintage limitation.

The modern population is the unchanged 5,658-fight PR #125 universe; its 4,260 outer-scored bouts and exact conditional training/scoring fight IDs are reused. Historical measurements retain earlier UFC bouts where available. Boundary rows describe unique fighters appearing in the frozen conditional training set at January 1. Training-prefight rows describe their original historical prediction dates, not values accumulated at the later boundary. Scoring rows include all eligible bouts, with 2026 truncated at the existing August 15 boundary. Division rows follow frozen target division, without inferring sex from unsupported metadata.

`career` here means available prior UFC history for the candidate measurement audit. `last5` means the last five prior UFC bouts, including measurement-missing bouts; tied dates crossing the boundary fail closed. This deliberately conservative coverage window is not an exact replay of F01's component-specific last5 eligible-observation selector. F01's available windows are inventoried separately and remain unchanged. Prior non-UFC outcome history cannot supply a UFC round-stat denominator. No prior UFC history is reported separately; it does not prove a professional debut. F01 likewise withholds automatic debut-prior substitution when debut/completeness is unproven.

A full-bout count requires all rounds 1..finish_round and nonmissing field values. Pair candidates sum only rounds with both measurements; conversion requires a complete attempted-submission bout before attaching the result. Ground-bucket pairs additionally require governed elapsed duration and a lower bound within that duration. Partial paired histories remain explicitly partial. `complete_history_pct` requires every prior UFC bout to have the relevant complete pair; observed-pair availability alone is insufficient. Zero denominator is distinct from missing history, and zero minute bucket means less than one minute under the contract, not necessarily no exposure. The contract's interval model is empirical evidence, not an independently published vendor unit guarantee.

Counts summed across target fighter states repeat a fighter's prior events at different prediction dates: columns explicitly say state-weighted. They are support distributions, not independent trial totals or confidence intervals. Bout-level records supply unique event counts; no statistical uncertainty calculation treats repeated fighter states as independent. Quantiles and missingness are descriptive; no style thresholds are chosen from outcomes.
