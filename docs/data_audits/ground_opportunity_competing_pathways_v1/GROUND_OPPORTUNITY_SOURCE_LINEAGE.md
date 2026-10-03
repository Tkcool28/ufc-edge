# Ground opportunity source lineage

Starting main: `3e2b14a8391ed17d072b4bbb9570b31bc6d12b85`. Main matched the supplied PR #125 merge; no intervening commits. Audit only. The supplied submission-mechanism research and simulator feasibility research are preserved as reference text in `research_context/` (Markdown trailing spaces normalized; original upload hashes retained in `RESEARCH_REFERENCE_ORIGINS.json`) as scientific starting references, not evidence that a candidate field is already operational.

## Actual inventory and disposition

| Surface | Exact path | Status and role |
| --- | --- | --- |
| Pinned UFCStats mirror | `data/raw/greco1899/8e40eb945e11/ufc_fight_stats.csv` and `manifest.json` | Actual historical per-fighter round measurements; Greco1899/scrape_ufc_stats commit 8e40eb945e1127bf0ef172ab211a34787948f312 |
| Canonical core | `data/canonical/v0/fighter_round_stats.csv`, `fights.csv`, `events.csv` | Actual normalized measurements and dated outcomes; field owner specified in `provenance/source_precedence_v0.md` |
| Raw official FightMetric | `data/raw/ufc_fightmetric_official/20260820T123046Z/fight_stat/page_*.json` | Actual UFC.com Drupal JSON:API snapshot, 57,382 raw rows including summaries/duplicates/unidentified payloads |
| Canonical position | `data/canonical/v0/fighter_round_position.csv` | Actual additive data: 32,156 fighter-round rows / 6,803 fights / 2,459 fighters. Coarse buckets and standups, not exact position seconds |
| Identity governance | `data/canonical/v0/source_identity_links.csv`; `data/derived/identity/ufc_greco_fight_alignment_candidate.csv` | Trusted canonical/provider IDs plus audited UFC athlete UUID corner mapping |
| Prior audits | `provenance/audits/fightmetric_*`; `canonical_fightmetric_position_v0_latest.*` | Completed semantic, overlap, era, duplicate, color and quality audits; not merely proposed ingestion |
| F01 | `src/ufc_edge/features/state.py`, `history.py`, `aggregations.py`; `features/feature_catalog.yaml` | Production formulas/windows/shrinkage; exact positional duration deliberately withheld |
| F02 / corrected physical profile | `features/f02/README.md`; `models/challengers/mov1_three_arm_directional_v1/SOURCE_LINEAGE_VALIDATION.json` | F01 replay inherits chronology. Corrected physical F02 SHA256 d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580, verified by prior frozen contract. This audit does not download or modify that matrix |
| PR #123 | `docs/model_diagnostics/mov1_directional_representation_v1/` | Completed representation/lineage audit; establishes lost directional alignment, not missing-ground-data causation |
| PR #124 | `models/challengers/mov1_three_arm_directional_v1/` | Frozen feature/fold/target contract and exact ordered fight IDs |
| PR #125 | `models/challengers/mov1_three_arm_directional_run_v1/run_v1/` | Frozen predictions, membership and diagnostics; evaluation archive SHA256 verified before selectively reading saved fight evidence |
| Simulator source leads | `provenance/source_inventory.md`, `features/data_requirements.json`, `schemas/fight_action_event_v0.md` | TIP/live-feed references and proposed event schema. No licensed exact-duration archive or populated atomic transition table is established by these documents |

## Measurement definitions and transformations

All core fields below share raw Greco CSV → `pipelines/build_canonical_core_v0.py` → canonical fighter-round statistics. Exact raw-to-canonical mappings are shown; annual depth/missingness/observed sums/zeros are in `year_field_coverage.csv`. First/last observed years are available there rather than assumed modern coverage.

