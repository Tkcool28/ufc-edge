# UFC Edge — Data Source Manifest

Status date: 2026-08-20 (America/Denver)

Purpose: durable manifest of every material data source investigated during the current acquisition pass, including what succeeded, what failed, why, what each source contains, potential uses, and how much UFC Edge should trust it for future refreshes.

This document summarizes source status. Detailed acquisition evidence remains in source-specific lock files, probe manifests, raw manifests, and `free_source_sweep_2026-08-20.md`.

## Rating key

Scores are independent and use 1 (weak) to 5 (strong):

- **Authority** — closeness to official event/stat producer
- **History** — measured/expected historical completeness for useful fields
- **Refresh** — reliability of obtaining future data with consistent semantics

`?` means the current acquisition pass has not measured the dimension well enough to assign a defensible score.

## Current source table

| Source | Current status | Authority | History | Refresh | Canonical role | What it contains / why we care |
|---|---|---:|---:|---:|---|---|
| **Official UFC.com FightMetric `fight_stat`** | **SCHEMA VERIFIED; BULK SNAPSHOT STARTED / RESULT UNVERIFIED** | 5 | ? | 4 | Intended PRIMARY if coverage passes | Official rich fighter/round stats; Time In Position; control positions; detailed striking; TD/sub/reversal/standup; knockdowns. Highest-value free simulator discovery. |
| **Official UFC.com `fight_roundboard`** | **SCHEMA VERIFIED; BULK SNAPSHOT STARTED / RESULT UNVERIFIED** | 5 | 2? | 4 | ADDITIVE / QA | FightMetric IDs, round, stat name/value/rank. Appears record-book oriented; must not be mistaken for full fighter-round history. |
| **Official UFC.com athlete/event/fight JSON:API** | **PIPELINE STARTED / RESULT UNVERIFIED** | 5 | ? | 4 | Intended PRIMARY/ADDITIVE by field | Official IDs, fighter profiles, event/fight context, FightMetric identity, gym/style/physical context where populated. Current snapshots can leak if backfilled historically. |
| **Greco1899 UFCStats scrape** | **INGESTED** | 3 | 4 | 3 | Historical PRIMARY today; future SECONDARY/QA if UFC official coverage passes | Pinned reproducible UFCStats-derived event, fight, result, fighter, tale-of-tape and round aggregates. Strong historical backbone; no ordered intra-round actions or rich TIP. |
| **ESPN public MMA APIs** | **PIPELINE STARTED / RESULT UNVERIFIED** | 4 | ? | 3 | ADDITIVE / QA | Event/fight detail, officials, sparse plays, competitor stats, result context, identity cross-checks. Not assumed to be full action-level play-by-play. |
| **UFC-DataLab OCR scorecards** | **INGESTED RAW / QA REQUIRED** | 2 | 3 | 2 | RAW-ONLY pending validation | Three judge totals per corner from official scorecard images. Sample QA exposed obvious fighter-pair/OCR association errors; cannot be canonical without fight/date/opponent validation. |
| **TidyTuesday / fightr dated UFC rankings** | **INGESTED RAW / QA REQUIRED** | 3 | 4 for 2013+ | 2 | ADDITIVE / historical context | Date, weight class, fighter, rank; observed coverage begins 2013-02-04. Useful only with strict as-of joins. Dataset-specific provenance/license remains partially unresolved. |
| **Kaggle `binduvr/pro-mma-fights` CC0** | **INGESTED RAW / QA REQUIRED** | 2 | 3 | 1 | ADDITIVE | 10,448 UFC/Bellator/ONE fights through 2021-08-11, originally scraped from Sherdog. Useful for pre-UFC/cross-promotion experience after identity mapping and UFC overlap deduplication. |
| **Kaggle `binduvr/pro-mma-fighters` CC0 companion** | **PUBLIC / READY TO INGEST** | 2 | 3 | 1 | ADDITIVE / identity aid | 5,151 UFC/Bellator/ONE fighter profiles through 2021-08-11; potential mapping/context companion to cross-promotion fight history. |
| **Official UFC weigh-in articles** | **BLOCKED through JSON:API collection** | 5 | ? | 2 | Desired PRIMARY for weigh-in data | Exact scale weights, misses, pounds over, catchweights, second attempts, purse penalties. Public pages exist, but `/jsonapi/node/article` collection returned HTTP 403; clean enumeration route unresolved. |
| **Official UFC scorecard articles** | **BLOCKED through JSON:API collection** | 5 | ? | 2 | Desired PRIMARY for judge scorecards | Public official scorecard pages exist, but clean JSON:API article collection returned HTTP 403. Do not count as acquired. |
| **MMA Decisions** | **PUBLIC / NOT INGESTED** | 3 | 4 | 3 | Potential ADDITIVE/SECONDARY | Official judge names and round-by-round scores plus media/fan scores. If used, official judge data must remain separate from fan/media scores. |
| **BestFightOdds** | **PUBLIC / NOT INGESTED** | 3 | 4 since ~2007 | 3 | MARKET DATA ONLY | Historical odds archive for later model-vs-market and price/value analysis. Sportsbook prices stay outside the independent core forecast model. |
| **FightMatrix** | **AVAILABLE / DELIBERATELY DEPRIORITIZED** | 3 | 4 | 3 | REFERENCE | Proprietary historical/generated ratings. Useful benchmark, but dated UFC ranking data reduces need to import external ratings into core fighter state. |
| **FightGeek PRECISION** | **ACCESS / PERMISSION REQUIRED** | 4 | 4? | 2 | Future high-value sequential source | Timestamped post-bout actions, position/stance time, initiated/counter strikes, combinations, strike source/methods. Strongest demonstrated historical sequential archive found; no legitimate public bulk download found. |
| **FightGeek SPEED** | **ACCESS / PERMISSION REQUIRED / TRIAL** | 4 | 2? | 3 | Future first-party collection candidate | Real-time/retroactive smaller action vocabulary. Trial does not imply entitlement to the historical PRECISION archive. |
| **Sportradar / IMG Arena UFC Fight Stats** | **ACCESS / PERMISSION REQUIRED** | 5 | ? | 5 if licensed | Future official live PRIMARY | Official live rich fight/round stats with sequence/timestamps and detailed Time In Position. Public docs do not prove multi-year historical packet backfill. |
| **IMG Arena Fight Details / Fight Actions** | **ACCESS REQUIRED; UFC ACTION ENDPOINT NOT VERIFIED** | 5 if UFC-equivalent verified | ? | ? | Future sequential source | PFL docs show event-level actions nearly ideal for empirical Markov transitions. Equivalent detailed UFC action entitlement/endpoint remains unverified. |
| **CageIntel** | **REFERENCE ONLY / DEAD LEAD** | 1 | 1 | 1 | None | Domain found parked/for sale. Do not plan features around it. |
| **Stats Fight** | **ACTIVE / BULK ACCESS UNRESOLVED** | 3 | ? | 2 | Potential future ADDITIVE | Rich action/position presentation and different stat semantics. No public bulk raw API/export found during sweep. Deferred for later access investigation. |
| **Live blogs / prose play-by-play** | **DELIBERATELY EXCLUDED as canonical** | 1–2 | 2 | 2 | REFERENCE ONLY | Editorial prose is inconsistent, omits actions, and is hard to normalize/timestamp reliably. |
| **Manual / computer-vision video annotation** | **FALLBACK ONLY** | potentially 5 if validated | configurable | 1 | Future fallback | Could generate frame/action-level truth but is expensive and validation-heavy. Only consider if legitimate sequential feeds cannot be obtained. |

