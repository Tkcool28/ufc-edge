# Canonical UFC Data

Canonical tables are deterministic derivatives of pinned raw snapshots. They are source-agnostic contracts shared by every model in this repository.

## Identity rules

- Prefer UFCStats URLs as stable source identities; never join fighters by display name alone.
- Create internal `fighter_id`, `fight_id`, and `event_id` deterministically from normalized source identities.
- Preserve original source URLs for auditability.
- Red/blue corner is fight context only, never fighter identity.

## Planned tables

### `events`
One row per UFC event.

Core fields: `event_id`, `event_name`, `event_date`, `location`, `source_event_url`.

### `fights`
One row per fight.

Core fields: `fight_id`, `event_id`, `bout`, `weight_class`, `method`, `end_round`, `end_time`, `time_format`, `referee`, `details`, `source_fight_url`.

### `fighters`
One row per fighter identity.

Core fields: `fighter_id`, `first_name`, `last_name`, `nickname`, `height_in`, `reach_in`, `dob`, `weight_lb_snapshot`, `stance_snapshot`, `source_fighter_url`.

`weight_lb_snapshot` and `stance_snapshot` are explicitly snapshots from the source, not guaranteed historical values for every prior fight.

### `fighter_rounds`
One row per fighter per completed/recorded round.

Core identity: `fight_id`, `fighter_id`, `opponent_id`, `round`.

Parsed stat fields include landed/attempted forms where the source encodes `X of Y`: significant strikes, total strikes, takedowns, head/body/leg strikes, and distance/clinch/ground strikes, plus knockdowns, submission attempts, reversals, control time, and percentages.

### `fighter_fights`
One row per fighter per fight, keyed by `fighter_id`, `opponent_id`, `fight_date` plus `fight_id` for uniqueness.

This is the canonical historical grain requested by the UFC model master plan. It may contain labels and post-fight observed totals for feature replay, but it is **not itself a pre-fight training matrix**.

## Leakage boundary

Canonical observed history may record what happened in a fight. Shared training features for that fight must be built strictly from rows with `fight_date < target_fight_date`. Same-fight statistics, result, method, and outcome may be labels or future history only; they cannot appear as predictors for that fight.
