# B5 mechanism heterogeneity

Unchanged PR #125 cell: **591 all-scored bouts**, **355 standard finishes**. Frozen observed SUB among finishes: **54.93%**; saved Arm C conditional predicted SUB: **48.06%**. All cell bouts are described, including decisions; the finish-only result is retained only as the existing diagnostic context. No membership, threshold or prediction changed.

## Strict-prior support

| candidate | fighter_states | missing_pair_pct | zero_den_pct_observed | den_p50 | complete_history_pct |
| --- | --- | --- | --- | --- | --- |
| sub_per_td | 1182 | 0.76 | 11.76 | 6.00 | 98.98 |
| control_per_td | 1182 | 0.76 | 11.76 | 6.00 | 98.98 |
| sub_per_ground_bucket | 1182 | 41.03 | 5.16 | 10.00 | 9.22 |
| ground_strikes_per_ground_bucket | 1182 | 41.03 | 5.16 | 10.00 | 9.22 |
| sub_per_elapsed_min | 1182 | 0.76 | 0.00 | 56.93 | 98.48 |
| ground_strikes_per_elapsed_min | 1182 | 0.76 | 0.00 | 56.93 | 98.48 |
| sub_conversion | 1182 | 0.76 | 14.92 | 3.00 | 98.98 |
| sub_conversion_faced | 1182 | 0.76 | 19.61 | 3.00 | 98.98 |

## Continuous count distributions, no outcome-selected style bins

| field | states | observed_states | zero_observed_pct | p10 | p25 | p50 | p75 | p90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| takedowns_attempted | 1182 | 1173 | 7.08 | 1.00 | 5.00 | 15.00 | 34.00 | 68.00 |
| takedowns_landed | 1182 | 1173 | 11.76 | 0.00 | 2.00 | 6.00 | 14.00 | 28.00 |
| submission_attempts | 1182 | 1173 | 14.92 | 0.00 | 1.00 | 3.00 | 7.00 | 12.00 |
| sig_ground_attempted | 1182 | 1173 | 5.20 | 2.00 | 15.00 | 45.00 | 103.00 | 192.80 |
| sig_ground_landed | 1182 | 1173 | 6.48 | 1.00 | 12.00 | 32.00 | 72.00 | 134.40 |
| control_sec | 1182 | 1173 | 1.45 | 94.00 | 324.00 | 812.00 | 1769.00 | 3137.20 |
| reversals | 1182 | 1173 | 40.41 | 0.00 | 0.00 | 1.00 | 2.00 | 4.00 |
| ground_bucket_min | 1182 | 694 | 5.33 | 2.00 | 4.00 | 10.00 | 20.00 | 29.00 |
| ground_control_bucket_min | 1182 | 1085 | 19.17 | 0.00 | 1.00 | 5.00 | 10.00 | 18.00 |
| back_control_bucket_min | 1182 | 1085 | 71.71 | 0.00 | 0.00 | 0.00 | 1.00 | 3.00 |
| standups | 1182 | 755 | 18.01 | 0.00 | 1.00 | 3.00 | 7.00 | 13.60 |
| submission_attempts_faced | 1182 | 1173 | 19.61 | 0.00 | 1.00 | 3.00 | 6.00 | 10.00 |
| control_sec_allowed | 1182 | 1173 | 2.56 | 84.20 | 283.00 | 708.00 | 1403.00 | 2552.80 |
| reversals_faced | 1182 | 1173 | 42.28 | 0.00 | 0.00 | 1.00 | 2.00 | 5.00 |

| cell | window | a | b | paired_states | spearman |
| --- | --- | --- | --- | --- | --- |
| B5 | career | submission_attempts | sig_ground_attempted | 1173 | 0.60 |
| B5 | career | submission_attempts | control_sec | 1173 | 0.68 |
| B5 | career | takedowns_landed | control_sec | 1173 | 0.92 |
| B5 | career | standups | reversals | 755 | 0.41 |

