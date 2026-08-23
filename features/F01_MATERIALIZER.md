# F01 — V1 Point-in-Time Fighter State Materializer

Status: **F01 implementation draft**

Authoritative semantics remain F00 `features/feature_catalog.yaml` version `0.1.1-draft`. F01 implements that contract; this document records implementation choices and validation boundaries without redefining feature meaning.

## Scope

```text
frozen canonical DATA
→ canonical history index
→ strict point-in-time eligibility
→ concept/component sufficient statistics
→ contract-approved windows
→ point-in-time population priors/shrinkage
→ auditable fighter state
→ canonical-ID matchup assembly
→ consumer projection
```

No model training, V2 opponent adjustment, simulator modeling, sportsbook input, web research, raw-provider recovery, DATA migration, or committed historical feature matrix is part of F01.

## Contract selection

F01 selects exactly `V1_MUST` and `V1_DERIVED`, optionally intersected with a consumer tag. It excludes `V2_OPPONENT_ADJUSTED`, `SIMULATOR_COMPONENT`, `PROXY_ONLY`, `RESEARCH_ONLY`, `DEFERRED`, and `UNSUPPORTED`.

The executable implementation registry must equal the contract-selected V1 set. A newly promoted V1 concept therefore fails closed until reviewed implementation exists.

Current active concepts (18):

- `prior_fight_count`
- `sig_strike_efficiency`
- `sig_target_mix`
- `sig_environment_mix`
- `knockdown_efficiency`
- `takedown_conversion`
- `finish_method_win_profile`
- `finish_method_loss_profile`
- `early_finish_profile`
- `age_at_fight`
- `layoff_days`
- `physical_size_profile`
- `scheduled_rounds`
- `title_bout`
- `weight_class`
- `prior_scale_weight_lbs`
- `knockdown_creation_vs_vulnerability`
- `reach_difference_cm`

The contract-derived core V1 vocabulary is 58 names: 53 fighter/context state names plus 5 matchup-interaction names.

## Modules

- `history.py` — canonical CSV indexing, strict date eligibility, recent-window tie policy, EWMA weights, prior explicit scale-weight lookup.
- `aggregations.py` — component-specific sufficient statistics, weighted pooling, mechanical shrinkage, support/missingness state.
- `state.py` — active concept implementations, PIT priors, auditable fighter state, central orientation and matchup interactions.
- `materializer.py` — public API, contract checks, deterministic selection, bounded real-data validation and provenance manifests.
- `tools/features/materialize_v1.py` — bounded CLI; stdout by default, no implicit output hierarchy.

F01 deliberately keeps one reference-correct implementation. An optimized replay engine should only be introduced later with equivalence tests if profiling justifies it.

## Fighter-state grain

Historical state identity is `fighter_id + prediction_as_of`. Target-bout context requires `target_fight_id`, so a complete pre-fight row may additionally carry that context key. Historical fighter state remains opponent-independent; matchup assembly occurs only after both fighter states are built at the same cutoff.

## Point-in-time and ordering

F01 treats canonical `events.event_date` as the trustworthy chronology boundary.

For target cutoff date `T`:

- only fights with `event_date < T` enter history;
- the target fight and every same-date fight are excluded;
- intra-day order is never inferred from `fight_id`, provider side, row order, or CSV order;
- current target winner/result/method/finish/round-stat fields do not enter predictors;
- rankings/profile snapshots are not selected into core V1;
- current-fight weigh-in context remains deferred.

`last3` / `last5` operate on concept/component-eligible fights. A same-date group is accepted only if the whole tied group fits in the remaining slots. If it crosses the N-fight boundary, the window is unavailable and returns `missing_observation` with an explicit ambiguity reason. `fight_id` may order a fully included tied group only for stable serialization; it never decides membership.

Career/EWMA do not require tie order. Same-date observations receive the same EWMA age.

## Windows and sufficient statistics

Variants are read from each concept's F00 flags; F01 does not auto-expand windows.

- `career`: all concept-eligible strict-prior observations.
- `last3`: up to three most recent eligible fights, with tied-boundary fail-closed behavior.
- `last5`: analogous five-fight window.
- `ewma_365d`: `2 ** (-age_days / 365)`.

EWMA applies weights to numerators and denominators separately. F01 never averages already-computed per-fight percentages when pooled sufficient statistics exist.

