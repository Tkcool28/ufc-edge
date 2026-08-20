# UFC Edge — Free Additive Data Sweep

Status date: 2026-08-20 (America/Denver)

Purpose: exhaust the credible **free** additive-data landscape before feature contracts are frozen. This is an acquisition record, not permission to merge fields or use mutable snapshots as historical features.

## Self-reporting rerun update

The acquisition workflows now persist terminal diagnostics under `provenance/runs/` and fail closed when a pull is incomplete.

Current evidence:

- **Official UFC FightMetric rich stats: SUCCESS / RAW SNAPSHOT LANDED.** Self-reporting run `32369217813` completed with exit code 0. Snapshot `data/raw/ufc_fightmetric_official/20260820T123046Z/` contains a manifest plus **57,382 `fight_stat` rows across 1,148 pages and 8,008 distinct non-null FightMetric IDs**. The main Time In Position/control fields are populated on about **64.8%** of rows overall; most standard strike/takedown/submission families are populated on about **94.4%**. This is now a real official historical source, not merely a schema lead. It remains RAW/QA until identity, round semantics, era coverage and overlap with Greco are audited.
- **General UFC.com athlete/event/fight acquisition: PROCESS TIMEOUT / NOT LANDED.** Run `32369240290` hit the 2,100-second process timeout. It fully collected **4,160 athletes across 84 pages** and **799 events across 16 pages**, then timed out while snapshotting fights. No HTTP rejection is present in the diagnostic. Fail-closed behavior prevented partial promotion.
- **ESPN MMA acquisition: terminal diagnostic not yet present at this check.** Its configured process window has not yet been exhausted, so it remains pending rather than failed.
- **Official UFC article JSON:API route remains BLOCKED** by HTTP 403 and was intentionally not rerun.

## Acquisition status

### 1. Greco1899 / UFCStats backbone

Status: **INGESTED**

Pinned round/fight/event/fighter source remains the current historical backbone and a future cross-source QA layer. It does not contain ordered intra-round actions or the richer official Time In Position vocabulary.

### 2. Official UFC.com Drupal JSON:API — resource catalog

Status: **VERIFIED / RESOURCE CATALOG STORED**

Probe artifacts:

- `provenance/ufc_jsonapi_resource_probe.json`
- `provenance/ufc_jsonapi_resource_probe.raw.json`

Verified sport surfaces include:

- `/jsonapi/node/athlete`
- `/jsonapi/node/event`
- `/jsonapi/node/fight`
- `/jsonapi/athlete_stat/athlete_stat`
- `/jsonapi/athlete_ranking/athlete_ranking`
- `/jsonapi/fight_stat/fight_stat`
- `/jsonapi/fight_roundboard/fight_roundboard`
- `/jsonapi/node/article` — advertised but collection access returns HTTP 403

### 3. Official UFC.com rich FightMetric `fight_stat`

Status: **INGESTED RAW / COVERAGE + IDENTITY QA REQUIRED**

Pipeline: `pipelines/ingest_ufc_fight_stat.py`
Workflow: `.github/workflows/ingest-ufc-fightmetric.yml`
Snapshot: `data/raw/ufc_fightmetric_official/20260820T123046Z/`
Self-report diagnostic: `provenance/runs/ufc_fightmetric_32369217813.json`

Manifest summary:

- `fight_stat`: **57,382 rows**, **1,148 pages**, **8,008 distinct non-null FightMetric IDs**
- `fight_roundboard`: **374 rows**, **8 pages**, **131 distinct non-null FightMetric IDs**
- FightMetric ID coverage in `fight_stat`: **54,187 / 57,382 = 94.43%**
- standard head/body/leg significant-strike and takedown/submission fields: roughly **94.4%** populated
- knockdowns: **85.45%** populated
- reversals: **84.13%** populated
- standups: **62.11%** populated

**Time / position coverage**

The following are each populated on **37,195 / 57,382 = 64.82%** of rows:

- `standing_time`
- `distance_time`
- `clinch_time`
- `control_time`
- `ground_ctl_time`
- `guard_ctl_time`
- `half_guard_ctl_time`
- `side_ctl_time`
- `mount_ctl_time`
- `back_ctl_time`

Additional TIP coverage:

- `neutral_time`: **64.80%**
- miscellaneous ground-control time: **63.95%**
- `ground_time`: **29.92%**

**Grappling**

- takedown attempts / landed
- submission attempts
- reversals
- standups

**Striking**

- significant and total attempts / landed
- head / body / leg
- distance / clinch / ground
- richer position/weapon/target combinations
- knockdowns

Some richer weapon-position combinations are substantially sparser: several kick-oriented families are ~31.5% populated and several detailed distance punch/kick combination families are ~3.9%. These must be treated as era/availability-dependent features rather than zero-filled history.

**Decision**

This source is now the leading free candidate for official rich UFC fighter-round/stat data and future simulator calibration. Before canonical promotion, audit:

1. FightMetric-to-fight/fighter identity mapping;
2. the meaning of round `0` rows;
3. non-null coverage by historical era;
4. overlapping values against Greco/UFCStats;
5. whether TIP fields are semantically consistent through time.

`fight_roundboard` remains a record-book/ranking surface, not full fighter-round history.

### 4. Official UFC.com athlete/event/fight point-in-time snapshot

Status: **PROCESS TIMEOUT / NOT LANDED; SOURCE ITSELF READABLE**

Pipeline: `pipelines/ingest_ufc_com.py`
Workflow: `.github/workflows/ingest-ufc-com.yml`
Diagnostic: `provenance/runs/ufc_com_32369240290.json`

Run evidence:

- athletes: **4,160 records across 84 pages completed**
- events: **799 records across 16 pages completed**
- timeout occurred after entering `snapshotting fights...`
- result: `process_timeout`
- exit code: `124`
- configured process timeout: **2,100 seconds / 35 minutes**

This is a pagination/runtime design problem, not evidence that UFC blocked the athlete/event APIs. Because the workflow is atomic, completed athlete/event data were correctly not promoted after the fights phase failed to finish.

**Next engineering fix:** split athlete/event/fight pulls into independently committable, checkpointed units or add resumable fight pagination. Do not solve this by blindly increasing the monolithic timeout.

Targeted additive fields remain leg reach, gym, style, Octagon debut, official FightMetric identity, event/fight IDs and current context.

Leakage warning: current career totals/rates, rankings, streaks and status are point-in-time state and **must not be backfilled** into older target fights.

### 5. ESPN public MMA APIs

Status: **SELF-REPORTING RERUN PENDING**

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

Do not promote or mark failed until the terminal diagnostic commit appears. If successful, inspect event-year coverage, endpoint success/failure counts, stat vocabulary, official coverage and sparse-play behavior before use.

### 6. UFC-DataLab OCR scorecard snapshot

Status: **INGESTED / RAW-ONLY PENDING QA**

Source: `komaksym/UFC-DataLab`
Pinned source commit: `3268146c05211de9deab8b9b4c0bb4a954815f0b`
License: MIT
Raw namespace: `data/raw/ufc_datalab_scorecards/3268146c0521/`

Sample rows contain obvious fighter-pair/OCR association errors. No row becomes canonical until matched independently against fight date/opponents and score plausibility. The CSV provides three judge totals per corner rather than a clean structured judge-by-round table.

### 7. Historical UFC rankings (TidyTuesday / fightr snapshot)

Status: **INGESTED / RAW-ONLY PENDING PROVENANCE + IDENTITY QA**

Pinned TidyTuesday commit: `107ff6c70de02dd807169e13aee7dc9d86ff88b6`
Raw namespace: `data/raw/tidytuesday_ufc_rankings/107ff6c70de0/`

Columns: date, weightclass, fighter, rank. Observed coverage begins 2013-02-04. Use only strict historical as-of joins; never nearest future ranking.