Correlations are descriptive associations of repeated prior-history counts, affected by fighter experience and overlap; they are not independent-sample tests or evidence of causation. `B3_B5_proxy_ratio_distributions.csv` reports supported nonzero-denominator descriptive ratios alongside availability, with underlying numerator/denominator counts in `B3_B5_strict_prior_states.csv.gz`. Total fight minute is explicitly a general-time normalization, never ground opportunity. Sparse diagnostic ratios are not recommended production values; no conversion ratio performance is calculated.

## What can actually be distinguished

| Proposed style | Measurable evidence now | Unresolved distinction |
| --- | --- | --- |
| Submission-oriented grappler | Prior recorded SUB attempts alongside ground-strike activity and TD counts | Attempt quality, bottom/scramble context and actual opportunity time absent |
| Control wrestler | Generic CTRL, coarse ground-control buckets and low recorded offensive counts can describe a proxy profile | Generic control is not top retention; low observed activity may reflect missing opportunity |
| Ground-and-pound wrestler | Significant ground-strike ATT/land available, relative to SUB counts | Not all ground-and-pound, not damage or grounded-minute offensive intensity |
| Scramble grappler | Reversals and partial standup counts | No transition sequence, ground-entry count, exposure per scramble or validated escape rate |
| Takedown-volume fighter | Attempt and completion counts with generic CTRL/TD proxy | Completion does not establish stable entry; alternate ground-entry mechanisms absent |

The cells contain descriptive variation in measurable offensive activity, but the audit **cannot assign verified mechanism classes** or establish that an unobserved mixture causes the residual calibration gap. B3/B5 differences in support are not new subgroup performance estimates. Both cells use identical source rules, and their annual/recent distributions are retained without pooling away era gaps. No individual fights were selected to illustrate a preferred hypothesis.

All audit histories use event_date < target event date; the target and every same-date bout are excluded. Only pinned UFC history through 2026-08-15 is used. No prospective confirmation outcomes, model fitting, feature promotion or frozen-source edits occur. This is retrospective event-date governance: 2026 acquisition snapshots cannot prove what a provider published before every old fight. Preserve that publication-vintage limitation.

The modern population is the unchanged 5,658-fight PR #125 universe; its 4,260 outer-scored bouts and exact conditional training/scoring fight IDs are reused. Historical measurements retain earlier UFC bouts where available. Boundary rows describe unique fighters appearing in the frozen conditional training set at January 1. Training-prefight rows describe their original historical prediction dates, not values accumulated at the later boundary. Scoring rows include all eligible bouts, with 2026 truncated at the existing August 15 boundary. Division rows follow frozen target division, without inferring sex from unsupported metadata.

`career` here means available prior UFC history for the candidate measurement audit. `last5` means the last five prior UFC bouts, including measurement-missing bouts; tied dates crossing the boundary fail closed. This deliberately conservative coverage window is not an exact replay of F01's component-specific last5 eligible-observation selector. F01's available windows are inventoried separately and remain unchanged. Prior non-UFC outcome history cannot supply a UFC round-stat denominator. No prior UFC history is reported separately; it does not prove a professional debut. F01 likewise withholds automatic debut-prior substitution when debut/completeness is unproven.

A full-bout count requires all rounds 1..finish_round and nonmissing field values. Pair candidates sum only rounds with both measurements; conversion requires a complete attempted-submission bout before attaching the result. Ground-bucket pairs additionally require governed elapsed duration and a lower bound within that duration. Partial paired histories remain explicitly partial. `complete_history_pct` requires every prior UFC bout to have the relevant complete pair; observed-pair availability alone is insufficient. Zero denominator is distinct from missing history, and zero minute bucket means less than one minute under the contract, not necessarily no exposure. The contract's interval model is empirical evidence, not an independently published vendor unit guarantee.

Counts summed across target fighter states repeat a fighter's prior events at different prediction dates: columns explicitly say state-weighted. They are support distributions, not independent trial totals or confidence intervals. Bout-level records supply unique event counts; no statistical uncertainty calculation treats repeated fighter states as independent. Quantiles and missingness are descriptive; no style thresholds are chosen from outcomes.