## Source-by-source decisions and failure notes

### 1. Official UFC.com FightMetric

**What passed**

- UFC JSON:API resource catalog is publicly readable.
- `/jsonapi/fight_stat/fight_stat` returned HTTP 200 in bounded probes.
- `/jsonapi/fight_roundboard/fight_roundboard` returned HTTP 200.
- `fight_stat` exposes a much richer official FightMetric schema than the Greco round aggregate table.

**Important fields discovered**

Time/position:

- `standing_time`
- `neutral_time`
- `distance_time`
- `clinch_time`
- `ground_time`
- `control_time`
- `ground_ctl_time`
- `guard_ctl_time`
- `half_guard_ctl_time`
- `side_ctl_time`
- `mount_ctl_time`
- `back_ctl_time`
- misc ground-control time

Grappling:

- takedown attempted/landed
- submission attempts
- reversals
- standups

Striking:

- significant/total attempted and landed
- punches/kicks
- head/body/legs
- distance/clinch/ground
- detailed target/weapon/position combinations
- knockdowns

**Potential uses**

- primary official fighter-round stat source
- environment/control component models
- standing/clinch/ground exposure
- positional control burden
- takedown/submission/standup/reversal rates
- richer striking exposure and finish-hazard inputs
- simulator transition-duration calibration

**What remains unresolved**

The first unsorted samples included legacy/null rows. Schema existence does not prove populated historical coverage. The bulk snapshot manifest must quantify non-null coverage by field/era before promotion.

### 2. Official UFC athlete/event/fight JSON:API

**What passed**

The resource catalog advertises structured sport resources including athletes, athlete stats/rankings, events and fights.

**Potential uses**

- primary UFC identity crosswalk
- event/fight IDs
- FightMetric ID bridge
- leg reach / gym / style / debut/context fields where available
- current official fighter state

**Risk**

Many athlete fields are current mutable snapshots. They cannot be injected into old fights unless an as-of history is available or the state is reconstructed chronologically.

### 3. Official UFC article collection

**What failed**

