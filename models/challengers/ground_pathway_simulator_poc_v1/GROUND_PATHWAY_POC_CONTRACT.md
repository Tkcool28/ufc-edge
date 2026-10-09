# Simplified ground-pathway POC V1 — preregistration
Starting main f70848818005e54d2db000ec73677f2fd27be033; merged PR161 verified 2026-10-09. Independent of PR162. Explicit current user authorization supersedes prior diagnostic-only next recommendations. No promotion or merge.

One fixed mechanistic model, population-ground ablation, pooled-SUB-conversion ablation and return-rate sensitivities 0.5/2. Primary return multiplier 1. No selection among variants. No predictive fitting, calibration fitting, parameter grid or outer-outcome adjustment. All constants fixed before prediction/scoring. Population rates estimated from permitted training history only; fixed prior strengths are transparent modeling choices, not estimated optimal hyperparameters. Historical results are developmental, not sealed confirmation.

## Success gates (all required for A)
1. Identity conditional LL minus Arm C <= -0.005 and paired event-bootstrap 95% upper bound <0.
2. Conditional Brier difference <=0.002.
3. Conditional LL improves in >=6 of 9 years.
4. At least one of unchanged B3/B5: LL improvement >=0.005, paired event-bootstrap upper bound <0, Brier worsening <=0.002.
5. Each supported A1/A2/A4 conditional LL worsening <=0.010, Brier <=0.005. N<25 unsupported, not passed.
6. Composed multiclass LL/Brier worsening <=0.005 each; each aggregate class mean absolute calibration gap <=0.03; each one-vs-rest calibration slope 0.75–1.25 where N>=100 and >=25 positives/negatives. Diagnostic fits never change predictions.
7. Identity beats population-ground ablation in LL by >=0.005 and paired event-bootstrap upper bound <0.

Classification: E if engineering fails (no valid scientific conclusion). A if every gate passes. C if identity shows no positive individual-loss contribution versus population-ground ablation (delta LL >=0 or delta Brier >=0). Otherwise B, explicitly limited to this assumption-driven structure and measurements; a failure versus Arm C is not proof that mechanistic simulation cannot work. D requires independently identifying positional inadequacy and cannot be established from this comparison alone. No unconditional causal classification of missing position data.

Report conditional LL/Brier; multiclass LL and summed Brier; mean class probabilities; fixed ten equal-width reliability bins; diagnostic calibration intercept/slope; all nine annual results; unchanged B3/B5/A1/A2/A4. Paired event and fight bootstrap 2000 draws, seed 161163, identity minus comparator, no multiple-testing claim. Sparse subgroup outputs N<25 counts only; calibration requires >=25 each class. Preserve all predictions/support records. No prospective outcomes, sportsbook data, F01/F02 mutation or unrestricted feature search.
