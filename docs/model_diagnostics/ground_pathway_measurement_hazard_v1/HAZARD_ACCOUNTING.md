# Hazard accounting

Exact reward integral: I=integral exp(Tt)dt over 0–5 minutes, where T is the transient S/GA/GB generator. The first row of I is weighted by successive round-survival mass. Action counts are occupancy times Poisson action rates; terminal counts are occupancy times absorbing hazards. Returns exclude mandatory round-end resets. Ever-entry tracks first entry before standing KO and round expiration.

| diagnostic | ever_entry | entries | ground_minutes | ground_share | returns | sub_attempts | ground_actions | sub_finishes | ground_ko | standing_ko |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0.816715 | 1.854897 | 2.382161 | 0.191271 | 1.099117 | 0.353351 | 7.967301 | 0.100154 | 0.041359 | 0.249948 |
| return_half | 0.816715 | 1.701851 | 2.953228 | 0.239954 | 0.700521 | 0.438922 | 9.916100 | 0.124395 | 0.051491 | 0.233259 |
| return_double | 0.816715 | 2.031441 | 1.708221 | 0.135320 | 1.530705 | 0.252881 | 5.689195 | 0.071689 | 0.029524 | 0.269624 |
| oracle_occupancy | 0.816715 | 1.451330 | 3.859297 | 0.320108 | 0.001312 | 0.575193 | 13.047113 | 0.163031 | 0.067810 | 0.206715 |
| oracle_attempts | 0.816715 | 1.784725 | 2.213237 | 0.185754 | 1.021563 | 0.589741 | 7.395003 | 0.167609 | 0.038429 | 0.241692 |
| oracle_conversion_pool | 0.816715 | 1.853908 | 2.378804 | 0.191100 | 1.097966 | 0.353175 | 7.951837 | 0.101647 | 0.041198 | 0.249445 |
| oracle_combined | 0.816715 | 1.783094 | 2.207819 | 0.185451 | 1.019665 | 0.589091 | 7.370171 | 0.169952 | 0.038171 | 0.240876 |

Raw finish rewards belong to the CTMC. Composed conditional probabilities renormalize KO/SUB, then multiply by unchanged external MOV0 F. Do not equate raw SUB 0.100154 with composed SUB 0.127442. All-fight distributions, all nine years, and every fight are saved in reward_distributions.csv, annual_rewards.csv and the record archive. Exact reward closure and baseline reproduction pass.

| group | n | ever_entry | entries | ground_minutes | returns | sub_attempts | ground_actions | sub_finishes | ground_ko | standing_ko | conversion_weighted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_FINISH | 2115 | 0.808559 | 1.822802 | 2.353803 | 1.072287 | 0.360978 | 8.057880 | 0.103254 | 0.043443 | 0.275911 | 0.297459 |
| B3 | 224 | 0.888471 | 2.503558 | 2.800386 | 1.633627 | 0.514405 | 9.516660 | 0.144530 | 0.052180 | 0.245985 | 0.292402 |
| B5 | 355 | 0.860202 | 2.081254 | 2.651096 | 1.210180 | 0.581770 | 8.789775 | 0.160848 | 0.043874 | 0.222773 | 0.281096 |
| A1 | 457 | 0.745685 | 1.564801 | 2.114801 | 0.881045 | 0.315493 | 7.585531 | 0.094300 | 0.044799 | 0.371968 | 0.312985 |
| A2 | 79 | 0.669510 | 1.264934 | 1.739141 | 0.691263 | 0.253871 | 6.763212 | 0.076213 | 0.038535 | 0.435756 | 0.311384 |
| A4 | 484 | 0.716609 | 1.488391 | 1.943929 | 0.865294 | 0.248868 | 7.444485 | 0.078995 | 0.050065 | 0.427136 | 0.328562 |


Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
