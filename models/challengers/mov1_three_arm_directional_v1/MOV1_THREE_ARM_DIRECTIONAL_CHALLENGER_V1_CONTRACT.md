# MOV1 three-arm directional finish-method challenger V1

Stage 1 preregistration only. Starting main `344984d1ffea725c6765802c0a51fe97a3a8a4ba`, exactly the supplied merged PR123 identity; no intervening commits. Branch `feat/mov1-three-arm-directional-contract-v1`. Supersedes the unimplemented single-arm proposal; does not continue its branch. Review and merge this contract before separately authorizing Stage 2. No training, new historical probabilities, future outcome inspection, automatic merge or model promotion.

## Scientific identification and immutable sources

Primary question: does compact directional representation C improve conditional finish-method probability accuracy versus frozen A? B versus A isolates appending a single submission relationship. C versus B tests the compact redesign beyond that addition; several representation changes occur together and cannot identify the effect of a particular removed feature. Smaller size and increased submission predictions are not success criteria.

Read PR113 archetypes, PR117 target-structure audit, PR118 contract, PR119 frozen linear run, PR120 boosted contract, PR121 results, PR122 three-family audit, PR123 representation audit. Exact PR heads/merges and research descriptions are retained in `RESEARCH_SOURCE_IDENTITIES.json`. Roadmap snapshots and provenance are in `research_context/`; this preregistration does not implement a simulator, winner-conditioned model, hazards or round transitions. Predict the fight before any downstream market comparison.

`SOURCE_MANIFEST.json` pins every consumed frozen source and artifact. PR123 evidence manifest SHA256 `e04409314831753ab00a218bc07f04273c73f19d28507581099f4e1adc5f6488`; corrected physical F02 SHA256 `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`, Actions run35182939981/artifact10481269402. Physical bytes must be verified before any Stage2 fit. Archive retrieval must retain those bytes, never regenerate a purported equivalent F02. Existing nulls and submission measurements are governed evidence, not measurement errors to fix.

## Target and population

K = P(KO_TKO | STANDARD_FINISH), KO=1, SUB=0; submission=1-K. Natural prevalence, no class weighting/resampling. Decisions do not train, select C or enter conditional loss, but are scored without looking at outcomes for composition. The exact PR117 population and PR118 folds are copied unchanged in `target_population.json` and `chronological_fold_plan.json`.

Modern 2015+ population:5658 eligible bouts,2822 finishes (1812KO/1010SUB). Outer2018–2026:4260 eligible scoring bouts,2115 conditional finishes (1361KO/754SUB). Last historical date2026-08-15. Sorted event_date/event_id/fight_id. For outer Y, finish training2015 throughY-1; inner validationY-2 andY-1, each fitted only on earlier 2015+ finishes. Exact class counts and ordered-ID digests are frozen for every scope. Do not drop any year, decision scoring row, missingness group or thin cell.

## Exact three arms

`feature_specifications.json` is the authoritative literal inventory, ordered expressions, units and rationale. No Stage2 feature decision remains open. Feature counts exclude intercept; division encoding is original training-only lexical full one-hot, no dropped category.

| Arm | Literal F02 sources | Features before one-hot | Features with outer-fold division encoding |
|---|---:|---:|---:|
| A: frozen MOV1-MIN |35|34|47|
| B: original MIN + SUB_DIRECTIONAL_SUM |35|35|48|
| C: compact directional logistic |23|15|28|

All historical outer folds have13 learned categories; report actual per-inner dimensions rather than forcing categories from future folds. The 13 governed reporting categories include Catch Weight even if absent from a particular fit. An unseen known division scores as an all-zero one-hot, as originally frozen.

A consumes `models/mov1/run_v1/oof_MOV1_MIN.csv` (SHA256 `f8841d5007d0dec1000ed3c93a1d397428b2e5668cfdeedca6d3afc7fe4f2b3a`) and existing model/selection records. `arm_a_reference.json` fixes original35 literal columns,16 pair mean/absolute-difference transforms, rounds, title, division, preprocessing, C grid and reference hashes. No retraining or normalization changes to A.

B preserves all A pair transforms and context, appends only one scaled numerical SUB_DIRECTIONAL_SUM after original scaled numerical columns and before title/one-hot. No removal or new source column. Same L2 logistic family, numerical settings and four-candidate budget as C.

C's exact ordered numerical inventory (followed by unscaled title and lexical division one-hot):

