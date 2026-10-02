# UFC EDGE — Betting Target Feasibility + Model Architecture Audit V1

## BETTING_TARGET_FEASIBILITY_MODEL_ARCHITECTURE_AUDIT_V1_COMPLETE

**Repository:** `Tkcool28/ufc-edge`
**Audited main:** `df2692934565b905f3b53380ec86b01bd42408fc`
**Current-main verification:** this is the current `main`; no newer commit was found after merged PR #71.
**Audit mode:** read-only. No DATA, F00/F01/F02, models, Validation Terrain, branches, PRs, or repository files were changed.

One documentation inconsistency exists but does not alter this audit: `PROJECT_STATUS.md` and the corrected-M1 freeze record reflect the current post-PR-71 state, while `docs/MASTER_MILESTONES.md` still contains an older repository-cleanup snapshot. Current status/freeze artifacts are therefore the higher authority.

---

## 1. Current capability map

The current UFC EDGE foundation is already sufficient to attempt useful method-of-fight probability modeling **without waiting for simulator-grade data**.

| Information family | Current capability | Audit finding |
|---|---|---|
| Winner probability | **Well represented** | Corrected M1 is frozen and broadly calibrated: 5,626 OOF fights, log loss `0.649120`, Brier `0.229025`, AUC `0.665906`, ECE `0.013466`. |
| Striking volume | **Well represented** | Significant-strike flow exists with career/recent/EWMA point-in-time history. |
| Striking efficiency | **Well represented** | Accuracy/defense and target/environment mix are governed F02 concepts. |
| Knockdown creation/vulnerability | **Well represented** | Knockdown rate, efficiency and creation-vs-vulnerability matchup state are present. |
| Grappling pressure | **Well represented** | Takedown pressure/conversion, generic control, submissions attempted and reversals exist. |
| Historical finish tendencies | **Well represented** | KO/TKO, submission and decision win/loss profiles plus first-round finish profiles already exist. |
| Physical profile | **Moderately/well represented** | Height/reach foundation was corrected and governed. Historical availability leakage is now explicitly controlled. |
| Age / experience / layoff | **Well represented** | All are strict pre-fight concepts; experience and layoff are also frozen Validation Terrain dimensions. |
| Scheduled rounds / title / weight class | **Well represented** | F02 exposes them once per fight as pre-fight context. M1 chose not to model them, but they are available to future models. |
| Missingness/completeness | **Governed** | Missing is distinct from zero; no-history is distinguished from observed inactivity where possible; completeness is permanently bucketed. |
| Opponent adjustment | **Not currently available as an active feature family** | The architecture exists in F00, but opponent-adjusted features remain `DEFERRED` / `V2_OPPONENT_ADJUSTED`. |
| Exact positional control state | **Poor/not available** | Generic `control_sec` is not top/back/ground/clinch duration. Exact positional duration remains a DATA requirement. |
| Submission threat-to-finish state | **Not available** | Submission attempts exist; exact position, threat duration and finish-given-threat do not. |
| Knockdown sequence/recovery | **Not available** | Knockdowns exist, but exact sequence, severity and recovery dynamics do not. |
| Late-round fatigue/hazard | **Poorly represented** | Late-round pace/fatigue concepts remain deferred/future derivation. |
| Exact simulator transition state | **Not available** | Transition matrices, escape hazard and exact position occupancy are not available at simulator quality. |

A particularly important finding comes from `MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE`: **all 15 rich-stat candidates examined for the permanent MOV terrain were classified PIT-safe and era-comparable**. The audit also successfully rediscovered the known historical reach-missingness leak as its positive control, which materially increases confidence that the MOV safety audit was capable of detecting the failure mode it was intended to catch.

Those 15 governed MOV-relevant concepts are:

`control_rate`, `early_finish_profile`, `finish_method_loss_profile`, `finish_method_win_profile`, `knockdown_creation_vs_vulnerability`, `knockdown_efficiency`, `knockdown_rate`, `reversal_rate`, `sig_environment_mix`, `sig_strike_efficiency`, `sig_strike_flow`, `sig_target_mix`, `submission_attempt_rate`, `takedown_conversion`, and `takedown_pressure`.

