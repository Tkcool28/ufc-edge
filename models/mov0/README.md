# MOV0 — STANDARD_FINISH Probability V1 Implementation Contract

Status: **CONTRACT COMPLETE ON FEATURE BRANCH — NO MODEL RUN**

MOV0 answers:

> **What is P(STANDARD_FINISH) before the fight, where STANDARD_FINISH means KO/TKO or submission rather than decision?**

This directory freezes the first UFC EDGE method-of-victory experiment so implementation requires no discretionary modeling choices. It does **not** contain trained MOV0 results.

## Authority and boundary

- Base main: `df2692934565b905f3b53380ec86b01bd42408fc`
- Corrected F02 logical SHA256: `2d1a367416e105ed6fe546eb8590ae7b555dd044304ad0ba40c7945420599ba0`
- Corrected F02 table SHA256: `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`
- Validation Terrain V1 is immutable and joined by `fight_id`; it is never rebuilt from MOV0 predictions.
- No sportsbook odds, ROI, Optuna, trees, boosting, post-hoc feature selection, MOV1, or simulator work is authorized.
- Predictors are materialized and frozen before the target is attached.

## Target contract

Positive class:

- `method=KO_TKO`, `result=win_loss`
- `method=SUBMISSION`, `result=win_loss`

Negative class:

- `method=DECISION`, `result=win_loss`
- `method=DECISION`, `result=draw`

A decision draw is a valid `STANDARD_FINISH=0` row because the fight reached a decision.

Excluded without coercion:

- DQ
- DRAW
- NO_CONTEST
- OTHER
- UNKNOWN
- null method
- canonical result states `no_contest`, `other`, `unknown`
- any future explicit overturned/invalid state until separately governed

The canonical result schema currently has no `overturned` enum.

### Exact governed population

Current certified modern-era UFC label population (2015–2026):

| State | N |
|---|---:|
| KO/TKO | 1,812 |
| Submission | 1,010 |
| STANDARD_FINISH = 1 | **2,822** |
| Decision = 0 | **2,836** |
| Total | **5,658** |
| Decision draws included as 0 | 45 |

Current otherwise-in-era UFC exclusions total 71:

| State | N |
|---|---:|
| `no_contest | OTHER` | 25 |
| `win_loss | DQ` | 13 |
| `no_contest | NO_CONTEST` | 32 |
| `draw | NO_CONTEST` | 1 |

**MOV0 V1 never uses pre-2015 rows.** The 2015–2017 certified-modern rows are available only as earlier-history training and inner-validation data. The outer OOF evaluation begins in 2018 and contains exactly **4,260** fights across 2018–2026.

## Predictor/target separation

The required order is:

`materialize predictors -> freeze predictor artifact/hash -> attach STANDARD_FINISH afterward by fight_id`

The target may not participate in feature generation, preprocessing fit, missingness repair, feature selection, terrain construction, or fold construction beyond eligibility/year membership.

## Surface ladder

### B0 — empirical baseline

No predictors.

For each outer fold:

`P(STANDARD_FINISH) = finish prevalence in outer-training history only`

No global or future prevalence.

### B1 — context baseline

Exact F02 columns:

- `scheduled_rounds`
- `ctx__title_bout`
- `ctx__weight_class`
- `f1__fs__prior_fight_count__career__raw`
- `f2__fs__prior_fight_count__career__raw`

Repository semantic note: `prior_fight_count` is **strict-prior canonical fight experience** across supported canonical promotions. It is not UFC-only experience. Validation Terrain's separate strict-prior UFC-experience diagnostic remains unchanged.

### MOV0-MIN — minimal direct finish surface

B1 plus career-only:

- early-finish win/loss rate
- KO/TKO and submission win profile
- KO/TKO and submission loss profile
- knockdown creation and allowed rate
- submission-attempt creation and faced rate
- takedown pressure creation and faced rate
- both career directional knockdown-creation-vulnerability interaction columns

Decision components of the finish-method profiles are omitted to avoid directly re-expressing the finish-vs-decision composition.

### MOV0-FULL — full justified finish surface

MOV0-MIN plus career-only:

- knockdown efficiency creation/vulnerability
- significant strikes landed/absorbed per minute
- significant-strike accuracy/defense
- clinch and ground significant-strike environment share
- head and body target share
- takedown success/defense

