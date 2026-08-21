# UFC Edge — Free Data Acquisition Closeout

Status date: **2026-08-21 (America/Denver)**

Purpose: replace stale operational assumptions from the 2026-08-20 sweep with the current evidence-based acquisition status. This is the boundary between **source hunting** and **canonical QA / point-in-time shaping**. It is not a feature freeze.

The governing rule remains: no planned feature family may depend on a source described only as “we will find it later.” Every material data family must be classified as acquired, explicitly QA-gated, deliberately excluded/deferred, permission-gated, or unavailable.

---

## Executive status

The credible free-data landscape needed for the current UFC model plan is now substantially exhausted.

Core UFC history, official fighter/event/fight identity surfaces, round statistics, rich FightMetric fields, ESPN MMA history, dated rankings, cross-promotion UFC/Bellator/ONE history, companion source profiles, and a full official UFC sitemap content catalog are physically stored in the repo.

The only active bulk acquisition at this closeout is the already-enumerated official UFC article series:

- **716 weigh-in article candidates**
- **583 scorecard article candidates**

Both are fetched only from a frozen official UFC sitemap catalog in immutable bounded chunks. No additional source discovery is required to complete those two families.

---

# A. INGESTED AND AUDITED / CORE-READY AS SOURCE EVIDENCE

## A1. Greco1899 / UFCStats historical backbone

**Status: INGESTED AND AUDITED — PRIMARY FOR SHARED ROUND COUNTS**

Pinned source commit:

`8e40eb945e1127bf0ef172ab211a34787948f312`

Raw namespace:

`data/raw/greco1899/8e40eb945e11/`

Primary role:

- UFC events / fights / results
- fighter-round strike counts
- takedown counts
- submission attempts
- reversals
- knockdowns
- significant-strike target/position splits
- precise `M:SS` control time

Shared Greco count fields were independently reconciled against the official UFC FightMetric archive over tens of thousands of exact fighter-round alignments and agree at roughly 99.35%–100% depending on field. Greco remains primary for this shared family because it is pinned, clean at exact fighter/round grain, and preserves second-level control precision.

See:

- `provenance/source_precedence_v0.md`
- `provenance/audits/ufc_greco_round_overlap_latest.json`

---

## A2. Official UFC FightMetric `fight_stat`

**Status: INGESTED AND AUDITED — ADDITIVE / QA / RICH-FIELD SOURCE**

Snapshot:

`data/raw/ufc_fightmetric_official/20260820T123046Z/`

Inventory:

- 57,382 `fight_stat` rows
- 1,148 pages
- 8,008 distinct non-null FightMetric IDs
- 54,187 identified rows
- 3,195 unidentified rows

Unidentified-row audit established that all 3,195 unidentified rows carry only a Drupal internal ID and no meaningful round/color/stat payload. They are raw/QA only.

Identity audit:

- official UFC fight rows: 12,069
- UFC fights with a FightMetric ID: 9,744
- distinct UFC FightMetric IDs: 9,612
- direct overlap with official `fight_stat`: 8,005 IDs
- one-to-one identity candidates: 7,913

Corner transport semantics are verified:

- `color = 0` → red corner
- `color = 1` → blue corner

This mapping won 99.566% exact agreement over 250,782 shared field comparisons versus 11.725% for the reversed orientation.

### Positional-time semantics

The archived positional `_time` family is **not exact seconds**.

Cross-source control evidence:

- raw `control_time == floor(Greco control_seconds / 60)` on 23,268 / 23,876 aligned comparisons = **97.454%**.

Quality audit of identified actual-round rows further shows a dominant 0–5 round-scale bucket representation:

- minimum 0–5 fraction across audited positional time fields: **99.621%**
- most fields: **99.88%–99.99%** in 0–5
- sparse values above 5 are quarantined as source anomalies pending independent proof
- on clean 0–5 rows, `standing - (distance + clinch)` is always within one bucket
- clean ground-control positional decomposition is within one bucket in **98.163%** of comparisons

Decision:

- preserve all official raw values;
- do not synthesize seconds;
- `>5` actual-round time values are not canonical eligible;
- a later coarse-exposure representation may use validated 0–5 buckets explicitly as coarse data;
- Greco remains the precise control-second source.

See:

- `provenance/audits/fightmetric_position_time_quality_latest.json`
- `schemas/source_field_map_v0.json`

---

## A3. Complete official UFC fight resource snapshot

**Status: INGESTED AND AUDITED AS RAW IDENTITY/CONTEXT EVIDENCE**

Snapshot:

`data/raw/ufc_com_resources/fights/20260821T055500Z/`