**Key capability conclusion:** the missing simulator state is a blocker for a faithful fight simulator and fine-grained hazard modeling. It is **not** a blocker for calibrated pre-fight probabilities of finish, decision, KO/TKO or submission.

---

## 2. Target feasibility table

### Audited population

Canonical DATA contains 9,252 fights from **March 11, 1994 through August 15, 2026**, including 8,769 UFC fights.

For comparability with corrected M1 and permanent Validation Terrain V1, the relevant model-evaluation population is UFC **2015 through August 15, 2026**:

| State | N |
|---|---:|
| All UFC terrain rows | **5,729** |
| `win_loss` | **5,626** |
| draw | **46** |
| no contest | **57** |

Canonical method counts over those 5,729 fights are:

| Canonical method | N |
|---|---:|
| DECISION | **2,836** |
| KO_TKO | **1,812** |
| SUBMISSION | **1,010** |
| DQ | **13** |
| OTHER | **25** |
| NO_CONTEST | **33** |

There are 45 draw fights whose canonical method is `DECISION`. That distinction matters: they are valid **fight-goes-to-decision** observations but are not valid **fighter-wins-by-decision** observations.

For clean fight-level MOV modeling, I would establish a `STANDARD_MOV_ELIGIBLE` population consisting only of canonical `KO_TKO`, `SUBMISSION`, or `DECISION`.

That produces **N=5,658**:

- DECISION: `2,836` — **50.12%**
- KO/TKO: `1,812` — **32.03%**
- SUBMISSION: `1,010` — **17.85%**

DQ/NO_CONTEST/OTHER/UNKNOWN should remain explicit states rather than being silently coerced into one of the three standard classes.

| Candidate target | Label quality / semantics | Historical N and balance | Feature support | Temporal safety / Validation Terrain | Material missing information | Feasibility |
|---|---|---|---|---|---|---|
| **Winner** | Existing governed F02 target: participant winner on `win_loss` rows. Draw/NC excluded. | **5,626**. F1 win 2,786 vs F2 win 2,840. | Very strong; corrected M1 already uses broad 197-D projection. | **Highest confidence.** Existing F02 target contract, chronological OOF, corrected leakage audit and complete V1 terrain. | Nonlinear interactions and opponent adjustment are deferred, but not label/data blockers. | **Mature / already modeled.** |
| **KO/TKO occurrence** | `method == KO_TKO` on standard-MOV population. | **1,812 / 5,658 = 32.0% positive.** | Strong: KD rate/efficiency, KD matchup, strike flow/efficiency/mix, finish history, durability. | High. MOV input audit passed; striking and joint MOV terrain directly relevant. Binary confidence terrain reusable. | No knockdown severity/recovery/sequence. | **High.** |
| **Submission occurrence** | `method == SUBMISSION` on standard-MOV population. | **1,010 / 5,658 = 17.9% positive.** | Good but weaker than KO: sub attempts, TD pressure/conversion, control, reversals, finish histories. | High PIT confidence; grappling and joint environments are directly useful. | Exact ground position, threat duration, submission type and finish-given-threat absent. | **Moderate-high.** |
| **Decision occurrence** | `method == DECISION`, including decision draws for fight-level target. | **2,836 / 5,658 = 50.1% positive.** | Strong because it is the complement of standard finish and context like scheduled rounds is available. | High. All major terrain dimensions apply. | Judge-round state is not needed to predict whether a fight reaches decision, although it would matter for deeper decision simulation. | **High.** |
| **Inside distance / standard finish** | `KO_TKO OR SUBMISSION`; DQ kept separate until sportsbook settlement semantics are explicitly governed. | **2,822 vs 2,836**, essentially 50/50. | **Strongest new-target support.** It combines the current striking, durability, submission and grappling information. | High. Binary confidence bins fit naturally; strike, grapple, joint MOV, completeness and duration terrain all apply. | No critical missing variable blocks a first model. | **Very high.** |
| **Goes distance** | `DECISION` vs standard KO/SUB finish. | **2,836 vs 2,822**, essentially 50/50. | Same strong support as standard finish. | High and directly compatible with V1 terrain. | Sportsbook-specific DQ/NC settlement rules must be handled only later during market integration. | **Very high.** |
| **Early vs late finish** | Among standard finishes only: R1 versus R2+. | **2,822** finishes: R1 `1,390`; R2+ `1,432`. | Moderate. Existing `early_finish_profile` is directly relevant; striking/grappling histories help. | Label is clean and PIT-safe. Scheduled-duration/title terrain matters heavily. | Active late-round pace/fatigue state is missing. | **Moderate.** |
| **Exact finish round** | Among KO/SUB finishes, predict canonical `finish_round`. | **2,822:** R1 1,390; R2 902; R3 471; R4 32; R5 27. | Incomplete for the question. | Label itself is deterministic and safe, but 3-vs-5-round context dominates possible classes. | Severe R4/R5 sparsity plus absent round/fatigue hazard state. | **Low as a five-class target today.** |
| **Joint fighter + method** | Six standard outcomes: F1/F2 × KO/SUB/DEC. | **5,613** winner-resolved standard-MOV fights. Smallest class is F2 submission at 483; largest F2 decision at 1,431. | Directional F02 state makes this technically possible. | High label safety; environmental terrain applies. | More difficult coherence/symmetry problem and smaller per-class samples. | **Viable later, not the first MOV experiment.** |

