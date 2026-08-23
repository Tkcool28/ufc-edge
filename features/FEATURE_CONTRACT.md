# UFC Edge FEATURES — F00 Feature Contract / Architecture

Status: **AUTHORITATIVE F00 DRAFT**

Feature contract version: **0.1.0-draft**

Frozen DATA contract: **0.4.0-draft**

DATA freeze: `provenance/data_phase_freeze_v0.json`

F00 defines the shared feature language for UFC Edge before production feature materialization. It describes the fight-generating process first; downstream models consume tagged subsets of one shared contract. F00 does not train models, create feature matrices, add sportsbook data, or build the simulator.

## 1. Boundary and future materialization flow

```text
frozen canonical observations (`data/canonical/v0/`)
        + frozen DATA semantics/provenance
        ↓
strict point-in-time historical eligibility
        ↓
independent fighter state at prediction_as_of
        ↓
deterministic fighter orientation + matchup join
        ↓
matchup interactions + known pre-fight context
        ↓
model-selected contract subset
        ↓
target attachment (training tables only)
```

Feature code may interpret canonical DATA through the frozen contract/provenance, but it may not read `data/raw/`, provider-specific layouts, RAW_QA_ONLY artifacts, or quarantined pre-F00 feature outputs. If canonical v0 cannot support a desired concept honestly, the catalog marks it `PROXY_ONLY`, `DEFERRED`, `UNSUPPORTED`, or `RESEARCH_ONLY`; FEATURES does not silently reopen DATA.

The concept catalog is authoritative. A materialized column is a deterministic projection of a concept plus approved variants; it is not a new definition.

## 2. Fighter state

A fighter state is a reusable, opponent-independent summary of one fighter using only information available strictly before `prediction_as_of`.

It may contain:

- supported historical performance;
- numerator/denominator exposure and support;
- approved persistence/form variants;
- stable or point-in-time context that belongs to that fighter rather than the current opponent.

The base state never bakes in the current opponent. Historical result fields such as prior method or prior outcome may contribute only from contests strictly before the target cutoff. Current-fight result, method, finish round/time, or round statistics are targets/post-fight observations and are forbidden predictors.

The initial state families cover striking creation/prevention, knockdown creation/vulnerability, wrestling entry/conversion/prevention, exact general control creation/allowance, submission-attempt activity, reversals, pace/persistence, historical method outcomes, durability proxies, physical context, and exposure/support.

## 3. Matchup feature

A matchup feature is a deterministic interaction of two already-built point-in-time fighter states and/or known pre-fight context.

Examples:

- strike creation versus opponent strike prevention;
- takedown pressure versus opponent takedown defense;
- control creation versus opponent control allowed;
- submission-attempt pressure versus opponent attempts faced;
- pace mismatch;
- knockdown creation versus vulnerability;
- reach difference.

Opponent-specific information is never stored in the base fighter-state row. This separation permits replay, reuse, audit, and later opponent-adjusted state without circular joins.

## 4. Deterministic fighter orientation

Canonical `fights.fighter_a_id` / `fighter_b_id` is transport context, not model meaning.

F00 modeling orientation is:

- `fighter_1_id = min(canonical fighter_id)` under bytewise/lexicographic string order;
- `fighter_2_id = max(canonical fighter_id)`;
- state columns join as `fighter_1_*` and `fighter_2_*`;
- directional interactions emit both directions where needed;
- signed deltas are always `fighter_1 - fighter_2` with that sign convention documented.

A later model may perform paired/symmetric augmentation, but that is training behavior rather than authoritative feature orientation. Red/blue/provider side is never a predictor by construction.

## 5. Point-in-time semantics

All predictive concepts declare an information cutoff rule.

1. Historical contests must have canonical event date strictly before the target cutoff unless a future DATA migration supplies trusted intra-day chronology proving availability before the cutoff.
2. Canonical v0 does not freeze trustworthy early-tournament bout order, so same-day prior contests are excluded rather than guessed.
3. Rankings and mutable profile snapshots must be observed strictly before `prediction_as_of`; nearest-future joins are forbidden.
4. Weigh-in observations may be used only when explicit canonical semantics prove they were available before the cutoff. F00's first structured weight concept uses prior-fight scale observations; it does not assume the current-fight weigh-in is known.
5. Historical opponent state for opponent adjustment is rebuilt as of immediately before that historical contest; the opponent's future career is forbidden.
6. Population priors used for shrinkage must themselves be fit using information available before the target cutoff in replay/backtest mode.
7. Simulator/component realized round observations are training labels only. They attach after the pre-fight predictor state is built and may not leak into that same fight's predictors.

## 6. Historical windows

Windows are contract variants, not automatically generated for every concept.

