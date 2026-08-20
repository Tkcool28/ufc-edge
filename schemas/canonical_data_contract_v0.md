# Canonical Data Contract v0

Status: **DATA-PHASE DRAFT — semantic contract, not feature contract**

Purpose: make every accepted source look the same downstream without destroying source provenance or inventing a new definition for the same concept each time a provider changes vocabulary.

The master plan's minimum UFC fight/fighter/round requirements remain the core of this contract. This document adds only the identity, provenance, rankings, weigh-in, scorecard, and rich-position structures required by sources already discovered during the data phase.

## 1. Boundary

```text
immutable raw source
        ↓
provider adapter
        ↓
canonical candidate rows
        ↓
identity + conflict reconciliation
        ↓
canonical tables + provenance
        ↓
later features/models/simulator
```

Provider-specific names stop at the adapter boundary.

Examples:

- Greco `SIG.STR.` and UFC FightMetric `sig_str_land`/`sig_str_att` map to canonical `sig_strikes_landed` / `sig_strikes_attempted` only after their semantics are verified.
- A source missing a statistic produces `null`, not zero.
- A new source may improve coverage or become the preferred authority. It does not get to redefine an existing canonical field.

## 2. Global rules

### 2.1 Canonical IDs

Canonical IDs are internal, immutable, opaque identifiers. Provider IDs/URLs are never used as the sole repository-wide identity.

Source identities are linked through `source_identity_links`.

Display-name-only matching may create a candidate link for review but may not create a trusted canonical identity by itself.

### 2.2 Units

Canonical units are fixed:

- heights/reaches: centimeters (`*_cm`)
- body/fight weights: pounds (`*_lbs`)
- durations: integer seconds (`*_sec`)
- dates: ISO `YYYY-MM-DD`
- UTC timestamps: ISO-8601 with `Z`
- strike/takedown/submission/reversal/knockdown counts: non-negative integers
- percentages/rates are not stored when numerator + denominator observations are available; derive them later

Source text such as `1:42`, `5' 11"`, `72"`, or `14 of 33` is parsed by the source adapter. Raw text remains in the immutable source snapshot.

### 2.3 Missing is not zero

- `0` = the source observation is valid and the event/count/time was observed as zero.
- `null` = unknown, unavailable, not collected, semantically unresolved, or not applicable.

No adapter may zero-fill missing source fields.

### 2.4 Temporal meaning

Every source snapshot has acquisition time. Mutable observations must also preserve the time they describe when known.

A present-day athlete profile, ranking, record total, gym, status, or listed weight is not automatically valid for an old fight.

### 2.5 Conflict behavior

Conflicting sources are preserved and audited. Reconciliation selects a canonical value only under a documented source/field rule.

No code may silently select:

- newest row;
- non-null row;
- higher numeric value;
- preferred provider;

unless that selection rule has been audited for the specific field/family.

### 2.6 Round zero

Official UFC FightMetric `round=0` is treated as a source fight-summary record, not an actual round. It remains available for QA/reconciliation but **must not** enter `fighter_round_stats` or `fighter_round_position` as a round.

Canonical fight totals are derived from actual rounds when the required round observations exist.

See `provenance/fightmetric_round0.md`.

## 3. Core canonical tables

## `fighters`

Grain: one canonical person/fighter.

| Field | Type | Null? | Meaning |
|---|---|---:|---|
| `fighter_id` | string | no | Internal immutable fighter ID. |
| `canonical_name` | string | no | Current repository display name; not identity by itself. |
| `dob` | date | yes | Verified date of birth. |
| `height_cm` | decimal | yes | Adult listed/measured height after source reconciliation. |
| `reach_cm` | decimal | yes | Reach after source reconciliation. |
| `stance` | enum/string | yes | Canonical stance only when source meaning is sufficiently stable. |

Mutable/current-only profile fields that cannot safely describe historical state stay in source observations/provenance until a dated representation is defined.

## `events`

Grain: one combat-sports event.

| Field | Type | Null? | Meaning |
|---|---|---:|---|
| `event_id` | string | no | Internal immutable event ID. |
| `promotion` | string | no | `UFC`, `Bellator`, `ONE`, etc. |
| `event_name` | string | no | Canonical event name. |
| `event_date` | date | no | Local event calendar date used for chronological replay. |
| `location` | string | yes | Canonical human-readable location. |

## `fights`

Grain: one bout. UFC and permitted external professional-MMA history may share this table; source quality/coverage remains explicit in provenance.

| Field | Type | Null? | Meaning |
|---|---|---:|---|
| `fight_id` | string | no | Internal immutable fight ID. |
| `event_id` | string | no | Canonical event ID. |
| `fighter_a_id` | string | no | One participant; A/B order is transport context, not predictive meaning. |
| `fighter_b_id` | string | no | Other participant. |
| `winner_id` | string | yes | Winner; null for draw/NC/unknown. |
| `result` | enum | no | `win_loss`, `draw`, `no_contest`, `other`, `unknown`. |
| `method` | enum/string | yes | Canonical result method family plus source detail retained in provenance. |
| `finish_round` | integer | yes | Actual ending round. |
| `finish_time_sec` | integer | yes | Elapsed time within ending round. |
| `scheduled_rounds` | integer | yes | Scheduled maximum rounds. |
| `weight_class` | string | yes | Canonical division/weight-class label. |
| `title_bout` | boolean | yes | Whether a recognized title was at stake. |
| `promotion` | string | no | Redundant convenience assertion; must agree with event. |

