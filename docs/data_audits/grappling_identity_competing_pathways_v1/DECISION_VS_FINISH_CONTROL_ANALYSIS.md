# Decision versus finish control

Separating outcomes materially clarifies the meaning of control totals. Within the same fighters, decision and own-finish-win histories show much different raw accumulation and exposure. These are medians across paired fighter-history means, not independent bout observations or causal effects.

| finish_subset | fighters | decision_control_sec | finish_control_sec | decision_share | finish_share | decision_min | finish_min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| own_KO_wins | 960 | 153.310 | 45.690 | 0.163 | 0.157 | 15.000 | 5.510 |
| own_SUB_wins | 719 | 190.778 | 119.143 | 0.206 | 0.362 | 15.000 | 6.127 |

The all-prior, decision-only, prior KO/TKO and prior submission states remain separate in outcome_separated_prior_states.csv.gz. The table above compares own finish wins specifically, preventing losses from being presented as the fighter's offensive success. At least one measured bout in each category is enough for this exploratory comparison; many fighters remain sparse.

| year | metric | fighters | spearman_with_mean_duration |
| --- | --- | --- | --- |
| 2018 | control_share | 970 | 0.009 |
| 2018 | sub_attempts_per_min | 970 | -0.190 |
| 2026 | control_share | 1728 | -0.008 |
| 2026 | sub_attempts_per_min | 1728 | -0.168 |

A short SUB win ends control accumulation; low total CTRL in such a win is not low retention ability. Decision-only control removes terminal-duration truncation within that subset, but conditioning on decisions selects opponent, durability and scheduled-length environments. It does not remove every bias. Both raw seconds and elapsed share must remain visible. A first experiment should isolate decision-only control rather than add finish timing, finish conversion and several proxies simultaneously.

Histories use event_date < target date, excluding the target and same-date bouts. The sealed source ends 2026-08-15. No predictive fits, source changes, hard fighter labels, prospective outcomes, threshold optimization or Arm C promotion. These are retrospective event-date histories; current acquisition snapshots do not prove historical publication vintages. A denominator screen means descriptive support, not proven reliability. Repeated fighter states and nested annual boundaries are not independent samples.
