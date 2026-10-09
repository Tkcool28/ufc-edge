# Striking pathway damage

Standing hazard is independently computed from geometric KO creation/vulnerability and KD creation/vulnerability, multiplied by latent non-ground fraction and population-control normalization. It is not the saved Arm C striking probability. The engine already overallocates KO relative to observed submissions: full KO34.58% versus31.95% actual. A1/A4 failure is not explained by excessive SUB stealing KO; their primary SUB means are too low.

| diagnostic | group | LL | Brier | conditional_SUB | ground_ko | standing_ko |
| --- | --- | --- | --- | --- | --- | --- |
| primary | A1 | 0.564255 | 0.189477 | 0.199799 | 0.043954 | 0.357654 |
| primary | A2 | 0.322416 | 0.094780 | 0.142935 | 0.037287 | 0.390513 |
| primary | A4 | 0.569154 | 0.187524 | 0.147577 | 0.048751 | 0.409423 |
| return_half | A1 | 0.549476 | 0.184809 | 0.236916 | 0.054080 | 0.337242 |
| return_half | A2 | 0.330765 | 0.096667 | 0.172972 | 0.046452 | 0.372063 |
| return_half | A4 | 0.547616 | 0.181295 | 0.179884 | 0.060680 | 0.386606 |
| oracle_occupancy | A1 | 0.545459 | 0.184051 | 0.290528 | 0.069966 | 0.305365 |
| oracle_occupancy | A2 | 0.352830 | 0.103381 | 0.218414 | 0.061262 | 0.342789 |
| oracle_occupancy | A4 | 0.534070 | 0.177059 | 0.229262 | 0.080249 | 0.349698 |
| oracle_attempts | A1 | 0.546932 | 0.183914 | 0.293656 | 0.040784 | 0.346298 |
| oracle_attempts | A2 | 0.360857 | 0.105337 | 0.221058 | 0.034780 | 0.379113 |
| oracle_attempts | A4 | 0.533045 | 0.176686 | 0.229526 | 0.045570 | 0.397636 |
| oracle_combined | A1 | 0.546555 | 0.183850 | 0.302991 | 0.040237 | 0.344364 |
| oracle_combined | A2 | 0.368687 | 0.107947 | 0.226964 | 0.034549 | 0.378063 |
| oracle_combined | A4 | 0.531475 | 0.176290 | 0.247557 | 0.044595 | 0.394385 |

A1/A4 improve under opportunity diagnostics, while A2 damage appears: attempt oracle LL 0.360857 exceeds Arm C0.348743; combined0.368687. Therefore a global opportunity correction is not a finished solution. External MOV0 F and decision probability are unchanged in every diagnostic. Damage arises in conditional KO/SUB allocation and standing/ground competition, not a changed finish model.

Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
