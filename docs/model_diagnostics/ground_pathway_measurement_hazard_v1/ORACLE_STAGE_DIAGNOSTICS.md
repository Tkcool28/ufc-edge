# Oracle stage diagnostics

Training-only January-1 division aggregates set each isolated oracle. Occupancy uses best available generic CTRL proxy; attempts match historical aggregate SUB activity per alive minute in a homogeneous training population chain; conversion uses unshrunk coherent training success/attempt ratio; combined changes creation/conversion while leaving entry/return fixed. All use target-independent division/year factors. Future and target outcomes do not enter parameter construction. These are proxy oracles, not omniscient states.

| diagnostic | LL | Brier | multiclass_LL | summed_Brier | full_SUB | conditional_SUB | ground_minutes | sub_attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0.627949 | 0.217752 | 0.982002 | 0.587638 | 0.127442 | 0.270067 | 2.382161 | 0.353351 |
| return_half | 0.612866 | 0.212130 | 0.974513 | 0.584847 | 0.148240 | 0.314020 | 2.953228 | 0.438922 |
| return_double | 0.670128 | 0.232101 | 1.002943 | 0.594575 | 0.099534 | 0.211109 | 1.708221 | 0.252881 |
| oracle_occupancy | 0.610802 | 0.211629 | 0.973488 | 0.584469 | 0.176899 | 0.374631 | 3.859297 | 0.575193 |
| oracle_attempts | 0.608726 | 0.210554 | 0.972458 | 0.583900 | 0.179333 | 0.379787 | 2.213237 | 0.589741 |
| oracle_conversion_pool | 0.625456 | 0.217339 | 0.980764 | 0.587228 | 0.128964 | 0.272887 | 2.378804 | 0.353175 |
| oracle_combined | 0.608541 | 0.210519 | 0.972366 | 0.583906 | 0.181647 | 0.384209 | 2.207819 | 0.589091 |

Attempt and occupancy checks recover respectively 95.30% and 85.00% of the LL gap. Both still fail Arm C; combined LL 0.608541 also fails. Mean SUB matching does not guarantee individual calibration. Occupancy oracle fails its target in 112/117 contexts; favorable performance cannot validate its physical meaning. Combined is the sole preregistered two-stage diagnostic, not a combination search.

Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