| Window | Definition |
| --- | --- |
| `career` | All eligible prior observations for the concept. |
| `last3` | Up to the three most recent eligible prior contests. If an unresolved same-date boundary would require inventing order, the window is unavailable. |
| `last5` | Same rule using up to five contests. |
| `ewma_365d` | All eligible prior observations weighted by `2 ** (-age_days / 365)`. The 365-day half-life is a mechanical F00 baseline, not a tuned hyperparameter. |

Each concept opts into only variants with an identified consumer and sufficient support. F00 deliberately does not create UFC-only and all-promotion duplicates for every feature.

Historical result/experience concepts may use all clean canonical supported-promotion fights. Round-stat concepts use only contests with the needed canonical round observations. An external-promotion fight without canonical round statistics can contribute to eligible result history but never contributes fabricated zero round statistics.

Round-specific state is opt-in and initially limited to `r1`, `r2`, and `r3plus` where the concept and sample support it. `round=0` is never a real round.

## 7. Rates, denominators, and exposure

A rate is invalid until its numerator, denominator, eligibility, zero-denominator behavior, missing-denominator behavior, and minimum support are explicit.

Primary exposure types are:

- elapsed eligible fight/round seconds for event rates;
- attempted events for conversion/accuracy/defense probabilities;
- landed/absorbed events for explicitly named efficiency proxies;
- eligible prior fights for historical result/method rates;
- observed opportunities only where canonical DATA actually supplies an opportunity count.

Examples:

- significant strikes landed per minute = observed significant strikes landed / eligible observed elapsed minutes;
- takedown success = takedowns landed / takedowns attempted, not takedowns landed / fights;
- submission-attempt rate = attempts / eligible elapsed fight minutes in v1; exact ground-opportunity rate is unsupported because exact ground minutes are not canonically observed;
- control rate = exact `control_sec` / eligible elapsed fight seconds; `control_sec` is **not** ground time;
- strike defense = `1 - opponent_landed / opponent_attempted` over compatible observed coverage.

A round contributes to a domain only when fields required by that concept are observed. Missing fields never borrow generic full-fight exposure and never become zero.

## 8. Missingness and zero

F00 preserves five semantic states:

- `observed_positive` — observed non-zero value/support;
- `observed_zero` — measured opportunity/count with value zero;
- `missing_observation` — canonical observation unavailable;
- `not_applicable` — concept has no meaning for that row;
- `insufficient_exposure` — observations exist but do not meet declared minimum support for a raw estimate.

Examples: zero takedown attempts makes raw takedown success undefined/null, not 0%; a missing takedown-attempt observation is separately missing; zero submission attempts over observed eligible exposure is a legitimate zero submission-attempt rate.

Future materializers must retain enough support/denominator lineage to distinguish these cases. They need not generate a separate missing-indicator column for every feature concept.

## 9. Small-sample shrinkage and debutants

F00 defines simple reproducible empirical-Bayes-style shrinkage families; it does not implement a full Bayesian system.

Population prior hierarchy:

- use weight class when at least 100 eligible historical fights exist strictly before the cutoff;
- otherwise use the global eligible historical population;
- do not infer an unsupported sex hierarchy.

Mechanical prior strengths:

- event/time rates: 15 equivalent eligible minutes;
- attempt/conversion probabilities: 20 equivalent attempts/opportunities;
- compositional shares: 30 equivalent events;
- fight-result/method rates: 6 equivalent fights.

These are contract semantics, not tuned values. Changing them after materialization begins requires a versioned contract change.

A true debutant with known zero personal history has `prior_fight_count = 0` and may receive the applicable population-prior estimate with zero personal support. A fighter whose historical source coverage is missing is **not** silently treated as a debutant and is not filled with a population prior merely to avoid nulls.

## 10. Opponent adjustment — V2 architecture

Opponent adjustment is postponed to `V2_OPPONENT_ADJUSTED`, but its leakage-safe definition is frozen now.

For every historical contest `H` contributing to fighter state at target time `T`:

1. build the historical opponent's state using only observations strictly before `H`;
2. calculate expected performance in `H` from that pre-`H` opponent state and the fighter's actual compatible exposure/opportunities in `H`;
3. calculate actual-minus-expected residual, or expected-minus-actual for suppression features with sign documented;
4. aggregate residuals over the chosen window using compatible exposure/opportunity weights;
5. never recompute the historical opponent using information learned after `H`.

Planned V2 families include significant-strike creation above expectation, strike suppression above expectation, takedown creation above expectation, control creation above expectation, and submission-attempt creation above expectation.

This is chronological opponent adjustment, not retrospective opponent-career strength.

## 11. Context policy

Core structured context is conservative:

- age at fight from canonical DOB and target event date;
- layoff from the most recent eligible prior canonical fight;
- canonical height/reach when present;
- scheduled rounds, title-bout flag, and weight class when known before cutoff;
- prior explicit scale-weight observations under canonical point-in-time semantics.

Mutable UFC profile snapshots are never backfilled into earlier fights. Rankings remain dated observations and are not treated as already-computed fighter quality. In F00 rankings are `RESEARCH_ONLY`, keeping external ranking consensus out of Model 0/1 core state.

Canonical stance is `PROXY_ONLY` because it is not a dated stance history and switch-stance behavior is not represented.

## 12. Simulator/component boundary

F00 identifies component quantities but does not build a simulator.

Aggregate canonical observations can later support component models for:

- strike-event intensity;
- knockdown-hazard proxy;
- takedown-attempt intensity;
- takedown success conditional on attempt;
- submission-attempt intensity;
- round/time persistence effects.

F00 does **not** claim support for:

- exact knockdown recovery sequences;
- exact finish conversion after a knockdown;
- exact submission finish probability conditional on threat/position;
- exact escape/reversal hazard conditional on state;
- exact standing or ground minutes;
- exact chronological state-transition matrices.

FightMetric positional data may support only quantized interval/profile proxies. Bucket bounds are not observed exact seconds. Greco exact `control_sec` remains authoritative for general control and is not converted into ground time.

Long-term environment mapping:

1. **distance striking** — significant distance/head/body/leg flow and prevention;
2. **pocket/clinch striking** — clinch significant-strike flow plus coarse positional context where supported;
3. **wrestling entry** — takedown attempts, conversion, attempts faced, defense;
4. **ground/control** — exact general control, reversals, ground significant strikes, quantized position proxies;
5. **submission environment** — submission attempts/faced plus control and wrestling context without invented exact threat sequences.

## 13. Targets and leakage separation

Targets are separate from predictors in `feature_catalog.yaml` and governed by `leakage_registry.yaml`.

Initial target families:

- winner/result;
- finish method;
- KO/TKO;
- submission;
- decision;
- finish round;
- finish time within terminal round.

Targets attach only after the prediction feature row is complete. Historical result/method fields may support historical summaries only when explicitly scoped `historical_only`; the same fields from the current target fight are forbidden.

F00 does not derive global total elapsed fight duration across all eras/promotions because canonical v0 does not expose a bout-level round-length/rule-set field sufficient to make one formula safe everywhere. That concept is `DEFERRED`.

Sportsbook odds, implied probability, line movement, ROI, CLV, and method prices are outside the core feature contract.

## 14. Statuses and consumers

Allowed statuses:

- `V1_MUST`
- `V1_DERIVED`
- `V2_OPPONENT_ADJUSTED`
- `SIMULATOR_COMPONENT`
- `RESEARCH_ONLY`
- `PROXY_ONLY`
- `DEFERRED`
- `UNSUPPORTED`

Allowed consumers:

- `model0`
- `model1`
- `tree`
- `component_striking`
- `component_wrestling`
- `component_ground`
- `component_submission`
- `component_durability`
- `simulator`
- `human_research`

Models select concepts by consumer/status tags from one catalog. They may not create a private alternative definition with the same semantic name.

## 15. Materialized naming

The future materializer generates deterministic names from concept, component where vector-valued, approved window, optional round band, and estimator semantics. The validator enumerates names before any data is written and fails on collisions.

```text
<layer_prefix>__<feature_name>[__<component>][__<round_band>][__<window>][__<estimator>]
```

Layer prefixes are `fs` fighter state, `ctx` context, `oa` opponent adjusted, `mx` matchup interaction, and `sim` simulator component. Historical rate concepts use `shrunk` when the declared shrinkage policy applies, otherwise `raw`.

Support/numerator/denominator lineage must remain available to audit a materialized estimate even when a model matrix selects only the estimate and a compact support subset.

## 16. Provenance requirement

A future materialization manifest must record at minimum:

- feature-contract version and catalog/schema/leakage-registry hashes;
- frozen DATA contract version and freeze-file identity;
- prediction cutoff semantics;
- canonical table/field lineage for every concept;
- window and shrinkage policy versions;
- orientation policy version;
- materialized-name list;
- materializer code SHA and run timestamp.

No provider-specific raw source path belongs in feature lineage. Canonical field provenance remains available through the DATA layer when source-level audit is needed.

## 17. Versioning

`0.1.0-draft` is reviewable architecture, not a frozen production matrix.

- Before first production materialization, reviewed draft additions/corrections increment the draft contract version explicitly.
- After materialization begins, changes to formula, denominator, cutoff, shrinkage, naming, orientation, or missingness require a new contract version and materialization manifest.
- Pure documentation/validator corrections that do not change semantics may use a patch increment.
- Breaking removals/renames or incompatible row/materialization semantics require a major version.

