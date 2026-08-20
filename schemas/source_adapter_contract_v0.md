# Source Adapter Contract v0

Status: **DATA-PHASE DRAFT**

Purpose: every provider parser must behave the same way before its output can participate in canonical reconciliation.

## 1. Adapter responsibility

Each adapter knows exactly one provider namespace and converts provider-specific records into canonical **candidate observations**.

An adapter may:

- parse provider IDs/URLs;
- parse source dates/times/durations;
- split landed/attempted composites;
- convert units;
- normalize provider enums into canonical candidates when mapping is verified;
- attach source/snapshot/record provenance;
- emit explicit nulls for missing values;
- preserve provider-specific unmapped fields for QA.

An adapter may **not**:

- choose between conflicting providers;
- create a trusted cross-provider identity from display name alone;
- zero-fill missing observations;
- backfill a current snapshot into historical fights;
- infer a statistic the provider did not actually observe;
- redefine a canonical field because its provider uses different terminology;
- silently discard duplicate/conflicting source rows.

## 2. Candidate envelope

Every emitted candidate row must carry enough lineage to reproduce it:

- `source_name`
- `source_snapshot_id`
- `source_collection`
- `source_record_id` or deterministic source-record key
- `source_url` when available
- `acquired_at_utc`
- `effective_date` / `observed_at_utc` when the source describes a dated state
- `adapter_version`
- `canonical_table`
- canonical candidate fields

The lineage envelope may be stored separately from the wide candidate row, but it must remain one-to-one traceable.

## 3. Parse rules

### Counts

Counts are non-negative integers. Parse source composites such as `14 of 33` into two separately named canonical candidates only when the provider semantics are verified.

### Time

All canonical durations are integer seconds. Source `MM:SS` strings are converted deterministically.

If a provider's fight-summary time differs from summed rounded round times by a small rounding amount, preserve both observations in provenance. Do not mutate raw values to force equality.

### Physical units

- inches/feet -> centimeters for height/reach
- source fight/scale weight -> pounds
- never substitute listed roster weight for fight-specific weigh-in weight

### Percentages

If numerator/denominator counts exist, canonical data stores the counts. Provider percentages remain QA/provenance evidence.

### Booleans

Unknown is `null`, not `false`.

## 4. Identity rules

Preferred identity evidence, strongest first:

1. exact official/provider stable ID explicitly linked by source;
2. exact stable URL/source identifier linked through another verified provider identity;
3. deterministic event + participants + date + provider fight ID bridge;
4. multi-field reconciliation using date, opponents, event, and physical/name context;
5. display-name-only candidate — **review required; never trusted automatically**.

Corner/order is transport context. It may help resolve a source row but must not become predictive semantic meaning.

## 5. Duplicate behavior

Adapters preserve source duplicates and versioned/conflicting rows until an audit establishes a deterministic rule.

A generic `latest wins`, `highest ID wins`, or `most non-null wins` rule is prohibited unless the specific source family has been audited and the rule is documented in provenance.

## 6. Temporal safety labels

Every source field family should be labeled as one of:

- `historical_observation` — explicitly describes the event/date state;
- `point_in_time_snapshot` — describes acquisition-time state and is unsafe for earlier backfill;
- `static_or_near_static` — e.g. DOB/height subject to source QA;
- `postfight_label` — outcome/round stats from the target fight;
- `unknown_temporal_semantics` — preserve, do not use historically until resolved.

These labels belong to data semantics. They are not feature definitions.

## 7. Source-specific adapters currently expected

- `greco1899` / UFCStats-derived CSVs
- `ufc_fightmetric_official`
- `ufc_com_resources`
- `espn_mma`
- `tidytuesday_ufc_rankings`
- `kaggle_pro_mma_fights`
- `kaggle_pro_mma_fighters`
- official UFC weigh-in source once acquisition is settled
- judge score source once acquisition is settled

Future paid/sequential providers must use the same boundary rather than creating a parallel canonical schema.

## 8. Promotion gate

A provider adapter is accepted only when tests demonstrate:

- deterministic parse output from a pinned raw fixture;
- no source file mutation;
- missing != zero;
- units match canonical contract;
- invalid impossible counts/times fail closed;
- identity links are explicit about confidence/review state;
- lineage is complete;
- target-fight/postfight fields remain marked as labels/observations rather than pre-fight state.
