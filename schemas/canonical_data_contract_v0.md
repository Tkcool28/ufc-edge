# Canonical Data Contract v0

Status: **DATA-PHASE DRAFT — semantic contract, not feature contract**  
Machine contract: `schemas/canonical_data_contract_v0.json` (`0.3.0-draft`)

Purpose: every accepted provider can have a different raw format, but downstream UFC Edge code gets one stable definition for each concept.

The master plan's fight/fighter/round requirements remain the core. Additional structures below exist only because the current data pass has already found dated rankings, official profiles/events, officials, scorecards, weigh-in requirements, external MMA history, and rich FightMetric position data.

## 1. Boundary

```text
immutable raw source
        ↓
provider adapter
        ↓
canonical candidate observations
        ↓
identity + conflict reconciliation
        ↓
canonical tables + field provenance
        ↓
later features / models / simulator
```

Provider vocabulary stops at the adapter boundary. A new source may add evidence or coverage; it may not redefine an existing canonical concept.

## 2. Global semantic rules

### IDs

Canonical IDs are internal, immutable, opaque IDs. UFC IDs, FightMetric IDs, UFCStats URLs, ESPN IDs, Sherdog URLs, etc. are linked through `source_identity_links`.

Display-name-only matching can create a review candidate but never a trusted identity automatically.

### Units

- height/reach: centimeters
- weight: pounds
- exact durations: integer seconds
- archived UFC position/TIP time: floor whole-minute buckets plus explicit interval bounds; never fabricated as exact seconds
- dates: `YYYY-MM-DD`
- timestamps: ISO-8601 UTC
- event/stat counts: non-negative integers

Raw strings remain raw; adapters perform deterministic conversion.

### Missing vs zero

- `0` means observed zero.
- `null` means unavailable, unknown, unresolved, uncollected, or not applicable.

No adapter may zero-fill missing data.

### Counts before rates

When landed/attempted counts exist, store the counts. Provider percentages remain provenance/QA evidence and are derived later if needed.

### Temporal meaning

Current UFC athlete rank, status, listed weight, gym, record totals, etc. are acquisition-time observations, not historical truth for old fights. Mutable profile fields therefore belong in dated profile/ranking observations rather than being silently backfilled.

### Conflicts

Conflicting provider observations are preserved. No generic `newest wins`, `non-null wins`, `largest wins`, or `preferred provider wins` rule is allowed without a field-family audit.

### Round 0

Official UFC FightMetric `round=0` is a source fight-summary record, not an actual round. It may be retained for QA/reconciliation but cannot enter canonical round tables.

See `provenance/fightmetric_round0.md`.

### Significant-strike split rule

The master-plan `HEAD`, `BODY`, `LEG`, `DISTANCE`, `CLINCH`, and `GROUND` split family is explicitly the **significant-strike** family used by UFCStats.

Canonical names therefore carry the `sig_` prefix:

- `sig_head_landed` / `sig_head_attempted`
- `sig_body_landed` / `sig_body_attempted`
- `sig_leg_landed` / `sig_leg_attempted`
- `sig_distance_landed` / `sig_distance_attempted`
- `sig_clinch_landed` / `sig_clinch_attempted`
- `sig_ground_landed` / `sig_ground_attempted`

This prevents an official UFC field such as total `head_str_land` from being confused with significant `head_sig_str_land`.

## 3. Core canonical tables

## `fighters`

Grain: one canonical fighter/person.

- `fighter_id`
- `canonical_name` — display name, not identity by itself
- `dob`
- `height_cm`
- `reach_cm`
- `leg_reach_cm`
- `stance`

Stable-ish physical values still require source reconciliation. Listed roster weight is deliberately not stored here because it can change.

## `fighter_profile_snapshots`

Grain: one dated point-in-time profile observation.

- `fighter_id`
- `observed_at_utc`
- `listed_weight_lbs`
- `listed_weight_class`
- `gym_text`
- `fighting_style_text`
- `status_text`
- `residence_text`
- `origin_text`

This table preserves useful mutable UFC/profile context without pretending a 2026 snapshot describes a 2015 fight.

## `events`

Grain: one combat-sports event.

- `event_id`
- `promotion`
- `event_name`
- `event_date`
- `event_start_utc`
- `location`

## `fights`

Grain: one bout.

- `fight_id`
- `event_id`
- `fighter_a_id`
- `fighter_b_id`
- `winner_id`
- `result`
- `method`
- `finish_round`
- `finish_time_sec`
- `scheduled_rounds`
- `weight_class`
- `title_bout`
- `promotion`

A/B or red/blue order is transport context, not predictive meaning.

Canonical method families: `KO_TKO`, `SUBMISSION`, `DECISION`, `DQ`, `DRAW`, `NO_CONTEST`, `OTHER`, `UNKNOWN`. Detailed source method text remains in provenance until a narrower canonical field is justified.

## `officials`

Grain: one canonical combat-sports official.

- `official_id`
- `canonical_name`

## `fight_officials`

Grain: one official assignment to one fight and role.

- `fight_id`
- `official_id`
- `role` = `referee`, `judge`, or `other`

