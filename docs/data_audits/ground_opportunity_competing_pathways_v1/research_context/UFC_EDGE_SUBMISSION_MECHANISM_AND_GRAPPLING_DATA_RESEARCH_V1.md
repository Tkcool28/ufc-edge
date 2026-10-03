# UFC_EDGE_SUBMISSION_MECHANISM_AND_GRAPPLING_DATA_RESEARCH_V1

## Executive findings

### Bottom line

The strongest conclusion from the repository evidence and verified external modeling literature is that **UFC EDGE's most important unresolved information gap is not basic ground access and not simply “more submission data.” It is the amount and quality of actual submission opportunity after grappling access has been achieved.**

UFC EDGE already possesses meaningful information about takedown activity/access, takedown conversion/defense, submission-attempt pressure, attempts faced, historical outcomes, striking context, and directional opponent matching. PR #125 is informative because Arm C improved global conditional KO-versus-submission estimation after restoring compact directional structure, yet B3 remained underpredicted. This weighs against the proposition that B3 is mainly an algorithm-complexity problem or simply a missing offense-by-defense interaction.

The B3 pattern is consistent with a representation that knows **that fighters grapple** without knowing sufficiently well **what kind of grounded environment they create once they get there**. This remains a hypothesis rather than a demonstrated causal explanation.

> Ground access ≠ Ground opportunity ≠ Submission creation ≠ Submission conversion.

Holmes, McHale and Żychaluk's MMA Markov model separately models action/work rates, takedown success, grounded control, ground striking, submission attempts, and submission success. It estimates offensive and defensive fighter abilities and regularizes sparse fighter histories. It acknowledges that limited data forced the ground game into a single ground-control state, and that positional data could support a more realistic model. [1–3]

**The highest-value next milestone is not another MOV1 classifier and not yet a simulator.** It is a strict-prior **Ground Opportunity and Competing Pathway Reconstruction Audit** to establish whether UFC EDGE's governed sources can historically reconstruct:

1. Actual or defensible proxy grounded exposure;
2. Submission creation conditional on that exposure; and
3. Submission-versus-ground-striking activity conditional on comparable exposure.

Only after that audit should a narrowly frozen experiment be authorized.

### Why B3 is the key diagnostic

Frozen modern finish universe: 2,822 standard finishes; 1,812 KO/TKO; 1,010 submissions. The overall submission proportion conditional on standard finish is 35.8% (1,010/2,822).

B3 has 224 historical standard finishes, with observed submission frequency **54.02%**. Arm C predicted **44.01%** on average: a **10.01 percentage-point** gap despite globally improving conditional log loss.

| B3 representation | Mean predicted SUB | Observed SUB | Predicted minus observed | Conditional LL |
|---|---:|---:|---:|---:|
| A — Original MIN | 44.79% | 54.02% | −9.23 pp | 0.702464 |
| B — MIN + directional SUB interaction | 44.61% | 54.02% | −9.41 pp | 0.703914 |
| C — Compact directional | 44.01% | 54.02% | **−10.01 pp** | 0.702832 |

B5 is different, with 355 historical standard finishes:

| B5 representation | Mean predicted SUB | Observed SUB | Predicted minus observed | Conditional LL |
|---|---:|---:|---:|---:|
| A — Original MIN | 45.95% | 54.93% | −8.98 pp | 0.706751 |
| B — MIN + directional SUB interaction | 46.29% | 54.93% | −8.64 pp | 0.706938 |
| C — Compact directional | 48.06% | 54.93% | **−6.87 pp** | **0.682100** |

B5's directional response is consistent with explicit alignment of submission pressure and opposing submission vulnerability being useful, but does not show that the full mechanism is observed. The remaining gap is material, and PR #125 is historical developmental evidence, not prospective confirmation.

### What is established versus hypothesized

- **Repository evidence:** Directional structure matters. Arm C improved over A by −0.007589 conditional log loss, with fight-level 95% CI [−0.012874, −0.002323] and event-cluster 95% CI [−0.012643, −0.002577]. It improved eight of nine outer years, with 2023 unfavorable. This is not an automatic promotion decision.
- **Published literature:** Separating action rates, attack/defense, takedown success, ground activity, submission activity, and finish mechanisms is a coherent MMA modeling strategy. Sparse histories require regularization. [1]
- **Reasoned hypothesis:** B3 may mix submission-oriented grapplers with control wrestlers, ground-and-pound fighters, scramblers, and takedown-volume fighters with different post-entry behavior.
- **Not established:** Ground-control duration by itself will fix B3. It is a candidate exposure denominator, not a validated causal or predictive solution.

