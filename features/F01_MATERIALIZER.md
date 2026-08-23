# F01 — V1 Point-in-Time Fighter State Materializer

Status: **F01 implementation draft**

Authoritative feature semantics remain in F00 `features/feature_catalog.yaml` version `0.1.1-draft`. F01 implements those semantics; this document does not redefine them.

## Scope

F01 builds the first production-quality reference path:

```text
frozen canonical DATA
→ canonical history index
→ strictly point-in-time eligible observations
→ concept-specific sufficient statistics
→ contract-approved windows
→ point-in-time population prior/shrinkage
→ auditable fighter state
→ deterministic canonical-ID matchup assembly
→ model-consumer projection
```

No model is trained. No V2 opponent adjustment, simulator, sportsbook input, web research, raw-provider recovery, or DATA migration is performed.

## Contract selection

Core F01 selection is deliberately narrower than F00's generic `materialized_feature_names()` universe. F01 selects exactly statuses `V1_MUST` and `V1_DERIVED`, optionally intersected with a requested consumer tag. It does not select `V2_OPPONENT_ADJUSTED`, `SIMULATOR_COMPONENT`, `PROXY_ONLY`, `RESEARCH_ONLY`, `DEFERRED`, or `UNSUPPORTED`.

The current active implementation registry must equal the contract-selected V1 concept set exactly. A newly promoted V1 concept therefore fails closed until a reviewed implementation exists; Python cannot silently expand the feature specification.

Under `0.1.1-draft`, the active concepts are:

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

The contract-derived V1 vocabulary is 58 names: 53 fighter/context state names and 5 matchup-interaction names.

## Modules

- `history.py` — canonical CSV indexing, strict event-date PIT filtering, safe recent-window selection, EWMA weights, explicit prior weigh-in lookup.
- `aggregations.py` — component-specific sufficient statistics, pooled weighted aggregation, mechanical shrinkage, semantic support state.
- `state.py` — executable dispatch for the contract-selected concepts, PIT priors, auditable fighter-state values, orientation and matchup interactions.
- `materializer.py` — public API, contract validation, deterministic selection, bounded real-data validation and provenance manifests.
- `tools/features/materialize_v1.py` — bounded CLI; stdout by default and no implicit generated-output directory.

The implementation deliberately remains one reference path. An optimized replay engine is deferred until profiling demonstrates a need; correctness and equivalence tests come first.

## Fighter-state grain

Historical fighter state is keyed by:

- `fighter_id`
- `prediction_as_of`

Target-bout context concepts require `target_fight_id`, so a full pre-fight row additionally records that context key. Historical state construction remains opponent-independent. Matchup assembly happens only after two independent fighter states are built at the same cutoff.

## Point-in-time policy

F01 uses canonical `events.event_date` as the trustworthy historical ordering boundary.

For cutoff date `T`:

- only fights with `event_date < T` enter historical state;
- the target fight and every same-date contest are excluded from history;
- intra-day bout order is never inferred from fight ID, row order, provider order, or CSV order;
- current target result/method/finish/round-stat fields never enter predictors;
- current profile/ranking context is not selected into core V1;
- current-fight weigh-in context remains deferred.

`last3` and `last5` operate on concept/component-eligible fights. Same-date groups are included only if the whole tied group fits within the remaining slots. If a same-date group crosses the N-fight boundary, that window is unavailable and the audit state records `missing_observation` plus an explicit ambiguity reason. Career/EWMA aggregation does not require tie order; same-date observations receive the same EWMA age.

## Windows and sufficient statistics

Variants are read from each concept's catalog flags; F01 never expands all windows universally.

- `career`: all concept-eligible prior observations.
- `last3`: up to three most recent eligible fights with fail-closed tied-boundary behavior.
- `last5`: same for five.
- `ewma_365d`: `2 ** (-age_days / 365)`.

Probabilities and compositions pool weighted numerators and denominators separately. F01 never averages per-fight percentages when count sufficient statistics exist.

Support is component-specific. For example, significant-strike accuracy and defense have different attempt denominators, and knockdown creation/vulnerability have different landed-strike denominators. This was caught during the architecture checkpoint before feature expansion.

## Missingness and audit state

Every materialized estimate has an `AuditValue` containing:

- source concept
- component
- window
- model value
- missingness state
- personal numerator
- personal denominator/support
- posterior denominator where shrinkage applies
- contributing fight count
- contributing observation count
- shrinkage rule
- prior source/value
- contributing fight IDs
- explicit reason when unavailable/missing

The five F00 semantic states remain distinct:

- `observed_positive`
- `observed_zero`
- `missing_observation`
- `not_applicable`
- `insufficient_exposure`

Examples:

- zero TD attempts with observed attempt fields → undefined raw conversion, positive observation coverage, `insufficient_exposure`; the shrunk model value may still equal the PIT prior.
- four observed attempts and zero landed → numeric 0 raw conversion, not missing.
- prior fights but no compatible canonical stat observations → `missing_observation`, not zero.
- a resolved canonical fighter with zero prior canonical fights → known zero personal history; population prior may be used where the F00 shrinkage rule permits.

## Shrinkage

F01 implements only the F00 mechanical rules:

- `attempt_probability_v1`: 20 equivalent opportunities
- `composition_v1`: 30 equivalent observed events
- `fight_rate_v1`: 6 equivalent fights
- `time_rate_v1`: rejected as non-materializable under contract `0.1.1-draft`

For component numerator `n`, support `d`, prior probability `p`, and prior strength `a`:

```text
posterior = (n + a*p) / (d + a)
```