`/jsonapi/node/article` is advertised in the resource catalog but a bounded collection request returned **HTTP 403 Forbidden**.

**Why this matters**

A listed JSON:API resource is not proof of readable collection access. The public HTML weigh-in and scorecard pages remain valuable, but UFC Edge must find a legitimate official index/search/sitemap or another clearly permitted source rather than treating the 403 as something to bypass.

### 4. Greco1899 UFCStats snapshot

**What passed**

Pinned source revision and six raw datasets are already stored immutably.

**Strengths**

- reproducible historical snapshot
- stable source URLs/IDs
- round-level UFCStats aggregates
- fighter tale-of-tape
- event/fight/results structure

**Weaknesses**

- independent/community scrape rather than official UFC delivery
- dependent on upstream scraper maintenance
- no atomic action order/timestamps
- no rich official FightMetric TIP vocabulary in the imported round table

**Future role**

Keep as a historical backbone until official UFC coverage is proven. If UFC official data proves sufficiently complete, retain Greco as redundancy, gap-fill candidate, and cross-source QA rather than blindly discarding it.

### 5. ESPN public MMA APIs

**What appears available**

- yearly event discovery
- event/competition details
- competitor stats
- officials
- sparse plays/status/result structures

**What is not assumed**

The plays feed is not assumed to be strike-by-strike empirical action data.

**Promotion condition**

A completed snapshot manifest must show credible event counts by year, endpoint coverage, observed stat vocabulary and failure rates.

### 6. UFC-DataLab OCR scorecards

**What passed**

Pinned MIT source snapshot imported successfully.

**What failed QA**

Inspection found obviously wrong fighter-pair/OCR associations and impossible-looking rows.

**Rule**

No OCR scorecard row becomes canonical until matched to an independently verified fight by date/opponents and score plausibility. OCR output is evidence, not truth.

### 7. Dated rankings snapshot

**What passed**

Large dated ranking table successfully imported; observed history starts 2013-02-04.

**Potential uses**

- pre-fight ranking/champion status
- ranking movement
- ranked/unranked context
- opponent-ranking context

**Rule**

Only the latest ranking strictly before prediction cutoff may be used. Never nearest future ranking.

### 8. CC0 cross-promotion fights

**What passed**

10,448 fight rows imported from UFC/Bellator/ONE through 2021-08-11.

**Potential uses**

- pre-UFC professional experience
- external promotion win/loss/method history
- experience depth before UFC debut

**Risks**

- historical snapshot is stale for current refresh
- identity crosswalk required
- UFC overlap with Greco must be deduplicated
- original upstream was Sherdog via a derived Kaggle dataset

## Data-family ownership — provisional

These are acquisition preferences only, not frozen feature contracts.

| Data family | Preferred source today | Backup/additive | Status before contract freeze |
|---|---|---|---|
| UFC fight/event identity | Official UFC JSON:API if snapshot succeeds | Greco, ESPN | UNRESOLVED until full snapshot audited |
| UFC fighter identity / FightMetric IDs | Official UFC | Greco, ESPN | UNRESOLVED |
| Historical fighter-round aggregates | Greco today | Official UFC `fight_stat` | May invert if official historical coverage passes |
| Rich position/TIP stats | Official UFC `fight_stat` | Sportradar/IMG later | Highest free-data priority |
| Cross-promotion fight history | CC0 pro-mma-fights | broader source later if needed | RAW / QA REQUIRED |
| Historical UFC rankings | dated TidyTuesday/fightr snapshot | FightMatrix benchmark | RAW / QA REQUIRED |
| Official judge round scores | Official UFC pages desired | MMA Decisions; OCR totals | GAP / acquisition unresolved |
| Fight-specific weigh-ins | Official UFC pages desired | other permitted source TBD | GAP / acquisition unresolved |
| Officials/referees | ESPN + UFC/Greco where available | cross-promotion source | Snapshot/QA pending |
| Market odds | BestFightOdds / sportsbook later | user DraftKings prices | Separate from core model |
| Empirical action sequence | FightGeek / official partner if licensed | future annotation | DEFERRED / ACCESS-GATED |

## Nightly acquisition closeout rule

Before ending an acquisition session:

1. inspect every workflow triggered during the session;
2. distinguish `workflow completed` from `valid source snapshot committed`;
3. verify resulting raw manifest(s), not merely green job status;
4. record failed/partial sources and concrete reasons;
5. update this manifest when status materially changes;
6. do not promote any unverified pipeline to `INGESTED`;
7. leave unresolved jobs clearly labeled for the next session.

## Next gate

The next major project phase after this source sweep is **canonical data-contract design**, not feature engineering.

Contracts should freeze grain, IDs, types, units, clocks, null semantics, provenance, conflict resolution, temporal availability, and validation thresholds. Feature families should be frozen only after the source inventory and contracts make the available information surface explicit.
