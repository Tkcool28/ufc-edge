# UFC Edge — Data Source Manifest

Status date: 2026-08-20 (America/Denver)

Purpose: durable manifest of every material data source investigated during the acquisition pass: what landed, what failed, why, what each source contains, likely use, and how much UFC Edge should trust future refreshes.

Detailed evidence lives in source lock files, immutable raw manifests, `provenance/runs/`, `provenance/audits/`, `provenance/free_source_sweep_2026-08-20.md`, and `provenance/acquisition_closeout_2026-08-20.md`.

## Rating key

Independent 1–5 ratings:

- **Authority** — closeness to the official event/stat producer.
- **History** — demonstrated historical completeness for the fields we care about.
- **Refresh** — expected reliability of obtaining future data with consistent semantics.

`?` means we do not yet have enough evidence to score defensibly.

## Current source table

| Source | Current status | Authority | History | Refresh | Intended role | What it gives UFC Edge |
|---|---|---:|---:|---:|---|---|
| **Official UFC FightMetric `fight_stat`** | **INGESTED RAW / SEMANTICS AUDITED / IDENTITY + ERA QA PENDING** | 5 | 4? | 4 | **PRIMARY candidate** | 57,382 official rows; 8,008 FightMetric IDs; rich round/fight stats; detailed striking; TD/sub/reversal/standup; Time In Position and positional control. |
| **Official UFC `fight_roundboard`** | **INGESTED RAW / RECORD-BOOK SURFACE** | 5 | 2 | 4 | ADDITIVE / QA | 374 record-book rows / 131 FightMetric IDs. Not a complete fighter-round table. |
| **Official UFC fight/event/athlete JSON:API** | **PUBLIC; RESOURCE-SCOPED ACQUISITION RUNNING** | 5 | ? | 4? | PRIMARY identity/context | Prior monolithic run proved 4,160 athletes and 799 events readable, then timed out while collecting fights. Refactored runner now commits fights/events/athletes independently. |
| **Greco1899 / UFCStats scrape** | **INGESTED** | 3 | 4 | 3 | Historical PRIMARY today; future SECONDARY/QA if UFC wins overlap audit | Pinned event/fight/result/fighter/TOTT/round aggregates with stable UFCStats source URLs. No rich TIP or atomic chronology. |
| **ESPN public MMA APIs** | **INGESTED RAW / ADDITIVE SEMANTICS QA PENDING** | 4 | 4 | 3 | ADDITIVE / QA | 911 UFC events / 9,412 competitions, 1993–2026; officials; results; competitor stats; position advances; sparse structural plays. |
| **UFC-DataLab OCR scorecards** | **INGESTED RAW / QA REQUIRED** | 2 | 3 | 2 | RAW ONLY until validation | Three judge totals per corner; known OCR/fighter-pair association errors. |
| **TidyTuesday / fightr historical UFC rankings** | **INGESTED RAW / QA REQUIRED** | 3 | 4 from 2013+ | 2 | ADDITIVE historical context | Dated weight-class rankings; strict past-only as-of joins. |
| **CC0 `binduvr/pro-mma-fights`** | **INGESTED RAW / QA REQUIRED** | 2 | 3 | 1 | ADDITIVE | 10,448 UFC/Bellator/ONE fights through 2021-08-11; pre-UFC/cross-promotion experience after identity + dedup QA. |
| **CC0 `binduvr/pro-mma-fighters`** | **INGESTED RAW / TEMPORAL QA REQUIRED** | 2 | 3 | 1 | ADDITIVE / identity aid | 5,151 companion fighter profiles, 22 columns, source URLs, DOB, physicals, association, weight class, 2021 snapshot career breakdowns. |
| **Official UFC weigh-in articles** | **PUBLIC CONTENT / JSON:API ARTICLE COLLECTION BLOCKED** | 5 | ? | 2 | Desired PRIMARY for weigh-ins | Exact scale weights, misses, amount over, catchweights, second attempts, purse penalties. Need a clean official enumeration route. |
| **Official UFC scorecard articles** | **PUBLIC CONTENT / JSON:API ARTICLE COLLECTION BLOCKED** | 5 | ? | 2 | Desired PRIMARY for judge scorecards | Official scorecard pages exist; clean bulk enumeration route unresolved. |
| **MMA Decisions** | **PUBLIC / NOT INGESTED** | 3 | 4 | 3 | Potential judge-score ADDITIVE/SECONDARY | Official judge names + round-by-round scores; media/fan scores must remain separately typed. |
| **BestFightOdds** | **PUBLIC / NOT INGESTED** | 3 | 4 since ~2007 | 3 | MARKET DATA ONLY | Historical prices for later model-vs-market/value evaluation, never core forecast inputs. |
| **FightMatrix** | **AVAILABLE / DEPRIORITIZED** | 3 | 4 | 3 | REFERENCE | External proprietary ratings benchmark. |
| **FightGeek PRECISION** | **ACCESS/PERMISSION REQUIRED** | 4 | 4? | 2 | Future sequential source | Timestamped historical actions, position/stance time, counters, combinations. |
| **FightGeek SPEED** | **ACCESS/PERMISSION REQUIRED / TRIAL** | 4 | 2? | 3 | Future first-party collection candidate | Real-time/retroactive smaller action vocabulary. |
| **Sportradar / IMG Arena UFC Fight Stats** | **ACCESS/PERMISSION REQUIRED** | 5 | ? | 5 if licensed | Future official live PRIMARY | Official live rich FightMetric/TIP feed. |
| **IMG Arena Fight Actions / Details** | **ACCESS REQUIRED; UFC EQUIVALENT NOT VERIFIED** | 5 if verified | ? | ? | Future sequential source | Event-level state/action data documented for combat products; UFC entitlement unresolved. |
| **Stats Fight** | **ACTIVE / BULK ACCESS UNRESOLVED** | 3 | ? | 2 | Future additive possibility | Rich action/position presentation; no public bulk raw route found. |
| **CageIntel** | **REFERENCE ONLY / DEAD LEAD** | 1 | 1 | 1 | None | Domain parked/for sale. |
| **Live blogs** | **DELIBERATELY EXCLUDED as canonical** | 1–2 | 2 | 2 | Reference only | Editorially incomplete/inconsistent chronology. |

