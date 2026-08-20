# Official UFC.com JSON:API — Supplemental Source Candidate

Status date: 2026-08-19 (America/Denver)

Status: **PUBLIC / READY FOR TARGETED INGESTION**

This is a supplemental-source note. It does not replace the pinned Greco/UFCStats historical backbone.

## Discovery

A recently verified open-source provider audit documents that `ufc.com` exposes Drupal JSON:API resources at:

`https://www.ufc.com/jsonapi`

The audit reports no API key requirement and verifies that UFC's `athlete_stat` entity carries the same FightMetric identifier/data family used by UFCStats.

Reference implementation/audit:

https://github.com/DanielTomaro13/sportsdata-mcp/blob/cbc1c71ef2ddd650c9c4e7cd0b858ed297b21bb7/documentation/UFC.md

The source is an exposed CMS JSON interface rather than a documented UFC product API, so availability/schema stability must be monitored.

## Potentially additive fields for UFC Edge

The athlete resource is reported to include fields beyond the current Greco tale-of-the-tape file, including:

- leg reach (`stats_reach_leg`)
- octagon debut
- fighting style relationship
- gym relationship
- strengths / descriptive metadata
- origin / residence
- current ranking and prior ranking position
- interim-title flag

The linked FightMetric career-stat entity contains 48 aggregate fields including striking/grappling splits, rates, defense, career record/method counts and bonuses.

## Historical leakage rule

Most career/current aggregate fields from a present-day UFC.com snapshot are **not historical training features**.

Examples that must not be backfilled into old fight rows:

- current career wins/losses
- current win streak
- current career strike totals/rates
- current takedown defense
- current ranking
- former champion / current status metadata if the value reflects information learned after the historical fight

These may be retained as source snapshots for current-card context, QA, identity mapping, or incremental future snapshots.

Static or near-static physical fields such as leg reach are safer, but still require source-date/provenance handling rather than silent overwrite.

## What this source does not solve

The verified UFC.com JSON surfaces found so far do not provide atomic strike/takedown/position events with chronological timestamps. This source therefore does **not** satisfy the empirical Markov transition requirement.

## Ingestion decision

Do not duplicate the entire FightMetric aggregate table simply because it is available. A targeted ingestion pass should first prove which fields are additive to Greco and stable enough to justify another source dependency.

Highest-value initial candidates:

1. fighter identity crosswalk including `fightmetric_id`
2. leg reach
3. fighting style
4. gym
5. octagon debut
6. current/prior ranking snapshots
7. event/fight-card cross-checks for upcoming fights

Respect source access constraints and use a deliberately low request rate. The reference implementation notes UFC.com's crawl-delay guidance and treats the interface as potentially changeable.
