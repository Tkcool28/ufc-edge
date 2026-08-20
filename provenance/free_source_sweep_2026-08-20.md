# UFC Edge — Free Additive Data Sweep

Status date: 2026-08-20 (America/Denver)

Purpose: exhaust the credible **free** additive-data landscape before feature contracts are frozen. This is an acquisition record, not permission to merge fields or use mutable snapshots as historical features.

## Immediately actionable / automated

### 1. Official UFC.com Drupal JSON:API

Status: **PIPELINE ADDED / SNAPSHOT REQUESTED**

Pipeline: `pipelines/ingest_ufc_com.py`
Workflow: `.github/workflows/ingest-ufc-com.yml`
Raw namespace: `data/raw/ufc_com/<snapshot_id>/`

Point-in-time snapshot includes:

- JSON:API resource index (to preserve the exposed resource catalog for later discovery)
- all athlete nodes
- linked athlete FightMetric aggregate stats
- current ranking relationship
- weight class
- fighting style
- gym
- athlete status
- all event nodes
- all fight nodes with red/blue corners and winner relationships

High-value fields beyond Greco include leg reach, gym, style, Octagon debut, official FightMetric identity, current ranking/status context and UFC's own event/fight IDs.

Leakage warning: present-day career totals/rates, rankings, streaks and status are point-in-time state and **must not be backfilled** into older target fights.

### 2. ESPN public MMA APIs

Status: **PIPELINE ADDED / SNAPSHOT REQUESTED**

Pipeline: `pipelines/ingest_espn_mma.py`
Workflow: `.github/workflows/ingest-espn-mma.yml`
Raw namespace: `data/raw/espn_mma/<snapshot_id>/`

The historical pass attempts to preserve, by year:

- scoreboard discovery payloads
- core event details with embedded competitions
- competition status/result detail
- officials/judges
- sparse play/timeline payloads
- per-fight competitor statistics

The manifest also records observed ESPN statistic names, play types, official-position labels, HTTP coverage and source gaps. Optional 404/empty payloads remain coverage evidence rather than being converted to zeroes.

ESPN IDs remain source-specific until a later crosswalk audit.

---

## Free sources found but NOT bulk-ingested yet

### 3. Official UFC weigh-in result articles

Status: **FREE / HIGH VALUE / ACQUISITION PATH TO RESOLVE**

UFC regularly publishes official weigh-in-result pages containing fight-specific scale weights and explicit missed-weight notes. This is directly additive because Greco's fighter `WEIGHT` value is a profile snapshot, not a historical per-fight weigh-in.

Potential uses after a leakage-safe historical parser exists:

- actual scale weight per bout
- weight miss flag
- amount overweight
- second-attempt success when reported
- catchweight indication
- replacement/late-card notes when explicitly reported

Preferred acquisition path: inspect the saved UFC.com JSON:API resource catalog for the news/article content type and obtain article data through the official JSON surface if available. Avoid building a separate HTML crawler until that path is checked.

### 4. Official UFC scorecard articles

Status: **FREE / HIGH VALUE / ACQUISITION PATH TO RESOLVE**

UFC publishes official judges' scorecards for current events. These pages provide official result context and scorecard images/text. This is valuable for the future simulator's decision branch, because Greco contains the fight outcome but not judge-by-judge round scoring.

Potential uses:

- judge identity
- per-round score by judge
- 10-8 / 10-10 frequency
- decision margin
- judge disagreement / split propensity
- decision-model training targets

Preferred acquisition path is again the UFC.com JSON:API article resource if the saved resource catalog exposes it.

### 5. MMA Decisions

Status: **FREE PUBLIC WEBSITE / HIGH VALUE / BULK-USE PATH NOT YET FROZEN**

MMA Decisions has event-by-event decision records dating to the 1990s and exposes judge names, round-by-round scores, referee, tale-of-the-tape context, media scores and fan-score information. The event index currently spans 1995–2026 and includes UFC events throughout that period.

Why it matters:

- broad historical scorecard coverage predating UFC's modern official scorecard article archive
- round-by-round judging labels for decision modeling
- judge identity and disagreement analysis

Do not mix fan/media scores with official judge scores. If this source is ingested, official scorecards must be a separate table/field family and raw HTML retained for audit.

### 6. BestFightOdds archive

Status: **FREE PUBLIC ARCHIVE / MARKET-DIAGNOSTIC VALUE / NOT CORE MODEL INPUT**

BestFightOdds states that all odds posted on the site are stored in its archive and that the archive dates back to 2007.

Potential use:

- historical opening/closing market baseline
- model-vs-market evaluation
- retrospective price/value analysis
- market-efficiency diagnostics

Policy for UFC Edge: sportsbook prices remain **outside the independent core forecast model**. Historical odds may be stored later in a separate market namespace and joined only for evaluation/diagnostics.

### 7. FightMatrix historical rankings

Status: **FREE WEB RANKINGS / PROPRIETARY RATING / API NOW ASSOCIATED WITH POLYDATA**

FightMatrix publishes current and generated historical rankings and multiple rating systems. It is attractive for opponent-strength and pre-UFC context, but the rating engine is proprietary and 2026 API access is being offered through a PolyData partnership.

Use, if any, should be as an external benchmark/context source rather than silently importing a proprietary rating into UFC Edge's own core state engine.

### 8. Sherdog Fight Finder

Status: **FREE PUBLIC FIGHT-RESULT DATABASE / POSSIBLE NON-UFC HISTORY SOURCE / BULK PATH NOT YET APPROVED**

Sherdog describes Fight Finder as a free worldwide fight-results database. Its main value to UFC Edge would be pre-UFC / non-UFC professional history that UFCStats does not contain.

Potential additive fields:

- complete professional fight chronology before UFC entry
- promotion/event outside UFC
- method/round/time
- opponent identity

This could improve experience, layoff, streak, durability and strength-of-schedule state at a fighter's UFC debut. A stable identity resolver and respectful acquisition method are required before bulk ingestion.

---

## Current free-data priority order

1. Finish and validate UFC.com raw snapshot.
2. Finish and validate ESPN raw snapshot + schema/coverage summary.
3. Inspect the stored UFC.com JSON:API index for article/news resources that can expose official weigh-in and scorecard pages without HTML crawling.
4. If UFC's official historical scorecard coverage is incomplete, evaluate MMA Decisions as the historical judge-scorecard supplement.
5. Evaluate Sherdog only if Greco/UFCStats + UFC.com/ESPN leave an unacceptable pre-UFC history gap.
6. Keep BestFightOdds in a separate market-data track for later model-vs-market work.
7. Treat FightMatrix as a benchmark candidate, not a required input.

## Gate before feature freezing

A data family should be marked one of:

- **INGESTED AND AUDITED**
- **AVAILABLE BUT DELIBERATELY EXCLUDED**
- **ACCESS/PERMISSION REQUIRED**
- **UNAVAILABLE**

No feature specification should depend on an unresolved `we will find it later` data source.