1. KD_CREATED_MEAN — mean career shrunk KD creation per15.
2. KD_ALLOWED_MEAN — mean career shrunk KD allowed per15.
3. KO_WIN_MEAN — mean career shrunk KO wins per prior fight.
4. KO_LOSS_MEAN — mean career shrunk KO losses per prior fight.
5. SUB_PRESSURE_MEAN — mean career shrunk submission attempts created per15.
6. SUB_EXPOSURE_MEAN — mean career shrunk submission attempts faced per15.
7. SUB_WIN_MEAN — mean career shrunk submission wins per prior fight.
8. TD_PRESSURE_MEAN — mean career shrunk takedown attempts created per15.
9. TD_DEFENSE_MEAN — mean career shrunk prevented fraction of opponent takedown attempts.
10. KD_DIRECTIONAL_MEAN — mean two existing career raw directional KD efficiency gaps.
11. KD_DIRECTIONAL_ABS_DIFF — absolute difference of those same gaps.
12. SUB_DIRECTIONAL_SUM — cross-fighter submission sum below.
13. TD_ACCESS_DIRECTIONAL_SUM — cross-fighter entry sum below.
14. scheduled_rounds — original rounds context.
15. ctx__title_bout — original unscaled boolean context.

The exact per-fighter suffixes for items1–9 are:

| Concept | Literal suffix, prefixed by both f1__ and f2__ |
|---|---|
|KD created|fs__knockdown_rate__created_per_15__career__shrunk|
|KD allowed|fs__knockdown_rate__allowed_per_15__career__shrunk|
|KO win|fs__finish_method_win_profile__ko_tko__career__shrunk|
|KO loss|fs__finish_method_loss_profile__ko_tko__career__shrunk|
|SUB pressure|fs__submission_attempt_rate__created_per_15__career__shrunk|
|SUB exposure|fs__submission_attempt_rate__faced_per_15__career__shrunk|
|SUB win|fs__finish_method_win_profile__submission__career__shrunk|
|TD pressure|fs__takedown_pressure__created_per_15__career__shrunk|
|TD defense|fs__takedown_conversion__defense__career__shrunk|

Directional KD inputs are `mx__knockdown_creation_vs_vulnerability__f1_vs_f2__career__raw` and `mx__knockdown_creation_vs_vulnerability__f2_vs_f1__career__raw`. Shared context uses `scheduled_rounds`, `ctx__title_bout`, `ctx__weight_class`.

## Formulas, directions and redundancy

For submission P1/P2=created per15 and V1/V2=faced per15:

`SUB_DIRECTIONAL_SUM = P1*V2 + P2*V1`.

Units:(attempts/15minutes)^2. Positive product represents opportunity alignment, not an established submission-conversion hazard. No SUM/MAX/MIN search. Same exact imputed inputs/formula in B/C. Simultaneous fighter swap preserves the sum; swapping just vulnerability alignment can change it despite identical original marginal mean/abs features. PR123 exact collision (.82 versus.18) remains a required test.

For takedown T1/T2=created attempts per15, D1/D2=prevented proportion in[0,1]:

`TD_ACCESS_DIRECTIONAL_SUM = T1*(1-D2) + T2*(1-D1)`.

No division by100: source defense is a fraction. Weakness is1-defense, derived after original source-level imputation. Units:attempts/15minutes. Does not estimate a causal takedown success rate or phase transition.

Existing KD source definitions are **signed efficiency differences**, not a product: `G12 = shrunk KD_per_landed_sig_strike1 - shrunk KD_per_absorbed_sig_strike2`, and G21 reverses fighters. C uses `(G12+G21)/2` and `abs(G12-G21)` exactly once. Positive gap means offensive efficiency exceeds opponent's historical absorbed-strike KD ratio; do not describe it as multiplying two risks. The source definition and observed complete-row semantic equality are verified outcome-free. Retain per15 KD intensities because their denominator differs. Do not add new KD products or duplicate directional sum (twice existing mean).

`redundancy_analysis.json` freezes all decisions. One marginal mean per core concept keeps intensity interpretable; no marginal abs/min/max expansion. Submission and TD means provide marginal activity alongside alignment. No separate mean TD weakness (affine complement of defense), duplicate cross means, KD efficiency marginal means, early-finish/last5/experience predictors, TD success/faced, SUB loss or whole original MIN inheritance. None was selected from outer loss comparisons. Synthetic varied inputs verify14 scaled numeric C columns have full centered rank; one-hot/intercept dependence is acknowledged and preserved under L2. Historical correlations cannot authorize removal.