The exact joint six-class counts are: F1 KO 894, F2 KO 918, F1 SUB 527, F2 SUB 483, F1 DEC 1,360, F2 DEC 1,431.

### Era concern

The canonical labels exist much farther back than 2015. That does **not** mean the project should simply use the full 1994–2026 label history for MOV modeling. Rich-stat coverage, support and source regimes are much cleaner in the permanent 2015–2026 terrain. The existing MOV safety audit specifically evaluated the relevant modern modeled population and found all 15 candidate rich-stat families era-comparable.

---

## 3. Recommended next predictive question

The primary next question should be:

> **“Can point-in-time UFC EDGE pre-fight state estimate the probability that a fight ends by a standard finish — KO/TKO or submission — rather than decision, with calibrated chronological out-of-sample performance materially better than a frozen empirical/context baseline?”**

This is the best next question supported by the repository evidence.

The target has **5,658** clean historical examples and is almost perfectly balanced:

- standard finish: **2,822**
- decision: **2,836**

It exploits information UFC EDGE already has rather than asking for simulator variables it does not have. It immediately creates a useful calibrated probability for two eventual markets—inside-distance and goes-distance—and it is the correct first node of a coherent hierarchical MOV architecture.

It also fits Validation Terrain V1 unusually well. Unlike a 3-class model, this is binary, so the existing binary confidence-bucket concept remains directly interpretable. Strike, grapple, completeness, scheduled rounds, title status, experience, layoff, weight class and joint MOV environments can all be reused without redefining the terrain.

This is also an orthogonal capability that corrected M1 does not provide at all. Another winner challenger would compete for incremental gain on a question UFC EDGE already answers; a finish model answers a currently unanswered betting-relevant question.

---

## 4. Secondary options

**KO/TKO probability** is the strongest immediate follow-on. Existing knockdown and striking features are unusually direct, and Validation Terrain already shows a meaningful historical gradient: KO/TKO rate rises from about **27.5% in `STRIKE_LOW`** to **39.8% in `STRIKE_ONE_SIDED`** and **43.2% in `STRIKE_TWO_SIDED`**. Those are descriptive outcome gradients, not evidence of predictive model performance, but they establish that the frozen terrain captures relevant context.

**Submission probability** is also viable. Historical submission rates in the frozen terrain rise from about **14.6% in `GRAPPLE_LOW`** to **22.9% in `GRAPPLE_ONE_SIDED`** and **30.5% in `GRAPPLE_TWO_SIDED`**. The main reason to place it after the finish node is not that it is unimportant; it is that the positive class is smaller and the missing positional-state data is more relevant to submission mechanics.

