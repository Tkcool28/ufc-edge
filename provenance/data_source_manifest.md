# UFC Edge — Data Source Manifest

Status date: 2026-08-20 (America/Denver)

Purpose: durable manifest of every material data source investigated during the current acquisition pass, including what succeeded, what failed, why, what each source contains, potential uses, and how much UFC Edge should trust it for future refreshes.

Detailed acquisition evidence remains in source-specific lock files, raw manifests, `provenance/runs/`, `free_source_sweep_2026-08-20.md`, and `acquisition_closeout_2026-08-20.md`.

## Latest self-reporting rerun update

The fail-closed runner diagnostics changed two source statuses materially:

- **Official UFC FightMetric rich stats: LANDED / RAW QA REQUIRED.** Run `32369217813` completed successfully (`exit_code=0`) and committed immutable snapshot `data/raw/ufc_fightmetric_official/20260820T123046Z/` plus manifest. The `fight_stat` collection contains **57,382 rows across 1,148 pages and 8,008 distinct non-null FightMetric IDs**. Standard fight-stat fields are populated on roughly 94.4% of rows; the main Time In Position/control-time family is populated on roughly 64.8% overall. This is strong enough to make official UFC FightMetric a real primary-source candidate, but coverage still varies by field/era and identity/time crosswalks are not yet audited.
- **Official UFC.com athlete/event/fight snapshot: PROCESS TIMEOUT / NOT LANDED.** Run `32369240290` hit the explicit 2,100-second process timeout (`exit_code=124`). Before timeout it fully fetched **4,160 athlete records across 84 pages** and **799 event records across 16 pages**, then stalled/ran too long while snapshotting the fights collection. This is not evidence of an HTTP rejection. Fail-closed behavior correctly prevented partial raw promotion.
- **ESPN MMA self-reporting rerun: still unresolved at this check.** No success/failure diagnostic commit is present yet. Its process window is longer than the elapsed check interval; do not classify it as failed until its durable diagnostic appears.
- **Official UFC article collection remains BLOCKED** through `/jsonapi/node/article` because bounded collection access returns HTTP 403. It was intentionally not rerun.

## Rating key

Scores are independent and use 1 (weak) to 5 (strong):

- **Authority** — closeness to official event/stat producer
- **History** — measured/expected historical completeness for useful fields
- **Refresh** — reliability of obtaining future data with consistent semantics

`?` means the current acquisition pass has not measured the dimension well enough to assign a defensible score.

## Current source table

