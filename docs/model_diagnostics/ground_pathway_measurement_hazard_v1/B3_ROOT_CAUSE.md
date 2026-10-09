# B3 root cause

Membership and observed finish cohort unchanged. Primary SUB 34.859272%, observed 54.017857%; deficit 19.158585%. Half return recovers 30.16% of that mean deficit.

| diagnostic | LL | Brier | conditional_SUB | entries | ground_minutes | sub_attempts | ground_ko | standing_ko |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0.758458 | 0.275256 | 0.348593 | 2.542943 | 2.828220 | 0.499973 | 0.049924 | 0.218018 |
| return_half | 0.715750 | 0.257523 | 0.406379 | 2.260743 | 3.578096 | 0.634588 | 0.063694 | 0.196292 |
| return_double | 0.847698 | 0.309092 | 0.272746 | 2.856475 | 1.985600 | 0.350132 | 0.034779 | 0.242197 |
| oracle_occupancy | 0.686015 | 0.244595 | 0.488337 | 1.777218 | 4.840305 | 0.864107 | 0.087721 | 0.159129 |
| oracle_attempts | 0.683213 | 0.242957 | 0.471243 | 2.412390 | 2.587201 | 0.816723 | 0.045629 | 0.207149 |
| oracle_conversion_pool | 0.757617 | 0.276162 | 0.349631 | 2.543130 | 2.827346 | 0.500461 | 0.049719 | 0.217393 |
| oracle_combined | 0.683939 | 0.243749 | 0.473716 | 2.412473 | 2.585614 | 0.817570 | 0.045307 | 0.206159 |

Finish-only reward comparison against the aggregate finish cohort:

| group | n | ever_entry | entries | ground_minutes | returns | sub_attempts | ground_actions | sub_finishes | ground_ko | standing_ko | conversion_weighted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_FINISH | 2115 | 0.808559 | 1.822802 | 2.353803 | 1.072287 | 0.360978 | 8.057880 | 0.103254 | 0.043443 | 0.275911 | 0.297459 |
| B3 | 224 | 0.888471 | 2.503558 | 2.800386 | 1.633627 | 0.514405 | 9.516660 | 0.144530 | 0.052180 | 0.245985 | 0.292402 |

Fighter-side directional input comparison:

| ability | mean | mean_prior | mean_effective_support | median_den |
| --- | --- | --- | --- | --- |
| access | 0.338310 | 0.258241 | 0.596323 | 54.425000 |
| control | 0.246076 | 0.186837 | 0.466168 | 30.000000 |
| submission | 0.055923 | 0.028935 | 0.596323 | 54.425000 |
| gnp | 0.832722 | 0.645059 | 0.464117 | 54.425000 |
| td_resistance | 0.635174 | 0.630527 | 0.355656 | 11.000000 |
| control_allowed | 0.178929 | 0.186837 | 0.466168 | 30.000000 |
| sub_faced | 0.030682 | 0.028935 | 0.596323 | 54.425000 |
| ground_allowed | 0.617165 | 0.645059 | 0.464117 | 54.425000 |
| sub_conversion | 0.297135 | 0.290955 | 0.084956 | 4.000000 |
| sub_conversion_allowed | 0.287703 | 0.290955 | 0.044741 | 1.000000 |

B3 has more entries and more SUB creation than aggregate, so the identity signal reaches the engine. However, realized opportunity is too short to express its submission work fully. Entry-only deficiency is insufficient: B3 ever entry is already 0.888471 and expected entries 2.503558 in finishes. Occupancy and attempt oracles improve B3 LL beyond its Arm C0.702832, but neither reaches observed SUB share. Conversion pooling adds little. Standing KO remains a large competing reward. These isolated responses are nonadditive and cannot partition an observed outcome deficit causally.

Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