**Joint fighter-by-method probability** is ultimately closer to sportsbook MOV markets than a fight-level method probability. It should come after the project proves it can estimate fight-level finish/method probabilities coherently. Directly jumping to six classes would mix winner learning, finish learning, method learning and calibration into one first experiment.

**Early-versus-late finish** is supportable, but current F02 lacks a mature late-round/fatigue representation. It is a reasonable future node after aggregate MOV works.

**Another winner challenger / M1B** remains legitimate future research, but it adds depth to an already functioning capability instead of adding an entirely missing betting probability.

---

## 5. M1B verdict

### M1B_SHOULD_WAIT

Corrected M1 is not perfect. Its architecture still has known limitations:

- it is a linear regularized model over antisymmetric feature differences;
- symmetric context such as scheduled rounds, title status and weight class was intentionally diagnostic-only in M1;
- nonlinear feature interactions are not represented;
- opponent-adjusted feature families remain deferred;
- `GRAPPLE_TWO_SIDED` remains a weaker discrimination environment;
- high-missingness populations remain harder.

Those are valid reasons to revisit the winner problem eventually.

They are **not** currently evidence that another winner model is the highest-value investment.

Corrected M1 is frozen, broadly calibrated and already provides a credible winner reference. Its aggregate ECE is `0.013466`, its calibration slope is `1.0593`, and its 2026 partial AUC is `0.6952`. Meanwhile UFC EDGE currently has **no frozen finish, KO, submission or decision probability model at all**.

The next marginal unit of model work therefore creates more project capability by opening MOV than by immediately attempting to improve M1.

If M1B is revisited later, its question should be explicit—for example whether nonlinear/opponent-adjusted representation improves winner log loss and calibration on the same permanent terrain—not simply “build a stronger model.”

---

## 6. MOV architecture recommendation

### HIERARCHICAL

The repository evidence favors a hierarchical architecture over either a single multiclass model or independent binary specialists.

### Multiclass

A single model over:

`P(KO/TKO), P(SUBMISSION), P(DECISION)`

has a perfectly usable overall sample:

- decision 2,836
- KO/TKO 1,812
- submission 1,010

The advantages are probability coherence and one direct objective.

Its disadvantages are material here. Submission is substantially smaller than the other classes, model failure is harder to localize, and Validation Terrain V1's current confidence scheme is intrinsically binary—its bins begin at 50%. A 3-class top prediction can legitimately be below 50%, so the confidence surface would not transfer as cleanly.

### Hierarchical

The data naturally create two unusually clean binary questions.

**Node 1:**

`P(STANDARD_FINISH)`

- finish: 2,822
- decision: 2,836

**Node 2, conditional on finish:**

`P(KO/TKO | FINISH)`

- KO/TKO: 1,812
- submission: 1,010

Then:

`P(DECISION) = 1 - P(FINISH)`

`P(KO/TKO) = P(FINISH) × P(KO/TKO | FINISH)`

`P(SUBMISSION) = P(FINISH) × [1 - P(KO/TKO | FINISH)]`

That gives coherent three-way probabilities while allowing each component to have its own baseline, calibration audit and terrain diagnostics.

It also makes failure interpretable. If the system predicts finishes well but cannot distinguish KO from submission, that will be obvious rather than buried inside one multiclass loss.

The main caution is that calibration errors propagate through multiplication, so the final composed KO/SUB/decision probabilities must be evaluated directly after both nodes are frozen.

### Independent binary specialists

Separate `P(KO)`, `P(SUB)`, and `P(DECISION)` models are useful diagnostic challengers and can support specialist subsets.

They are a weaker primary architecture because independent probabilities can become incoherent:

`P(KO) + P(SUB) + P(DECISION) ≠ 1`

That then requires an additional normalization or coupling layer.

**Recommended backbone:** hierarchical.
**Recommended specialist binaries:** later challengers/diagnostics, not the probability backbone.

---

## 7. Simulator dependency