`control_rate` and `reversal_rate` are deferred because their direction for finish-vs-decision is target-ambiguous.

No last-3, last-5, EWMA, or round-band duplicate is allowed in V1. `sig_strike_flow.attempted_per_min`, distance share, and leg share are omitted as overlapping/compositional re-expressions.

The complete literal allowlists are machine-readable in `feature_surface_v1.json`.

## Feature rationale

| Concept | Exact mechanism for MOV0 | Class | Orientation | Missingness | Surface | Decision |
|---|---|---|---|---|---|---|
| scheduled_rounds | More scheduled fight time creates more opportunity for a finish before the terminal decision. | direct | shared, side-free | training-only numeric imputation | B1 | B1_CONTEXT |
| title_bout | Title context changes fight structure and competitive setting beyond raw prevalence. | indirect | shared, side-free | training-only categorical imputation | B1 | B1_CONTEXT |
| weight_class | Finish frequency can differ structurally by division because size/style distributions differ. | indirect | shared, side-free | training-only categorical imputation | B1 | B1_CONTEXT |
| prior_fight_count | Strict-prior canonical fight experience changes how much stable fighter-specific history exists and may proxy fight maturity. | indirect | pair mean + absolute difference | normally observed, no new indicator | B1 | B1_CONTEXT |
| early_finish_profile | Prior round-one finish wins/losses directly measure early terminal-outcome history. | direct | componentwise mean + absolute difference | pooled-side training median | MIN | MOV0_MIN |
| finish_method_win_profile | Prior KO/TKO and submission win rates directly measure finish creation. | direct | componentwise mean + absolute difference | pooled-side training median | MIN | MOV0_MIN |
| finish_method_loss_profile | Prior KO/TKO and submission loss rates directly measure finish vulnerability. | direct | componentwise mean + absolute difference | pooled-side training median | MIN | MOV0_MIN |
| knockdown_creation_vs_vulnerability | Relative knockdown creation versus opponent vulnerability is a direct striking-finish pathway. | direct | directional-pair mean + absolute difference | pooled-direction training median | MIN | MOV0_MIN |
| knockdown_rate | Knockdowns created/allowed per exposure measure severe striking events preceding many KO/TKO finishes. | direct | componentwise mean + absolute difference | pooled-side training median | MIN | MOV0_MIN |
| submission_attempt_rate | Submission attempts created/faced measure direct submission threat and vulnerability. | direct | componentwise mean + absolute difference | pooled-side training median | MIN | MOV0_MIN |
| takedown_pressure | Takedown pressure measures how often the fight is pushed toward grappling states where finishes can develop. | direct | componentwise mean + absolute difference | pooled-side training median | MIN | MOV0_MIN |
| knockdown_efficiency | Strike-normalized knockdown creation/vulnerability adds power/durability information beyond time rate. | direct | componentwise mean + absolute difference | pooled-side training median | FULL | MOV0_FULL |
| sig_strike_flow | Landed/absorbed significant-strike flow measures sustained damaging exchange volume. | indirect | componentwise mean + absolute difference | pooled-side training median | FULL | MOV0_FULL |
| sig_strike_efficiency | Accuracy/defense describes how efficiently damaging exchanges are delivered and avoided. | indirect | componentwise mean + absolute difference | pooled-side training median | FULL | MOV0_FULL |
| sig_environment_mix | Clinch/ground striking share distinguishes environments with different finish pathways. | indirect | componentwise mean + absolute difference | pooled-side training median | FULL | MOV0_FULL |
| sig_target_mix | Head/body targeting describes where potentially damaging offense is directed. | indirect | componentwise mean + absolute difference | pooled-side training median | FULL | MOV0_FULL |
| takedown_conversion | Takedown success/defense indicates whether grappling pressure becomes realized positional opportunity. | indirect | componentwise mean + absolute difference | pooled-side training median | FULL | MOV0_FULL |
| control_rate | Control can create finish opportunity or suppress action and preserve a decision. | ambiguous | would require symmetric transform | no new indicator authorized | deferred | DEFER |
| reversal_rate | Reversals may represent either escape from danger or creation of danger. | ambiguous | would require symmetric transform | no new indicator authorized | deferred | DEFER |

## Fighter-order invariance

MOV0 predicts a fight-level event, so signed winner-style differences are prohibited.

