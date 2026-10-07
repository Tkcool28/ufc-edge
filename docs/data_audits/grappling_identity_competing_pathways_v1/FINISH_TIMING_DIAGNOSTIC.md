# Finish timing diagnostic

Modern historical submissions are not generally earlier than KO/TKO. The proposed 'submission hunters end immediately after access' explanation is unsupported by these bout-level clocks: access timing is unobserved.

| year | method | bouts | elapsed_known | R1_pct | R2_pct | R3plus_pct | median_elapsed_min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | KO_TKO | 451 | 451 | 51.220 | 29.933 | 18.847 | 4.950 |
| 2018 | SUBMISSION | 256 | 256 | 42.969 | 32.422 | 24.609 | 7.000 |
| 2026 | KO_TKO | 1691 | 1690 | 50.680 | 31.047 | 18.273 | 4.983 |
| 2026 | SUBMISSION | 948 | 948 | 46.097 | 33.861 | 20.042 | 6.342 |

All-UFC, modern-era and scheduled-round strata are retained in finish_timing.csv. Early UFC single-round formats cannot be pooled as though R1 always means five minutes; governed elapsed exposure is left missing where unsupported.

First versus second historical finish wins, unique fighters, strict event-date ordering:

| year | method | first_R1 | fighters | second_R1_pct |
| --- | --- | --- | --- | --- |
| 2018 | SUBMISSION | False | 83 | 38.554 |
| 2018 | SUBMISSION | True | 134 | 54.478 |
| 2018 | KO_TKO | False | 133 | 43.609 |
| 2018 | KO_TKO | True | 195 | 62.564 |
| 2026 | SUBMISSION | False | 160 | 46.250 |
| 2026 | SUBMISSION | True | 210 | 50.476 |
| 2026 | KO_TKO | False | 249 | 43.373 |
| 2026 | KO_TKO | True | 350 | 61.714 |

This is a selected repeated-winner sample, not conditional hazard or a calibrated ability estimate. Three prior submission wins occur in only a small share of original training histories; first-three/next-three blocks have insufficient repeated-win support for the screened early-finish-share coefficient. Finish timing mostly adds duration/outcome context here, rather than a robust new identity dimension. No elapsed time from TD/access to submission or KO is inferable.

Histories use event_date < target date, excluding the target and same-date bouts. The sealed source ends 2026-08-15. No predictive fits, source changes, hard fighter labels, prospective outcomes, threshold optimization or Arm C promotion. These are retrospective event-date histories; current acquisition snapshots do not prove historical publication vintages. A denominator screen means descriptive support, not proven reliability. Repeated fighter states and nested annual boundaries are not independent samples.