| Target | Simulator-grade data required? | Finding |
|---|---|---|
| Winner | **No** | Already modeled successfully. |
| Standard finish / inside distance | **No** | Current features and labels are sufficient for a serious first model. |
| Goes distance | **No** | Same binary problem in reverse. |
| Fight-level KO/TKO | **No** | Existing damage/striking history is meaningful enough to test. |
| Fight-level submission | **No** | Can be modeled now, although richer positional data could improve it. |
| Decision | **No** | Does not require judge-state simulation to estimate whether the fight reaches decision. |
| Fighter-by-method joint probability | **No, in principle** | Direct supervised modeling is possible from current labels/features; simulator is not mathematically required. |
| R1 vs later finish | **Not strictly** | Current data permit it, but missing fatigue/late-round state weakens the model story. |
| Exact finish round | **Not necessarily a full simulator, but more state is needed** | Current R4/R5 N and temporal-hazard representation are poor. |
| Position-by-position fight simulator | **Yes** | Exact positional duration/state transitions remain genuinely blocking. |
| Submission finish-given-threat hazard | **Yes / materially richer data needed** | Attempt counts are insufficient to reconstruct positional threat. |
| Knockdown→recovery→finish simulation | **Yes / richer sequence data needed** | Current DATA lacks sequence/severity/recovery state. |

The important architectural result is that **MOV probability modeling and simulator construction should not be treated as the same prerequisite chain**.

A useful calibrated MOV system can be built and validated well before UFC EDGE can construct a trustworthy state-transition simulator.

---

## 8. Blocking data gaps

There is **no current DATA blocker for the proposed finish-versus-decision experiment**.

Only two gaps materially block later targets:

| Data gap | What it actually blocks |
|---|---|
| **Exact positional duration / ground-top-back-clinch state** | High-fidelity submission hazard, positional simulator states, transition modeling, escape/reversal hazard. |
| **Mature round/fatigue state** | Credible exact-round and late-finish hazard modeling, especially R3/R4/R5 behavior. |

Opponent adjustment is a potentially valuable **feature-development** gap, not a DATA blocker.

Current-fight injuries, camp changes, travel, qualitative weigh-in observations and similar research context may eventually add value, but the repository provides no evidence that they are prerequisites for a useful first MOV probability model.

---

## 9. Proposed next experiment

### Proposed experiment: `MOV0_STANDARD_FINISH_PROBABILITY_V1`

### Exact target

Population:

- UFC
- permanent modeling/evaluation era
- canonical `method ∈ {KO_TKO, SUBMISSION, DECISION}`

Label:

`standard_finish = 1` for `KO_TKO` or `SUBMISSION`

`standard_finish = 0` for `DECISION`

Current historical target N:

- positive: **2,822**
- negative: **2,836**
- total: **5,658**

DQ, NO_CONTEST, OTHER and UNKNOWN remain explicit exclusions. Decision draws remain valid negative examples because the fight did reach a decision.

A new frozen MOV target contract should be created before training. The target attachment must follow the same F02 discipline already used for winner modeling:

`freeze predictors first → attach labels afterward`.

### Research question

> **Can current governed pre-fight state produce calibrated standard-finish probabilities that outperform simple market-blind empirical/context baselines under chronological out-of-sample validation?**

### Minimum feature surface

Use a deliberately bounded surface rather than all 200 F02 predictors.

The first candidate should consume the **15 MOV concepts whose availability was already explicitly audited as PIT-safe and era-comparable**:

`control_rate`
`early_finish_profile`
`finish_method_loss_profile`
`finish_method_win_profile`
`knockdown_creation_vs_vulnerability`
`knockdown_efficiency`
`knockdown_rate`
`reversal_rate`
`sig_environment_mix`
`sig_strike_efficiency`
`sig_strike_flow`
`sig_target_mix`
`submission_attempt_rate`
`takedown_conversion`
`takedown_pressure`

Add only the minimum governed context/support needed to interpret those histories:

`prior_fight_count`
`scheduled_rounds`
`ctx__title_bout`
`ctx__weight_class`

Do **not** add opponent adjustment, physical-profile missingness, rankings, current weigh-in state, simulator proxies, trees/boosting or new feature engineering in this first experiment.