## Missingness, point-in-time safety and preprocessing

Raw values retained; completeness measured before imputation. Submission completeness means all four raw P/V values observed; compact completeness means all20 career raw values observed. Context completeness separately reported. No null-to-zero assumption, complete-case default or new indicator predictor.

One pooled finite **training-history** median for both sides of each governed source pair, shared exactly across B/C; never separate-side medians. If all training values absent, fail closed. Reused KD directional pair is imputed directly using its original pair median, not reconstructed from newly imputed efficiency constituents. After imputation construct means/abs/cross sums, then fit population-variance scaling on training numerical columns (zero variance scale1). Title mode and normalized division mode use training only with original tie breaks; title/one-hot unscaled. Categories learned only from permitted training. Source shrinkage/PIT history remains unchanged. Future/outer values never affect medians, scaling, categories, C or feature definitions.

`missingness_preprocessing.json` gives exact policies; `SOURCE_MANIFEST.json` pins F01/F02 code, data governance and original temporal evidence. Independent submission/takedown source-lineage replay verifies strict-prior dates, exclusion of target/same-date data and real zero-history nulls. No new F02 materialization or changed feature-engine semantics.

## Logistic settings, budget and chronology

B/C: LogisticRegression, L2, lbfgs, intercept=True, tol1e-4, max_iter3000, random_state17, class_weight=None. Pinned Python3.12/numpy1.26.4/pandas2.2.3/pyarrow17/scipy1.14.1/sklearn1.5.2; threadpool limit1. C grid ordered[0.03,0.1,0.3,1.0]. Each arm separately selects minimum concatenated inner finish-row log loss; differences<=1e-12 tie, first grid candidate. Fresh outer preprocessing/refit on all permitted finish history. No outer-label model selection. Numerical nonconvergence/nonfinite results invalidate run; no automatic grid/solver changes.

Stage2 budget:144 inner fits +18 outer fits +2 preregistered2021 same-C reproduction fits =164; zero A fits. Save all inner and outer fitted parameters, selection evidence and predictions. Actual fit-count/identity mismatch blocks completion. Stage1 uses numerical preprocessing probes only, with predictive estimator entrypoints disabled.

## Metrics, uncertainty and interpretation

`conditional_metrics.json`, `uncertainty_persistence.json`, `interpretation_rules.json` fix complete formulas and gates. C-A is primary; B-A and C-B separate secondary questions. Conditional mean binary log loss is primary; Brier supports probability accuracy. Fixed10-bin ECE, unpenalized diagnostic calibration intercept/slope (N>=100 and both classes/variation; explicit failure statuses; never applied), AUC secondary, actual rates, mean probabilities and fixed reliability bins retained.

Paired losses: candidate-reference, negative favorable.10,000 resamples, seed17/default_rng, sorted fight rows; fight resampling and event-cluster resampling with replacement, all paired event rows and fight-weighted mean. No refitting. Same paired draws across arms/metrics. Quantiles linear. Primary C-A two-sided95% intervals; B-A/C-B97.5% each (Bonferroni for two secondary comparisons). Subgroup95% is descriptive, acknowledging overlapping/previously inspected panels, not a confirmatory search battery.

Supported conditional improvement requires LL delta<0 and both fight/event upper bounds<0; pooled Brier<=0 and both upper bounds<=0.002; LL improves>=6/9 years, median annual delta<0, and pooled LL remains favorable after excluding **each** single year. Clearly worse supported LL or Brier beyond frozen tolerance means current specification not supported. Everything else valid but mixed/inadequate is inconclusive. Identity/numerical failure means INVALID_INCOMPLETE, not a scientific negative. Report all annual deltas, best/worst-year contribution and leave-one-year-out results. Calibration/AUC cannot substitute for these gates.

B3/B5 separately report actual KO/SUB, mean K/1-K, per-fight losses, quantiles/histograms, calibration gap, annual behavior and complete/incomplete raw sources. Correction requires better individual LL/Brier and smaller absolute group calibration gap, not simply more submission. Supported-cell description additionally requires N>=100 and both95% LL intervals favorable; never call this independent architecture confirmation. A1/A2/A4 and HW/LHW preservation gates use both95% LL upper<=0.01 and Brier upper<=0.005; uncertain preservation explicitly reported. Aggregate improvement can coexist with a pathway tradeoff.

