# Comparable-access separation

Boundary and block tables preserve every stratum; primary first/next residual rank dependence:

| year | scope | access_quartile | control_cut | sub_cut | n | spearman | pearson | ci_low | ci_high | direction_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | same_access_first_residual | 0 | NA | NA | 111 | 0.034 | 0.049 | NA | NA | 0.509 |
| 2018 | same_access_next_residual | 0 | NA | NA | 111 | 0.280 | 0.277 | NA | NA | 0.578 |
| 2019 | same_access_first_residual | 0 | NA | NA | 118 | 0.150 | 0.169 | NA | NA | 0.551 |
| 2019 | same_access_next_residual | 0 | NA | NA | 118 | 0.283 | 0.277 | NA | NA | 0.621 |
| 2020 | same_access_first_residual | 0 | NA | NA | 139 | 0.161 | 0.175 | NA | NA | 0.500 |
| 2020 | same_access_next_residual | 0 | NA | NA | 139 | 0.127 | 0.135 | NA | NA | 0.540 |
| 2021 | same_access_first_residual | 0 | NA | NA | 163 | 0.147 | 0.160 | NA | NA | 0.528 |
| 2021 | same_access_next_residual | 0 | NA | NA | 163 | 0.080 | 0.087 | NA | NA | 0.531 |
| 2022 | same_access_first_residual | 0 | NA | NA | 188 | 0.137 | 0.150 | NA | NA | 0.521 |
| 2022 | same_access_next_residual | 0 | NA | NA | 188 | 0.066 | 0.078 | NA | NA | 0.543 |
| 2023 | same_access_first_residual | 0 | NA | NA | 212 | 0.140 | 0.163 | NA | NA | 0.558 |
| 2023 | same_access_next_residual | 0 | NA | NA | 212 | 0.053 | 0.053 | NA | NA | 0.545 |
| 2024 | same_access_first_residual | 0 | NA | NA | 230 | 0.159 | 0.185 | NA | NA | 0.574 |
| 2024 | same_access_next_residual | 0 | NA | NA | 230 | 0.046 | 0.051 | NA | NA | 0.539 |
| 2025 | same_access_first_residual | 0 | NA | NA | 251 | 0.143 | 0.167 | NA | NA | 0.560 |
| 2025 | same_access_next_residual | 0 | NA | NA | 251 | 0.067 | 0.073 | NA | NA | 0.526 |
| 2026 | same_access_first_residual | 0 | NA | NA | 266 | 0.142 | 0.163 | NA | NA | 0.559 |
| 2026 | same_access_next_residual | 0 | NA | NA | 266 | 0.093 | 0.098 | NA | NA | 0.536 |

2026 discordant-region replication:

| year | region | n | total | share | retention | independence_prevalence | excess | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026 | 1 | 52 | 266 | 0.195 | 0.288 | 0.222 | 0.066 | -0.032 | 0.167 |
| 2026 | 2 | 67 | 266 | 0.252 | 0.224 | 0.241 | -0.017 | -0.101 | 0.071 |

Region coding: 0 = low control/low SUB; 1 = low control/high SUB; 2 = high control/low SUB; 3 = high both. “High” is relative to prespecified first-block within-access median, not a natural class or a tactical-intent threshold. Bootstrap excess compares retention against the second-block marginal prevalence within each access stratum. Full boundary distributions and all four regions are in separation.csv, regions.csv and region_replication.csv.

Support/shrinkage sensitivity (2026):

| year | screen | representation | x | y | n | spearman | pearson | ci_low | ci_high | direction_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026 | primary | raw | control | submission | 1193 | 0.120 | 0.122 | NA | NA | 0.534 |
| 2026 | primary | pooled | control | submission | 1193 | 0.132 | 0.132 | NA | NA | 0.534 |
| 2026 | strict | raw | control | submission | 789 | 0.161 | 0.161 | NA | NA | 0.553 |
| 2026 | strict | pooled | control | submission | 789 | 0.154 | 0.154 | NA | NA | 0.547 |

These descriptive sensitivities do not change the raw replication gates. Weak redundancy alone does not establish repeatable individual assignment. Both region retention and continuous repeatability must be considered.

Histories use strict event-date priors with target and same-date exclusion, sealed through 2026-08-15. Continuous behavioral rates do not establish intention, top control, true ground exposure or causal effects. This is developmental historical evidence; repeated fighters and nested boundaries are dependent. No predictive model or prospective confirmation outcomes were used.