### 8. CC0 cross-promotion professional fight history

Status: **INGESTED / RAW-ONLY PENDING IDENTITY + DEDUP QA**

Source: Kaggle `binduvr/pro-mma-fights`, version 1
License: CC0 / Public Domain
Raw namespace: `data/raw/kaggle_pro_mma_fights/v1/`

Verified contents:

- **10,448 fights**
- 17 columns
- UFC, Bellator MMA and ONE Championship
- source retrieval through 2021-08-11
- upstream originally scraped from Sherdog

Primary value: pre-UFC and cross-promotion professional experience. UFC fights overlapping Greco must be deduplicated.

---

## Free sources investigated but not yet cleanly ingested

### 9. Official UFC weigh-in result articles

Status: **FREE / HIGH VALUE / JSON:API ARTICLE COLLECTION BLOCKED**

Public UFC pages publish fight-specific scale weights and miss/catchweight/purse-penalty notes. `/jsonapi/node/article` returns HTTP 403 for collection access. Do not bypass it.

Still desired:

- actual scale weight per bout
- weight-miss flag
- amount overweight
- second-attempt result when reported
- catchweight indication
- explicit purse-forfeit note

Next free acquisition path should use a legitimate official UFC index/search/sitemap or another source with clear redistribution terms.

### 10. Official UFC scorecard articles

Status: **FREE / HIGH VALUE / JSON:API ARTICLE COLLECTION BLOCKED**

Public official scorecard pages exist, but JSON:API enumeration is blocked. UFC-DataLab OCR provides a noisy partial layer. MMA Decisions remains a cleaner potential source for judge-by-round structure.

### 11. MMA Decisions

Status: **FREE PUBLIC WEBSITE / HIGH VALUE / BULK-USE PATH NOT YET FROZEN**

Exposes event-by-event official judge names and round scores. Official judge data must remain separate from media/fan scoring.

### 12. BestFightOdds archive

Status: **FREE PUBLIC ARCHIVE / MARKET-DIAGNOSTIC VALUE / NOT CORE MODEL INPUT**

Potential use: opening/closing line history and model-vs-market evaluation. Sportsbook prices remain outside the independent core forecast model.

### 13. FightMatrix historical rankings

Status: **AVAILABLE / DELIBERATELY DEPRIORITIZED**

Useful as a benchmark, but dated UFC rankings reduce the need to import proprietary external ratings into core state.

### 14. Broader Sherdog Fight Finder history

Status: **PARTIALLY COVERED BY CC0 SNAPSHOT / FULL WORLDWIDE HISTORY UNRESOLVED**

The CC0 dataset covers UFC/Bellator/ONE through August 2021, not all regional promotions. Broader acquisition should be pursued only if identity/coverage QA shows the gap materially affects UFC debutants.

---

## Current free-data priority order

1. **Audit the landed official UFC FightMetric snapshot**: identity crosswalk, round-0 semantics, coverage by era and Greco overlap.
2. **Refactor UFC.com athlete/event/fight ingestion** into split or resumable collections; do not blindly rerun the same monolithic timeout path.
3. **Inspect ESPN's terminal self-report when it appears**; do not start another run in the meantime.
4. Crosswalk scorecards, dated rankings and cross-promotion fights after raw acquisition is stable.
5. Revisit official weigh-ins through a clean non-403 route.
6. Use MMA Decisions if OCR scorecard QA proves insufficient.
7. Keep historical odds on a separate market-data track.

## Gate before feature freezing

Every desired data family must be marked one of:

- **INGESTED AND AUDITED**
- **INGESTED RAW / QA REQUIRED**
- **AVAILABLE BUT DELIBERATELY EXCLUDED**
- **ACCESS/PERMISSION REQUIRED**
- **UNAVAILABLE**

No feature specification should depend on an unresolved `we will find it later` source. The landed FightMetric data materially improves the simulator outlook, but contracts should not treat its sparse/era-dependent fields as universally available until the coverage audit is complete.
