# MOV0 CONFIDENCE TERRAIN + FEATURE-BEHAVIOR DIAGNOSTIC V1

Status: **MOV0_CONFIDENCE_TERRAIN_FEATURE_BEHAVIOR_DIAGNOSTIC_V1_COMPLETE**

Coefficient recovery status: **COEFFICIENT_RECOVERY_VALIDATED**

This is a post-freeze explanatory diagnostic. The authoritative MOV0 V1 OOF predictions remain unchanged and authoritative. No MOV0 feature surface, fold, preprocessing rule, selected C, solver setting, threshold, or calibration procedure was changed.

## 1. Authoritative sources

- Frozen MOV0 run source HEAD: `dd4e7de7de4baa24090388fcf845c996564f2bf8`
- Frozen MOV0 workflow run: `35376956316`
- Frozen MOV0 artifact: `mov0-standard-finish-probability-v1`
- Frozen MOV0 artifact ID: `10561085362`
- MOV0-MIN OOF SHA256: `786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57`
- MOV0-FULL OOF SHA256: `9d543356b157fefaabe27f7f4d1b5663536e4cf659fdf11fedd8531c4b13faa0`
- Corrected F02 table SHA256: `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`
- Immutable Validation Terrain V1 compressed SHA256: `d3358cfc468a791861ee6fb87473f119f949d705c54abfcb504d9ebbecdcb5d2`
- Diagnostic workflow run: `35469722253`
- Diagnostic artifact ID: `10592955918`
- Diagnostic artifact digest: `sha256:ee425b7456c91a0fa713fb9d072afc33a28966fe9fec8c02be590877874a1f85`

Frozen probability bins from PR #111:

- `<0.30`
- `0.30–<0.40`
- `0.40–<0.50`
- `0.50–<0.60`
- `0.60–<0.70`
- `>=0.70`

## 2. Coefficient-recovery validation

MASTER/PM authorized `COEFFICIENT_RECOVERY_REFIT_ONLY` because the original frozen artifact did not preserve fitted coefficient tables.

The refit used exactly the frozen corrected F02 input, 2015+ chronology, outer folds, feature surfaces, preprocessing, selected C values, and solver/settings. It did not re-select hyperparameters.

For B1, MOV0-MIN, and MOV0-FULL across all outer years 2018–2026:

- fight identity/count matched the frozen OOF;
- all 27 surface/year validation sets reproduced the frozen probabilities within `atol <= 1e-12`;
- maximum absolute recovered-vs-frozen probability difference over all fits was `2.5368596112684827e-13`.

Therefore coefficient interpretation is permitted under the amendment. The recovered predictions do not replace the frozen OOF predictions.

## 3. Confidence-bucket terrain composition

High finish confidence is not evenly distributed across fight environments.

For MOV0-FULL, the share of each terrain environment placed in `>=0.70` includes:

- 5-round fights: **26.5%**
- 3-round fights: **5.3%**
- STRIKE_TWO_SIDED: **23.8%**
- STRIKE_ONE_SIDED: **12.4%**
- STRIKE_LOW: **6.0%**
- GRAPPLE_TWO_SIDED: **13.1%**
- GRAPPLE_ONE_SIDED: **12.6%**
- GRAPPLE_LOW: **7.0%**
- Light Heavyweight: **25.7%**
- Heavyweight: **17.4%**
- Flyweight: **3.6%**

About 70% of HIGH_MISSINGNESS fights fall in the combined `0.40–0.60` middle range for both MIN and FULL. The model therefore tends to express less extreme confidence where historical fighter-state information is incomplete.

These composition findings are descriptive only; terrain prevalence is not itself evidence of prediction quality.

## 4. Bucket × terrain calibration

The globally monotonic bucket ordering established by PR #111 remains valid, but conditioning on specific terrain environments reveals local reversals and calibration weaknesses.

Examples:

- Middleweight MOV0-MIN:
  - `0.50–0.60`: observed finish rate **67.3%**, N=156
  - `0.60–0.70`: observed finish rate **56.3%**, N=126
- Middleweight MOV0-FULL:
  - `0.50–0.60`: **63.8%**, N=138
  - `0.60–0.70`: **59.9%**, N=147