Meanings are never silently mutated in place.

## 18. Architecture self-review checkpoint

F00 performed the required self-review before expanding the catalog and made these corrections:

1. **Prior art hard-wired implementation too early.** The quarantined contract tied concepts to concrete `features/v0` tables and broadly generated windows. F00 makes concepts authoritative and variants opt-in.
2. **Provider A/B orientation was unsafe.** F00 replaced it with canonical-ID ordering and explicit directional interactions.
3. **`control_sec` could have been overstated.** It is defined as general control only; it never becomes ground time or a submission-opportunity denominator.
4. **Historical target fields need scope, not a blanket ban.** Prior method/result history is useful, but current-fight labels leak. F00 adds explicit time scope and validates the distinction.
5. **Current-fight weigh-in availability was too easy to assume.** V1 structured weight context is limited to provably prior observations; current-event timing is deferred.
6. **Rankings could become a hidden quality prior.** Rankings remain dated and `RESEARCH_ONLY` instead of feeding Model 0/1 automatically.
7. **Opponent adjustment could leak through retrospective opponent careers.** F00 requires nested historical as-of opponent state before any V2 implementation.
8. **External-promotion history could be mistaken for zero UFC-style stats.** Outcome/experience eligibility is separate from round-stat eligibility.
9. **Small samples and missing data could collapse together.** True debutants can receive a prior while source-missing histories remain missing.
10. **FightMetric buckets could masquerade as exact state time.** Only quantized interval/profile proxies are permitted.
11. **Variant count could explode.** Recent/EWMA/round variants need a named consumer/support rationale; they are not generated universally.
12. **Simulator precision could outrun observation precision.** Exact transitions, knockdown recovery, and submission-threat conversion are explicitly unsupported under frozen DATA.
13. **Validator wording was initially too literal.** GitHub CI rejected semantically valid `strictly-before`/`strictly pre-H` wording; the validator now normalizes equivalent strict-prior wording without weakening chronology.
14. **Simulator training labels needed an explicit boundary.** Realized same-fight round outcomes may be component-training labels after predictor construction, but simulator components cannot be baseline Model 0/1/tree requirements and cannot enter the same fight's pre-fight state.

After these corrections, fighter state and matchup interactions are separate; targets are isolated; predictive features are as-of; rates declare denominators; zero/missing are distinguishable; shrinkage/debutants are explicit; opponent adjustment is chronological; orientation is provider-neutral; external promotions are deliberate; coarse positional fields remain coarse; profiles/rankings are point-in-time; no core concept requires raw/provider layouts; variants are opt-in; and the repository remains understandable from this document plus the machine-readable contract files.

## 19. Answers to the 17 F00 architecture questions

1. **What is fighter state?** Opponent-independent pre-fight historical state at a declared cutoff.
2. **What is a matchup feature?** Deterministic interaction of two independent fighter states/context.
3. **What historical windows exist?** Career plus opt-in last3, last5, 365-day EWMA, and sparse opt-in round bands.
4. **How are rates normalized?** Explicit numerator/denominator/eligibility with no implicit denominator substitution.
5. **How is exposure represented?** Elapsed seconds, attempts/opportunities, landed/absorbed events, or fight counts according to concept.
6. **How are small samples shrunk?** Versioned population-prior shrinkage by weight class when supported, otherwise global.
7. **How are debutants handled?** Known zero personal support plus population prior, never conflated with missing history.
8. **How is missingness represented?** Observed positive, observed zero, missing, not applicable, insufficient exposure.
9. **How is opponent adjustment defined?** Historical actual-minus-expected residual using the opponent's strictly pre-contest state.
10. **How is fighter ordering defined?** Lexicographically sorted canonical fighter IDs; no provider/red-blue meaning.
11. **Which concepts are V1?** Foundational striking, wrestling/control/submission activity, durability/pace/history, context, and a small set of deterministic matchup interactions.
12. **Which wait for V2?** Chronological opponent-adjusted creation/suppression families.
13. **Which are simulator-specific?** Event intensities/probabilities and persistence components; no simulator is built in F00.
14. **Which are research-only?** Rankings/profile narrative, camp/coaching, injury, short-notice, qualitative weigh-in, travel and similar human-handicap inputs.
15. **Which are unsupported?** Exact sequence/state quantities not observed canonically, including exact KD recovery/conversion and exact ground/standing time.
16. **How will a later materializer consume this?** Load/validate the versioned catalog, build PIT fighter states, orient/join matchups, create allowed variants, attach targets only for training, and emit a versioned manifest.
17. **How do models select subsets?** Consumer/status tags from the shared catalog; no model-specific feature silos.
