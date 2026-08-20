# UFC Edge — Free Additive Data Sweep

Status date: 2026-08-20 (America/Denver)

Purpose: exhaust the credible **free** additive-data landscape before feature contracts are frozen. This is an acquisition record, not permission to merge fields or use mutable snapshots as historical features.

## Acquisition status

### 1. Greco1899 / UFCStats backbone

Status: **INGESTED**

Pinned round/fight/event/fighter source remains the canonical historical backbone candidate. It does not contain ordered intra-round actions or the rich Time In Position vocabulary discovered below.

### 2. Official UFC.com Drupal JSON:API — resource catalog

Status: **VERIFIED / RESOURCE CATALOG STORED**

Probe artifacts:

- `provenance/ufc_jsonapi_resource_probe.json`
- `provenance/ufc_jsonapi_resource_probe.raw.json`

The live catalog exposes hundreds of resource types. High-value verified sport surfaces include:

- `/jsonapi/node/athlete`
- `/jsonapi/node/event`
- `/jsonapi/node/fight`
- `/jsonapi/athlete_stat/athlete_stat`
- `/jsonapi/athlete_ranking/athlete_ranking`
- `/jsonapi/fight_stat/fight_stat`
- `/jsonapi/fight_roundboard/fight_roundboard`
- `/jsonapi/node/article` (advertised, but collection access currently returns HTTP 403)

The bounded surface probe confirmed `fight_stat` and `fight_roundboard` return HTTP 200.

### 3. Official UFC.com rich FightMetric `fight_stat`

Status: **BULK SNAPSHOT PIPELINE STARTED; SCHEMA VERIFIED LIVE**

Pipeline: `pipelines/ingest_ufc_fight_stat.py`
Workflow: `.github/workflows/ingest-ufc-fightmetric.yml`
Raw namespace: `data/raw/ufc_fightmetric_official/<snapshot_id>/`

The verified live schema materially exceeds Greco's round table and includes:

**Time / position**

- standing_time
- neutral_time
- distance_time
- clinch_time
- ground_time
- control_time
- ground_ctl_time
- guard_ctl_time
- half_guard_ctl_time
- side_ctl_time
- mount_ctl_time
- back_ctl_time
- misc ground-control time

**Grappling**

- takedown attempts / landed
- submission attempts
- reversals
- standups

**Striking**

- significant and total attempts / landed
- punches / kicks
- head / body / leg
- distance / clinch / ground
- detailed combinations such as distance-head-punch and distance-head-kick attempts/landed
- knockdowns

This is a major simulator-data discovery. The first unsorted legacy sample rows contained null stats, so historical coverage must be measured rather than assumed. The bulk snapshot manifest computes non-null counts/fractions for every field and specifically all TIP fields.

`fight_roundboard` is also being preserved, but it is a record-book surface, not assumed to enumerate every fighter-round.

### 4. Official UFC.com athlete/event/fight point-in-time snapshot

Status: **PIPELINE STARTED; FINAL RAW COMMIT NOT YET VERIFIED**

Pipeline: `pipelines/ingest_ufc_com.py`
Workflow: `.github/workflows/ingest-ufc-com.yml`
Raw namespace: `data/raw/ufc_com/<snapshot_id>/`

Targeted additive fields include leg reach, gym, style, Octagon debut, official FightMetric identity, event/fight IDs and current context.

Leakage warning: current career totals/rates, rankings, streaks and status are point-in-time state and **must not be backfilled** into older target fights.

### 5. ESPN public MMA APIs

Status: **PIPELINE STARTED; FINAL RAW COMMIT NOT YET VERIFIED**

Pipeline: `pipelines/ingest_espn_mma.py`
Workflow: `.github/workflows/ingest-espn-mma.yml`
Raw namespace: `data/raw/espn_mma/<snapshot_id>/`

The historical pass attempts to preserve:

- yearly scoreboard discovery payloads
- core event details / competitions
- competition status and detailed result
- officials / judges
- sparse play/timeline payloads
- per-fight competitor statistics

The manifest records HTTP coverage and observed stat/play/official vocabularies. Optional missing endpoints remain missing-source evidence rather than zeroes.

### 6. UFC-DataLab OCR scorecard snapshot

Status: **INGESTED / RAW-ONLY PENDING QA**

Source: `komaksym/UFC-DataLab`
Pinned source commit: `3268146c05211de9deab8b9b4c0bb4a954815f0b`
License: MIT
Raw namespace: `data/raw/ufc_datalab_scorecards/3268146c0521/`

Imported only the additive OCR scorecard CSV and upstream license, not the source's duplicate UFCStats datasets.

Important quality finding: sample rows contain obvious fighter-pair/OCR association errors. No row becomes canonical until matched against Greco fight date/opponents and validated. The published CSV contains three judge totals per corner, not a full structured judge-by-round table.

### 7. Historical UFC rankings (TidyTuesday / fightr snapshot)

Status: **INGESTED / RAW-ONLY PENDING PROVENANCE + IDENTITY QA**

