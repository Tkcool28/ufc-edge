# Aggregate conditional comparison

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

| model | finish_N | actual_KO | mean_KO | log_loss | brier | AUC | ECE | calibration_intercept | calibration_slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LINEAR_MIN | 2115 | 0.643499 | 0.663152 | 0.615366 | 0.213614 | 0.663563 | 0.031387 | 0.010552 | 0.830658 |
| XGB | 2115 | 0.643499 | 0.652944 | 0.611050 | 0.211944 | 0.667017 | 0.022657 | -0.053615 | 1.015144 |
| LGBM | 2115 | 0.643499 | 0.654087 | 0.611886 | 0.212159 | 0.666430 | 0.019856 | -0.031574 | 0.967678 |
| CAT | 2115 | 0.643499 | 0.657840 | 0.611210 | 0.211777 | 0.670908 | 0.022934 | -0.021467 | 0.920548 |
| SELECT | 2115 | 0.643499 | 0.657083 | 0.614896 | 0.213543 | 0.663533 | 0.022994 | 0.010201 | 0.873607 |

The same 2,115 outcomes underpin all rows. These repeat the global results already observed in PR121, not new independent evidence.
