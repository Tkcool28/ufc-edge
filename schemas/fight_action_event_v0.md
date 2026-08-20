# Fight Action Event Schema v0

Status: **provisional acquisition schema**

This schema reserves a vendor-neutral place for sequential combat data before UFC Edge selects or licenses a specific play-by-play provider.

It is **not** a frozen model feature schema and does not define the simulator's final Markov state space.

## Purpose

Different sequential sources describe actions differently. UFC Edge should preserve source-faithful raw payloads while normalizing the minimum common event information needed to compare vendors and later construct simulator transitions.

The normalized event table should allow us to answer:

- What happened?
- Who initiated it?
- When in the fight did it happen?
- Was it successful?
- What phase/position was the fight in before and after it, if the source knows?
- What finer strike/grappling attributes did the source provide?
- Can the normalized event always be traced back to the untouched source record?

---

## Proposed canonical table: `fight_action_events`

One row per source-observed action or state-change event.

### Identity / provenance

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `action_event_id` | string | yes | UFC Edge stable normalized event ID |
| `source_name` | string | yes | e.g. `fightgeek_precision`, `img_arena_ufc`, `espn_mma` |
| `source_record_id` | string/null | when available | Native event/action ID |
| `source_sequence_no` | integer/string/null | when available | Native monotonic sequence number |
| `source_fight_id` | string | yes | Source-native fight identifier |
| `fight_id` | string | after identity mapping | UFC Edge canonical fight ID |
| `raw_snapshot_id` | string | yes | Immutable raw-source snapshot/batch identifier |
| `raw_record_locator` | string | yes | File/object/offset or equivalent pointer back to raw source record |

### Time / order

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `round` | integer | yes | Fight round |
| `round_clock_sec` | numeric/null | preferred | Source-displayed round clock in seconds |
| `round_elapsed_sec` | numeric/null | derived if semantics known | Seconds elapsed from start of current round |
| `fight_elapsed_sec` | numeric/null | derived if semantics known | Seconds elapsed from fight start |
| `source_timestamp_utc` | datetime/null | when available | Timestamp attached by source/data feed |
| `video_timestamp_sec` | numeric/null | when available | Timestamp into source video used by video-logged providers |
| `event_order` | integer | yes after normalization | Deterministic ordering within fight after source semantics are validated |

### Actor / participants

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `source_actor_fighter_id` | string/null | when applicable | Source-native acting fighter |
| `actor_fighter_id` | string/null | after mapping | UFC Edge fighter initiating action |
| `target_fighter_id` | string/null | when applicable | UFC Edge opponent receiving/defending action |
| `controller_fighter_id` | string/null | when applicable | Fighter controlling the positional state |

### Core event classification

`event_type` is a deliberately broad normalization vocabulary. Preserve vendor-specific labels separately.

Suggested initial values:

- `fight_open`
- `round_start`
- `round_end`
- `fight_end`
- `position_change`
- `strike`
- `knockdown`
- `takedown`
- `submission`
- `reversal`
- `standup`
- `escape`
- `other`

Fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `event_type` | enum | yes | Broad UFC Edge action/state event class |
| `source_event_type` | string/null | yes if source supplies | Exact vendor/source label |
| `action_outcome` | string/null | when applicable | e.g. `attempted`, `landed`, `successful`, `failed`, `completed` |

### Position / state observations

Do **not** force a provider into a state vocabulary it did not actually observe.

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `position_before` | string/null | when source supports | Normalized observed position immediately before event |
| `position_after` | string/null | when source supports | Normalized observed position immediately after event |
| `source_position_before` | string/null | when source supports | Untouched source label |
| `source_position_after` | string/null | when source supports | Untouched source label |
| `position_observation` | string/null | when event itself is state marker | Explicit observed state such as distance/clinch/mount |

Candidate normalized position vocabulary should remain provisional until the source audit is finished. Likely concepts include:

- `distance`
- `clinch`
- `standing_other`
- `ground_guard`
- `ground_half_guard`
- `ground_side_control`
- `ground_mount`
- `ground_back_control`
- `ground_other`
- `unknown`

Do not invent transitions between these states when a source only provides aggregate time-in-position totals.

### Strike detail

All nullable because source richness varies.

| Field | Type | Meaning |
|---|---|---|
| `strike_landed` | boolean/null | Whether the strike landed |
| `strike_significant` | boolean/null | Source designation of significant strike |
| `strike_target` | string/null | `head`, `body`, `leg`, other source label |
| `strike_weapon` | string/null | e.g. arm/punch, elbow, knee, kick |
| `strike_source` | string/null | Source-specific origin/method description |
| `strike_initiative` | string/null | e.g. initiated/counter when provider supports it |
| `combination_id` | string/null | Links strikes belonging to a recorded combination/set |
| `combination_order` | integer/null | Strike order within combination |

### Grappling detail

| Field | Type | Meaning |
|---|---|---|
| `takedown_landed` | boolean/null | Takedown result when event is a takedown |
| `submission_completed` | boolean/null | Submission result |
| `submission_type` | string/null | Choke/lock or source-specific technique |
| `reversal_landed` | boolean/null | Reversal result when source distinguishes attempt/result |
| `standup_landed` | boolean/null | Stand-up result when source distinguishes attempt/result |

### Raw extension

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `source_attributes_json` | JSON | yes | Vendor-specific fields not yet normalized; must not replace immutable raw storage |

---

# Companion positional exposure table

Some sources, notably the verified IMG Arena UFC Fight Stats feed, expose **time in position** rather than every atomic position transition. Do not fabricate action events from those totals.

Reserve a separate normalized table:

## `fight_position_exposure`

Grain: one fighter × fight × round × position bucket × source.

Suggested fields:

- `fight_id`
- `fighter_id`
- `round`
- `source_name`
- `position_type`
- `position_time_sec`
- `is_control_time`
- `raw_snapshot_id`
- `raw_record_locator`

Known IMG Arena UFC TIP concepts currently include:

- back control
- clinch
- control
- distance
- ground control
- ground
- guard control
- half-guard control
- miscellaneous ground control
- mount control
- neutral
- side control
- standing

This table can improve simulator phase-duration models even when a source does not expose exact state-change timestamps.

---

# Raw-source rule

Never reduce a rich provider payload to this schema and then discard the source data.

For every sequential provider:

1. Store an immutable source-faithful raw snapshot/export first.
2. Record source terms/license/access conditions in provenance.
3. Normalize into `fight_action_events` and/or `fight_position_exposure` deterministically.
4. Preserve a locator from every normalized row back to the raw record.
5. Add source-specific validation tests before combining sources.

---

# Non-goals at v0

This document does **not** decide:

- the final Markov states
- the Markov time step
- transition smoothing/shrinkage
- feature windows
- fighter skill priors
- damage-state representation
- fatigue-state representation
- whether transition probabilities are empirical, modeled, or hybrid

Those decisions belong after the acquisition inventory is settled and the actual historical coverage of each source is known.