| Measurement | Raw field → canonical field | Units and denominator | Existing F01/F02 representation |
| --- | --- | --- | --- |
| TD attempts | `TD` attempted → `takedowns_attempted` | Recorded count, activity per governed total fight minutes | takedown_pressure created/faced per15 |
| TD landed | `TD` landed → `takedowns_landed` | Recorded count; success denominator is TD attempts | takedown_conversion.success; raw landed count reconstructible, not a standalone ground-exposure feature |
| TD defense | Paired opponent `TD` counts | (opponent attempts − landed)/opponent attempts | takedown_conversion.defense; no escape interpretation |
| SUB attempts created | `SUB.ATT` → `submission_attempts` | Provider-recorded attempts; /total fight minutes | submission_attempt_rate.created_per15; threat quality and attempt phase not observed |
| SUB attempts faced | Opponent same fight/round `SUB.ATT` | Actual opponent count on matching total exposure | submission_attempt_rate.faced_per15; exposure-confounded, not pure defense |
| SUB finishes | Raw results `METHOD` plus winner → `fights.method=SUBMISSION`, winner_id/result | Complete bout outcome; F01 wins/losses /prior fight count | finish_method_win/loss_profile, not finish/attempt conversion |
| Ground significant ATT | `GROUND` attempted → `sig_ground_attempted` | Significant ground-strike count; not all ground-and-pound | sig_environment_mix.ground_share = ground/(distance+clinch+ground attempts), not per ground minute |
| Ground significant land | `GROUND` landed → `sig_ground_landed` | Recorded significant count | Raw available; no dedicated F01 ground-location landed rate |
| Elapsed exposure | results terminal round/time + dated rules registry | Seconds/minutes via `src/ufc_edge/features/elapsed_exposure.py`; never ground time | Existing governed time denominators |
| Generic control | `CTRL` M:SS → `control_sec` | Generic control seconds, includes no guaranteed top-only/ground-only definition | control_rate.created_share/allowed_share versus total elapsed exposure |
| Reversals | `REV.` → `reversals` | Recorded counts; opponent paired counts | reversal_rate created/faced per15, not escape probability |
| Ground/position duration | Official `ground_time`, `ground_ctl_time`, guard/half/side/mount/back fields → position buckets and bounds | Coarse floor-minute model; bounds b×60..b×60+59, intersect known round time; ground occupancy differs from one fighter's control | Not materialized as exact F01/F02 duration; DATA_REQUIRED |
| Standups | Official `grap_stand_land` → `fighter_round_position.standups` | Source landed-count transport; no attempted standups/escape trials or standardized opportunity denominator | Canonical only, not F01/F02 feature |
| Escapes/ground entries/transitions | No validated canonical field/table | Ground entries are not equivalent to TD completions; escape and event-sequence opportunity absent | Not available |

Official raw count equivalents include `grap_take_att/land`, `grap_sub_att`, `grap_rev_land`, `ground_sig_str_att/land`. `control_time` in that archive is coarse and never replaces precise Greco CTRL. Additional stored `ground_str_att/land`, ground head/body/leg and sparse ground weapon splits are **raw candidate fields**. Their names do not prove all-ground offense semantics or finish quality. Prior summary-additivity evidence supports `ground_str_att/land` as counts, but this audit does not promote their clinical/weapon/total-versus-significant definitions. `raw_additive_inventory.csv` reports transport coverage including raw summaries and duplicates; it is not eligible fighter-state coverage.

Core fighter mapping first uses canonical Greco fight URL and exact event/bout context, then a unique normalized fighter-name mapping with participant validation; ambiguous names are excluded. Official position mapping uses trusted FightMetric fight IDs, athlete UUIDs and audited numeric 0=red/1=blue mapping (99.566% exact in 250,782 shared count comparisons), not display-name inference. Round 0 is source summary, never another actual round. Unresolved duplicates and identity failures are quarantined. Core and position builders, their source manifests and ID crosswalks are all hash-identified.

## Existing windows, shrinkage and minimum support