| Source | Current status | Authority | History | Refresh | Canonical role | What it contains / why we care |
|---|---|---:|---:|---:|---|---|
| **Official UFC.com FightMetric `fight_stat`** | **INGESTED RAW / COVERAGE + IDENTITY QA REQUIRED** | 5 | 4? | 4 | PRIMARY candidate | 57,382 official rows; 8,008 distinct FightMetric IDs; rich fighter/round stats, Time In Position, control positions, detailed striking, TD/sub/reversal/standup, knockdowns. |
| **Official UFC.com `fight_roundboard`** | **INGESTED RAW / RECORD-BOOK SURFACE** | 5 | 2 | 4 | ADDITIVE / QA | 374 rows, 131 distinct FightMetric IDs, stat/rank/round records. Not full fighter-round history. |
| **Official UFC.com athlete/event/fight JSON:API** | **PROCESS TIMEOUT / NOT LANDED** | 5 | ? | 3 | Intended PRIMARY/ADDITIVE by field | Run fetched 4,160 athletes and 799 events, then exceeded 35 minutes during fights pagination. Needs split/resumable acquisition rather than blind timeout increase. |
| **Greco1899 UFCStats scrape** | **INGESTED** | 3 | 4 | 3 | Historical PRIMARY today; future SECONDARY/QA if official UFC coverage passes | Pinned reproducible UFCStats-derived event, fight, result, fighter, tale-of-tape and round aggregates. Strong historical backbone; no ordered intra-round actions or rich TIP. |
| **ESPN public MMA APIs** | **SELF-REPORTING RERUN PENDING** | 4 | ? | 3 | ADDITIVE / QA | Event/fight detail, officials, sparse plays, competitor stats, result context, identity cross-checks. Not assumed to be full action-level play-by-play. |
| **UFC-DataLab OCR scorecards** | **INGESTED RAW / QA REQUIRED** | 2 | 3 | 2 | RAW-ONLY pending validation | Three judge totals per corner from official scorecard images. Sample QA exposed obvious fighter-pair/OCR association errors. |
| **TidyTuesday / fightr dated UFC rankings** | **INGESTED RAW / QA REQUIRED** | 3 | 4 for 2013+ | 2 | ADDITIVE / historical context | Date, weight class, fighter, rank; observed coverage begins 2013-02-04. Strict historical as-of joins only. |
| **Kaggle `binduvr/pro-mma-fights` CC0** | **INGESTED RAW / QA REQUIRED** | 2 | 3 | 1 | ADDITIVE | 10,448 UFC/Bellator/ONE fights through 2021-08-11. Useful for pre-UFC/cross-promotion experience after identity mapping and UFC-overlap deduplication. |
| **Kaggle `binduvr/pro-mma-fighters` CC0 companion** | **PUBLIC / READY TO INGEST** | 2 | 3 | 1 | ADDITIVE / identity aid | 5,151 UFC/Bellator/ONE fighter profiles through 2021-08-11. |
| **Official UFC weigh-in articles** | **JSON:API ARTICLE ROUTE BLOCKED** | 5 | ? | 2 | Desired PRIMARY for weigh-ins | Exact scale weights, misses, pounds over, catchweights, second attempts, purse penalties. Public pages exist; clean enumeration route unresolved. |
| **Official UFC scorecard articles** | **JSON:API ARTICLE ROUTE BLOCKED** | 5 | ? | 2 | Desired PRIMARY for judge scorecards | Public official scorecard pages exist, but collection access through JSON:API is 403. |
| **MMA Decisions** | **PUBLIC / NOT INGESTED** | 3 | 4 | 3 | Potential ADDITIVE/SECONDARY | Official judge names and round-by-round scores plus media/fan scores. Keep official scores separate from fan/media scores. |
| **BestFightOdds** | **PUBLIC / NOT INGESTED** | 3 | 4 since ~2007 | 3 | MARKET DATA ONLY | Historical odds archive for later model-vs-market and price/value analysis. |
| **FightMatrix** | **AVAILABLE / DELIBERATELY DEPRIORITIZED** | 3 | 4 | 3 | REFERENCE | Proprietary historical/generated ratings; useful benchmark. |
| **FightGeek PRECISION** | **ACCESS / PERMISSION REQUIRED** | 4 | 4? | 2 | Future high-value sequential source | Timestamped post-bout actions, position/stance time, initiated/counter strikes, combinations, strike source/methods. |
| **FightGeek SPEED** | **ACCESS / PERMISSION REQUIRED / TRIAL** | 4 | 2? | 3 | Future first-party collection candidate | Real-time/retroactive smaller action vocabulary. |
| **Sportradar / IMG Arena UFC Fight Stats** | **ACCESS / PERMISSION REQUIRED** | 5 | ? | 5 if licensed | Future official live PRIMARY | Official live rich fight/round stats with sequence/timestamps and detailed Time In Position. |
| **IMG Arena Fight Details / Fight Actions** | **ACCESS REQUIRED; UFC ACTION ENDPOINT NOT VERIFIED** | 5 if UFC-equivalent verified | ? | ? | Future sequential source | PFL docs show event-level actions ideal for empirical Markov transitions; equivalent UFC entitlement remains unverified. |
| **CageIntel** | **REFERENCE ONLY / DEAD LEAD** | 1 | 1 | 1 | None | Domain parked/for sale. |
| **Stats Fight** | **ACTIVE / BULK ACCESS UNRESOLVED** | 3 | ? | 2 | Potential future ADDITIVE | Rich action/position presentation; no public bulk raw API/export found. |
| **Live blogs / prose play-by-play** | **DELIBERATELY EXCLUDED as canonical** | 1–2 | 2 | 2 | REFERENCE ONLY | Editorial prose is inconsistent, incomplete and difficult to normalize reliably. |
| **Manual / computer-vision video annotation** | **FALLBACK ONLY** | potentially 5 if validated | configurable | 1 | Future fallback | Potential frame/action truth but expensive and validation-heavy. |