## Archetype, terrain and complete-system reporting

Preserve all15 PR113/PR117 MATCH/NO_MATCH/UNASSIGNABLE memberships, thresholds and unknown handling. No reclassification or threshold correction; PR117 historical discrepancy notes retained. All divisions including separately men's/women's Flyweight and Catch Weight, original Validation Terrain V1 dimensions, rounds3/5, experience0/1-2/3-7/8+, completeness, every outer year and division-by-archetype status. No archetype/terrain identifier as predictor. Separate all-bout and conditional finish denominators. Gates:N<25 counts only,25–49 exploratory,50–99 moderate uncertainty,100+ normal; calibration separately N>=100. Retain empty/unknown cells; undefined AUC/calibration null with reason. These panels explain performance and do not select models.

Every arm composes with unchanged frozen MOV0-MIN F: KO=F*K, SUB=F*(1-K), DEC=1-F. All4260 identities matched before outcome joining, finite probabilities[0,1], sum1 within1e-12, decision probabilities identical. Multiclass log loss, **summed** three-class Brier, KO/SUB/DEC calibration/ECE and annual results. Composed support uses same comparison intervals/annual gates and Brier upper tolerance0.004. Compute decision-node identity and conditional/composed LL-difference relation, record any log clipping exceptions. Conditional improvement never automatically assigns system improvement.

## Independent forward confirmation

Historical outcomes have been repeatedly inspected; this experiment provides developmental evidence. `forward_confirmation_protocol.json` freezes the independent test before any new labels.

Exclude Aug16–Oct2 from confirmation and do not inspect them in Stage1/initial historical Stage2. Enrollment starts next UTC day after latest of Oct2, contract merge, and all three model freezes; only prospectively scored events. Fixed outer2026 A/B/C models, all trained on2015–2025 and inner2024/2025; no refits, calibration or later C choices. Governed future feature histories may append strictly prior canonical observations under identical semantics, with every input/model/prediction hashed pre-event. Cutoff event-date00:00UTC or earlier; same-date information excluded. Frozen MOV0 outer2026 record required/reproduced before composed enrollment; its retrieved original artifact has preprocessing but lacks fitted coefficients. This is a known BLOCKED_MISSING_FROZEN_MOV0_RECORD prerequisite for forward composition and needs separately authorized frozen-record recovery; no MOV0 fitting in Stage1 or historical Stage2, no substitution. The conditional forward cohort remains defined independently.

All announced bouts scored without outcomes; same canonical eligibility once labels unsealed. One final analysis after first full event reaching500 finishes and75 per class, or24months, whichever comes first;30-event minimum. If gates unmet at deadline, insufficient; no performance-based extension. Four fixed6month persistence bins:>=3 qualified bins(N>=100) must improve LL and every leave-one-qualified-bin-out pooled delta favorable; otherwise confirmation inconclusive. Primary/secondary metrics and uncertainty criteria unchanged. No interim comparative performance peeks. Unsupported sources/scoring failure pause cohort completion; no cherry-picking missing fights. No automatic production promotion.

## Validation, artifacts and Stage2 boundary

Required engineering checks and output records are in `required_engineering_checks.json`. `tools/contracts/validate_mov1_three_arm_contract_v1.py` SHA-verifies frozen inputs, reuses original no-training population/fold validator, checks every27 inner/outer history's train-only shared source imputation/scaling, exact B MIN prefix, labels blindness, swap including asymmetric nulls, KD semantic equality, feature counts, completeness, source immutability and illustrative probability algebra. It disables logistic predictive fit/prediction entrypoints. Tests preserve PR123 exact collision and exercise formulas, dimensional rank, imputation order, score isolation, missingness, swap and composition. Runtime fitting/convergence/persisted-probability checks are frozen requirements for Stage2 and are not claimed to have been executed in Stage1.

`VALIDATION_EVIDENCE.json` records outcome-free verification; dedicated read-only CI downloads/hashes physical F02 and reproduces this evidence byte-for-byte, then independently replays submission/takedown lineage. `CONTRACT_MANIFEST.json` hashes all Stage1 specifications, research provenance, validation code/tests/workflow/evidence and completion marker; its own digest is reported externally to avoid self-reference. No old model/data/governance artifact may change. No production or simulator code, extra model families, calibration wrappers, sportsbook inputs, ROI/EV, outcome-based subsets or automatic merge. Stop after reporting the frozen contract PR.