Support is component-specific. This matters for paired quantities: significant-strike accuracy and defense have different attempt denominators; knockdown creation/vulnerability have different landed-strike denominators; takedown success/defense have different attempt denominators.

## Missingness and audit state

Every materialized value has an `AuditValue` carrying:

- column and source concept
- component/window
- model-facing value
- one of the five F00 missingness states
- personal numerator and denominator/support
- posterior denominator where applicable
- contributing fight/observation counts
- shrinkage rule
- prior source/value
- contributing fight IDs
- explicit reason when unavailable

States remain distinct:

- `observed_positive`
- `observed_zero`
- `missing_observation`
- `not_applicable`
- `insufficient_exposure`

Examples:

- 0 TD landed from 4 observed attempts → raw conversion 0, real observed zero.
- 0 observed TD attempts → raw conversion undefined; denominator support 0, not a failed conversion rate.
- prior fights but no compatible round-stat rows → missing observation, not zero-filled statistics.
- layoff with no prior canonical fight → not applicable.

## Zero canonical history versus true debut

F00 permits a population-prior estimate for a **known true debutant**, but canonical v0 does not expose a historical-completeness/debut flag. Therefore F01 does **not** equate `prior_fight_count == 0` with a proven MMA debut.

For a resolved fighter with zero strict-prior canonical fights:

- `prior_fight_count` is legitimately observed zero for the canonical history count;
- rate/composition personal support remains zero;
- F01 withholds population-prior substitution with `prior_source = withheld:zero_canonical_history_debut_unproven`;
- audit reason records that true debut status is not proven by canonical v0.

The generic shrinkage primitive still supports the F00 true-debut rule if a future canonical/contract version supplies a trustworthy debut/completeness signal. Until then, F01 fails conservative rather than turning coverage uncertainty into debutant semantics.

## Shrinkage and population priors

Mechanical strengths only:

- `attempt_probability_v1`: 20 equivalent opportunities
- `composition_v1`: 30 equivalent events
- `fight_rate_v1`: 6 equivalent fights
- `time_rate_v1`: rejected under `0.1.1-draft`

For personal numerator `n`, support `d`, population probability `p`, prior strength `a`:

```text
posterior = (n + a*p) / (d + a)
```

Population priors are rebuilt as-of each cutoff. A complete-history prior is never reused for earlier rows.

Hierarchy:

1. count canonical target-weight-class fights strictly before cutoff;
2. if count >= 100, select that weight-class population, otherwise global;
3. within the selected population, calculate each concept/component prior only from compatible observed numerator/denominator rows.

The 100-fight hierarchy threshold and statistical support are deliberately separate. Missing stat rows may be part of the historical fight universe but never become round-stat denominator support. If the selected population has no compatible support, the prior is unavailable.

## Context details

- age uses canonical DOB and target event date with deterministic day-based years (`days / 365.2425`); missing DOB stays missing;
- layoff is target event/cutoff date minus the **maximum strict-prior event date**. Multiple fights sharing that prior date do not make calendar days-since-date ambiguous;
- height/reach use contract-authorized canonical fighter values and preserve missingness;
- prior scale weight uses only scale observations linked to strict-prior canonical fights. Ordering uses linked fight date, explicit `weigh_in_date`, explicit attempt number, then observation ID only as a deterministic final tie key;
- stance remains `PROXY_ONLY`; rankings remain `RESEARCH_ONLY`; current-fight weigh-in context remains `DEFERRED`.

## Elapsed-exposure safety

F01 pins to:

```text
elapsed_exposure_policy.allowed_sources = []
```

F01 does not assume standard historical round duration, derive historical elapsed duration from finish fields, treat scheduled rounds as round length, use `control_sec` as elapsed or ground time, convert positional buckets to exact duration, or read provider/raw files to recover time exposure.

Any blocked time concept promoted into V1 fails the implementation/contract selection gate. `time_rate_v1` also raises if invoked.

## Matchup orientation and dependency closure

Central orientation:

```text
fighter_1_id = lexicographically smaller canonical fighter_id
fighter_2_id = lexicographically larger canonical fighter_id
```

Input/provider A/B order therefore cannot alter the projection.

Current active V1 interactions:

- `knockdown_creation_vs_vulnerability`
- `reach_difference_cm`