---

# 1. Official UFC FightMetric — current leading stats source

Successful self-reporting run: `32369217813`  
Raw snapshot: `data/raw/ufc_fightmetric_official/20260820T123046Z/`

Authoritative `fight_stat` manifest:

- **57,382 rows** / **1,148 pages**
- **8,008 distinct non-null FightMetric IDs**
- round counts: `0=16,229`, `1=16,229`, `2=11,572`, `3=8,873`, `4=690`, `5=594`
- FightMetric ID populated on **54,187 / 57,382 = 94.43%**
- core classic fields are generally highly populated, but coverage is field-specific; e.g. `sig_str_att` itself is only about **66.49%** while `sig_str_land` is about **94.43%**
- main TIP/control family is approximately **64.82%** populated overall
- `ground_time` is only **29.92%**
- some richer weapon/context families are around **31.5%**, and some very specific distance combinations around **3.86%**

Never infer zero from any missing official field.

`fight_roundboard` is only **374 rows / 131 FightMetric IDs** and is explicitly classified as record-book/additive data, not complete fighter-round history.

## Round `0` is resolved

Audit artifacts:

- `provenance/audits/fightmetric_semantics_latest.json`
- `provenance/audits/fightmetric_semantics_latest.md`

Verdict: **round `0` is supported as the source-provided per-fighter fight summary row**, not a real round.

Evidence:

- **15/16** well-powered count-field families support summary additivity at the audit threshold.
- **13/13** time-field families support summary additivity once source rounding is handled explicitly.
- Position-time summary fields often differ from the sum of rounded round values by about one second, so an exact-only test was rejected as too strict.

Canonical contract implication:

1. exclude `round=0` from canonical fighter-round records;
2. preserve it separately as a source summary/QA record;
3. derive modeling fight totals from validated rounds `1+`;
4. when source summary and derived totals disagree, do not silently overwrite either;
5. permit explicit second-level tolerance for time-summary QA only where validated.

## Conflicting FightMetric source versions

Audit artifacts:

- `provenance/audits/fightmetric_duplicate_versions_latest.json`
- `provenance/audits/fightmetric_duplicate_versions_latest.md`