For every f1/f2 semantic numeric pair:

1. fit one median on the pooled non-null training values from both sides;
2. impute both sides using that same training-only median;
3. project to:
   - `mean(f1, f2)`
   - `abs(f1 - f2)`

The directional knockdown matchup pair is treated analogously.

Mandatory future implementation test:

> Swap Fighter 1 and Fighter 2 and require identical predicted STANDARD_FINISH probability within `atol=1e-12, rtol=0`.

## Missingness

F02 nulls remain null in the frozen predictor artifact. Missing is not zero.

MOV0 V1 allows no new missingness indicators. Numeric imputation is fitted only within the relevant training history. Categorical context uses training-only imputation and encoding. Validation rows never influence preprocessing.

## Model family

B1, MOV0-MIN, and MOV0-FULL use ridge logistic regression only:

- penalty: L2
- solver: `lbfgs`
- `C = [0.03, 0.1, 0.3, 1.0]`
- `max_iter=3000`
- `tol=1e-4`
- `fit_intercept=true`
- no class weights
- random seed 17
- chronological inner log loss only
- frozen grid-order tie break

No elastic net, trees, boosting, random forests, neural networks, stacking, Optuna, synthetic resampling, or performance-driven feature selection.

## Chronological validation

Outer OOF years are **2018–2026**.

MOV0 V1 may use only rows dated **2015-01-01 or later** for training, validation, preprocessing, imputation, scaling, and hyperparameter selection. Each outer model trains on eligible 2015+ rows strictly earlier than the validation year. Hyperparameter selection uses only the two immediately preceding calendar years as inner chronological validation folds, and every inner model trains only on 2015+ history earlier than its inner validation year.

2018 is the earliest defensible outer year: a 2017 outer fold would require a 2015 inner-validation fold with no earlier 2015+ training history. The 2018 fold instead uses 2016 and 2017 as inner validation years; the 2016 inner model trains only on 2015.

Exact outer validation Ns sum to **4,260** and are frozen in `validation_plan_v1.json`. The first outer fold (2018) trains on exactly **1,398** eligible 2015–2017 fights.

Required ladder:

1. B1 vs B0
2. MOV0-MIN vs B1
3. MOV0-FULL vs MOV0-MIN

## Metrics and robustness

Primary: log loss.

Secondary:

- Brier
- calibration slope/intercept
- fixed 10-bin ECE
- reliability table
- ROC AUC
- prevalence
- mean prediction
- per-fold metrics
- descriptive-only accuracy

For every comparison, report aggregate and fold-by-fold log-loss differences, median fold delta, better/worse/tied folds, strongest favorable and unfavorable fold, and the fraction of total aggregate improvement contributed by the single strongest favorable fold.

Supporting uncertainty diagnostics:

- paired fight-level bootstrap, 2,000 replicates, seed 17
- event-cluster bootstrap, 2,000 replicates, seed 17

These are supporting diagnostics, not proof that all fight observations are independent.

## Validation Terrain V1

Join the permanent assignment by `fight_id`. Do not regenerate it.

Required diagnostics:

- experience
- layoff
- scheduled rounds
- title status
- exact weight class
- completeness
- striking environment
- grappling environment
- joint MOV environment

Watch explicitly:

- `HIGH_MISSINGNESS`
- 3-round
- 5-round
- `STRIKE_TWO_SIDED`
- `GRAPPLE_TWO_SIDED`

Existing sample-size governance remains unchanged.

## Result classification

Future execution must return exactly one of:

- `CLEAR_SUCCESS`
- `INCONCLUSIVE`
- `CURRENT_SPECIFICATION_NOT_SUPPORTED`

No hard numeric success threshold is invented here.

A failed MOV0 V1 specification must **not** be translated into `FINISH_MODELING_FAILED`.

## Future hierarchy

MOV0 supplies:

`P(DECISION) = 1 - P(STANDARD_FINISH)`

A later, separately authorized MOV1 may estimate:

`P(KO_TKO | STANDARD_FINISH)`

then:

`P(KO_TKO) = P(STANDARD_FINISH) * P(KO_TKO | STANDARD_FINISH)`

`P(SUBMISSION) = P(STANDARD_FINISH) * (1 - P(KO_TKO | STANDARD_FINISH))`

MOV1 is not started by this contract.
