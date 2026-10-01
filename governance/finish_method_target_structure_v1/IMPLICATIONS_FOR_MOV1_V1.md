# IMPLICATIONS FOR MOV1 V1

Descriptive reference only. MOV1 is not implemented or authorized by these findings.

## STRUCTURE SUPPORTED

- **A distinct conditional method target is justified to test:** `P(KO_TKO | STANDARD_FINISH)` on the existing KO_TKO/SUBMISSION population, preserving MOV0 decision-draw/exclusion governance. UFC-wide conditional KO is 64.2%; Heavyweight 78.1%, Light Heavyweight 73.3%, men's Flyweight 50.7%, Women's Strawweight 40.5%. These contrasts survive three-round restriction and broadly recur across fixed eras, with era-level conditional uncertainty especially in smaller divisions.
- **Categorical division context warrants preregistration.** Weight-class-specific intercepts or a deliberately constrained pooled/hierarchical intercept specification are reasonable candidate experiments. This audit supports testing group structure, not selecting one model family, prior, grouping, strength of shrinkage or ordinal weight effect. Retain Catch Weight separately; normalize labels through the existing map without changing immutable terrain.
- **Separate striking and grappling pathway hypotheses warrant preregistration.** A1/A4 have KO-oriented aggregate structure; B1/B2/B3/B5 show submission enrichment. B3 and B5 composition-standardized submission differences remain positive across eras. Use existing governed continuous inputs or explicitly frozen state definitions; do not automatically turn audit membership into new model features.
- **Scheduled rounds should remain separately governed context.** Heavyweight structure survives three-round restriction; C3's generic finish uplift mostly disappears against a five-round reference. This supports separating division from duration rather than letting either stand in for the other.
- **Coherent composition remains essential:** P(DECISION)=1−P(FINISH); P(KO)=P(FINISH)×P(KO|FINISH); P(SUB)=P(FINISH)×[1−P(KO|FINISH)]. The composed probabilities must themselves be evaluated chronologically and calibrated; individual node performance does not establish their joint quality.

## STRUCTURE NOT ESTABLISHED

- Separate models or unconstrained slopes for every division; interactions inferred from mostly thin class × archetype cells.
- A2 two-sided damage or C1 damage-plus-grappling as permanent interactions: temporal/cross-division samples are too sparse.
- Uniform independent A4 KO uplift after composition adjustment: the earliest era is slightly negative for adjusted absolute KO contrast.
- A3 accuracy/absorption or C3 five-round finish history as independent method/finish predictors; strong state information cannot be assumed from plausible wording alone.
- A fixed submission majority for any division in every era; Women's Strawweight reverses its majority in 2021–2023, and smaller division conditional samples are weak.
- Permanent numerical priors equal to the rates in this report, hard-coded outcome thresholds, nonlinear forms, causal access effects, winner-specific method probabilities, or guaranteed generalization.

## OPEN QUESTIONS

1. Does a minimal conditional KO-vs-SUB model improve chronological probability quality beyond training-only division/duration prevalence? Which frozen context baseline is appropriate?
2. Does constrained partial pooling improve generalization relative to ordinary regularized categorical intercepts? Compare these explicitly rather than assuming hierarchy is superior.
3. Do continuous governed KD, KO-history, submission-pressure and access terms retain method signal after context and training-only preprocessing? The descriptive archetypes overlap and correlate.
4. Are small bounded interactions necessary, or do additive terms capture the available signal? Any experiment must freeze its interaction list before performance inspection.
5. Does conditional-on-finish selection change predictor relationships or calibration, and how do errors propagate into three-way composed probabilities?
6. What remains after training-only handling of unknown states and era drift? Audit-wide thresholds are descriptive historical references, not permission to fit preprocessing on future folds.

Any future model must be a separate authorized task, frozen before training, evaluated chronologically, market-blind, and checked against permanent terrain plus composed probability quality. This audit is outcome-visible architecture research, not a new untouched validation set. No model is built here.