The experience `6–10` terrain family shows a similar middle/upper reversal.

At the highest confidence range, 3-round fights remain overconfident:

- MIN `>=0.70`: mean prediction **74.3%**, observed **64.5%**, N=121
- FULL `>=0.70`: mean prediction **74.6%**, observed **66.3%**, N=202

FULL `>=0.70` STRIKE_LOW is also overconfident:

- mean prediction **75.6%**
- observed finish rate **65.7%**
- N=140

Conclusion: MOV0 confidence retains useful ordering information inside many environments, but one global probability calibration is not equally reliable across all terrain.

## 5. MIN → FULL migration

At the top end:

- **194** fights were `>=0.70` under both MIN and FULL; **69.6%** finished.
- **120** fights were promoted by FULL from below `0.70` into `>=0.70`; **66.7%** finished.
- **18** fights were demoted by FULL from MIN `>=0.70`; this group is too small for substantive interpretation.

The promoted group moved from an average MIN probability of approximately **66.3%** to an average FULL probability of approximately **72.3%**.

FULL therefore expands the high-confidence population, but the promoted fights did not realize a higher finish rate than fights MIN already considered high confidence.

## 6. High-confidence feature behavior

The FULL-only feature profile of fights promoted into `>=0.70` is especially characterized by:

- poorer average significant-strike defense;
- higher significant strikes absorbed per minute;
- higher striking accuracy;
- more symmetric efficiency/conversion profiles.

These directions agree with recovered FULL coefficient signs that raise finish probability.

This explains how FULL becomes more confident, but it does not establish that the added confidence is better calibrated or more useful than MIN.

## 7. Weight-class investigation

### Heavyweight

- N: **311**
- observed finish prevalence: **58.5%**
- MIN log loss: **0.6568**
- MIN AUC: **0.623**
- FULL log loss: **0.6626**
- FULL AUC: **0.609**
- FULL raises probability versus MIN in **225/311** fights.
- Mean FULL-minus-MIN shift: about **+2.0 percentage points**.

The additional FULL surface systematically pushes Heavyweight fights upward while worsening aggregate probability performance versus MIN. This is consistent with a possible environment-dependent feature-effect problem.

### Light Heavyweight

- N: **319**
- observed finish prevalence: **64.3%**
- MIN log loss: **0.6601**
- MIN AUC: **0.545**
- FULL log loss: **0.6575**
- FULL AUC: **0.553**

The previously frozen B1 terrain result was better on log loss than either MOV0 surface. Light Heavyweight appears to contain a strong structural high-finish baseline while fighter-level ranking within the division remains weak.

Weight class is one-hot categorical in MOV0; no ordinal weight-class explanation applies.

### Flyweight

- N: **248**
- observed finish prevalence: **47.2%**
- MIN log loss: **0.6961**
- MIN AUC: **0.549**
- FULL log loss: **0.6966**
- FULL AUC: **0.560**

Only 5 MIN fights and 9 FULL fights reach `>=0.70`, so high-confidence division-specific conclusions are unsupported. Most Flyweight predictions remain in the middle of the probability range.

## 8. Coefficient stability

Stable finish-increasing MIN relationships across all nine outer years include:

- scheduled rounds;
- pair-mean prior first-round finish wins;
- pair-mean prior first-round finish losses;
- pair-mean KO/TKO win history;
- pair-mean submission attempts created per 15;
- pair-mean submission attempts faced per 15.

Stable decision-increasing relationships include:

- pair-mean prior fight count;
- absolute difference in the directional knockdown creation-vs-vulnerability matchup.

Representative mean recovered coefficients:

- scheduled rounds: approximately **+0.194**
- first-round finish-win pair mean: approximately **+0.174**
- submission attempts faced/15 pair mean: approximately **+0.120**
- submission attempts created/15 pair mean: approximately **+0.115**
- first-round finish-loss pair mean: approximately **+0.113**
- KO/TKO win pair mean: approximately **+0.094**
- prior fight count pair mean: approximately **-0.096**
- directional KD matchup absolute difference: approximately **-0.162**

FULL adds stable relationships including:

- higher knockdown-creation efficiency mean → higher finish probability;
- higher strikes absorbed/min mean → higher finish probability;
- higher significant-strike defense mean → lower finish probability;
- greater ground significant-strike share mean → higher finish probability;
- greater takedown-defense disparity → lower finish probability;
- greater striking-accuracy disparity → lower finish probability.

Several other FULL-only variables are sign-unstable across years and should not be treated as robust state inputs from this diagnostic alone.

All pair variables are fighter-order-invariant mean/absolute-difference transforms. No Fighter-1/Fighter-2 side effect should be inferred.

## 9. Feature profiles across confidence

For MIN:

- first-round finish-win pair mean: roughly **-1.20 SD** in `<0.30` to **+1.58 SD** in `>=0.70`;
- KO/TKO-win pair mean: roughly **-1.10 SD** to **+1.25 SD**;
- knockdowns-created pair mean: roughly **-0.87 SD** to **+1.33 SD**.

For FULL:

- knockdown-creation efficiency: roughly **-0.80 SD** to **+0.78 SD**;
- significant-strike defense: roughly **+0.35 SD** to **-0.99 SD**;
- striking accuracy: roughly **-0.02 SD** to **+0.95 SD**;
- ground significant-strike share: roughly **-0.57 SD** to **+0.49 SD**.

Thus the confidence spectrum reflects meaningful changes in historical finish pressure, vulnerability, damage exchange, and fight-environment variables—not only structural context such as weight class.

## 10. Terrain × feature behavior

Supported cross-links include:

- High-striking-pressure environments are disproportionately represented at high FULL confidence and show elevated damage/strike-flow state.
- Heavyweight FULL confidence is pushed upward by the broader feature surface even though FULL performs worse than MIN there.
- Light Heavyweight has high structural finish prevalence but weak within-division fighter-state discrimination.
- HIGH_MISSINGNESS fights cluster in middle confidence.
- Five-round fights receive far more high-finish-confidence assignments, consistent with scheduled exposure being a stable finish-increasing predictor.

These are predictive associations, not causal mechanisms.

## 11. FUTURE_SPECIALIZATION_HYPOTHESES

See `FUTURE_SPECIALIZATION_HYPOTHESES.md`.

Candidates are hypotheses only and are not authorized for implementation.

## 12. IMPLICATIONS_FOR_HIERARCHICAL_MOV_AND_FUTURE_SIMULATOR

See `IMPLICATIONS_FOR_HIERARCHICAL_MOV_AND_FUTURE_SIMULATOR.md`.

The evidence supports preserving the current hierarchical direction:

`P(STANDARD_FINISH)`
→ `P(KO_TKO | STANDARD_FINISH)`
→ composed DECISION / KO_TKO / SUBMISSION probabilities.

Stable state candidates include early finish history, knockdown production/efficiency, submission pressure, striking defense/absorption, and scheduled duration. These are candidate predictive state inputs only; MOV0 coefficients are not causal simulator transition probabilities.

## 13. Limitations

- MOV0 remains a pre-fight global logistic model, not a causal fight-process model.
- Terrain cells can become sparse after simultaneous conditioning on probability bucket and environment.
- Local monotonicity violations are descriptive and were not used to redesign buckets.
- FULL-vs-MIN differences are not evidence that FULL should replace MIN.
- Coefficients are regularized predictive parameters and can be affected by correlation among predictors.
- Weight-class observations do not prove specialized models will improve performance.
- The coefficient refit was authorized solely for recovery and validated against frozen OOF predictions.
- No betting-market information was used.

## 14. Guardrail confirmation

No feature surface changed.

No fold changed.

No preprocessing changed.

No selected C changed.

No model settings changed.

No probability threshold was optimized.

No recalibration was performed.

No sportsbook data, ROI, or EV analysis was performed.

MOV1 was not started.

No specialized model was built.

No simulator code was built.

The only model fitting performed after freeze was the explicitly authorized `COEFFICIENT_RECOVERY_REFIT_ONLY`, and it passed the frozen-OOF reproduction guard.

## Final status

`MOV0_CONFIDENCE_TERRAIN_FEATURE_BEHAVIOR_DIAGNOSTIC_V1_COMPLETE`

This diagnostic is descriptive. It does not promote or retire MIN/FULL and does not authorize a next model phase by itself.
