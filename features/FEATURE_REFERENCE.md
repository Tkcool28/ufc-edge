# UFC Edge Feature System Reference

> GENERATED from the authoritative feature catalog + governance registries. Do not hand-edit.

- Feature contract: 0.1.2-draft
- Governance version: 1.0.0
- Durable concepts: **60**
- Active V1 concepts: **24**
- F01-selected values: **104** = 99 fighter-state/context + 5 matchup interactions
- Catalog-declared active variants (including round-specific declarations): **164**

## Authority map

- Semantics/formulas/eligibility: features/feature_catalog.yaml
- Stable IDs/lifecycle/methodology identity: features/feature_governance.json
- Terminology: features/terminology.json
- Dependency graph: features/dependencies.json
- Known missing data: features/data_requirements.json
- Simulator needs: features/simulator_requirements.json
- Evolution history: features/migrations/feature_migrations.json
- Runtime implementation: src/ufc_edge/features/
- Generated inventory: features/feature_inventory.json

## Concept inventory

| Feature ID | Canonical name | Layer | Lifecycle | Contract status | Methodology | Consumers |
| --- | --- | --- | --- | --- | --- | --- |
| FS_PRIOR_FIGHT_COUNT_V1 | prior_fight_count | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, simulator |
| FS_SIG_STRIKE_FLOW_V1 | sig_strike_flow | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_striking, simulator |
| FS_SIG_STRIKE_EFFICIENCY_V1 | sig_strike_efficiency | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_striking |
| FS_SIG_TARGET_MIX_V1 | sig_target_mix | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model1, tree, component_striking, simulator |
| FS_SIG_ENVIRONMENT_MIX_V1 | sig_environment_mix | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model1, tree, component_striking, component_ground, simulator |
| FS_KNOCKDOWN_RATE_V1 | knockdown_rate | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_striking, component_durability, simulator |
| FS_KNOCKDOWN_EFFICIENCY_V1 | knockdown_efficiency | fighter_state | ACTIVE | V1_DERIVED | 1.0.0 | model1, tree, component_durability, simulator |
| FS_TAKEDOWN_PRESSURE_V1 | takedown_pressure | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_wrestling, simulator |
| FS_TAKEDOWN_CONVERSION_V1 | takedown_conversion | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_wrestling, simulator |
| FS_CONTROL_RATE_V1 | control_rate | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_ground, simulator |
| FS_SUBMISSION_ATTEMPT_RATE_V1 | submission_attempt_rate | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_submission, simulator |
| FS_REVERSAL_RATE_V1 | reversal_rate | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model1, tree, component_ground, simulator |
| FS_FINISH_METHOD_WIN_PROFILE_V1 | finish_method_win_profile | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_striking, component_submission, component_durability, simulator |
| FS_FINISH_METHOD_LOSS_PROFILE_V1 | finish_method_loss_profile | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_durability, component_submission, simulator |
| FS_EARLY_FINISH_PROFILE_V1 | early_finish_profile | fighter_state | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, component_durability, simulator |
| FS_SIG_STRIKE_DIFFERENTIAL_RATE_V1 | sig_strike_differential_rate | fighter_state | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_striking |
| FS_CONTROL_DIFFERENTIAL_RATE_V1 | control_differential_rate | fighter_state | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_ground |
| FS_LATE_ROUND_PACE_RATIO_V1 | late_round_pace_ratio | fighter_state | DEFERRED | DEFERRED | 1.0.0 | model1, tree, simulator |
| CTX_AGE_AT_FIGHT_V1 | age_at_fight | context | ACTIVE | V1_DERIVED | 1.0.0 | model0, model1, tree, component_durability, simulator |
| CTX_LAYOFF_DAYS_V1 | layoff_days | context | ACTIVE | V1_DERIVED | 1.0.0 | model0, model1, tree, simulator |
| CTX_PHYSICAL_SIZE_PROFILE_V1 | physical_size_profile | context | ACTIVE | V1_DERIVED | 1.0.0 | model1, tree, component_striking |
| CTX_SCHEDULED_ROUNDS_V1 | scheduled_rounds | context | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, simulator |
| CTX_TITLE_BOUT_V1 | title_bout | context | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, simulator |
| CTX_WEIGHT_CLASS_V1 | weight_class | context | ACTIVE | V1_MUST | 1.0.0 | model0, model1, tree, simulator |
| CTX_PRIOR_SCALE_WEIGHT_LBS_V1 | prior_scale_weight_lbs | context | ACTIVE | V1_DERIVED | 1.0.0 | tree, human_research |
| MX_SIG_CREATION_VS_PREVENTION_V1 | sig_creation_vs_prevention | matchup_interaction | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_striking |
| MX_KNOCKDOWN_CREATION_VS_VULNERABILITY_V1 | knockdown_creation_vs_vulnerability | matchup_interaction | ACTIVE | V1_DERIVED | 1.0.0 | model1, tree, component_durability |
| MX_TAKEDOWN_PRESSURE_VS_DEFENSE_V1 | takedown_pressure_vs_defense | matchup_interaction | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_wrestling |
| MX_CONTROL_CREATION_VS_ALLOWED_V1 | control_creation_vs_allowed | matchup_interaction | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_ground |
| MX_SUBMISSION_PRESSURE_VS_ALLOWED_V1 | submission_pressure_vs_allowed | matchup_interaction | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_submission |
| MX_PACE_MISMATCH_V1 | pace_mismatch | matchup_interaction | DEFERRED | DEFERRED | 1.0.0 | model1, tree, simulator |
| MX_REACH_DIFFERENCE_CM_V1 | reach_difference_cm | matchup_interaction | ACTIVE | V1_DERIVED | 1.0.0 | model1, tree, component_striking |
| OA_SIG_CREATION_V1 | oa_sig_creation | opponent_adjusted | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_striking, simulator |
| OA_SIG_SUPPRESSION_V1 | oa_sig_suppression | opponent_adjusted | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_striking, simulator |
| OA_TAKEDOWN_CREATION_V1 | oa_takedown_creation | opponent_adjusted | DEFERRED | V2_OPPONENT_ADJUSTED | 1.0.0 | model1, tree, component_wrestling, simulator |
| OA_CONTROL_CREATION_V1 | oa_control_creation | opponent_adjusted | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_ground, simulator |
| OA_SUBMISSION_CREATION_V1 | oa_submission_creation | opponent_adjusted | DEFERRED | DEFERRED | 1.0.0 | model1, tree, component_submission, simulator |
| SIM_STRIKE_EVENT_INTENSITY_V1 | sim_strike_event_intensity | simulator_component | DEFERRED | DEFERRED | 1.0.0 | component_striking, simulator |
| SIM_KNOCKDOWN_HAZARD_PROXY_V1 | sim_knockdown_hazard_proxy | simulator_component | DEFERRED | DEFERRED | 1.0.0 | component_striking, component_durability, simulator |
| SIM_TAKEDOWN_ATTEMPT_INTENSITY_V1 | sim_takedown_attempt_intensity | simulator_component | DEFERRED | DEFERRED | 1.0.0 | component_wrestling, simulator |
| SIM_TAKEDOWN_SUCCESS_PROBABILITY_V1 | sim_takedown_success_probability | simulator_component | SIMULATOR_REQUIRED | SIMULATOR_COMPONENT | 1.0.0 | component_wrestling, simulator |
| SIM_SUBMISSION_ATTEMPT_INTENSITY_V1 | sim_submission_attempt_intensity | simulator_component | DEFERRED | DEFERRED | 1.0.0 | component_submission, simulator |
| SIM_FATIGUE_PERSISTENCE_MULTIPLIER_V1 | sim_fatigue_persistence_multiplier | simulator_component | DEFERRED | DEFERRED | 1.0.0 | component_striking, component_wrestling, component_ground, simulator |
| SIM_POSITION_OCCUPANCY_PROFILE_V1 | position_occupancy_profile | simulator_component | PROXY_ONLY | PROXY_ONLY | 1.0.0 | component_ground, simulator |
| CTX_STANCE_PROFILE_V1 | stance_profile | context | PROXY_ONLY | PROXY_ONLY | 1.0.0 | tree, component_striking, human_research |
| FS_HISTORICAL_FIGHT_DURATION_V1 | historical_fight_duration | fighter_state | DEFERRED | DEFERRED | 1.0.0 | model1, tree, simulator |
| CTX_CURRENT_FIGHT_WEIGHIN_CONTEXT_V1 | current_fight_weighin_context | context | DEFERRED | DEFERRED | 1.0.0 | tree, human_research |
| RES_RANKING_STATE_ASOF_V1 | ranking_state_asof | research | RESEARCH_ONLY | RESEARCH_ONLY | 1.0.0 | human_research |
| RES_PROFILE_CONTEXT_ASOF_V1 | profile_context_asof | research | RESEARCH_ONLY | RESEARCH_ONLY | 1.0.0 | human_research |
| RES_CAMP_COACHING_CHANGES_V1 | camp_coaching_changes | research | RESEARCH_ONLY | RESEARCH_ONLY | 1.0.0 | human_research |
| RES_INJURY_REPORT_V1 | injury_report | research | RESEARCH_ONLY | RESEARCH_ONLY | 1.0.0 | human_research |
| RES_SHORT_NOTICE_CIRCUMSTANCES_V1 | short_notice_circumstances | research | RESEARCH_ONLY | RESEARCH_ONLY | 1.0.0 | human_research |
| RES_QUALITATIVE_WEIGHIN_APPEARANCE_V1 | qualitative_weighin_appearance | research | RESEARCH_ONLY | RESEARCH_ONLY | 1.0.0 | human_research |
| RES_TRAVEL_CIRCUMSTANCES_V1 | travel_circumstances | research | RESEARCH_ONLY | RESEARCH_ONLY | 1.0.0 | human_research |
| UNSUP_EXACT_KNOCKDOWN_SEQUENCE_DYNAMICS_V1 | exact_knockdown_sequence_dynamics | unsupported | UNSUPPORTED | UNSUPPORTED | 1.0.0 | simulator, human_research |
| UNSUP_EXACT_SUBMISSION_FINISH_GIVEN_THREAT_V1 | exact_submission_finish_given_threat | unsupported | UNSUPPORTED | UNSUPPORTED | 1.0.0 | component_submission, simulator |
| UNSUP_EXACT_ESCAPE_STATE_HAZARD_V1 | exact_escape_state_hazard | unsupported | UNSUPPORTED | UNSUPPORTED | 1.0.0 | component_ground, simulator |
| UNSUP_EXACT_GROUND_STANDING_TIME_V1 | exact_ground_standing_time | unsupported | UNSUPPORTED | UNSUPPORTED | 1.0.0 | component_ground, simulator |
| UNSUP_EXACT_STATE_TRANSITION_MATRIX_V1 | exact_state_transition_matrix | unsupported | UNSUPPORTED | UNSUPPORTED | 1.0.0 | simulator |
| UNSUP_JUDGE_ROUND_SCORING_STATE_V1 | judge_round_scoring_state | unsupported | UNSUPPORTED | UNSUPPORTED | 1.0.0 | human_research |