Population priors are computed separately for every prediction cutoff. No all-history prior is reused for historical rows.

Prior hierarchy implementation:

1. Count canonical historical fights in the target weight class strictly before the cutoff.
2. If that fight count is at least 100, choose the weight-class prior population; otherwise choose global.
3. Within the selected population, the feature prior numerator/denominator uses only rows compatible with that specific concept/component.

Thus missing round-stat fights can help establish that the weight-class history universe has 100 fights, but they **do not** become statistical denominator support for a round-stat prior. If the selected population has no compatible statistical support, the prior is unavailable rather than fabricated.

## Elapsed-exposure safety

F01 pins to:

```text
elapsed_exposure_policy.allowed_sources = []
```

It never assumes standard historical round duration, reconstructs historical elapsed fight duration from terminal fields, treats `scheduled_rounds` as round length, treats `control_sec` as elapsed/ground time, uses quantized position buckets as exact duration, or reads raw/provider data to recover exposure.

Any catalog change that makes a blocked elapsed feature active fails the F01 registry/selection gate.

## Matchup orientation and dependency closure

Central orientation is exactly F00 version 1:

```text
fighter_1_id = lexicographically smaller canonical fighter_id
fighter_2_id = lexicographically larger canonical fighter_id
```

Input/provider order does not alter the matchup projection.

Only two matchup concepts are currently V1-active:

- `knockdown_creation_vs_vulnerability`
- `reach_difference_cm`

They consume already-materialized upstream V1 state. A missing or unselected dependency fails closed; a deferred upstream concept cannot be revived through an interaction.

## Target boundary

F01 does not attach training targets. Its public fighter/matchup objects contain predictors/audit state only. A later training-table task must first freeze the predictor row and only then attach labels. Current `winner_id`, result, method, finish round/time and current fight round stats are never read by F01 as target-fight predictors.

## Output and provenance

F01 intentionally creates no default feature-store directory and commits no matrix. The CLI writes JSON to stdout unless an explicit runtime `--output` path is supplied.

A provenance manifest includes:

- feature contract version
- feature catalog/schema/leakage-registry hashes
- DATA contract version
- DATA freeze hash/status
- canonical manifest hash/build identity
- materializer code commit
- prediction cutoff
- consumer/status scope
- fighter-orientation policy
- window policy
- shrinkage policy
- elapsed-exposure policy
- materialized names
- row count
- generation timestamp

The timestamp is outside the deterministic payload. `deterministic_payload_sha256` therefore remains identical for the same DATA/contract/code/cutoff/scope even when generation timestamps differ.

## Architecture checkpoint — 16 questions

1. **Can target fight enter history?** No. Eligibility is `event_date < cutoff_date`; same-day target is excluded.
2. **Can same-day unresolved order leak?** No. Same-day target history is excluded; recent-window tied boundaries fail closed.
3. **Can future population priors leak?** No. Prior scans use the same strict cutoff and cache by cutoff date/concept/component/scope.
4. **Can missing stats become zeros?** No. Component stats exist only when their required canonical fields are observed.
5. **Can external fights without round stats enter stat denominators?** No. They can enter result/experience history but create no round-stat sufficient statistics.
6. **Can a DEFERRED time feature sneak in?** No. Core selection is V1-only and cross-checks the F00 blocked list; time-rate shrinkage raises.
7. **Can an interaction activate a deferred dependency?** No. Active interaction registry is exact and dependencies must already exist in selected fighter state.
8. **Can provider A/B ordering leak?** No. Canonical IDs are sorted once centrally.
9. **Can current weigh-in/profile/ranking data backfill historically?** No. Profile/ranking concepts are not selected; scale weight is linked only to strictly prior fights; current weigh-in is deferred.
10. **Are EWMA numerator/denominator aggregates correct?** Yes. Weights apply to sufficient statistics separately, not already-computed ratios.
11. **Can true zero prior history be distinguished from missing history?** Yes for resolved canonical fighter identities. Zero canonical prior fights is explicit; unresolved/unknown fighter identity fails before materialization and missing compatible domains remain missing.
12. **Is shrinkage support domain-specific?** Yes. Every component carries its own denominator and only compatible rows enter prior support.
13. **Are targets attached after predictors?** F01 attaches no targets at all.
14. **Are names generated from the contract?** Yes. Layer prefix, components, variant flags and estimator suffix come from catalog metadata and are checked against F00's global generated-name set.
15. **Is the repo compact?** Yes. Four coherent modules, one CLI, one test file, one workflow and this document; no generated/run hierarchy.
16. **Can one value be explained?** Yes. `AuditValue` preserves sufficient statistics, support, prior, lineage, shrinkage rule and missingness reason.

## Risks/mistakes caught before broad expansion

- A first draft represented support with one denominator per concept. Review caught that paired components often have different denominators; the representation was changed to component-specific sufficient statistics before feature formulas expanded.
- Recent-window selection was deliberately implemented by same-date groups rather than a convenient `(event_date, fight_id)` truncation. Fight ID is used only for deterministic serialization inside a fully included tied group, never to infer chronology.
- F01 selection is not based on F00's generic non-materialized-status list because that would also admit V2/simulator/proxy concepts. Core selection explicitly requires V1 status plus consumer projection.
- Population-prior hierarchy separates the 100-fight universe test from feature-compatible statistical support so missing stat rows never become denominator evidence.
- Runtime output has no implicit repository directory, avoiding a premature DATA/FEATURES storage decision or committed historical matrix.

F01 remains an infrastructure task. Model training, opponent adjustment, simulator work and sportsbook integration remain out of scope.
