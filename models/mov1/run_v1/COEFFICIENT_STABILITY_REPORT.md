# Conditional logistic coefficient interpretation

Coefficients are secondary association diagnostics, not causal importance or feature-selection evidence. Numeric transforms are standardized within each finish-training fold; title and one-hot terms remain unscaled. All coefficients, intercepts, signs and per-fold feature availability are preserved. Different scaler/regularization values and correlated predictors limit magnitude comparison across years.

| MIN standardized component | Positive / negative years | Mean coefficient | Range |
|---|---|---|---|
| directional_knockdown_matchup::mean | 0 / 9 | -0.110352 | [-0.206260, -0.042539] |
| fs__early_finish_profile__r1_finish_loss__career__shrunk::mean | 9 / 0 | 0.063046 | [0.029656, 0.129004] |
| fs__early_finish_profile__r1_finish_win__career__shrunk::mean | 0 / 9 | -0.063972 | [-0.101452, -0.032573] |
| fs__finish_method_loss_profile__ko_tko__career__shrunk::mean | 6 / 3 | 0.022473 | [-0.036835, 0.102029] |
| fs__finish_method_loss_profile__submission__career__shrunk::mean | 5 / 4 | 0.041657 | [-0.054075, 0.204857] |
| fs__finish_method_win_profile__ko_tko__career__shrunk::mean | 9 / 0 | 0.176804 | [0.104990, 0.260688] |
| fs__finish_method_win_profile__submission__career__shrunk::mean | 0 / 9 | -0.117853 | [-0.190862, -0.041266] |
| fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 9 / 0 | 0.129431 | [0.079451, 0.251111] |
| fs__knockdown_rate__created_per_15__career__shrunk::mean | 9 / 0 | 0.181042 | [0.131749, 0.211231] |
| fs__prior_fight_count__career__raw::mean | 7 / 2 | 0.087540 | [-0.027479, 0.162578] |
| fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 0 / 9 | -0.142808 | [-0.203126, -0.088918] |
| fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 0 / 9 | -0.173541 | [-0.219318, -0.129106] |
| fs__takedown_conversion__defense__career__shrunk::mean | 9 / 0 | 0.161424 | [0.129885, 0.197872] |
| fs__takedown_conversion__success__career__shrunk::mean | 0 / 9 | -0.108775 | [-0.130363, -0.081192] |
| fs__takedown_pressure__created_per_15__career__shrunk::mean | 0 / 9 | -0.068319 | [-0.093844, -0.028638] |
| fs__takedown_pressure__faced_per_15__career__shrunk::mean | 2 / 7 | -0.012278 | [-0.042595, 0.033092] |

MIN pair-mean KO wins, KD creation and KD allowed are positive in9/9 years. Submission wins, submission attempts created/faced, TD pressure created and TD conversion success are negative in9/9. TD defense is positive9/9, consistent with less submission access. Method-loss histories are less stable: KO loss mean positive6/9 and submission loss mean positive5/9 rather than consistently submission-oriented; do not retrofit the features to expected signs.

Context-only division terms consistently align with the audit: HW/LHW positive9/9; Flyweight and women’s Strawweight/Flyweight negative9/9. With fighter state included, residual HW is positive only2/9, LHW8/9 and Flyweight3/9; their predictions still preserve the broad method structure. Residual coefficients do not equal total division effects. Women’s Strawweight/Flyweight remain negative9/9 in MIN, yet their composition/calibration is imperfect.

FULL retains the declared linear dependency between directional KD gap mean and marginal efficiency means. L2 regularization handles the fitted redundant subspace; coefficient attribution is particularly limited. No predictor was removed, added or reinterpreted after this review.