They consume already-selected upstream V1 state. Missing/unselected dependencies fail closed, and a deferred dependency cannot be revived indirectly through matchup code.

## Target boundary

F01 attaches no training targets. Predictor state is the only public output. Tests mutate current target winner/result/method/finish fields and require the predictor projection to remain identical. A future training-table task must freeze predictors first and attach labels afterward.

## Runtime output and provenance

F01 creates no default feature-store directory. The CLI writes JSON to stdout unless the caller explicitly requests a runtime output path.

Manifest deterministic identity includes:

- feature contract version
- feature catalog/schema/leakage-registry hashes
- DATA contract version
- DATA freeze hash/status
- canonical manifest hash/build identity
- materializer code commit
- prediction cutoff
- consumer/status scope
- orientation policy
- window policy
- shrinkage policy
- elapsed-exposure policy
- materialized names
- row count

`generated_at_utc` is deliberately outside the deterministic payload hash, so generation timestamps do not change `deterministic_payload_sha256`.

## Architecture checkpoint — 16 questions

1. **Can the target fight enter history?** No: historical eligibility requires event date strictly before cutoff date.
2. **Can same-day unresolved order leak?** No: same-date target history is excluded and recent-window tied boundaries fail closed.
3. **Can future priors leak?** No: prior scans use the same strict cutoff and cache by cutoff/concept/component/scope.
4. **Can missing stats become zero?** No: a component contributes only when its required canonical observations exist.
5. **Can external fights without round stats enter stat denominators?** No: result/count history can include them, but round-stat sufficient-stat lineage cannot.
6. **Can a deferred time feature sneak in?** No: core selection is V1-only, checks the blocked list, and rejects active time shrinkage.
7. **Can a matchup interaction revive a deferred dependency?** No: only active interactions exist and upstream state must already be selected.
8. **Can provider/red-blue ordering leak?** No: canonical IDs are sorted centrally.
9. **Can current weigh-in/profile/ranking data backfill?** No: those current/research concepts are not selected; prior scale weight is strict-prior linked.
10. **Does EWMA aggregate sufficient statistics correctly?** Yes: numerator and denominator are weighted separately.
11. **Can true debut be distinguished from zero canonical history?** Not with canonical v0; therefore F01 explicitly withholds debutant prior semantics when only zero canonical history is known.
12. **Is shrinkage support domain-specific?** Yes: component-specific denominators and compatible prior rows only.
13. **Are targets attached only after predictors?** F01 attaches none.
14. **Are names generated from the contract?** Yes: layer prefix/components/variant flags/estimator suffix come from F00 and are collision-checked.
15. **Is the repo compact?** Yes: four coherent modules, one CLI, one focused test file, one workflow, one implementation document.
16. **Can one value be explained?** Yes: audit state preserves sufficient statistics, support, prior, lineage, rule and reason.

## Risks/mistakes caught before completion

- Initial aggregation used one denominator per concept. Review caught that paired components can have different supports; F01 moved to component-specific sufficient statistics before expansion.
- The first same-date boundary test accidentally used a tied group that exactly filled the remaining slots. CI correctly showed the materializer was right and the fixture was wrong; the fixture now crosses a one-slot boundary.
- A first prior-threshold fixture forgot that population sufficient statistics include both fighters in a fight. The expected support was corrected from `1/2` to `2/4` without changing the production prior logic.
- `prior_scale_weight_lbs` initially used an opaque observation ID too early in ordering. It now prefers explicit weigh-in chronology and uses the ID only as a final deterministic tie key.
- Layoff initially treated multiple bouts on the same latest date as ambiguous. Since layoff requires only the maximum date, that over-conservative behavior was removed.
- Review identified that zero prior **canonical** history does not prove a true debut. F01 now withholds population-prior substitution unless a future canonical signal can prove debut/completeness.
- F01 selection deliberately does not reuse F00's broad generic materializable set because that would admit non-core V2/simulator/proxy concepts.
- CI source parsing is artifact-free; it does not create bytecode that would invalidate the clean-checkout gate.
- Runtime output has no implicit repository directory, avoiding a premature DATA/FEATURES storage decision.

F01 remains feature infrastructure only. Modeling, V2 opponent adjustment, simulator work, sportsbook work, and DATA changes require separate reviewed tasks.