## Source-by-source decisions and failure notes

### 1. Official UFC.com FightMetric

**Acquisition evidence**

Self-reporting run `32369217813` started `2026-08-20T12:30:45Z`, ended `2026-08-20T13:32:23Z`, and returned `exit_code=0`. Immutable snapshot ID: `20260820T123046Z`.

`fight_stat` manifest summary:

- **57,382 rows**
- **1,148 pages** at 50-row pagination
- **8,008 distinct non-null FightMetric IDs**
- round values: round 0 = 16,229; round 1 = 16,229; round 2 = 11,572; round 3 = 8,873; round 4 = 690; round 5 = 594
- FightMetric ID populated on 54,187 rows (**94.43%**)
- standard head/body/leg significant-strike and takedown/submission fields: about **94.43%** populated
- knockdowns: **49,031 / 57,382 = 85.45%**
- reversals: **48,275 / 57,382 = 84.13%**
- standups: **35,641 / 57,382 = 62.11%**

Time In Position / control coverage:

- standing, distance, clinch, control, ground-control, guard, half-guard, side, mount, back: **37,195 / 57,382 = 64.82%** each
- neutral time: **37,185 / 57,382 = 64.80%**
- miscellaneous ground control: **36,695 / 57,382 = 63.95%**
- `ground_time`: **17,166 / 57,382 = 29.92%**

Some newer/more granular weapon-position combinations are much sparser: several kick-related families are around **31.52%**, while several distance punch/kick combination fields are around **3.86%**. Missing must remain missing, never zero-filled.

`fight_roundboard` manifest summary:

- **374 rows**
- **8 pages**
- **131 distinct non-null FightMetric IDs**
- clearly a record-book/ranking surface, not full round history

**Important fields**

Time/position: `standing_time`, `neutral_time`, `distance_time`, `clinch_time`, `ground_time`, `control_time`, `ground_ctl_time`, `guard_ctl_time`, `half_guard_ctl_time`, `side_ctl_time`, `mount_ctl_time`, `back_ctl_time`, misc ground-control time.

Grappling: takedown attempted/landed, submission attempts, reversals, standups.

Striking: significant/total attempted and landed, head/body/legs, distance/clinch/ground, richer target/weapon/position combinations, knockdowns.

**Decision**

This is no longer merely a promising schema. It is a successfully acquired official bulk source and should become the leading candidate for rich UFC round/stat data. Do **not** yet replace Greco wholesale: first audit FightMetric IDs against fight/fighter identities, interpret round 0 semantics, quantify coverage by historical era, and compare overlapping values to Greco/UFCStats.

### 2. Official UFC athlete/event/fight JSON:API

**What passed during the failed run**

Run `32369240290` demonstrated that the public collections are readable and pagination works:

- athletes: **4,160 records / 84 pages completed**
- events: **799 records / 16 pages completed**

The process then entered `snapshotting fights...` and hit the workflow's explicit **2,100-second process timeout**, yielding `exit_code=124` and result `process_timeout`.

**Concrete failure cause**

The pipeline exceeded its allotted 35-minute process window while collecting the fights resource. There is no diagnostic evidence of HTTP 403/429 or another request exception in this run. Because the pipeline is atomic/fail-closed, completed athlete/event partial output was correctly not promoted.

**Best next fix**

Split athlete, event and fight collections into independently checkpointed/resumable acquisition units, or add page-level resume state for the fights collection. This avoids throwing away completed collections and avoids solving a pagination/runtime design problem by simply increasing a monolithic timeout.

**Risk**

Many athlete fields are current mutable snapshots. They cannot be injected into old fights unless an as-of history exists or state is reconstructed chronologically.

