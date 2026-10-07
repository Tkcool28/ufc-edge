# Control behavior diagnostic

Generic control contains repeatable behavioral information. In disjoint first-three versus next-three prior bouts, elapsed control share has substantially stronger rank persistence than CTRL per landed TD. This supports studying control tendency; it does not measure top retention after a specific entry.

| year | metric | unique_fighters | spearman |
| --- | --- | --- | --- |
| 2018 | td_attempts_per15 | 278 | 0.633 |
| 2018 | control_share | 278 | 0.469 |
| 2018 | control_sec_per_fight | 323 | 0.395 |
| 2018 | control_sec_per_td | 53 | 0.297 |
| 2018 | control_allowed_share | 278 | 0.300 |
| 2026 | td_attempts_per15 | 723 | 0.639 |
| 2026 | control_share | 723 | 0.484 |
| 2026 | control_sec_per_fight | 840 | 0.441 |
| 2026 | control_sec_per_td | 127 | 0.256 |
| 2026 | control_allowed_share | 723 | 0.310 |

Comparable TD-attempt activity still leaves a wide continuous control-share distribution:

| access_quartile | metric | supported_fighters | p25 | p50 | p75 |
| --- | --- | --- | --- | --- | --- |
| 1 | control_share | 131 | 0.054 | 0.083 | 0.128 |
| 2 | control_share | 130 | 0.117 | 0.170 | 0.237 |
| 3 | control_share | 130 | 0.179 | 0.253 | 0.338 |
| 4 | control_share | 131 | 0.254 | 0.344 | 0.424 |

These are training-fighter boundary snapshots with three matched bouts and at least 15 elapsed minutes. Access quartiles are outcome-blind descriptive strata, not style labels. Opponent selection, TD conversion, clinch control and career development are unadjusted. Control allowed is useful as an opponent-history measurement, with weaker persistence; it cannot become a standup/escape probability.

Histories use event_date < target date, excluding the target and same-date bouts. The sealed source ends 2026-08-15. No predictive fits, source changes, hard fighter labels, prospective outcomes, threshold optimization or Arm C promotion. These are retrospective event-date histories; current acquisition snapshots do not prove historical publication vintages. A denominator screen means descriptive support, not proven reliability. Repeated fighter states and nested annual boundaries are not independent samples.
