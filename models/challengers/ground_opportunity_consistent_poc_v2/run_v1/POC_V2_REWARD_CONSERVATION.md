# Reward conservation

Starting main: `222c7a76bc75bd66e0517930863ebeab41baf99f`. Branch: `feat/ground-opportunity-consistent-poc-v2`.

Status: **BLOCKED_OPPORTUNITY_FEASIBILITY**. No target outcomes recovered for scoring; zero outcomes scored.

All 2422 valid states meet frozen occupation/reward/flux/probability and closed-form gates. All 18 PR165 synthetic tests and two equation-equivalence tests pass. Every 4260 saved construction record regenerates exactly.

{
  "cross_runtime_frozen_tolerances_pass": true,
  "exact_regeneration": true,
  "maximum_boundary_flux_residual": 4.6629367034256575e-15,
  "maximum_conditional_identity_error": 2.993586600830156e-09,
  "maximum_reward_residual": 3.013327672926006e-08,
  "same_runtime_deterministic": true,
  "saved_records_replayed": 4260
}

Unavailable states are not claimed to conserve requested occupancy or rewards. Their failed fits retain residual/Jacobian and achieved shares; certified early rejections have no solver and use null/not-applicable solution fields.
