# B5 root cause

Membership and observed finish cohort unchanged. Primary SUB 39.578134%, observed 54.929577%; deficit 15.351443%. Half return recovers 33.77% of that mean deficit.

| diagnostic | LL | Brier | conditional_SUB | entries | ground_minutes | sub_attempts | ground_ko | standing_ko |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0.714952 | 0.260218 | 0.395781 | 2.098714 | 2.653908 | 0.581244 | 0.043434 | 0.214472 |
| return_half | 0.687687 | 0.247700 | 0.447622 | 1.892601 | 3.237540 | 0.713603 | 0.053247 | 0.196519 |
| return_double | 0.780354 | 0.288025 | 0.321706 | 2.344053 | 1.941517 | 0.422521 | 0.031612 | 0.236217 |
| oracle_occupancy | 0.673530 | 0.240673 | 0.514828 | 1.568245 | 4.125859 | 0.919480 | 0.068444 | 0.168825 |
| oracle_attempts | 0.665016 | 0.236639 | 0.519525 | 1.981334 | 2.390949 | 0.931510 | 0.039004 | 0.203216 |
| oracle_conversion_pool | 0.716476 | 0.261137 | 0.395164 | 2.099950 | 2.655381 | 0.581702 | 0.043356 | 0.214224 |
| oracle_combined | 0.666507 | 0.237375 | 0.519085 | 1.983481 | 2.393844 | 0.932746 | 0.038902 | 0.202876 |

Finish-only reward comparison against the aggregate finish cohort:

| group | n | ever_entry | entries | ground_minutes | returns | sub_attempts | ground_actions | sub_finishes | ground_ko | standing_ko | conversion_weighted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_FINISH | 2115 | 0.808559 | 1.822802 | 2.353803 | 1.072287 | 0.360978 | 8.057880 | 0.103254 | 0.043443 | 0.275911 | 0.297459 |
| B5 | 355 | 0.860202 | 2.081254 | 2.651096 | 1.210180 | 0.581770 | 8.789775 | 0.160848 | 0.043874 | 0.222773 | 0.281096 |

Fighter-side directional input comparison:

| ability | mean | mean_prior | mean_effective_support | median_den |
| --- | --- | --- | --- | --- |
| access | 0.297335 | 0.263873 | 0.608353 | 58.275000 |
| control | 0.225475 | 0.187215 | 0.485325 | 30.000000 |
| submission | 0.054905 | 0.029989 | 0.608353 | 58.275000 |
| gnp | 0.772898 | 0.632480 | 0.472861 | 58.275000 |
| td_resistance | 0.617344 | 0.635141 | 0.409889 | 14.000000 |
| control_allowed | 0.207118 | 0.187215 | 0.485325 | 30.000000 |
| sub_faced | 0.043654 | 0.029989 | 0.608353 | 58.275000 |
| ground_allowed | 0.667201 | 0.632480 | 0.472861 | 58.275000 |
| sub_conversion | 0.285299 | 0.282962 | 0.089468 | 3.000000 |
| sub_conversion_allowed | 0.277700 | 0.282962 | 0.070874 | 3.000000 |

B5 creation is stronger than aggregate, and input submission/allowed-work rates retain pressure-vulnerability alignment before conversion. The signal is compressed by square-root construction and scarce conversion support, not wholly erased: identity predicts SUB39.58% versus population31.85%. Occupancy and attempt checks bring SUB near51–52%, with LL improvements. Training pooled conversion alone slightly worsens B5 LL, rejecting a simple conversion-only explanation. Ground KO is small relative to standing KO. There is no defensible additive causal decomposition of the observed deficit.

Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
