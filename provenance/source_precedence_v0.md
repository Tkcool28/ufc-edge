# UFC Edge source precedence v0

Status: **data-phase policy, not feature freeze**

This document records source ownership decisions supported by completed acquisition and QA audits. It does **not** define model features. A source may be authoritative for one field family and only additive/QA for another.

## 1. Shared UFC round-count statistics

**Primary canonical source: pinned Greco/UFCStats snapshot** for fields already represented there at exact fighter/round grain:

- knockdowns
- significant strikes landed/attempted
- total strikes landed/attempted
- takedowns landed/attempted
- submission attempts
- reversals
- significant-strike target splits (head/body/leg)
- significant-strike position splits (distance/clinch/ground)
- precise control time (`M:SS` -> canonical seconds)

Why Greco remains primary for this shared family:

1. It is already pinned and immutable in this repo.
2. Its fighter/round representation is clean and directly parseable.
3. Its control time preserves second-level precision.
4. The official UFC FightMetric archive strongly validates the shared counts rather than materially replacing them: in the conservative exact-alignment audit, 32,612 of 32,638 aligned Greco fighter-round keys had an official FightMetric counterpart, and shared count fields were approximately 99.35% to 100% exact depending on field.
5. The official FightMetric archive contains duplicate source versions for some keys and a substantial set of UFC fight nodes without stat rows, so replacing a clean pinned core with it would add conflict-resolution complexity without adding useful information for the shared count family.

**Official UFC FightMetric role for shared counts:** independent QA and possible coverage fallback only after stable fight identity and duplicate-version rules are satisfied. Missing official data never overwrites present Greco data.

## 2. Official UFC FightMetric additive fields

**Primary source: official UFC FightMetric archive** for fields not present in the Greco/UFCStats round table, including richer positional/control-state observations and additional strike-detail fields.

These fields remain in an additive namespace until their units/semantics are individually proven. They must not be silently coerced into canonical seconds or other units merely because a field name contains `_time`.

### Proven transport semantics

- `fightmetric_id` is a source fight identity, not a canonical UFC Edge fight ID.
- `round = 0` is a summary row and is **not** an actual round.
- numeric `color` is transport syntax:
  - `0 = red`
  - `1 = blue`

The color mapping was promoted only after a direct semantic audit across 250,782 shared field comparisons: the 0=red/1=blue orientation matched 99.566%, while the reversed orientation matched 11.725%.

### Time-field caution

Official archived `control_time` is **not second-resolution control time**. Against Greco `M:SS` control values, the raw UFC integer matched `floor(control_seconds / 60)` in 23,268 of 23,876 comparisons (97.454%). Therefore:

- do **not** map archived UFC `control_time` to canonical `control_sec`;
- do **not** multiply it by 60 and pretend the lost seconds are known;
- preserve the raw integer and source field name;
- use Greco for canonical precise control seconds where available.

A follow-up quality audit shows that the broader positional `_time` family is overwhelmingly encoded on a **0–5 round-scale bucket** among non-null identified actual-round rows. The weakest field still had 99.621% of non-null values in 0–5; most were above 99.88%. On clean 0–5 rows, `standing_time - (distance_time + clinch_time)` was always within one bucket, and the ground-control positional decomposition was within one bucket in 98.163% of comparisons.

Rare `>5` values are present and are treated as source anomalies rather than legitimate exact-duration observations. Therefore:

- `>5` actual-round positional time values are not canonical eligible without independent proof;
- future adapters may expose validated 0–5 values only as an explicitly **coarse bucket/exposure representation**;
- no positional bucket may be converted back into synthetic seconds;
- all raw source rows remain preserved for auditability.

See `provenance/audits/fightmetric_position_time_quality_latest.json`.

## 3. FightMetric rows without stable fight identity

Rows without `fightmetric_id` are **raw/QA only**.

Current audit:

- total `fight_stat` rows: 57,382
- identified rows: 54,187 (94.432%)
- unidentified rows: 3,195
- every unidentified row inspected/population-counted contained only `drupal_internal__id`; round and color were null

These 3,195 rows contain no usable fight/stat payload and are excluded from canonical tables unless independent stable identity plus meaningful content is ever proven.

## 4. Duplicate official UFC/FightMetric source versions

No global "newest row wins" rule is promoted.

The reconciliation audit found multi-version fighter-round keys. In Greco comparisons, the newest version was strictly best for most scored duplicates, but at least one newest version was not best. Therefore duplicate resolution remains an explicit QA problem, not an ingestion convenience.

Rules:

- never silently deduplicate by `drupal_internal__id`, insertion order, page order, or recency;
- preserve all raw versions;
- a future resolver may use cross-source agreement plus source chronology, but it must be deterministic, audited, and documented;
- unresolved duplicate keys are not eligible to fill canonical data when a clean Greco value already exists.

## 5. Official UFC fight/event identity

Official UFC fight UUIDs, athlete UUID relationships, and direct event relationship membership are preferred identity evidence when present, but the current official fight collection has duplicate/conflicting FightMetric-ID relationships and missing event memberships.

Current direct evidence:

- official UFC fight rows: 12,069
- UFC fights with non-null FightMetric ID: 9,744
- distinct UFC FightMetric IDs: 9,612
- direct overlap with official `fight_stat`: 8,005 IDs
- one-to-one overlap candidates: 7,913
- duplicate FightMetric-ID groups on UFC fight nodes: 128, of which only 7 were semantically identical on compared fight fields and 121 conflicted
- direct unique fight->event/date bridge rows: 8,909
- official fights without event membership: 3,153

Therefore official UUID relationships are strong **identity evidence**, but no universal official-fight-node canonicalization rule is promoted yet.

## 6. Cross-promotion history

The CC0 Kaggle/Sherdog-derived professional fight archive is additive for pre-UFC and non-UFC professional history. It must not overwrite UFC fight/stat records already covered by the UFC-specific sources. UFC overlaps are deduplicated during canonicalization.

## 7. Rankings

Historical dated rankings remain a separate observation table. Only observations available strictly before the target prediction cutoff may be used. Future/nearest-forward ranking values are prohibited.

## 8. Weigh-ins and judge scorecards

These remain separate data families and do not influence the source rules above.

- Official UFC public content indexes are the preferred free acquisition route for fight-specific weigh-in reports and official scorecard source pages/images.
- OCR scorecard data already ingested from UFC-DataLab remains **raw/noisy secondary evidence** until matched to a fight and validated against official material.
- No OCR-derived fighter association or judge total is canonical merely because the row parses.

## 9. General precedence rule

When two sources overlap, prefer the source that provides the **cleanest proven semantic representation at the required grain**, not automatically the source with the strongest brand name or newest timestamp.

A lower-precedence source may:

- validate a primary source;
- fill genuinely missing fields if identity and semantics pass QA;
- provide additive fields absent from the primary source;
- remain raw evidence when conflict or unit semantics are unresolved.

Missing is never converted to zero, and conflicts are never silently resolved.