## Known missing-data requirements

### DR_EXACT_POSITIONAL_DURATION_V1 — Exact positional control duration

Status: **DATA_REQUIRED**. Priority: **SIMULATOR_REQUIRED**.

Forbidden substitutions: generic control_sec as exact positional duration; FightMetric bucket bounds as exact duration.

### DR_JUDGE_ROUND_SCORES_V1 — Canonical judge-round scores

Status: **DATA_REQUIRED**. Priority: **RESEARCH_ONLY**.

Forbidden substitutions: fight result as judge-round scoring state.

## Simulator contract

- **distance standing** — AVAILABLE_BUT_APPROXIMATE.
- **clinch** — PROXY_ONLY. Blocked by: DR_EXACT_POSITIONAL_DURATION_V1.
- **wrestling entry** — AVAILABLE_NOW.
- **ground/top-control environment** — DATA_REQUIRED. Blocked by: DR_EXACT_POSITIONAL_DURATION_V1.
- **submission environment** — FUTURE_DERIVATION. Blocked by: DR_EXACT_POSITIONAL_DURATION_V1.
- **escape/reversal** — DATA_REQUIRED. Blocked by: DR_EXACT_POSITIONAL_DURATION_V1.
- **damage/knockdown** — AVAILABLE_NOW.
- **round/fatigue state** — FUTURE_DERIVATION.

## Repository hygiene

features/v0/, features/provenance/, legacy v0 builders/validators, and archived feature workflows are quarantined pre-F00 prior art. They are not semantic authorities and may not be consumed by new models without an explicit reviewed migration.

New generated matrices, replay outputs, run directories, and feature stores remain runtime artifacts and are not committed by this foundation milestone.