This is intentionally not a claim that those excluded concepts are useless. It isolates whether the already-audited MOV information is sufficient.

### Frozen baselines

**B0 — empirical constant:** training-period standard-finish prevalence.

**B1 — context-only logistic baseline:** scheduled rounds + title status + governed weight class + prior UFC experience only.

The richer MOV candidate must beat **B1**, not merely B0.

### Candidate model

A simple regularized logistic regression is sufficient for the first test.

No tree model, boosting, feature selection or sportsbook information should be introduced until the question “is there clean pre-fight MOV signal?” has been answered.

### Validation

Use the same chronological philosophy as M1:

- train only on earlier history;
- annual OOF validation over 2015–2026;
- preprocessing fit only on each training period;
- no random CV;
- no target-driven terrain changes;
- no sportsbook odds;
- no ROI.

### Metrics

Primary:

**log loss**

Secondary:

**Brier score**, calibration slope/intercept, ECE, reliability curve, ROC AUC for discrimination context.

Accuracy should not be an acceptance metric.

### Validation Terrain V1

Evaluate the model on the permanent terrain without changing any thresholds:

- model confidence;
- UFC experience;
- layoff;
- scheduled rounds;
- title status;
- exact weight class;
- completeness;
- striking environment;
- grappling environment;
- joint MOV environment.

The most important failure checks for this target are:

`HIGH_MISSINGNESS`
`3_ROUND vs 5_ROUND`
`STRIKE_TWO_SIDED`
`GRAPPLE_TWO_SIDED`
the major joint strike/grapple cells.

The existing V1 sample governance remains unchanged.

### Proposed acceptance/rejection logic

These would be **new experiment gates**, not claims that the repository has already adopted them:

**Accept the candidate for a freeze review only if:**

1. chronological OOF log loss is lower than both B0 and B1;
2. the paired 95% bootstrap interval for candidate-minus-B1 per-fight log loss has an upper bound below zero;
3. Brier is not worse than B1 by more than `0.002`;
4. global ECE is `≤ 0.03`;
5. calibration slope is between `0.80` and `1.20`;
6. absolute calibration intercept is `≤ 0.10`;
7. no Validation Terrain cell with `N ≥ 100` shows an absolute calibration gap greater than `0.10`;
8. the apparent improvement is not confined to a single post-hoc subgroup.

**Reject or redesign if:**

- improvement is only in AUC/accuracy while log loss does not improve;
- aggregate gain disappears under chronological OOF;
- calibration deteriorates materially;
- performance depends on a thin terrain cell;
- high-missingness rows produce unstable probabilities;
- or the candidate requires changing the frozen terrain after seeing results.

If Node 1 passes, the next separately authorized experiment should be:

`P(KO_TKO | STANDARD_FINISH)`

on the **2,822** standard finishes, with 1,812 KO/TKO versus 1,010 submissions.

Only after both nodes independently pass should UFC EDGE compose and freeze final fight-level:

`P(KO/TKO), P(SUBMISSION), P(DECISION)`.

---

## 10. Final direction

The audit does **not** support waiting for simulator data before producing useful MOV probabilities.

It also does **not** support making M1B the automatic next project merely because it follows M1 chronologically.

The strongest repository-supported next step is a bounded, binary first node for a hierarchical MOV system:

> **standard finish versus decision**

The reasons are unusually clean:

- deterministic canonical label;
- **5,658** usable historical fights;
- essentially perfect class balance;
- strong existing causal/proxy feature support;
- 15 relevant inputs already independently audited for temporal safety and era comparability;
- permanent Validation Terrain already contains striking/grappling environments designed specifically to expose MOV-context failures;
- binary calibration fits the existing validation architecture;
- no simulator-grade data is required;
- and success immediately creates a new betting-relevant calibrated probability instead of incrementally refining an already serviceable winner model.

## M1B verdict

**M1B_SHOULD_WAIT**

## MOV architecture

**HIERARCHICAL**

## Final direction

# PROCEED_TO_HIERARCHICAL_MOV_DESIGN
