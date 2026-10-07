# UFC_EDGE_GROUND_EXPOSURE_SOURCE_DISCOVERY_AND_BACKFILL_FEASIBILITY_V1

Research date: 2026-10-03. Repository: Tkcool28/ufc-edge. Live main verified before research: `b8194cd37831348bd856900cba134d05ff21e430`, the merge of PR #158. Prior evidence-manifest SHA-256 verified: `6fe5387b3d4b184fc61e2c1c1ca1fe0844daa8b6b6e056ac83e62c86d5dd447b`.

## 1. Executive conclusion

**D — No suitable broad historical ground-exposure source was verified from accessible evidence.** This is a finding about verification and access, not proof that the desired archive does not exist. No provider passes acquisition, historical coverage, semantic precision and licensing gates together. Do not backfill production or promote Arm C on this evidence.

The best concrete acquisition lead is **Sportradar UFC detailed results**, because its public live-stat documentation contains actual one-second-display `groundTime` and fighter-specific `groundControlTime` values, separately from generic `controlTime`, with round attribution and ground strikes. The documentation directs consumers to final detailed results following post-match checks. However, historical entitlement, oldest available date, missingness, final-export semantics and research rights require provider confirmation. A documentation example is not an accessible historical archive.

The official UFC Record Book exposes precise-looking career top/bottom totals, but its inspected fight and round leaderboards do not expose the underlying bout durations. UFCalendar currently documents ground-time seconds, but an unauthenticated sample request returned 401. Its original time source, rounding and historical positional coverage remain unverified. There is **no evidence sufficient to classify UFCalendar as genuine second-resolution exposure or as converted minute buckets**.

A fixed 28-fight audit panel and 156 baseline fighter-round records are preserved. **Candidate records acquired for that panel: 0/28.** The mandatory multi-era candidate sample comparison is therefore incomplete. A separate accessible Sportradar documentation example, Garry–Prates (2025-04-26), supplies ten fighter-round observations and supports a targeted sample-access request, not a historical recommendation.

Recommended next action: request a no-purchase archive coverage/rights response and authorized final-record sample for the fixed panel from Sportradar; seek FightGeek archival coverage and UFCalendar field provenance in the same research handoff. No vendor messages were sent. If those gates fail, conduct a six-bout, two-rater video-annotation feasibility pilot under lawful footage access, with a measured workload and agreement assessment before any expansion.

## 2. Requirements inherited from PR #158

The six priority reports were read first; the internal audit was not repeated. Existing takedowns, submissions, ground significant strikes and generic control describe access/activity, but do not supply a reliable ground-duration denominator. Generic control can include standing or clinch control. A low submission count per bout cannot distinguish sustained safe control from little actual grounded exposure.

PR #158 found 32,156 fighter-round positional rows across 6,803 fights. Legacy ground fields represent floor-minute intervals: bucket b implies [60b, 60b+59] seconds, subject to round elapsed time. A zero bucket is not proof of zero ground time. Useful coverage concentrates in 2013–2018, with none usable during 2021–2026. Complete prior-ground-bucket history was 22.51% at the 2018 boundary and 6.18% at the 2026 boundary. Training-window prior-history completeness for 2015–2017 was 17.75%; conditional experiments would retain only 707 training bouts and 470 outer scoring bouts.

A replacement needs real elapsed grounded duration; preferably fighter/round top, bottom and ground control, with definitions covering scrambles, one fighter standing over another, clinch and neutral ground. Submission attempts and ground strikes must align to that same exposure. Entries, escapes, transitions and reversal semantics matter. True time alone would improve sustained-opportunity measurement, but **does not establish submission threat quality or finishing opportunity**; that needs action context or annotations. No raw counts should automatically be renamed submission creation.

The archive must cover earlier bouts contributing to 2015–2017 fighter histories, not merely start in 2015, and support every 2018–2026 outer period through the frozen historical cutoff 2026-08-15. Features must use event dates strictly before target dates, excluding same-date bouts. Present-day reconstructed event statistics and contemporaneous publication vintages are separate research claims.

## 3. Official UFC Record Book

Sources: https://statleaders.ufc.com/ ; https://statleaders.ufc.com/en/fight ; https://statleaders.ufc.com/en/round ; https://statleaders.ufc.com/en/fight-comb ; https://statleaders.ufc.com/en/round-comb . Official announcement: https://www.ufc.com/news/new-tool-launched-ufc-stats-records-research . Terms URL attempted: https://www.ufc.com/terms .