### 3. Official UFC article collection

`/jsonapi/node/article` is advertised but bounded collection access returns **HTTP 403 Forbidden**. Do not bypass the 403. Public HTML weigh-in and scorecard pages remain candidates through a legitimate index/search/sitemap path or another permitted source.

### 4. Greco1899 UFCStats snapshot

Pinned source revision and six raw datasets remain stored immutably. Strengths: reproducible historical event/fight/results/fighter/TOTT/round data. Weaknesses: community scrape, no atomic action chronology, and no rich TIP vocabulary in the imported table.

**Future role:** retain as historical backbone and QA redundancy until official UFC coverage is audited sufficiently to replace specific families.

### 5. ESPN public MMA APIs

Potential fields include yearly event discovery, event/competition details, competitor stats, officials, sparse plays/status/result structures. The current self-reporting rerun has not yet emitted its terminal diagnostic, so status remains **pending**. Do not infer success or failure from elapsed time before the configured process window ends.

### 6. UFC-DataLab OCR scorecards

Pinned MIT snapshot imported. Sample inspection exposed incorrect fighter-pair/OCR associations. No row becomes canonical until independently matched by date/opponents and score plausibility.

### 7. Dated rankings snapshot

Historical ranking table imported; observed history starts 2013-02-04. Only the latest ranking strictly before prediction cutoff may be joined. Never use a nearest future ranking.

### 8. CC0 cross-promotion fights

10,448 UFC/Bellator/ONE fight rows through 2021-08-11 are imported. Requires fighter identity crosswalk, UFC-overlap deduplication, and explicit acknowledgement that the historical snapshot is stale for current refresh.

## Data-family ownership — provisional

| Data family | Preferred source today | Backup/additive | Status before contract freeze |
|---|---|---|---|
| UFC fight/event identity | Official UFC JSON:API | Greco, ESPN | Source readable; monolithic ingestion needs split/resume fix |
| UFC fighter identity / FightMetric IDs | Official UFC | Greco, ESPN | Crosswalk not yet audited |
| Historical fighter-round aggregates | Greco + official UFC `fight_stat` | cross-source QA | Official raw now landed; overlap/era audit required before inversion |
| Rich position/TIP stats | **Official UFC `fight_stat`** | Sportradar/IMG later | **RAW LANDED; ~64.8% overall TIP coverage; era QA required** |
| Cross-promotion fight history | CC0 pro-mma-fights | broader source later if needed | RAW / QA REQUIRED |
| Historical UFC rankings | dated TidyTuesday/fightr snapshot | FightMatrix benchmark | RAW / QA REQUIRED |
| Official judge round scores | Official UFC pages desired | MMA Decisions; OCR totals | GAP / acquisition unresolved |
| Fight-specific weigh-ins | Official UFC pages desired | other permitted source TBD | GAP / acquisition unresolved |
| Officials/referees | ESPN + UFC/Greco where available | cross-promotion source | ESPN result pending |
| Market odds | BestFightOdds / sportsbook later | user DraftKings prices | Separate from core model |
| Empirical action sequence | FightGeek / official partner if licensed | future annotation | DEFERRED / ACCESS-GATED |

## Acquisition closeout rule

Before ending an acquisition session:

1. inspect every workflow triggered during the session;
2. distinguish `workflow completed` from `valid source snapshot committed`;
3. verify resulting raw manifest(s), not merely green job status;
4. record failed/partial sources and concrete reasons;
5. update this manifest when status materially changes;
6. do not promote any unverified pipeline to `INGESTED`;
7. leave unresolved jobs clearly labeled for the next session.

## Next gate

After ESPN reaches a terminal diagnostic and the UFC.com pagination design is repaired, the next major project phase remains **canonical data-contract design**, not feature engineering.

Contracts should freeze grain, IDs, types, units, clocks, null semantics, provenance, conflict resolution, temporal availability, and validation thresholds. Feature families should be frozen only after the source inventory and contracts make the available information surface explicit.
