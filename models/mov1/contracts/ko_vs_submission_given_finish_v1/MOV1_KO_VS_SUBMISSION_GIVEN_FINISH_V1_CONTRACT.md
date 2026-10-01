# MOV1_KO_VS_SUBMISSION_GIVEN_FINISH_V1 implementation contract

Status: FROZEN_CONTRACT_ONLY. Starting main: `4d641e259d4420fd77290603cabcce33c90bf6c8` (merged #117). This freezes the first conditional experiment; no estimator is trained, no MOV1 performance is evaluated and no simulator is built. Machine-readable specifications in this directory are normative; this document explains them. On conflict, stop and version the contract rather than deciding during the run.

## Scientific target and population

`P(KO_TKO | STANDARD_FINISH)`, KO=1, submission=0, submission probability=1−K. The exact modern canonical UFC population is 5,658 bouts: 1,812 KO/TKO, 1,010 submissions and 2,836 decisions (including 45 decision draws). Conditional training eligibility comprises 2,822 finishes. DQ, NC, OTHER, UNKNOWN, null/ambiguous methods remain excluded according to frozen MOV0 governance; `target_population.json` pins the audit manifest and exclusion reference.

Training, selection and preprocessing use only 2015+ prior-year finishes. Scoring uses every eligible pre-fight state, including eventual decisions; the score function must not require method/outcome. Across outer2018–2026 there are 4,260 scoring bouts and 2,115 conditional evaluation bouts. First generate an exact-ID complete score table; only then join labels for metrics. Neither decisions nor their labels affect fitted medians, modes, encoders, scaling, coefficients or conditional prevalence.

## Frozen ladder and exact feature surfaces

C0: outer-training KO proportion among finishes, identical for all outer-year score rows. C1: rounds, title, canonical categorical division and paired prior canonical experience. MOV1-MIN: C1 plus the existing career method histories, early-finish timing, KD rate and directional matchup, submission attempts, TD pressure and **TD success/defense**. MOV1-FULL: MIN plus KD efficiency, significant-strike flow/accuracy/defense, clinch/ground shares and head/body shares.

The literal allowlists have C1=5, MIN=35, FULL=55 raw columns; transformations produce respectively4,34,54 noncategorical model columns, plus training-learned division one-hot columns. FULL KD efficiency pair means have a declared linear relation with MIN’s directional gap mean; marginal intensity and side contrasts add information that the gap alone cannot recover. The redundant subspace remains explicitly governed under L2, with no post-hoc removal. See `c1_allowlist.json`, `mov1_min_allowlist.json`, `mov1_full_allowlist.json` and the 55-row `feature_rationale.csv` for every literal column, mechanism, orientation, missingness and nonredundancy justification. MIN promotes already-governed TD conversion/defense from the broader MOV0 surface to fulfill the specified grappling-access pathway. This is target-specific preregistration, not performance selection.

Historical outcomes in F02 are strict-prior information. No current-target metadata, audit rate, terrain bucket or archetype flag enters predictors. Only career variants are used. No ordinal weight encoding, new interactions, division-specific slopes, hierarchy, trees, resampling, availability flags or optimized thresholds. Early-finish history remains a generic first-round non-decision timing proxy with exact F02 semantics; it is not redefined as first-round KO history. Ground significant-strike share is not ground-KO location.

## Symmetry and preprocessing

For every listed semantic/directional pair, fit a single pooled finite-value median on the current finish-only training history, impute both sides, then calculate pair mean and absolute difference. Scale numeric pair transforms and rounds using training-only StandardScaler. Title uses training mode/boolean0/1. Normalize raw division with the pinned existing literal_map, training-mode impute and one-hot encode training categories; known but training-unseen divisions get the documented all-zero vector. Retain immutable terrain rawlabels for diagnostic compatibility. Unknown raw labels or all-missing training components fail closed. Null is not zero; no new missingness indicator is authorized.

All inner preprocessing is freshly fit within each inner history, and outer refit preprocessing within outer training. No globally fitted preprocessing or future availability. Existing F02 shrinkage is consumed unchanged. The 2015+ gate applies to model fitting/preprocessing rows; frozen F02 career states retain their governed strict-prior history, which can include earlier bouts. No pre-2015 row enters MOV1 fitting, and no career state is recomputed or truncated in this task. Swapping all paired and directional columns must produce identical probability within atol1e−12, rtol0 for all fitted surfaces and scoring rows. Contract-only validation verifies swap closure/specification; the actual fitted-probability test belongs to the later run.

## Chronology and selection

| Year | Finish train | KO / SUB train | Finish validation | KO / SUB validation | All scoring |
|---|---:|---:|---:|---:|---:|
| 2018 | 707 | 451 / 256 | 241 | 151 / 90 | 470 |
| 2019 | 948 | 602 / 346 | 231 | 152 / 79 | 507 |
| 2020 | 1179 | 754 / 425 | 220 | 138 / 82 | 443 |
| 2021 | 1399 | 892 / 507 | 239 | 166 / 73 | 492 |
| 2022 | 1638 | 1058 / 580 | 268 | 171 / 97 | 505 |
| 2023 | 1906 | 1229 / 677 | 258 | 158 / 100 | 505 |
| 2024 | 2164 | 1387 / 777 | 223 | 141 / 82 | 502 |
| 2025 | 2387 | 1528 / 859 | 252 | 163 / 89 | 504 |
| 2026 | 2639 | 1691 / 948 | 183 | 121 / 62 | 332 |

`chronological_fold_plan.json` freezes both class counts, exact ordered-ID digests and the two preceding inner-year train/validation counts per fold; `expected_fold_counts.csv` is its readable outer summary. 2026 is a partial fixed snapshot. No incoming data silently changes these counts. No pre2015 rows or random CV. Select C independently for C1/MIN/FULL using concatenated conditional inner-row log loss; no outer outcomes enter selection. Tie within1e−12 resolves to first grid candidate.

Regularized logistic regression: L2, lbfgs, intercept true, max_iter3000, tol1e−4, no class weights, seed17, C=[0.03,0.1,0.3,1.0]. Exact dependency versions are frozen in `model_regularization.json`. Nonconvergence or invalid probabilities halts the run; no silent solver/grid repair.

## Conditional and complete-system evaluation

Conditional primary metric is binary log loss on outer finishes only. Report Brier, intercept/slope, 10-bin ECE/reliability, ROC AUC, observed KO prevalence and mean prediction overall/byyear. Compare C1−C0, MIN−C1, FULL−MIN. Fixed conditional buckets are <.30, .30–<.40, .40–<.50, .50–<.60, .60–<.70, .70–<.80, ≥.80; never tune them. Report all bins with N, calibration/Wilson, years and division/archetype composition. For all-score buckets report distribution, without converting decisions into negative conditional labels.

Use **frozen MOV0-MIN** F as the primary node. DEC=1−F; KO=F×K; SUB=F×(1−K). Require finite bounds and sum1 within1e−12, no renormalization. Frozen MOV0-FULL sensitivity is explicitly deferred. S0 combines F+C0; S1 F+C1; S2 F+MIN; S3 F+FULL. Evaluate on **all4,260 outer bouts**, primary multiclass log loss, plus summed3-class Brier, classwise calibration/reliability and mean assigned probabilities by actual outcome, overall and annually. Compare S1−S0, S2−S1, S3−S2. With shared F, unclipped composed log-loss deltas on decisions are zero; conditional loss and complete loss are mathematically related, while Brier/calibration add distinct assessment.

For every major conditional/composed comparison report aggregate and annual deltas, favorable/unfavorable/tied years and both 2,000-replicate seed17 paired fight/event bootstrap95 intervals. State dependence limitations and single-year dominance. `interpretation_rules.json` freezes qualitative CLEAR_SUCCESS / INCONCLUSIVE / CURRENT_SPECIFICATION_NOT_SUPPORTED classifications; no posthoc numeric success gate or automatic model promotion. Classifications require the declared annual, uncertainty, calibration and composed evidence and must report contrary findings.

## Terrain, archetypes and interpretation

Join immutable Validation Terrain V1 without rebuilding. Report all canonical divisions (Catch Weight separately), rounds/title, experience/layoff/completeness, strike/grapple/joint environments and all15 exact #113 archetypes using pinned PR117 membership/unknown handling. The known-state formulas/thresholds are unchanged; disclose historical unknown-negation flag differences instead of treating unknown as absence. Freeze weight×archetype status and round/era summaries only, not an unbounded interaction search. Use separate all-bout and finish-only sample gates: NORMAL≥100, MODERATE50–99, THIN25–49, INSUFFICIENT<25. Retain small-cell counts; suppress substantive performance interpretations.

Especially examine HW/LHW KO-heavy composition, balanced Flyweight and women’s Strawweight/Flyweight submission enrichment, KO damage archetypes, and TD-access/submission-pressure archetypes. Report F and K both on all bouts and finish subset, composed KO/SUB/DEC means and actual matching outcome rates. PR117 2015+ reference rates are context, not claimed OOF truth. No subgroup findings can alter the first-run surface.

`IMPLICATIONS_FOR_HYBRID_SIMULATOR.md` freezes an eventual interpretation plan only. The decomposition can support a probability architecture if validated; coefficients/descriptive rates are never causal hazards or round transitions. No simulator code, sportsbook prices, ROI/EV, MOV0 changes or auto merge.

## Validation and immutable handoff

The contract validator checks pinned foundation/contract hashes, all literal corrected F02 columns, PIT-governed families, complete score coverage, finite training support, exact fold counts/ID digests, train-label exclusion, categorical mapping and symmetric closure. It does not train/predict a model. `future_run_artifact_specification.json` fixes eventual output schemas, provenance, mandatory runtime checks and undefined-metric handling. Runtime score invariance, convergence and measured calibration remain mandatory future-run checks. The manifest hashes every contract artifact except itself and pins source files. V1 may be read by future tasks but must not silently change; a scientifically material amendment requires a separately named preregistration before training.
