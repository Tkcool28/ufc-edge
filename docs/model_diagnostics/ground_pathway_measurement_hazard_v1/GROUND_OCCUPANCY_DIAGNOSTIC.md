# Ground occupancy diagnostic

Observed input is decision-only generic CTRL, not total ground time. For symmetric population q, entry e=access*TD-success and return=e*(1-q)/q. The bilateral generator has stationary ground share 2q/(1+q), not 2q. Actor occupancy q/(1+q) is below q; multiplying conditional work s/q by occupancy reconstructs s/(1+q) even before resets and absorbing finishes.

Training finite-horizon population ground-share mean is 0.203046, against CTRL target 0.377612. 112/117 division-year targets cannot be reached even at effectively zero return. Entry scarcity, round reset and finish absorption constrain this proxy oracle. It is not evidence CTRL equals ground truth.

| diagnostic | ground_minutes | ground_share | sub_attempts | full_SUB | LL | Brier |
| --- | --- | --- | --- | --- | --- | --- |
| primary | 2.382161 | 0.191271 | 0.353351 | 0.127442 | 0.627949 | 0.217752 |
| return_half | 2.953228 | 0.239954 | 0.438922 | 0.148240 | 0.612866 | 0.212130 |
| oracle_occupancy | 3.859297 | 0.320108 | 0.575193 | 0.176899 | 0.610802 | 0.211629 |

CTRL may include clinch, omits neutral/bottom activity and scramble duration, and the decision-only sample differs from all-history activity. Those mismatches cannot be numerically corrected without a measurement contract. Inflated control denominators can lower conditional SUB work; changing decision selection can bias either direction.

Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