- complete collection snapshot
- 12,069 fight rows
- 242 pages
- 7 durable chunks
- red-corner athlete relationship IDs: 11,441
- blue-corner athlete relationship IDs: 11,377
- final-winner relationship IDs: 8,640

The collection is intentionally not treated as a clean one-row-per-FightMetric-ID canonical table: 128 duplicate FightMetric-ID groups exist, and 121 of those have semantic conflicts on compared fight fields. No automatic newest-wins/dedup rule is promoted.

---

## A4. Official UFC athlete and event resource snapshots

**Status: INGESTED / DIRECT OFFICIAL IDENTITY + PROFILE EVIDENCE**

Namespaces:

- `data/raw/ufc_com_resources/athletes/20260820T194553Z/`
- `data/raw/ufc_com_resources/events/20260820T194553Z/`

Athlete surface includes official source identifiers and profile/context fields such as DOB, height, arm reach, leg reach, listed weight, Octagon debut, residence/origin and relationships to gym/style/status/ranking/stat resources.

Current career aggregates/rank/status are point-in-time observations and are never backfilled into older fights.

Direct fight→event relationship audit produced 8,909 unique dated bridge rows. Missing event membership remains missing; title/name inference is prohibited.

---

## A5. ESPN public MMA historical snapshot

**Status: INGESTED RAW / SCHEMA INVENTORY AUDITED**

Snapshot:

`data/raw/espn_mma/20260820T123114Z/`

Coverage:

- 1993–2026
- 911 UFC events
- 9,412 competitions
- 18,794 successful competitor-stat responses
- officials and sparse structural play endpoints preserved

Observed useful concepts include:

- knockdowns
- takedown attempts / takedowns
- submission attempts
- reversals
- distance/clinch/ground breakdowns
- time in control
- advances to back/half guard/mount/side
- judges and referees
- sparse timeline events such as round start/end, knockdown, takedown attempt, submission attempt, reversal and fight completion

ESPN remains a separate provider namespace until identity and field-semantic crosswalks pass. Sparse plays are not mislabeled as strike-by-strike action data.

---

## A6. Official UFC sitemap content catalog

**Status: INGESTED AND COMPLETE FOR CURRENT OFFICIAL CONTENT DISCOVERY**

Snapshot:

`data/raw/ufc_content_catalog/20260821T205500Z/`

Derived candidate catalog:

`data/derived/discovery/ufc_content_candidates.csv`

Inventory:

- 67,702 distinct official UFC sitemap URLs
- 716 weigh-in article candidates
- 583 scorecard article candidates

This supersedes attempts to enumerate `/jsonapi/node/article`, whose collection route returns HTTP 403. The 403 is not bypassed; the public official sitemap is the legitimate enumeration surface.

---

# B. INGESTED RAW / QA REQUIRED BEFORE CANONICAL USE

## B1. Historical UFC rankings

**Status: INGESTED RAW / POINT-IN-TIME + IDENTITY QA REQUIRED**

Source: TidyTuesday / `fightr`

Raw namespace:

`data/raw/tidytuesday_ufc_rankings/107ff6c70de0/`

Observed coverage begins 2013-02-04.

Historical rule: use only ranking observations strictly available before the prediction cutoff. Nearest-future joins are prohibited.

---

## B2. CC0 UFC/Bellator/ONE professional fight history

**Status: INGESTED RAW / IDENTITY + DEDUP + TEMPORAL QA REQUIRED**

Source: Kaggle `binduvr/pro-mma-fights`, version 1

License: CC0 / Public Domain

Raw namespace:

`data/raw/kaggle_pro_mma_fights/v1/`

- 10,448 professional fights
- through 2021-08-11
- UFC, Bellator MMA and ONE Championship
- source URLs retained

Primary role: provide legitimate free pre-UFC/cross-promotion experience for later UFC fighters. UFC overlaps are deduplicated against the UFC-specific backbone during canonicalization.

---

## B3. CC0 companion fighter profiles

**Status: INGESTED RAW / IDENTITY SUPPORT ONLY UNTIL TEMPORAL QA**

Source: Kaggle `binduvr/pro-mma-fighters`, version 1

License: CC0 / Public Domain

Raw namespace:

`data/raw/kaggle_pro_mma_fighters/v1/`

- 5,151 fighters
- 22 columns
- source state through 2021-08-11

Profile URLs/names/physical/context fields may support cross-promotion identity matching. Career wins/losses and aggregates are 2021 snapshot totals and **must never be injected into historical pre-fight targets**.

---

## B4. UFC-DataLab OCR scorecard snapshot

**Status: INGESTED RAW / NOISY SECONDARY EVIDENCE**

Source: `komaksym/UFC-DataLab`

License: MIT

Raw namespace:

`data/raw/ufc_datalab_scorecards/3268146c0521/`

Known issue: obvious OCR/fighter-pair association failures exist. No OCR row is canonical until it independently matches fight identity/date/opponents and score plausibility. The published CSV contains judge totals rather than a complete clean judge-by-round relational table.

Official UFC scorecard articles/images are preferred for the new raw archive.

---

# C. ACTIVE FINITE ACQUISITION — NO MORE SOURCE HUNTING REQUIRED

## C1. Official UFC fight-specific weigh-in reports

**Status: ACTIVE BOUNDED INGESTION**

Series:

`20260821T210000Z`

State:

`provenance/ufc_official_articles_active_series.json`

Candidates: **716**

Collector:

`pipelines/ingest_ufc_official_articles_chunked.py`

Raw target:

`data/raw/ufc_official_articles/20260821T210000Z/weigh_in/`

Desired later extraction includes actual scale weight, missed-weight flag, amount overweight, catchweight language, second-attempt result where stated, and purse-penalty text. Article text remains raw until a separate deterministic parser/identity audit is built.

---

## C2. Official UFC scorecard articles

**Status: ACTIVE BOUNDED INGESTION**

Same series and collector as weigh-ins.

Candidates: **583**

Raw target:

`data/raw/ufc_official_articles/20260821T210000Z/scorecard/`

Raw HTML is the first official layer. Scorecard images/links and structured judge-round extraction require a separate acquisition/parser audit; OCR output is not assumed correct.

---

# D. AVAILABLE BUT DELIBERATELY EXCLUDED / DEFERRED

## D1. Full worldwide/regional Sherdog fight history

**Status: DEFERRED — NO CLEAN LIVE REDISTRIBUTABLE FREE SOURCE ESTABLISHED**

A previously published all-Sherdog derived dataset was identified in external research, but the original Kaggle dataset has since been deleted. Do not build a required feature family around a vanished source or an unverified mirror.

The legitimate CC0 UFC/Bellator/ONE snapshot remains the free pre-UFC/cross-promotion layer for now.

If later debutant analysis proves that missing regional history materially harms calibration, reopen this as an explicit acquisition task rather than silently imputing experience.

---

## D2. MMA Decisions

**Status: DELIBERATELY NOT BULK-INGESTED**

The public site provides useful judge-by-round structure, but the conservative bulk-use/robots probe did not establish a clean ingestion path. Do not bypass the site restriction. Official UFC scorecard material is now being acquired instead.

---

## D3. BestFightOdds

**Status: DEFERRED TO MARKET-DATA TRACK**

Useful later for opening/closing line diagnostics and model-vs-market evaluation. It is not a core independent forecast input and is not required to begin feature/model construction.

---

## D4. FightMatrix

**Status: DELIBERATELY DEPRIORITIZED**

Potential benchmark only. Dated historical UFC rankings already provide a cleaner free point-in-time ranking family without importing a proprietary external rating engine into core state.

---

# E. ACCESS/PERMISSION-GATED SOURCES — LATER PASS

The user explicitly deferred these until after the free-data pass:

1. FightGeek PRECISION
2. Stats Fight
3. IMG Arena / Sportradar

They remain optional future enhancements, especially if simulator validation shows that coarse free position exposure or missing ordered action sequences are a limiting factor.

No current feature specification should assume those sources will be obtained.

---

# F. What the free pass now supports

Without the three deferred premium sources, the repo now has enough legitimate free evidence to build and validate the planned first-generation mechanical baseline using:

- exact UFC fight outcomes/method/round/time
- fighter-round strikes, KD, TD, sub-attempt, reversal and precise control statistics
- round-specific persistence/fade behavior
- official identity/profile/context surfaces
- dated ranking observations
- cross-promotion experience for UFC/Bellator/ONE fighters
- ESPN independent result/stat/official/sparse-transition evidence
- rich official UFC positional/control buckets for later coarse phase-exposure modeling, with anomaly quarantine
- finite official weigh-in/scorecard article archives currently being drained

What free data **does not** provide cleanly is a universally precise second-by-second ordered action stream. That limitation must remain visible when designing Simulator V1; it is not filled by invented timing.

---

# G. Gate to leave source hunting

After the active official weigh-in and scorecard article families reach their family-level completeness manifests, the free **acquisition** pass is closed.

The next work is not more broad source hunting. It is:

1. canonical identity/crosswalk QA;
2. deterministic parsing and source-semantic normalization;
3. point-in-time replay/leakage gates;
4. coverage masks/sample-quality metadata;
5. only then shaping and freezing feature families.

Any unresolved data family above is already explicitly classified, so feature design can fail closed rather than depend on a hypothetical future source.