This gives Greco referees, ESPN officials, and later judge data one common home.

## `fighter_round_stats`

Grain: **one fighter in one actual round of one fight**.  
Primary key: `(fight_id, fighter_id, round)`.

Core fields:

- `fight_id`
- `fighter_id`
- `opponent_id`
- `round` (`>=1`)
- `knockdowns`
- `control_sec`
- `reversals`
- `submission_attempts`
- `sig_strikes_landed` / `sig_strikes_attempted`
- `total_strikes_landed` / `total_strikes_attempted`
- `takedowns_landed` / `takedowns_attempted`
- `sig_head_landed` / `sig_head_attempted`
- `sig_body_landed` / `sig_body_attempted`
- `sig_leg_landed` / `sig_leg_attempted`
- `sig_distance_landed` / `sig_distance_attempted`
- `sig_clinch_landed` / `sig_clinch_attempted`
- `sig_ground_landed` / `sig_ground_attempted`

Rules:

- attempts >= landed when both are known;
- `round=0` forbidden;
- source percentages do not replace counts;
- canonical fight totals are derived from real rounds when complete round observations exist.

## `fighter_round_position`

Grain: one fighter in one actual round. This is the simulator-oriented Time In Position extension.

Official UFC archived position/TIP values are **floor whole-minute buckets**, not exact seconds. The audit in `provenance/fightmetric_position_time_semantics.md` showed this directly. Canonical storage therefore preserves the bucket and explicit quantization interval instead of inventing second-level precision.

For each position family (`standing`, `neutral`, `distance`, `clinch`, `ground`, `ground_control`, `guard_control`, `half_guard_control`, `side_control`, `mount_control`, `back_control`, `misc_ground_control`) store:

- `<position>_bucket_min` — observed integer floor-minute bucket
- `<position>_lower_sec` — inclusive interval lower bound (`bucket_min * 60`)
- `<position>_upper_sec` — inclusive quantization upper bound (`bucket_min * 60 + 59`), to be intersected with known round duration before use

Also store:

- `fight_id`
- `fighter_id`
- `round` (`>=1`)
- `standups`

The lower/upper fields are **bounds, not observed exact durations**. General exact `control_sec` has one canonical home (`fighter_round_stats`) and is intentionally not duplicated here.

## 4. Additive canonical tables

## `rankings`

One fighter/division ranking observation on one date:

- `ranking_date`
- `fighter_id`
- `weight_class`
- `rank_numeric`
- `is_champion`
- `ranking_body`

Historical use requires the observation to precede the target information cutoff.

## `weigh_ins`

One fight-specific fighter weigh-in attempt:

- `fight_id`
- `fighter_id`
- `weigh_in_date`
- `attempt_number`
- `scale_weight_lbs`
- `contract_limit_lbs`
- `missed_weight`
- `pounds_over`
- `catchweight_bout`
- `purse_penalty_pct`
- `official_status_text`

Roster/listed weight is not a substitute for scale weight.

## `judge_round_scores`

One judge score for one fighter in one actual round:

- `fight_id`
- `round`
- `judge_id` (nullable until identity is resolved)
- `judge_name`
- `fighter_id`
- `opponent_id`
- `points`

Official judge scores stay separate from media/fan scores.

## `source_identity_links`

One canonical entity ↔ provider identity link:

- `entity_type`
- `canonical_id`
- `source_name`
- `source_entity_type`
- `source_id`
- `source_url`
- `match_method`
- `match_confidence`
- `review_status`
- `valid_from` / `valid_to`

Provider identity is evidence, not repository-wide identity by itself.

## `field_provenance`

One source contribution/selection record for one canonical field:

- `table_name`
- `row_key`
- `field_name`
- `source_name`
- `source_snapshot_id`
- `source_record_id`
- `source_field_name`
- `selection_status` = `selected`, `agreeing`, `conflicting`, `rejected`, `unmapped`
- `selection_rule`
- `quality_note`

This lets UFC later replace Greco as the selected source for a field without changing what the field means.

## 5. Adapter acceptance gate

An adapter may emit a canonical candidate only when all material semantics are known:

1. target table/field;
2. source record identity;
3. source snapshot/version;
4. parse rule;
5. canonical type;
6. unit;
7. null/zero meaning;
8. temporal meaning;
9. identity linkage method;
10. source role (authoritative/additive/QA/unresolved).

If a material point is unresolved, preserve the raw record and mark the mapping unresolved. Do not guess.

## 6. Data-phase completion checks

Before v0 can be promoted from draft:

- complete official UFC fight identity bridge;
- quantify FightMetric coverage by calendar era;
- resolve/confine conflicting FightMetric versions;
- compare overlapping FightMetric vs Greco/UFCStats fields;
- verify official athlete/event/fight identity and temporal behavior;
- settle fight-specific weigh-in source/coverage;
- settle judge-round score source/coverage;
- map ESPN fields only where grain/semantics match;
- validate rankings and external-MMA identity joins;
- generate canonical tables deterministically and validate them against this contract.

Predictive feature formulas are outside this contract and belong to the next project phase/chat.
