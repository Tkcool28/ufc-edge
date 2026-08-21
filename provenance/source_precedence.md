# UFC Edge source precedence

Status: **data-phase working policy**  
Scope: canonical data selection only. This document does not define model features.

The purpose of source precedence is to make cross-source conflict handling deterministic
without pretending that one provider is universally best. Raw source data is never
overwritten; precedence applies only when selecting values for canonical tables.

## General rules

1. **Stable identity before values.** A provider value is ineligible unless its fight,
   fighter, event, and round identity can be resolved at the canonical grain.
2. **Missing is not zero.** A missing provider observation never becomes numeric zero.
3. **Higher authority does not override incompatible semantics.** A field must have the
   same meaning, grain, and unit before sources are compared or substituted.
4. **No invented precision.** Quantized time values are never expanded into exact seconds.
5. **Conflicts remain traceable.** Selected canonical values retain field provenance;
   disagreeing source observations remain available for QA.
6. **Field/era-specific rules are allowed.** Precedence is not a blanket provider rank.

## Identity spine

### Preferred: official UFC.com

Use official UFC UUID relationships and direct FightMetric identifiers where available.
The completed official snapshots provide stable fight, athlete, and event identities.

Evidence:
- 12,069 official fight nodes in the complete deterministic-NID snapshot;
- 9,744 fight nodes carry `fightmetric_id`;
- 7,913 direct one-to-one UFC fight ↔ FightMetric candidates after cardinality checks;
- 8,909 unique fight-event-date bridge candidates;
- direct red/blue athlete relationships are used rather than display-name-only joins.

### Fallback/QA: Greco/UFCStats

Preserve UFCStats event/fight/fighter URLs as stable provider identities. They are useful
for historical coverage and independent QA, but display names alone are never canonical
identity.

## Shared fighter-round count statistics

### Primary candidate: official UFC FightMetric

For rounds with resolved official fight identity, audited numeric corner semantics, and
an admissible source version, official UFC FightMetric is the preferred source for shared
count statistics.

Cross-source audit evidence over 6,904 exact fight alignments:
- 32,638 aligned Greco fighter-round keys;
- 32,612 matched FightMetric fighter-round keys;
- 32,342 uncontested/single-version FightMetric keys;
- most shared striking/takedown count fields agree with Greco at roughly 99.35%–99.92%;
- FightMetric numeric corner semantics are independently promoted as `0=red`, `1=blue`
  after 99.566% exact agreement across 250,782 comparisons versus 11.725% under the
  reversed mapping.

Fields in this policy include, when semantics/coverage are present:
- knockdowns;
- significant strikes landed/attempted;
- total strikes landed/attempted;
- takedowns landed/attempted;
- submission attempts and reversals;
- significant head/body/leg splits;
- significant distance/clinch/ground splits.

### Fallback and independent QA: Greco/UFCStats

Use Greco/UFCStats when the official FightMetric observation is missing, lacks stable
identity, or has an unresolved conflicting source version. Greco remains an independent
comparison source even where official UFC is selected canonically.

## Precise control time

### Primary: Greco/UFCStats `CTRL`

Canonical `fighter_round_stats.control_sec` requires exact seconds. Greco/UFCStats `CTRL`
is parsed from `M:SS` and is the current preferred free source for precise control time.

### Not eligible for exact seconds: archived official FightMetric `control_time`

The archived Drupal value is integer-quantized rather than exact seconds. In 23,876
aligned observations:

- raw == floor(Greco control seconds / 60): **97.454%**;
- raw == exact seconds: 31.504%;
- raw × 60 == exact seconds: 31.961%;
- raw == nearest minute: 74.514%;
- raw == ceil minute: 32.874%.

Therefore archived `control_time` must not emit `control_sec`. It remains a coarse source
observation until a source-neutral quantized-time representation is explicitly defined.

## Rich positional/TIP time fields

### Unique free historical source: official UFC FightMetric

The official archive exposes standing, neutral, distance, clinch, ground, guard,
half-guard, side, mount, back, and other positional/control time fields with substantial
historical coverage, especially in later eras.

However, these archived fields are integer-quantized and are **not currently mapped to
canonical `*_sec` fields**. The source-field registry deliberately leaves them unresolved
rather than fabricating second-level precision.

Until their quantization semantics are individually verified, preserve them in raw data
and audited derived evidence only.

## `round=0`

Official FightMetric `round=0` is treated as a source-provided fight summary, not an
actual round. Canonical fighter-round tables include rounds 1+ only. Round-zero records
remain QA/summary evidence; canonical totals are derived from actual rounds.

## Duplicate FightMetric source versions

A blanket newest-wins rule is prohibited.

Current independent evidence across 270 aligned multi-version fighter-round keys:
- newest source version strictly best versus Greco on shared counts: 268;
- newest tied best: 1;
- newest not best: 1.

Resolution order:
1. one source version → admissible if other gates pass;
2. duplicate versions identical on canonical fields → collapse safely;
3. one version is a strict enrichment with identical overlapping values → prefer enriched
   version;
4. conflicting versions with independent Greco evidence → adjudicate by shared-field
   agreement and retain the decision provenance;
5. conflicting versions without independent evidence → quarantine/unresolved.

## Fighter physical/profile data

Prefer official UFC stable identity-linked observations for fields whose temporal
semantics are appropriate. Current profile/rank/status/gym/style observations are
point-in-time snapshots and cannot be silently backfilled into historical fights.

Greco TOTT remains a historical fallback/QA source for DOB, height, reach, stance, and
listed weight where applicable.

## Fight-specific weigh-ins

No canonical primary source is selected yet.

Rejected shortcut: official fight-node `red_corner_fight_weight` /
`blue_corner_fight_weight` do **not** represent actual scale weights. Verified missed-weight
cases disagree with official weigh-in article values.

Preferred acquisition path: official UFC public sitemap → official weigh-in result pages.

## Judge-round scores

No trusted canonical source is selected yet.

- UFC-DataLab OCR snapshot is raw/QA only because fighter-pair/OCR errors are known.
- MMA Decisions remains reference-only because the conservative crawl gate did not pass.
- preferred current path is official UFC sitemap/scorecard archive; structured extraction
  depends on whether official score details are present in HTML or only embedded images.

## ESPN MMA

Role: **additive/QA**, not automatic replacement for official UFC/Greco shared stats.
Its officials, structural plays, position advances, and other context may populate
canonical data only after each field's grain and semantics are verified in the source
adapter registry.

## External professional history and rankings

- CC0 UFC/Bellator/ONE fight/profile snapshots are additive historical identity/experience
  sources. Snapshot career totals are never backfilled as historical state.
- dated UFC rankings are historical observations and must be joined strictly from
  information available before the target cutoff; future ranking snapshots are prohibited.

## Promotion rule

No source/field becomes canonical because it is convenient, official, or similarly named.
It must pass identity, grain, semantic, unit, temporal, and conflict-resolution gates in
the source adapter registry and canonical contract.
