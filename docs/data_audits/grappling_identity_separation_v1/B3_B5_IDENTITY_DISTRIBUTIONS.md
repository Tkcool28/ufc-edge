# Frozen B3/B5 identity distributions

| cell | year | metric | representation | states | supported | support_share | p10 | p25 | p50 | p75 | p90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_SCORED | ALL | control | raw | 8520 | 6569 | 0.771 | 0.027 | 0.073 | 0.164 | 0.285 | 0.432 |
| ALL_SCORED | ALL | submission | raw | 8520 | 5737 | 0.673 | 0.000 | 0.000 | 0.025 | 0.056 | 0.095 |
| ALL_SCORED | ALL | gnp | raw | 8520 | 5737 | 0.673 | 0.165 | 0.341 | 0.618 | 0.986 | 1.507 |
| B3 | ALL | control | raw | 824 | 685 | 0.831 | 0.068 | 0.162 | 0.306 | 0.461 | 0.617 |
| B3 | ALL | submission | raw | 824 | 650 | 0.789 | 0.004 | 0.028 | 0.065 | 0.096 | 0.153 |
| B3 | ALL | gnp | raw | 824 | 650 | 0.789 | 0.300 | 0.492 | 0.835 | 1.279 | 2.010 |
| B5 | ALL | control | raw | 1182 | 996 | 0.843 | 0.064 | 0.131 | 0.234 | 0.360 | 0.525 |
| B5 | ALL | submission | raw | 1182 | 899 | 0.761 | 0.000 | 0.031 | 0.061 | 0.089 | 0.128 |
| B5 | ALL | gnp | raw | 1182 | 899 | 0.761 | 0.303 | 0.481 | 0.786 | 1.161 | 1.806 |

Use all frozen scored cell bouts, both fighter sides. Membership IDs came from PR160 and were hash verified; no target method/outcome or saved probability was used in constructing this report. Compare supported continuous dispersion, not median-derived style labels. Cell-specific support differs and may explain apparent concentration. B3 has broad decision-control dispersion (IQR 0.162–0.461) and SUB activity dispersion (0.028–0.096 attempts/minute), consistent with mixed observed ground pathways. B5 has a narrower SUB IQR (0.031–0.089) but its median 0.061 is slightly below B3’s 0.065, and its SUB p10 is zero. Thus B5 is not uniformly high-SUB or more active than B3; both exceed the full scored median 0.025 among supported sides. B5 control median 0.234 is below B3 0.306. These descriptive results do not establish stable fighter archetypes. Neither cell identifies the attacking side or proves a causal mechanism. Annual/raw/pooled distributions and missingness are retained in cell_distributions.csv and cell_states.csv.gz.

Decision-only control is sparser than all-history SUB, so heterogeneity among supported states cannot be generalized to unsupported cell sides.

Histories use strict event-date priors with target and same-date exclusion, sealed through 2026-08-15. Continuous behavioral rates do not establish intention, top control, true ground exposure or causal effects. This is developmental historical evidence; repeated fighters and nested boundaries are dependent. No predictive model or prospective confirmation outcomes were used.