Recommended method families for data normalization: `KO_TKO`, `SUBMISSION`, `DECISION`, `DQ`, `DRAW`, `NO_CONTEST`, `OTHER`, `UNKNOWN`. Source-specific detail (e.g. unanimous/split/technical decision; choke type; doctor stoppage) is retained separately until its own canonical field is justified.

## `fighter_round_stats`

Grain: **one fighter in one actual round of one fight**.

Primary key: `(fight_id, fighter_id, round)`.

Required master-plan fields:

| Field | Type | Null? |
|---|---|---:|
| `fight_id` | string | no |
| `fighter_id` | string | no |
| `opponent_id` | string | no |
| `round` | integer >= 1 | no |
| `knockdowns` | integer | yes |
| `control_sec` | integer | yes |
| `reversals` | integer | yes |
| `submission_attempts` | integer | yes |
| `sig_strikes_landed` | integer | yes |
| `sig_strikes_attempted` | integer | yes |
| `total_strikes_landed` | integer | yes |
| `total_strikes_attempted` | integer | yes |
| `takedowns_landed` | integer | yes |
| `takedowns_attempted` | integer | yes |
| `head_landed` | integer | yes |
| `head_attempted` | integer | yes |
| `body_landed` | integer | yes |
| `body_attempted` | integer | yes |
| `leg_landed` | integer | yes |
| `leg_attempted` | integer | yes |
| `distance_landed` | integer | yes |
| `distance_attempted` | integer | yes |
| `clinch_landed` | integer | yes |
| `clinch_attempted` | integer | yes |
| `ground_landed` | integer | yes |
| `ground_attempted` | integer | yes |

Rules:

- attempts must be >= landed when both are known;
- `round=0` is forbidden;
- percentages from providers are QA evidence, not canonical substitutes for counts;
- fight totals are derived from actual rounds, not copied from a summary row when actual round rows are available.

## `fighter_round_position`

Grain: one fighter in one actual round. This is the simulator-oriented extension for official FightMetric/other verified Time In Position data.

Primary key: `(fight_id, fighter_id, round)`.

Fields may include:

- `standing_sec`
- `neutral_sec`
- `distance_sec`
- `clinch_sec`
- `ground_sec`
- `control_sec`
- `ground_control_sec`
- `guard_control_sec`
- `half_guard_control_sec`
- `side_control_sec`
- `mount_control_sec`
- `back_control_sec`
- `misc_ground_control_sec`
- `standups`

All are nullable. A provider's similar-looking position field is not mapped here until semantics are verified.

## 4. Additive canonical tables

## `rankings`

Grain: one fighter/division ranking observation on one as-of date.

Fields:

- `ranking_date`
- `fighter_id`
- `weight_class`
- `rank_numeric` (nullable)
- `is_champion` (nullable boolean)
- `ranking_body`

Historical use requires the observation to be available strictly before the target cutoff.

## `weigh_ins`

Grain: one fighter's official fight-specific weigh-in observation for one fight/attempt.

Fields:

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
- `official_status_text` (nullable source-normalized context, not a model feature by itself)

A roster/listed weight is not a substitute for `scale_weight_lbs`.

## `judge_round_scores`

Grain: one judge's score for one fighter in one actual round of one fight.

Fields:

- `fight_id`
- `round`
- `judge_id` (nullable until judge identities are canonicalized)
- `judge_name`
- `fighter_id`
- `opponent_id`
- `points`

Official judge scoring must remain separate from media/fan scoring.

## `source_identity_links`

Grain: one link from a canonical entity to one provider identity.

Fields:

- `entity_type` (`fighter`, `event`, `fight`, `judge`)
- `canonical_id`
- `source_name`
- `source_entity_type`
- `source_id`
- `source_url`
- `match_method`
- `match_confidence`
- `review_status`
- `valid_from` / `valid_to` when identity namespace changes are time-bounded

Provider identity is evidence, not canonical truth by itself.

## `field_provenance`

Grain: one source contribution/selection record for one canonical field value.

Minimum fields:

- `table_name`
- `row_key`
- `field_name`
- `source_name`
- `source_snapshot_id`
- `source_record_id`
- `source_field_name`
- `selection_status` (`selected`, `agreeing`, `conflicting`, `rejected`, `unmapped`)
- `selection_rule`
- `quality_note`

This sidecar makes source replacement auditable without changing the canonical field definition.

## 5. Adapter acceptance gate

A source adapter may emit a canonical candidate only when all are known:

1. target canonical table + field;
2. source record identity;
3. source snapshot/version;
4. parse rule;
5. canonical type;
6. canonical unit;
7. null/zero semantics;
8. temporal meaning;
9. identity linkage method;
10. whether the observation is authoritative, additive, QA-only, or unresolved.

If any material semantic is unresolved, preserve the raw source and mark the mapping unresolved. Do not guess.

## 6. Data-phase completion checks

Before this contract is promoted from `v0` draft:

- complete official UFC fight identity bridge;
- quantify FightMetric calendar-era coverage;
- reconcile conflicting FightMetric versions;
- compare overlapping official FightMetric vs Greco/UFCStats fields;
- verify dated athlete/event/fight identity behavior;
- settle fight-specific weigh-in source/coverage;
- settle judge-round score source/coverage;
- map ESPN additive fields only where semantics match;
- validate rankings and external-MMA identity joins;
- generate canonical tables through deterministic code and validate them against this contract.

Feature formulas are explicitly outside this contract.