The decisive question is: **Given successful access to grappling, can UFC EDGE distinguish fighters who create submission opportunities from those who primarily create control or ground-striking opportunities?**

## Repository evidence and existing-data capability inventory

### Repository boundary and provenance

Required starting anchor: `3e2b14a8391ed17d072b4bbb9570b31bc6d12b85` (main following PR #125).

The GitHub connector was used before external literature lookup. The PR #125 report directory was enumerated and its principal report read at the supplied anchor:

`models/challengers/mov1_three_arm_directional_run_v1/run_v1/FINAL_REPORT.md`

A current main tree was enumerated, giving tree SHA `78f1a67bf1735975c0bab34d63fb6ae230cd1215`. **The matching live branch commit SHA was not retained in the research synthesis**, so that tree SHA must not be substituted for a commit SHA. Whether main advanced beyond the required anchor remains to be verified in the next handoff.

The repository tree exposed FightMetric position-time/position-state audit material. Its exact source paths and coverage results were not preserved in the research synthesis, so this is classified as a **candidate repository source, not a verified production feature**.

### Existing-data capability matrix

“Available” is deliberately conservative. A feature name is not proof that it measures the desired mechanism.

| Concept | Already available? | Source / lineage | Historical coverage | Limitation / classification |
|---|---|---|---|---|
| Ground access | Yes, implemented | F01/F02 fighter state; PR #125 directional takedown-access interaction | PR #123 found ~20% of historical training fights lacked complete directional source measurements | Measures access, not subsequent grounded state. Available/implemented. |
| Takedown pressure | Yes, implemented | Governed F02 history and directional construction | PR #123 sampled strict-prior reconstruction passed 48/48 | Attempts may not lead to successful entry. Available/implemented. |
| Takedown conversion | Source measurement present | F01/F02 construction lineage | Exact fold-by-fold denominator support needs audit | Unstable with few attempts; not sustained opportunity. Available/derivable. |
| Opponent takedown defense | Yes | F01/F02 fighter-side history | Prior-history, debut and denominator limitations | Only speaks to entry/access. Available/implemented. |
| Submission attempts created | Yes | F02 source measurements; PR #123 | Directional-source completeness imperfect | Existing rate denominator may hide actual ground opportunity. Available/implemented. |
| Submission attempts faced | Yes | F02 source measurements; PR #123 | Same chronology/completeness qualification | Mixes opponent quality, ground exposure and defense. Available/implemented. |
| Submission opportunity | Partially observed | SUB attempt counts/rates as proxy | Actual exposure denominator unknown | Total fight time ≠ ground-state opportunity. Partially derivable; inadequately represented. |
| Ground control | Not verified as governed F02 input | FightMetric/position-time repository audit candidate | Unresolved | Provenance, definition, historical depth and reproducibility need audit. Potentially available/unused. |
| Ground-and-pound | Ground-striking source information exists | F01/F02 striking context and repository research | Exact era-by-era completeness unknown | Need common grounded-exposure denominator. Available/derivable, mechanistic use unresolved. |
| Historical submission finishes | Yes | Finish-method target/history, PRs #117–#119 | 1,010 in modern universe; less in early folds | Sparse fighter-level successes. Available, requires regularization. |
| Submission conversion | Crudely derivable; not verified as governed feature | SUB finishes divided by attempts, if histories governed | Sparse, especially for debuts and early years | Attempts differ in quality; naked rates statistically fragile. |
| Submission defense/exposure | Partial | SUB attempts faced plus opponent outcome history | Directional completeness/debut limits | Low attempts faced might mean little exposure, not strong defense. |
| Positional grappling | Not established in production | Position-time/FightMetric audit candidate | Unverified | No verified governed mount/back/guard/transition history. |
| Fight-state duration | Total time yes; ground time unverified | Historical elapsed-exposure governance | Total time available; state-specific coverage unresolved | Fight minutes are an imperfect SUB opportunity denominator. |
| Directional offense/defense alignment | Yes | PRs #123–#125 | ~80% complete source cases under supplied audit | Does not recover unobserved post-entry states. |
| Significant-strike environment | Yes | Existing MIN/F02 and PR #125 compact marginals | Broad historical support | Competing KO context, not direct SUB opportunity. |
| Division/context | Yes | Arm C preserved original context encoding | Broad, but small division/fold subgroups | Cannot substitute for mechanism. |
| Scheduled rounds | Context present in project architecture | MOV/F02 context lineage | Five-round sample much smaller | Mechanistic interaction not established in this research. |
| Physical profile | Historically incomplete | F01/F02 profile lineage | Exact coverage unavailable in synthesis | Not the identified post-entry observation gap. |
| Opponent-adjusted latent SUB skill | Not established as MOV1 mechanism | No verified feature; conceptual comparison to Holmes et al. | N/A | Longer-term regularized estimation possibility, not immediate milestone. [1] |

### Exact meaning of PR #125

Arm A was frozen original MOV1-MIN, conditional log loss **0.615366**. Arm B retained MIN plus one directional submission interaction, **0.615496**: B versus A **INCONCLUSIVE**. Arm C used nine core marginal means, two directional knockdown summaries, one submission-pressure interaction, one takedown-access interaction, and original context/division encoding, conditional log loss **0.607777**: C versus A and C versus B **SUPPORTED_IMPROVEMENT** under the frozen criteria.

This supports a real representation issue without proving representation is now complete. B3's continuing underprediction even under Arm C weakens the rationale for merely adding more transformations of the same takedown-offense/defense and SUB-pressure/vulnerability variables. A missing observable post-entry state is now the more targeted information question.

### Primary experiment artifacts

Within `models/challengers/mov1_three_arm_directional_run_v1/run_v1/`:

- `FINAL_REPORT.md`
- `FOCUSED_B3_DIAGNOSTIC.md`
- `FOCUSED_B5_DIAGNOSTIC.md`
- `B1_B5_PATHWAY_COMPARISON.md`
- `STRIKING_PRESERVATION_REPORT.md`
- `SCIENTIFIC_INTERPRETATION_REPORT.md`
- `ANNUAL_COMPARISON.md`
- `COMPLETE_SYSTEM_COMPOSITION_REPORT.md`
- `FORWARD_CONFIRMATION_READINESS_REPORT.md`

Project research lineage includes PRs #113 and #117–#125, with #123–#125 particularly important to this finding. Not all underlying code/coverage details were captured in the final synthesis; the proposed next audit explicitly resolves them rather than claiming unverified completeness.

## Scientific evidence and submission-mechanism decomposition

### Holmes, McHale and Żychaluk

Holmes, Benjamin; McHale, Ian G.; Żychaluk, Kamila. *A Markov chain model for forecasting results of mixed martial arts contests*. **International Journal of Forecasting**, 39(2), 2023, 623–640. DOI: [10.1016/j.ijforecast.2022.01.007](https://doi.org/10.1016/j.ijforecast.2022.01.007). [1–3]

This work estimates fighter abilities feeding a fight-level Markov chain rather than directly predicting a binary winner. It does not collapse all grappling to a single statistic: strike/takedown/SUB action work rates and action accuracy are modeled separately, with attacking and defending fighter effects and weight-class context. Its Bayesian generalized linear framework applies weakly informative priors where fighters have few relevant observed actions. [1]

The modeled process includes standing activity, takedown success/failure, grounded control, ground striking, submission attempts/success, escapes/return to standing, and round progression. The simulation operates in one-second intervals and starts rounds standing. The paper explicitly acknowledges using one simplified generic ground position because granular positional history was unavailable; richer positions could support a more realistic chain. [1]

**Applicability:** A conceptual reference for mechanism separation and shrinkage, **not** a mandate to adopt its architecture or begin simulator implementation.

### A — Ground access

Takedown activity, success, defensive matchup, and conventional entry matter. But takedown success is an **entry transition**, not an observed submission opportunity.

Illustrative (synthetic, not repository data): two fighters may each land ten takedowns across twenty ground minutes; one creates twelve submission attempts and twenty ground-strike attempts, the other two submissions and one hundred ground-strike attempts. Equal takedown counts conceal different grounded pathways.

### B — Sustained opportunity

Following entry, the meaningful questions are whether a ground state is sustained, its duration, positional quality, and whether the contest returns quickly to standing. A takedown followed by an immediate scramble is different from prolonged back control. Ground-control duration may add a useful exposure denominator, but its incremental predictive value has **not** yet been demonstrated for UFC EDGE. Nor is generic CTRL time identical to submission-relevant position time.

### C — Submission creation and denominators

Illustrative (synthetic): with sixty historical fight minutes and six submission attempts, a fighter with six grounded minutes has 1.00 SUB attempts per grounded minute, while one with thirty grounded minutes has 0.20. Both have 0.10 per total fight minute. The difference is exactly what the broad time denominator can obscure.

| Candidate measurement | What it measures | Principal weakness |
|---|---|---|
| SUB ATT / fight | Overall attempt volume | Unequal fight lengths |
| SUB ATT / fight minute | Attempt rate per general exposure | Standing time treated like ground opportunity |
| SUB ATT / completed takedown | Creation per conventional entry | Ground arises by other means; entry duration varies |
| SUB ATT / grounded minute | Creation conditional on ground exposure | Requires trustworthy ground duration |
| SUB ATT / control minute | Creation conditional on controller time | Can miss bottom submissions and scrambles |
| SUB ATT / position-minute | Position-specific creation | Requires granular positional records not verified in production |

If historical semantics/coverage support it, SUB ATT per grounded minute is a targeted audit candidate. SUB ATT per completed TD is a feasible **proxy/fallback**, but should not be mislabeled actual grounded exposure.

### D — Submission conversion

The naïve `historical SUB finishes / historical SUB attempts` ratio is too fragile to introduce directly. A 1-for-1 fighter should not be treated as possessing a known 100% finishing propensity; 0-for-1 does not establish zero propensity. A regularized Beta-binomial or hierarchical logistic estimate is conceptually suitable, retaining numerator, denominator and effective support. [1]

However, attempts are not necessarily exchangeable Bernoulli trials: a deep rear-naked choke and an opportunistic low-quality guillotine can both be one recorded attempt. The ratio partly conceals **opportunity quality** inside an apparent conversion skill. Given only 1,010 submission finishes in the whole modern universe, fighter-level prior-only conversion support is smaller still. Conversion is therefore secondary in the immediate audit.

### E — Submission defense

Low SUB attempts faced could reflect excellent positional defense, excellent takedown defense that prevents exposure, stand-ups, weak-opponent attempt rates, or little grounding at all. A more mechanism-aligned decomposition would distinguish **opportunity suppression** (`opponent SUB attempts / relevant opponent ground exposure`) from **conversion prevention** (`opponent SUB finishes / opponent attempts`)—both with strict-prior support and shrinkage. The current system has clearer numerator availability than denominator availability.

### F — Competing grounded finish pathways

After entry, a fighter can maintain control, attempt a submission, throw ground strikes, permit a return to standing, or end the round without a finish. Holmes et al. represent grounded striking and submission as distinct processes. [1]

A future measure of SUB-vs-ground-strike orientation on comparable exposure may better distinguish submission seekers from GnP/control wrestlers. For example, a smoothed grounded-offense share could be investigated conceptually, but no scaling parameter should be fitted against B3 outcomes before a frozen, scientifically justified specification. It is necessary first to verify source definitions and chronology.

## B3 versus B5 investigation

### B3 — Potential latent mixture

B3's frozen criteria are takedown access plus submission pressure. Such a cell may mix:

| Candidate grappling style | Ground access | SUB creation | Ground striking | Why distinction matters |
|---|---|---|---|---|
| Submission hunter | High | High | Low/moderate | Genuine submission-seeking environment |
| Control wrestler | High | Low | Low/moderate | Strong control does not guarantee SUB-heavy finishes |
| Ground-and-pound wrestler | High | Low/moderate | High | Competing KO/TKO pathway |
| Scramble grappler | Variable/high | Variable | Variable | Short duration per entry can confound counts |
| Takedown-volume fighter | High attempt volume, mixed success | Variable | Variable | Attempt pressure may exaggerate sustained access |

**Support for investigating mixture:** PR #123 proved lost matchup alignment was real; PR #125 restored directional takedown access and SUB pressure yet B3 still averaged ~44% predicted SUB versus 54.02% observed. The external mechanistic model likewise separates entry, grounded striking, SUB activity and SUB success. [1]

**Limits/contrary considerations:** B3 contains 224 standard finishes, so observed cell frequency has sampling uncertainty. No existing verified analysis yet shows that control time or ground-strike orientation produces stable, chronological B3 subgroups. The mixture explanation remains a hypothesis, not a finding.

**Prospective diagnostic without retraining:** Within the *unchanged frozen B3 membership*, describe strict-prior SUB attempt density and ground-strike density on a defensible shared grounded denominator, with missingness and historical support. Do not select cut points against B3 outcomes or cherry-pick fights.

### B5 — Explicit pressure/vulnerability alignment

B5's definition includes submission pressure versus submission vulnerability. Arm C improved its mean prediction from 45.95% to 48.06%, lowered conditional LL from 0.706751 to 0.682100, and narrowed the mean gap from 8.98 to 6.87 percentage points. This is consistent with directional attacker/defender alignment capturing a mechanism already closer to SUB creation and opponent exposure.

**Limits:** Attempts faced remain confounded by available ground opportunity. B5's 355 finishes are more than B3's 224 but do not provide abundant fighter-level conversion trials. Its residual calibration gap may still involve unmeasured grounded opportunity.

### At most two future hypotheses

**Hypothesis A — Opportunity-normalized submission creation.** Strict-prior SUB attempt propensity normalized by a defensible grounded/control exposure measure contains information beyond takedown access and SUB attempts normalized by general fight time. Its first target is B3. It fails feasibility if exposure is missing, definitionally unstable, or unsupported in early chronological folds.

**Hypothesis B — Competing grounded offense.** Conditional on access, the relative tendency toward SUB creation versus ground striking distinguishes SUB-oriented grappling from control/GnP. It fails feasibility if ground strikes are incomplete, lack a comparable denominator, or merely duplicate existing broad striking signal.

Neither hypothesis licenses immediate retraining or unrestricted feature search.

## External data feasibility and bookmaker benchmark

### Build versus source

Do **not** purchase or integrate a general-purpose commercial feed yet. The exact missing variable to resolve is trustworthy historical **ground-state/control exposure**, potentially with position transitions if proven necessary.

| Candidate source | Possible incremental contribution | Verification needed | Decision |
|---|---|---|---|
| Existing governed F01/F02 | TD/SUB attempts, outcomes, striking, elapsed exposure | Determine whether unused raw fields permit grounded denominator | **Use first** |
| Repository FightMetric/position-time material | Potential duration/position data | Exact paths, definition, vintage, coverage, ID mapping, rights | **Audit before outside acquisition** |
| Official UFCStats detail | Existing public basis for UFC statistical variables | Confirm exact missing field, historical definitions and permissible use | Conditional on repo gap |
| Alternate public play-by-play | Potential event/timing transitions | Reproducibility, historical coverage, provenance and usage terms | Only for a defined missing variable |
| Commercial MMA feeds | Potential richer positional and timing coverage | Provider field spec, full backfill, licensing, stable IDs, snapshots | No generic purchase recommendation |
| Manual historical annotation | Position/transition observations | Huge cost and reproducibility burden | Small feasibility proof only, if needed |

A proposed source must document field definitions, earliest available date, UFC coverage by year, fighter and bout identifiers, revisions, missingness, timestamps, whether prior-to-fight reconstruction is possible, export/snapshot options, and permissible research/model-development usage. A claim of “advanced MMA analytics” without such evidence is not enough.

The research did **not** complete a comprehensive independently verified vendor-by-vendor documentary audit; historical control-time depth, proprietary feed fields, and licensing remain unresolved. Holmes et al. show aggregate statistics can support a simplified state model but position-level simulation needs richer information. [1]

### Bookmaker method-of-victory probabilities as an independent benchmark

Holmes et al. compare their model with bookmaker odds, showing the relevance of a market benchmark. [1] No verified public evidence establishes that professional sportsbooks use any particular private Markov simulator or proprietary state model.

A later, independent question is whether historically contemporaneous no-vig MOV prices assigned more submission probability to B3-type fights than UFC EDGE did. For decimal prices `d_i`, naïve implied probability is `q_i = 1/d_i`. For a **complete, mutually exclusive** partition, simple multiplicative no-vig normalization is `p_i = q_i / Σ_j q_j`. A market may include fighter-specific A_KO, A_SUB, A_DEC, B_KO, B_SUB, B_DEC and perhaps draws/other. Removing vig from an incomplete pair of prices is misleading.

Requirements: consistent pre-specified timestamps, full outcome partition or principled treatment of missing outcomes, source/book identification, stale-line handling, opening versus closing distinction, awareness of liquidity and method-market margins. This is an **external diagnostic benchmark only**, never a MOV1 training feature and not ROI/EV research.

## Statistical feasibility

The modern universe has 1,010 submissions, but prior-only training periods contain fewer. The relevant conversion support at fighter `i` and historical prediction time `t` is prior attempts `n_(i,t)`, not the full 1,010 outcomes. Defensive support is the fighter's prior attempts faced. These are often zero/small. Holmes et al.'s fighter-ability shrinkage addresses the general sparse-technique problem. [1]

Candidate rates must preserve counts, denominator, exposure and uncertainty. An audit should tabulate every chronological outer training boundary rather than claiming full-sample feasibility:

| Candidate | Nonmissing fighters | Zero numerator | Median denominator | Low-support share | Debut share | Earliest reliable era |
|---|---:|---:|---:|---:|---:|---|
| SUB ATT / grounded minute | To audit | To audit | To audit | To audit | To audit | To audit |
| SUB ATT / TD landed | To audit | To audit | To audit | To audit | To audit | To audit |
| SUB finish / SUB ATT | To audit | To audit | To audit | To audit | To audit | To audit |
| Ground-strike ATT / grounded minute | To audit | To audit | To audit | To audit | To audit | To audit |
| Opponent SUB ATT / opponent exposure | To audit | To audit | To audit | To audit | To audit | To audit |

Distinguish three cases: (1) no prior UFC history, which calls for a population prior; (2) history but no relevant opportunity/exposure, which is substantive about style without identifying conversion; (3) observed opportunity with zero successes, which is evidence but still needs shrinkage. Do not turn all three into a naked zero or generic imputation.

Measurement error is also structural: TD landed is not stable control; SUB ATT is not standardized opportunity quality; CTRL time is not time in a finish-capable position; ground significant strikes are not equivalent to all ground-and-pound. These caveats require explicit governance.

## Simulator implications

A possible *conceptual* progression is standing → ground access → ground exposure, then competing submission opportunity, ground striking, return to standing and round expiration, with SUB and KO/TKO as finish outcomes. This is exploratory, not a frozen simulator specification.

A reduced mechanistic factorization can be written illustratively as `P(SUB) = P(G) × P(SO | G) × P(SUB finish | SO)`, with `G` genuine ground exposure and `SO` submission opportunity. It cannot be responsibly estimated as a mechanistic model if those states are unobserved or indefensibly proxied.

| Stage | Supportable scope |
|---|---|
| Current MOV0/MOV1 | Finish probability plus conditional finish method |
| Next | Audit of ground opportunity and competing grounded offense |
| Possible intermediate | Small conditional pathway or competing-risk specialist using verifiable observables |
| Later | Ground-state transition model |
| Only if richer records exist | Position-specific semi-Markov/event-driven simulator |

Holmes et al. provide a conceptually useful state-model example *and* warn, through their simplified generic ground state, against claiming unobserved positional detail. [1]

## Recommended path

### Research priorities (practical value, data availability, scientific testability — not a model leaderboard)

| Priority | Target | Practical value | Availability | Testability | Decision |
|---|---|---|---|---|---|
| **1** | Reconstruct grounded exposure; normalize SUB creation | Very high | Unknown, possibly in repository | High if provenance established | **Immediate milestone** |
| **2** | SUB versus grounded-strike activity per common exposure | Very high | Partial/likely | High if denominator survives | Same audit |
| 3 | Smoothed SUB conversion conditional on attempts | High | Numerator/attempts exist | Restricted by sparse history | Assess support only |
| 4 | Opponent opportunity suppression/conversion defense | High | Partial | Moderate | After denominator audit |
| 5 | Historical market MOV benchmark | Diagnostic | External odds required | High once obtained | Separate later work |
| 6 | Commercial positional data acquisition | Potentially high | Unverified | Vendor dependent | Only after exact deficit established |
| 7 | Full Markov/semi-Markov simulator | Long-term high | Not established | Low now | Premature |
| 8 | Fourth generic MOV1 classifier | Low information gain | Existing F02 | Easy but weak research value | Do not pursue now |

### One immediate milestone

**UFC_EDGE_GROUND_OPPORTUNITY_AND_COMPETING_PATHWAY_DATA_AUDIT_V1**

One decisive question: **Can strict-prior history measure what fighters do per unit of genuine grounded opportunity well enough to distinguish submission creation from control/ground-and-pound?**

Attempt defensible `SUB ATT / grounded minute`, fallback (explicitly labeled proxy) `SUB ATT / TD landed`, and parallel `GROUND STR ATT / grounded minute` or a comparable denominator. Evaluate `SUB finishes / SUB ATT` **support** but do not lead with conversion unless support proves sufficient. If data survives lineage and early-fold checks, authorize a separate frozen mechanistic experiment; if not, specify precisely the missing historical per-fighter ground/control duration and minimum era/coverage requirements before investigating external acquisition.

## Copyable next GitHub handoff

```text
UFC EDGE — GROUND OPPORTUNITY & COMPETING PATHWAY DATA AUDIT V1

PURPOSE
Determine whether existing governed UFC EDGE history distinguishes
submission-oriented grappling from control/GnP-oriented grappling without
training or modifying any predictive model. This is a source-lineage,
chronology, coverage and statistical-feasibility audit only.

AUTHORITATIVE START
Repository: Tkcool28/ufc-edge
Required anchor: 3e2b14a8391ed17d072b4bbb9570b31bc6d12b85
1. Read the live main HEAD commit SHA and compare it with the anchor.
2. If advanced, list intervening commits relevant to F01/F02, grappling,
   position-time/FightMetric research, MOV1 or simulator research.
3. Never substitute a git tree SHA for the commit SHA.

READ FIRST
Inspect PRs #123–#125 and the PR #125 run_v1 report directory:
models/challengers/mov1_three_arm_directional_run_v1/run_v1/
Required files:
FINAL_REPORT.md
FOCUSED_B3_DIAGNOSTIC.md
FOCUSED_B5_DIAGNOSTIC.md
B1_B5_PATHWAY_COMPARISON.md
STRIKING_PRESERVATION_REPORT.md
SCIENTIFIC_INTERPRETATION_REPORT.md
ANNUAL_COMPARISON.md
COMPLETE_SYSTEM_COMPOSITION_REPORT.md
FORWARD_CONFIRMATION_READINESS_REPORT.md
Also locate and inspect all relevant FightMetric, position-time,
control-time, ground-position, UFCStats-source and simulator-feasibility
artifacts; cite their actual paths and definitions.

CENTRAL QUESTION
Can genuine grounded opportunity, rather than total fight exposure,
be reconstructed strictly from prior history?

SOURCE LINEAGE
Trace raw source through governed fighter state for:
- takedown attempts and landed;
- takedown conversion and opponent TD attempts/defense;
- submission attempts created/faced and submission finishes;
- total elapsed fight exposure;
- ground significant-strike attempts/landed;
- control/ground duration, position time, reversals or stand-ups if present.
For each: raw definition and path; transformations; career/recent windows;
denominator; shrinkage; imputation; missingness; earliest reliable date;
strict-prior availability; fighter orientation. Do not change F01/F02.

GROUND-EXPOSURE FEASIBILITY
Check actual ground/control minutes or seconds, ground entries, and
completed takedowns (only as clearly labeled fallback proxy).
For each chronological outer training boundary report eligible fighters/
fights, nonmissing numerator/denominator, zero denominator, median and
10th/25th/75th/90th percentile denominator, debuts, division and era.
Do not call a proxy actual ground exposure without semantic justification.

CANDIDATE MEASURES — DATA FEASIBILITY ONLY
1. SUB attempts / grounded minute, if defensible.
2. SUB attempts / completed TD as fallback.
3. Ground strikes attempted / grounded minute on matching exposure.
4. SUB finishes / attempts, with support preserved.
5. Opponent SUB attempts / grounded opportunity faced, if reconstructible.
No naked rates without numerator and denominator support.

B3 AND B5
Do not change frozen definitions/thresholds or train a model.
Describe separately whether strict-prior histories reveal heterogeneous
high-SUB/low-GnP, low-SUB/high-GnP, high-control/low-finishing, or
high-access/low-sustained-opportunity styles. No outcome-optimized cuts,
replacement archetypes or anecdotal fight selection.

CONVERSION SUPPORT
Per outer fold, report shares of fighters with prior SUB attempts in
0, 1, 2–4, 5–9 and 10+ bins, and repeat for attempts faced.
Assess whether fighter-level conversion would mostly reflect a prior.

FIGHTMETRIC / POSITION-TIME DECISION
Resolve exact source/path, field semantics, historical depth, fighter/bout
ID matching, missingness by era, reproducibility today, pre-fight temporal
availability, rights/licensing and genuinely incremental data versus F02.
If the source cannot support reliable exposure, state that directly.

REQUIRED RESEARCH OUTPUTS
GROUND_OPPORTUNITY_SOURCE_LINEAGE.md
GROUND_EXPOSURE_COVERAGE.md
EARLY_FOLD_SUPPORT_REPORT.md
B3_MECHANISM_HETEROGENEITY.md
B5_MECHANISM_HETEROGENEITY.md
SUBMISSION_CONVERSION_SUPPORT.md
FIGHTMETRIC_POSITION_TIME_DECISION.md
NEXT_EXPERIMENT_FEASIBILITY.md
Machine-readable CSV/JSON coverage tables must accompany the reports.

NEXT_EXPERIMENT_FEASIBILITY.md must conclude exactly one:
A — EXISTING DATA SUFFICIENT FOR FROZEN MECHANISM EXPERIMENT
B — EXTERNAL GROUND-EXPOSURE SOURCE REQUIRED
C — CURRENT INFORMATION CANNOT SUPPORT THE PROPOSED DISTINCTION
If A, report candidate measurements/support but do not train.
If B, specify exact missing field and required minimum historical coverage.

GUARDRAILS
No MOV0/MOV1 retraining; no F02 change; no B3/B5 revision; no
prospective confirmation unsealing; no PR #125 promotion; no sportsbook
features; no ROI/EV; no threshold optimization or unrestricted search;
no simulator implementation; no unrelated MOV0 fitted-record recovery.
Preserve PR #125 as developmental historical evidence.

SUCCESS CRITERION
Answer whether UFC EDGE can measure submission creation versus
control/GnP per unit of genuine grounded opportunity under strict prior
chronology. Predictive-performance results are not required.
```

## Source record and limitations

### Repository primary sources

- Repository: `Tkcool28/ufc-edge`; reference anchor `3e2b14a8391ed17d072b4bbb9570b31bc6d12b85`.
- PR lineage: #113 and #117–#125; most directly #123 (directional audit), #124 (three-arm contract), #125 (implementation and run).
- PR #125 main report: `models/challengers/mov1_three_arm_directional_run_v1/run_v1/FINAL_REPORT.md`.
- Associated B3, B5, pathway, striking, scientific interpretation, annual, composition and forward-readiness reports named in the inventory above.
- The repository tree contains position-time/FightMetric-related research, but exact path/coverage was not preserved in the research record. Audit target, not verified usable field.
- Observed tree SHA `78f1a67bf1735975c0bab34d63fb6ae230cd1215`; **not** a live HEAD commit SHA. Current main-commit comparison remains open.

### External scientific reference

[1] Holmes, B., McHale, I. G., & Żychaluk, K. (2023). *A Markov chain model for forecasting results of mixed martial arts contests.* International Journal of Forecasting, 39(2), 623–640. DOI: https://doi.org/10.1016/j.ijforecast.2022.01.007

[2] University of Liverpool repository record: https://livrepository.liverpool.ac.uk/3154619/

[3] ScienceDirect article: https://www.sciencedirect.com/science/article/pii/S0169207022000073

**Research limits:** External-source analysis obtained in the completed report was concentrated on the Holmes paper, not a finished vendor-by-vendor and broad peer-reviewed survey. Do not treat specific commercial-feed licensing, historical control-time availability, bookmaker archive quality, or positional backfill as verified. This does not prevent the immediate recommendation: answer the existing-source exposure question first, and let an actual negative finding specify any external data requirement.

> **Practical conclusion:** Determine whether UFC EDGE can measure submission creation and ground striking per unit of genuine grounded opportunity. Do not build another generic classifier, buy an unspecified MMA feed, or build the simulator first.