Found **714 conflicting `(fightmetric_id, color, round)` keys across 109 FightMetric fight IDs**. They are not byte-identical duplicates.

Version evidence:

- newest Drupal row has more non-null metric fields on **672/714 = 94.12%** of conflicting keys;
- newest Drupal row has more TIP fields on **672/714 = 94.12%**;
- newest Drupal row never has fewer TIP fields in this audit.

This strongly resembles a later enrichment/correction pass, but **no automatic `highest Drupal internal ID wins` rule is frozen yet**. We must first map the rows to actual fights and compare shared statistics against Greco/UFCStats. Raw preserves every conflicting source row.

## Remaining FightMetric gates

1. acquire official fight identity resource;
2. prove FightMetric ID ↔ official fight/corner/athlete cardinality;
3. attach official event dates;
4. quantify TIP/basic-stat coverage by actual calendar year/era;
5. cross-check shared round stats against Greco;
6. use that overlap to validate or reject a source-version selection rule;
7. only then decide which statistical families can promote official UFC over Greco.

---

# 2. Official UFC fight/event/athlete identity data

Original monolithic run `32369240290` proved:

- **4,160 athletes / 84 pages** readable;
- **799 events / 16 pages** readable;
- process then exceeded its explicit 2,100-second window while collecting fights;
- there was no evidence of an HTTP 403/429 failure in that diagnostic.

The original all-or-nothing acquisition design was the failure, not source availability.

## Resource-scoped replacement

Current implementation:

- `pipelines/ingest_ufc_com_resource.py`
- `.github/workflows/ingest-ufc-com.yml`
- raw namespaces `data/raw/ufc_com_resources/{fights,events,athletes}/<snapshot_id>/`

Rules:

- fights run first because they are the critical FightMetric identity bridge;
- each collection receives its own bounded process window;
- each successful collection commits immediately with a manifest;
- each run writes durable status/log diagnostics;
- partial failed raw directories are not promoted;
- a failure in one collection cannot erase completed collections.

Prepared follow-on audit:

- `pipelines/audit_ufc_fight_identity_surface.py`
- `.github/workflows/audit-ufc-fight-identity.yml`

Once a complete fight snapshot lands, the audit inventories direct FightMetric fields, official fight UUIDs, corners, athlete relationships, event/date candidates and their non-null/cardinality surface. It does **not** authorize name-only crosswalking.

---

# 3. ESPN MMA — successfully acquired additive layer

Raw snapshot: `data/raw/espn_mma/20260820T123114Z/`

Verified manifest coverage:

- **911 UFC events**
- **9,412 competitions**
- event discovery spanning **1993–2026**
- core event requests: **911/911 HTTP 200**
- scoreboards: **34/34 HTTP 200**
- officials: **9,412/9,412 HTTP 200**
- plays: **9,412/9,412 HTTP 200**
- competitor-stat requests: **18,794 HTTP 200 / 28 HTTP 404** out of 18,822

Useful observed fields include:

- `advanceToBack`, `advanceToHalfGuard`, `advanceToMount`, `advanceToSide`
- `controlTimeSeconds`
- distance/clinch/ground strike splits
- head/body/leg + punch/kick splits
- knockdowns
- judge score totals
- officials/referees
- result/method context

The plays surface is sparse/structural (`end-round`, `end-fight`, etc.), not assumed to be empirical strike-by-strike chronology.

Role: **retain as additive/QA redundancy**, especially for officials, position-advance counts, identities, and cross-source disagreement checks. Do not duplicate official UFC fields into canonical tables merely because ESPN also supplies them.

---

# 4. Greco1899 / UFCStats

Pinned raw snapshot remains the working historical backbone until the official UFC overlap audit finishes.

Strengths:

- stable UFCStats event/fight/fighter URLs;
- fight outcomes/method/round/time/referee;
- fighter TOTT metadata;
- round-level classic striking/wrestling/control splits;
- pinned and reproducible historical source revision.

Weaknesses:

- community scrape rather than direct UFC CMS source;
- no rich positional TIP family;
- no individual ordered actions inside rounds.

Future role if official UFC passes: **secondary/QA + historical fallback for fields/eras with official gaps**.