The site states UFC 28 onward and displayed an update of 2026-09-30 07:45 GMT. Career categories include top-position time, bottom-position time, control time and positional percentages. For example, Georges St-Pierre top time is 2:22:05 versus 2:42:04 control; Demian Maia top time is 2:01:15. These non-minute totals rule out simple multiplication of every career minute total by 60, but do not prove the precision, completeness or lineage of every underlying historical bout.

The publicly inspected fight leaderboard has 29 category headings and round leaderboard seven; these cover finish/count records without downloadable ground, top or bottom duration records. Combined fight/round pages did not yield a qualifying exposure dataset. Career leaderboards are aggregates, even when linked to fighter profiles. No documented official bulk export or validated public per-bout positional API was found. Server-rendered HTML and the linked application JavaScript were inspected without bypassing restrictions; no underlying legitimate duration request was established. This negative result is limited to inspected public surfaces, not an assertion about UFC's internal database.

**Original dataset:** UFC's official statistics system is the publisher; exact backend, field provenance and historical revision process are unresolved. Do not assume PR #158's legacy Drupal bucket feed powers these career totals. **Granularity:** career positional totals accessible; fight/round time source records unresolved. **Top/bottom:** independent career categories exist, but independently attributable historical fight values were not obtained. **Current maintenance:** page update is evidence of maintenance, not a verified year-by-year positional archive through 2026. **Matching:** names/profile links can seed candidate identity resolution; they cannot establish bout-level joins without event/opponent/round records. **Rights:** no reusable dataset license established; attempted UFC terms access was blocked. Official public display does not establish permission for bulk collection or redistribution.

Conclusion: **unsuitable through currently accessible leaderboard surfaces; a UFC data-access inquiry remains conditional.**

## 4. UFCalendar API

Sources: https://api.ufcalendar.com/docs ; https://api.ufcalendar.com/openapi.json ; https://api.ufcalendar.com/v1/plans ; https://www.ufcalendar.com/developers ; https://www.ufcalendar.com/developers/ufc-stats-api ; https://www.ufcalendar.com/developers/terms .

Current OpenAPI contains both `FightStatLine` and `RoundStatLine` with nullable integer fields:

| Field | Documented meaning | Unresolved semantics |
|---|---|---|
| `ground_time_sec` | Seconds on the ground; null where positional data unavailable | Upstream source, grounded rule, precision, truncation |
| `clinch_time_sec` | Seconds in clinch | Exclusivity, standing versus ground clinch |
| `distance_time_sec` | Seconds at distance | Partition definition and timing rules |
| `control_time_sec` | Seconds of control | Ground versus standing components |

`GET /v1/fights/{id}/stats` and `GET /v1/fights/{id}/rounds` are documented, require bearer authentication, and support fight/round attribution with fighter identifiers and corners. The schema offers submission and ground-strike counts, but no independently documented top/bottom durations or separate ground-control field. Fighter position representation changed on 2026-09-24 from stored 1/2 positions to a/b corners; consumers must version mapping, not assume schema permanence.

One bounded request to the documentation's example fight `https://api.ufcalendar.com/v1/fights/83379/stats` without credentials returned **401**. No account, key, trial or subscription was created. Ground values remain unobserved. An integer type and the word seconds are inadequate evidence: legacy b minutes returned as 60b seconds would not add true exposure information. There is no actual UFCalendar sample here on which to run minute-multiple, round-reconciliation or lineage checks.

The provider describes public sources and its own systems and is not league-licensed. General UFCStats/Wikipedia attribution does not identify the source of the positional seconds. Advertised broad statistics coverage (8,819 fight-stat lines, 41,526 round lines, 98% statistics coverage) is not field-specific ground coverage. Catalog history beginning in 1993 does not demonstrate ground-duration history. Earliest/latest valid ground records, annual missingness, division support, null versus zero, and fighter continuity all remain unknown.

Plans endpoint/public pricing at research time: 24-hour trial, 100 requests, 30/minute, one key, no card; Hobby $19/month or $190/year, 30,000 monthly requests, 60/minute; Pro $49/month or $490/year, 200,000, 300/minute; Business $149/month or $1,490/year, 1,000,000, 600/minute. Verify again before acquisition. Search pagination restrictions are not a license to split queries to evade bulk-export limits; request an approved bounded panel and coverage export first.

Terms effective 2026-08-20, updated 2026-09-26: trial is evaluation/noncommercial; display/analysis permissions vary by plan; Business describes internal redistribution, while substantial raw-data redistribution remains prohibited. Research/model-use rights, retained snapshots after cancellation and publishing raw evidence require explicit clarification. Provider revisions and version policy do not supply historical publication vintages.