| concept | windows | shrinkage | minimum_support |
| --- | --- | --- | --- |
| sig_environment_mix | career, last5 | composition_v1 | Raw composition requires 20 observed environment attempts; shrunk composition may use less known support. |
| takedown_pressure | career, last3, last5, EWMA365d | time_rate_v1 | Raw display requires 5 eligible minutes; shrunk estimate may use smaller known support. |
| takedown_conversion | career, last5, EWMA365d | attempt_probability_v1 | Raw estimate requires 5 attempts; shrinkage retains smaller known support. |
| control_rate | career, last3, last5, EWMA365d | time_rate_v1 | Raw display requires 5 eligible minutes; shrunk estimate may use smaller known support. |
| submission_attempt_rate | career, last3, last5, EWMA365d | time_rate_v1 | Raw display requires 5 eligible minutes; shrunk estimate may use smaller known support. |
| reversal_rate | career | time_rate_v1 | Raw display requires 10 eligible minutes; shrunk estimate may use smaller known support. |
| finish_method_win_profile | career, last5 | fight_rate_v1 | Raw rate requires 3 eligible prior fights; shrinkage supports smaller known samples. |
| finish_method_loss_profile | career, last5 | fight_rate_v1 | Raw rate requires 3 eligible prior fights; shrinkage supports smaller known samples. |

Time-rate prior strength is 15 exposure-minutes, attempt-probability strength 20 attempts, composition strength 30 attempts, fight-rate strength 6 fights. F01 population priors are built from strictly prior history (weight-class then governed fallback), not whole-sample outcomes; EWMA half-life is 365 days. No new shrinkage or conversion prior is fitted in this audit. Any future rate requires a separately frozen definition and support/uncertainty policy.

## Chronology and reconstruction

All audit histories use event_date < target event date; the target and every same-date bout are excluded. Only pinned UFC history through 2026-08-15 is used. No prospective confirmation outcomes, model fitting, feature promotion or frozen-source edits occur. This is retrospective event-date governance: 2026 acquisition snapshots cannot prove what a provider published before every old fight. Preserve that publication-vintage limitation.

The modern population is the unchanged 5,658-fight PR #125 universe; its 4,260 outer-scored bouts and exact conditional training/scoring fight IDs are reused. Historical measurements retain earlier UFC bouts where available. Boundary rows describe unique fighters appearing in the frozen conditional training set at January 1. Training-prefight rows describe their original historical prediction dates, not values accumulated at the later boundary. Scoring rows include all eligible bouts, with 2026 truncated at the existing August 15 boundary. Division rows follow frozen target division, without inferring sex from unsupported metadata.

`career` here means available prior UFC history for the candidate measurement audit. `last5` means the last five prior UFC bouts, including measurement-missing bouts; tied dates crossing the boundary fail closed. This deliberately conservative coverage window is not an exact replay of F01's component-specific last5 eligible-observation selector. F01's available windows are inventoried separately and remain unchanged. Prior non-UFC outcome history cannot supply a UFC round-stat denominator. No prior UFC history is reported separately; it does not prove a professional debut. F01 likewise withholds automatic debut-prior substitution when debut/completeness is unproven.

A full-bout count requires all rounds 1..finish_round and nonmissing field values. Pair candidates sum only rounds with both measurements; conversion requires a complete attempted-submission bout before attaching the result. Ground-bucket pairs additionally require governed elapsed duration and a lower bound within that duration. Partial paired histories remain explicitly partial. `complete_history_pct` requires every prior UFC bout to have the relevant complete pair; observed-pair availability alone is insufficient. Zero denominator is distinct from missing history, and zero minute bucket means less than one minute under the contract, not necessarily no exposure. The contract's interval model is empirical evidence, not an independently published vendor unit guarantee.

Counts summed across target fighter states repeat a fighter's prior events at different prediction dates: columns explicitly say state-weighted. They are support distributions, not independent trial totals or confidence intervals. Bout-level records supply unique event counts; no statistical uncertainty calculation treats repeated fighter states as independent. Quantiles and missingness are descriptive; no style thresholds are chosen from outcomes.

All requested count proxies, generic control allowed, reversals and coarse position/standup histories can be reconstructed into **separate diagnostic files** from immutable inputs. A new exact grounded-duration field cannot be reconstructed from these aggregates without assumptions. No canonical/F01/F02/frozen prediction artifact changes are needed or authorized.
