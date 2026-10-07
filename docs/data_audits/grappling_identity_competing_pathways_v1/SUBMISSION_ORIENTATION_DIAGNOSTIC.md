# Submission orientation diagnostic

Recorded submission activity has moderate repeatability and measurable variation among similar-access histories. Together with control it supports a partial continuous submission-seeking representation. Low SUB counts alongside high CTRL are observable behavior, not proof of deliberate safe grinding.

| year | metric | unique_fighters | spearman |
| --- | --- | --- | --- |
| 2018 | sub_attempts_per_fight | 325 | 0.370 |
| 2018 | sub_attempts_per_min | 278 | 0.353 |
| 2018 | sub_attempts_per_td | 54 | 0.416 |
| 2018 | sub_attempts_per_control_min_PROXY | 130 | 0.210 |
| 2018 | sub_wins_per_fight | 325 | 0.228 |
| 2018 | sub_to_ground_attempts_PROXY | 95 | 0.270 |
| 2026 | sub_attempts_per_fight | 842 | 0.372 |
| 2026 | sub_attempts_per_min | 723 | 0.356 |
| 2026 | sub_attempts_per_td | 128 | 0.330 |
| 2026 | sub_attempts_per_control_min_PROXY | 313 | 0.228 |
| 2026 | sub_wins_per_fight | 842 | 0.245 |
| 2026 | sub_to_ground_attempts_PROXY | 194 | 0.336 |

| access_quartile | metric | supported_fighters | p25 | p50 | p75 |
| --- | --- | --- | --- | --- | --- |
| 1 | sub_attempts_per_min | 131 | 0.000 | 0.015 | 0.038 |
| 1 | sub_attempts_per_td | 24 | 0.172 | 0.400 | 1.000 |
| 2 | sub_attempts_per_min | 130 | 0.010 | 0.029 | 0.058 |
| 2 | sub_attempts_per_td | 78 | 0.111 | 0.348 | 0.612 |
| 3 | sub_attempts_per_min | 130 | 0.011 | 0.033 | 0.061 |
| 3 | sub_attempts_per_td | 102 | 0.123 | 0.257 | 0.435 |
| 4 | sub_attempts_per_min | 131 | 0.004 | 0.035 | 0.072 |
| 4 | sub_attempts_per_td | 118 | 0.052 | 0.167 | 0.364 |

SUB per TD retains a small selected cohort; SUB per control minute is less repeatable and control is not submission opportunity. The median original training-date SUB count is only one in the 2018 and 2026 folds. Sparse rates need substantial pooling. SUB wins per prior fight are legal prior outcomes but overlap existing finish-profile information. Do not estimate finish-per-attempt probability: PR #158 documents wins with zero recorded attempts and no verified Bernoulli attempt trials. No attempt quality or access-to-attempt timing is identified.

Histories use event_date < target date, excluding the target and same-date bouts. The sealed source ends 2026-08-15. No predictive fits, source changes, hard fighter labels, prospective outcomes, threshold optimization or Arm C promotion. These are retrospective event-date histories; current acquisition snapshots do not prove historical publication vintages. A denominator screen means descriptive support, not proven reliability. Repeated fighter states and nested annual boundaries are not independent samples.