Conclusion: **conditional precision/provenance inquiry, not an approved historical source. Neither outcome A/B nor bucket-republication outcome C is established.**

## 5. Sample audit and actual accessible record

Selection was frozen after public source/access reconnaissance but before extracting candidate or canonical panel measurements. It is purposive by era and recognizable bout characteristics, not a random missingness estimator. `SAMPLE_SELECTION.json` declares 27 named bouts plus the earliest canonical UFC bout in 2026 selected by date then fight ID, without conditioning on outcome. Same-year rematches use the earliest match; Grasso–Shevchenko therefore means 2023-03-04. The separate documentation example was available by convenience and is not retroactively added to the fixed panel.

The panel spans 2004-01-31 to 2026-01-24 and ten divisions. It contains bottom-submission cases (Silva–Sonnen; Craig–Ankalaev; Craig–Hill), submission finishes (Maia–Condit; Makhachev–Hooker), control-heavy bouts (Usman–Woodley; Almeida–Lewis), ground-and-pound (Khabib–Johnson; Rockhold–Weidman), short exchanges (Rousey–Zingano; Pereira–Hill), and prolonged exchanges. These selection descriptors are contextual research judgments, not newly fitted labels. Men's bantamweight and women's featherweight are absent; no division-wide coverage inference is warranted.

`SAMPLE_PANEL.csv` preserves dates, identities, division and existing UFCStats/FightMetric/UFC.com IDs. `SAMPLE_ROUND_COMPARISON.csv` preserves 156 fighter-rounds with elapsed time, control, submission attempts, significant ground strikes, reversals and available legacy buckets (54 fighter-round ground buckets). Candidate fields are blank and explicitly unobserved, never zero. Their source statuses distinguish missing public surface, authentication required and commercial entitlement required. The fixed panel has **zero verified external ground-duration records**. No 20–30-fight successful audit is claimed.

### Supplemental Sportradar example

Source: https://docs.sportradar.com/ufc/stream-endpoints-websocket/fight-stats . Extracted numeric facts are in `SPORTRADAR_DOCUMENTATION_SAMPLE.json`; comparisons in `SUPPLEMENTAL_DOCUMENTATION_COMPARISON.csv`. This is a public documentation example, not a fetched final historical API response. Fight Garry–Prates, 2025-04-26: provider fight ID 9325, card 953; fighter IDs 3742/4147 and UFC fighter IDs 3717/4075. Round states:

| Round | Ground | Clinch | Distance | Garry ground control | Prates ground control |
|---|---:|---:|---:|---:|---:|
| 1 | 12 | 2 | 286 | 12 | 0 |
| 2 | 4 | 29 | 267 | 0 | 4 |
| 3 | 66 | 41 | 193 | 66 | 0 |
| 4 | 32 | 81 | 187 | 32 | 0 |
| 5 | 61 | 49 | 190 | 0 | 61 |

All values are seconds as displayed. Each common partition totals 300; fight ground time totals 175, clinch 202, distance 1,123, total 1,500. Fighter ground control totals 110 and 65; generic control totals 189 and 106. Per-round summed ground control equals common ground time **in this example**. This supports second-granularity display and a meaningful ground/control distinction; it does not establish universal exclusivity or allow ground control to be relabeled top position. Explicit top/bottom durations were not identified. Neutral ground and one-upright cases need provider rules.

Against pinned UFC EDGE: generic control matches 10/10 fighter-rounds; submission attempts (all zero) match 10/10; significant ground strikes landed match 9/10 and attempted 8/10. In round 5, Garry documentation is 0/1 versus canonical 0/0; Prates is 14/16 versus canonical 12/13. This live-style example has sequence 763 and timestamp 2025-04-27T04:34:07.047372Z; it must not substitute for the provider's checked final detailed results. Differences cannot be resolved here as corrections versus different counting rules. Public example formatting also contains an omitted comma and mixed ID types; a blue stand-up example has attempts zero but landed four, so no escape-success rate should be computed from it.

The nonmultiples of 60 rule out simple floor-minute-to-second conversion for this example. Video-level accuracy, clock rounding, interval definitions and historical consistency remain unverified. No bucket-pattern test was possible for UFCalendar. An observed reconciliation is reported without imposing it on providers whose states may overlap.

## 6. Broader search and original-source assessment

Both first sources failed the accessible historical-record gate, triggering broader search. Marketing alone did not qualify a provider.