Pinned TidyTuesday commit: `107ff6c70de02dd807169e13aee7dc9d86ff88b6`
Raw namespace: `data/raw/tidytuesday_ufc_rankings/107ff6c70de0/`

File: `ufc_rankings_dataset.csv`
Published columns:

- date
- weightclass
- fighter
- rank

Observed coverage begins 2013-02-04. This is useful because each ranking observation has an explicit date, enabling a strict historical as-of join later. Never use the nearest future ranking.

Dataset-specific licensing/provenance remains partially unresolved; preserve the source namespace and use for private research/modeling until clarified further.

### 8. CC0 cross-promotion professional fight history

Status: **INGESTED / RAW-ONLY PENDING IDENTITY + DEDUP QA**

Source: Kaggle `binduvr/pro-mma-fights`, version 1
License: CC0 / Public Domain
Raw namespace: `data/raw/kaggle_pro_mma_fights/v1/`

Verified contents:

- 10,448 fights
- 17 columns
- UFC, Bellator MMA and ONE Championship
- source retrieval through 2021-08-11
- upstream originally scraped from Sherdog

Columns include source URLs, event/promotion/date/location, both fighters, result, method/detail, referee, round and time.

Primary value: pre-UFC and cross-promotion professional experience/context for fighters who later enter the UFC. UFC fights overlapping Greco must be deduplicated rather than counted twice.

---

## Free sources investigated but not yet cleanly ingested

### 9. Official UFC weigh-in result articles

Status: **FREE / HIGH VALUE / JSON:API ARTICLE COLLECTION BLOCKED**

Current UFC pages clearly publish fight-specific scale weights and explicit miss/catchweight/purse-penalty notes.

The JSON:API resource catalog advertises `/jsonapi/node/article`, but a bounded live collection request returned HTTP 403. Therefore the initial plan to enumerate all weigh-in articles directly through JSON:API is **not currently viable**.

A queued filtered article snapshot may also fail for this reason; do not count it as acquired until a raw commit exists.

Still desired:

- actual scale weight per bout
- weight-miss flag
- amount overweight
- second-attempt result when reported
- catchweight indication
- explicit purse-forfeit note

Next free acquisition path should use a respectful official UFC index/search/sitemap or another source with clear redistribution terms, rather than bypassing the 403.

### 10. Official UFC scorecard articles

Status: **FREE / HIGH VALUE / JSON:API ARTICLE COLLECTION BLOCKED**

Official UFC scorecard pages exist publicly, but the same article-collection 403 blocks the clean JSON:API enumeration path.

The already-ingested UFC-DataLab OCR snapshot provides a noisy partial scorecard layer. A future official page/index route or MMA Decisions can fill judge-by-round structure if needed.

### 11. MMA Decisions

Status: **FREE PUBLIC WEBSITE / HIGH VALUE / BULK-USE PATH NOT YET FROZEN**

MMA Decisions exposes event-by-event official judge names and round scores and extends much farther back than UFC's modern scorecard article archive. If ingested, official judge scores must be kept separate from media/fan scoring.

### 12. BestFightOdds archive

Status: **FREE PUBLIC ARCHIVE / MARKET-DIAGNOSTIC VALUE / NOT CORE MODEL INPUT**

BestFightOdds states its stored archive dates to 2007. Potential future use is model-vs-market evaluation, opening/closing line history and retrospective value checks. Sportsbook prices remain outside the independent core forecast model.

### 13. FightMatrix historical rankings

Status: **AVAILABLE / DELIBERATELY DEPRIORITIZED**

FightMatrix publishes historical/proprietary ratings. We now possess dated UFC rankings directly, reducing the need to import a proprietary external rating into the core state engine. FightMatrix can remain a benchmark candidate.

### 14. Broader Sherdog Fight Finder history

Status: **PARTIALLY COVERED BY CC0 SNAPSHOT / FULL WORLDWIDE HISTORY STILL UNRESOLVED**

The CC0 10,448-fight dataset gives us UFC/Bellator/ONE history through August 2021. It does not cover every regional promotion worldwide. A broader Sherdog acquisition should be pursued only if identity/coverage QA shows this remaining gap materially affects UFC debutants.

---

## Current free-data priority order

1. Finish and audit the official UFC `fight_stat` bulk snapshot — this is now the highest-value free data task.
2. Finish and validate the general UFC.com athlete/event/fight snapshot.
3. Finish and validate ESPN history + additive fight surfaces.
4. Crosswalk the three already-ingested additive datasets only after raw acquisition is stable: scorecards, dated rankings, cross-promotion fights.
5. Revisit official weigh-ins via a clean enumeration route because fight-specific scale weights remain a real gap.
6. Use MMA Decisions only if the scorecard QA shows the OCR layer is insufficient.
7. Keep historical odds on a separate market-data track.

## Gate before feature freezing

Every desired data family must be marked one of:

- **INGESTED AND AUDITED**
- **INGESTED RAW / QA REQUIRED**
- **AVAILABLE BUT DELIBERATELY EXCLUDED**
- **ACCESS/PERMISSION REQUIRED**
- **UNAVAILABLE**

No feature specification should depend on an unresolved `we will find it later` source.