---

# 5. Cross-promotion history

## Fight history

`binduvr/pro-mma-fights` v1 is stored raw:

- **10,448 fights**
- UFC/Bellator/ONE
- source state through 2021-08-11
- CC0/Public Domain

Use only after fighter identity crosswalk + UFC overlap deduplication.

## Fighter companion

`binduvr/pro-mma-fighters` v1 is now stored raw:

- **5,151 profiles**
- **22 columns**
- source URL, fighter name/nickname, DOB, age/death date, location/country, height/weight, association, weight class, and career W/L method breakdowns
- CC0/Public Domain

The profile/source URL can aid identity mapping to the companion fight table. Career totals are a **2021 point-in-time snapshot** and are explicitly forbidden from historical backfill.

---

# 6. Historical rankings

Dated UFC ranking snapshot begins 2013-02-04.

Required temporal rule: use only the latest ranking observation **strictly before** the target information cutoff. Never nearest future ranking.

---

# 7. Scorecards / judges

Current raw OCR layer is not trusted canonically because sample QA found fighter-pair/OCR association errors.

Preferred source order:

1. official UFC scorecard pages if a clean enumerator is established;
2. MMA Decisions for official judge names + per-round scores if needed;
3. OCR snapshot as a QA/recovery layer only.

Official, media, and fan score types must never share the same semantic field without an explicit source/type dimension.

---

# 8. Weigh-ins

Still a real free-data gap.

Official UFC public pages expose the desired data:

- actual scale weight;
- miss flag;
- pounds over;
- catchweight;
- second attempt when reported;
- purse penalty when reported.

The JSON:API article collection route returns HTTP 403 and is rejected. Do not bypass it. Find a legitimate official sitemap/search/index enumeration path or another permitted source.

---

# 9. Sequential action data

Not blocking the first predictive model.

Deferred access-gated sources:

- FightGeek PRECISION — strongest demonstrated historical sequential lead;
- FightGeek SPEED — possible future first-party collection;
- IMG/Sportradar — strongest verified official live rich-stat/TIP route; atomic UFC action entitlement still unresolved.

The successful official UFC TIP acquisition materially reduces dependence on premium data for the first state-duration/transition simulator.

---

# Provisional data-family ownership

| Data family | Preferred source now | Backup/additive | Gate before contract freeze |
|---|---|---|---|
| UFC fight/event identity | Official UFC JSON:API | Greco, ESPN | Resource-scoped fight snapshot + identity cardinality audit |
| UFC fighter identity | Official UFC | Greco, ESPN | stable crosswalk; no name-only joins |
| Historical round aggregates | Greco pending overlap audit | Official UFC + ESPN QA | UFC↔Greco disagreement/version audit |
| Rich TIP / positional stats | **Official UFC FightMetric** | ESPN positional counts; IMG later | calendar-era coverage + duplicate-version resolution |
| Cross-promotion experience | CC0 pro-MMA fights + profiles | broader source later if needed | identity + UFC-overlap dedup QA |
| Historical UFC rankings | dated fightr snapshot | FightMatrix benchmark | identity + temporal QA |
| Judge round scores | official UFC desired | MMA Decisions; OCR recovery | clean source ingestion + source-type contract |
| Fight-specific weigh-ins | official UFC desired | permitted alternate TBD | clean enumeration route |
| Officials/referees | ESPN + Greco/UFC | cross-source QA | normalize identity/string semantics |
| Empirical action chronology | premium sources later | future annotation | deferred/access-gated |
| Historical odds | BestFightOdds later | user sportsbook prices | separate market namespace |

---

# Gate before feature engineering

Do not freeze feature sets until:

1. official UFC fight identity is acquired and audited;
2. FightMetric coverage is labeled by actual calendar era;
3. FightMetric vs Greco overlap/disagreement is quantified;
4. conflicting FightMetric source-version behavior has a validated rule or remains explicitly quarantined;
5. the weigh-in source decision is resolved or consciously deferred;
6. canonical data contracts define grain, IDs, units, clocks, nulls, provenance, temporal availability, source conflict policy, and validation thresholds.

After that, feature families can be frozen from the data we demonstrably possess rather than from hoped-for future fields.