| Candidate and exact source | Added measurement / precision | History and access | Verdict / cost and rights |
|---|---|---|---|
| Sportradar: https://docs.sportradar.com/ufc ; fight-stats URL above | `groundTime`, `groundControlTime`, generic control, per-round positions including guard/half/side/mount/back, ground total/significant strikes, reversals, stand-ups and submissions; one-second display in actual example | Octagon-side live collection described; static detailed results advertised for past fights. Oldest date, final REST URL, yearly completeness, division coverage, transitions and archived field definitions unresolved. Token/entitlement needed; live stream alone is not a backfill | Strongest conditional lead. Quote required; retention/model/derivative/redistribution rights unresolved. Current stream documentation points to `wss://dde-streams.data.srarena.io/mma/fights/{id}/livestats`; legacy stream retirement was scheduled 2026-09-30; confirm operational interface |
| FightGeek: https://fightgeek.co/precision/ ; https://fightgeek.co/our-data/ | Post-bout slow-motion video and timestamped positional/action logging described; actual resolution/definitions require sample | Primary researcher report https://rstudio-pubs-static.s3.amazonaws.com/1288698_cd551de2166f4fad9bd154f8853b9e62.html describes provider Precision files; cleaned printed dates 2007-09-23–2022-07-30. Narrative says Nov 23 and code comment May 27 for earliest 2007: exact oldest date unresolved. 487 UFC bouts **after decisions-only filtering**, not archive coverage. Bulk 2018–2020; 2023–2026 and finishes unverified. No authorized raw CSV download found | Conditional historical/video lead. Quote and research rights required; filtered research sample cannot repair early folds by itself |
| SportsDataIO: https://sportsdata.io/developers/data-dictionary/mma ; https://sportsdata.io/developers/api-documentation/mma | Generic `TimeInControl`, advances and reversals, submission attempts; no ground/top/bottom duration documented in inspected FightStat schema | Historical depth/positional missingness unresolved; commercial authentication; trial values may be scrambled, inappropriate for semantic numeric verification | Unsuitable essential denominator under documented schema. Quote/rights unresolved; counts could add context only |
| Cito: https://docs.citoapi.com/docs/api/ufc/bouts/ ; https://citoapi.com/mma-stats-api/ | Bout/round stats, generic control and ground strike splits; no verified actual ground-duration definition/sample | Advertised archive counts are not positional field coverage. Backfill method described but field lineage, precision and rights unknown | Not qualified. Price/rights unresolved; no acquisition recommended for denominator |
| Published MMA dataset: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2019.00029/full | Counts/passes and outcomes; no verified actual ground duration | 2,831 male bouts 2000–2015; original FightMetric access agreement, no validated open exposure export | Not a new duration source; original archive inquiry would require permission |
| Public UFCStats mirror: https://huggingface.co/datasets/01x3ATM3/UFC_FIGHT_DATA_2013_TO_2025 | Generic CTRL and significant ground strikes; no distinct duration verified | Publisher viewer covers 2013-04-27–2025-05-31 | No incremental denominator; redistribution/license not assumed |
| Video timing study: https://www.cambridgepublish.com/css/article/download/243/250/797 | Video-coded timing states, including one fighter upright and one grounded | Small 2014–2015 three-division study; published aggregates, no verified reusable bout export | Supports a manual-protocol feasibility question, not broad archive availability |

Genius Sports and Stats Perform searches produced no verified UFC historical ground-duration schema/sample suitable for recommendation. UFCStats/FightMetric mirrors and archived bucket resources do not overcome PR #158's semantic limit. Research estimating time from strike/control ratios is imputation, not measured grounded exposure. No accessible original FightMetric archive with precise bout durations was verified. Third-party Record Book wrappers remain aggregate wrappers until raw bout provenance is demonstrated.

## 7. Historical coverage and early-fold implications

| Boundary | PR #158 complete prior bucket history | Verified new historical ground coverage |
|---|---:|---|
| 2018 | 22.51% | Unknown; no qualified archive |
| 2019 | 25.03% | Unknown |
| 2020 | 15.63% | Unknown |
| 2021 | 10.03% | Unknown |
| 2022 | 8.64% | Unknown |
| 2023 | 7.80% | Unknown |
| 2024 | 7.08% | Unknown |
| 2025 | 6.64% | One documentation bout; not population coverage |
| 2026 | 6.18% | Unknown |

Do not convert source inaccessibility into an estimated zero field-coverage rate. Earliest and latest genuine available ground records, year/division missingness and longitudinal fighter completeness require a provider census or an authorized export denominator. Neither the Record Book scope statement nor UFCalendar overall stats counts answer them. FightGeek's decisions-only research subset cannot substantiate coverage of submission/GNP finishes or reconstruct all early fighter histories. Sportradar's one recent example cannot substantiate 2015–2017.

There is consequently **no demonstrated improvement to early-fold coverage** and no justified narrow historical model experiment yet. A small source-validation backfill is justified only after access/rights authorization; choosing a modeling population after observing availability would violate the predeclared population requirement.

A provider should supply per-field coverage by event year/division, date ranges, missing-reason codes, fighter join continuity, rule-change dates and revision timestamps. Identity joins should require event date, event identifier, both fighter identities and round, with explicit rematch and corner checks. Existing UFCStats URL, FightMetric numeric ID and UFC.com UUID links are available for the sample; provider fighter IDs are not interchangeable with them. Current event-stat backfills can support a disclosed reconstructed-data study; no source here establishes what was published before each historical target bout. Do not market a reconstructed archive as verified point-in-time availability.

## 8. Licensing, reproducibility and bounded acquisition

No services purchased, accounts/trials opened, unrestricted scraping, restriction bypasses, model training, production ingestion, frozen prediction edits or prospective outcome evaluation were performed. Public historical facts were used for source semantics only. Raw proprietary exports must not be committed publicly without specific redistribution permission. Public access and schema documentation do not grant those rights.

The offline audit script verifies the prior manifest and five canonical input hashes, joins the fixed panel, and reproduces comparisons. Inputs are not copied into this report directory: recover them from the pinned repo paths in PR #158's manifest (and the pinned fighters table), place them under `inputs/`, include PR #158 `EVIDENCE_MANIFEST.json`, and run `python reproduce_sample_audit.py`. The validation file records hashes, counts and the incomplete access gate. `SOURCE_CHECKS.json` preserves request/definition findings and hashes of locally fetched public evidence without republishing entire copyrighted pages. `EVIDENCE_MANIFEST.json` hashes the deliverable files; it excludes itself and the completion marker to avoid circular hashes.

Provider inquiries must resolve (1) ground versus top/bottom/ground-control definitions, (2) true measured seconds versus converted floor minutes, (3) final historical availability before 2015 through 2026-08-15, (4) annual/division/fighter missingness, (5) authorized fixed-panel export and stable IDs, (6) corrected final records and version history, (7) retained research snapshots and model use, (8) permissible evidence/derived aggregate publication, and (9) a quote for only the required archive scope. Stop before paid acquisition or license acceptance.

## 9. Specific next GitHub handoff

**UFC_EDGE_GROUND_EXPOSURE_VENDOR_SAMPLE_AND_RIGHTS_GATE_V1** — see `NEXT_GITHUB_HANDOFF.md`. Request final detailed-results sample and field-level coverage from Sportradar first, investigate FightGeek archival availability, and ask UFCalendar to identify positional upstream source and provide values for the same fixed panel. Do not replace access-gated bouts with convenient recent ones. Require the 28-bout semantic comparison, explicit missingness and licensing decision before recommending any broader backfill. A provider response without numeric samples cannot pass.

If no lawful historical feed can pass, use six prespecified panel bouts: Silva–Sonnen, Rockhold–Weidman, Craig–Ankalaev, Usman–Woodley, Almeida–Lewis and Pereira–Hill. Total fight clock is 6,575 seconds (109.58 minutes). At an **untested planning assumption** of 3–6 times video duration per rater, two raters require about 10.96–21.92 person-hours, plus protocol design and adjudication. This is not an observed annotation-cost estimate. Monetary cost is those measured hours times an agreed rate, plus any separately quoted footage rights.

Predeclare grounded-state and actor rules, neutral/scramble states, top/bottom/one-upright states, clip/clock handling and unknown-camera intervals. Independently annotate transition times and submission/ground-strike context; measure boundary agreement, duration differences, missing visibility and actual hours. Set acceptable agreement and visibility gates before coding, then adjudicate. Lawful viewing does not automatically permit downloaded clips or redistribution. Do not extrapolate a six-bout pilot into a mass campaign or early-fold repair.

## 10. Final answer

**Trustworthy second-granularity ground measurements are visibly documented in one Sportradar example, but a trustworthy, licensed historical backfill adequate for UFC EDGE has not been found and verified.** Pursue a bounded final-record/coverage/rights gate with Sportradar, with FightGeek and UFCalendar as specific unresolved leads. If that gate fails, the next strategy is a measured six-bout annotation pilot, accepting substantial labor and uncertain historical scalability. No next model experiment is supported yet.

Completion means source-discovery findings and limitations are delivered; it does not mean the sample-acquisition gate passed.

`UFC_EDGE_GROUND_EXPOSURE_SOURCE_DISCOVERY_V1_COMPLETE`
