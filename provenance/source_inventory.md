# UFC Edge — Data Source Inventory

Status date: 2026-08-19 (America/Denver)

This document tracks what data exists, what UFC Edge actually possesses, and what remains access-gated. It is a **data acquisition inventory**, not a frozen feature specification.

## Status vocabulary

- **INGESTED** — raw source bytes are stored immutably in UFC Edge.
- **PUBLIC / READY TO INGEST** — source is currently reachable without a commercial credential, but is not yet in our raw store.
- **ACCESS REQUIRED** — the data exists, but acquisition/licensing must be resolved before it can become a UFC Edge dependency.
- **REFERENCE ONLY** — useful for methodology or QA, but not intended as a canonical raw source.

## Source matrix

| Source | Status | Grain | Sequential? | Simulator / Markov value | Current decision |
|---|---|---|---:|---|---|
| Greco1899 UFCStats scrape | **INGESTED** | fighter-round + fight/event/fighter metadata | No | High for rate/success/exposure models; supports a Holmes-style simulator from aggregate fighter skills | Primary historical backbone |
| ESPN public MMA core API | **PUBLIC / READY TO INGEST** | fighter, event, fight, per-fight statistics, sparse fight timeline | Limited | Useful supplementary identity/context/position-advance and cross-check data; its play feed appears structural rather than strike-by-strike | Evaluate and ingest only fields that add information beyond Greco |
| FightGeek PRECISION | **ACCESS REQUIRED** | timestamped post-bout play-by-play / advanced combat actions linked to source video | **Yes** | **Very high**: direct empirical action/state transitions, combinations/sequences, position/stance time, initiated/counter actions | Highest-priority historical sequential-data lead |
| FightGeek SPEED | **ACCESS REQUIRED / TRIAL AVAILABLE** | live or retroactively logged smaller combat event set | Yes, smaller vocabulary | Medium-high for future collection; not evidence of access to FightGeek's historical UFC archive | Possible future first-party collection path |
| Sportradar / IMG Arena UFC Fight Stats | **ACCESS REQUIRED** | live changing fight + round statistics with sequence numbers/timestamps | Change-stream, not necessarily atomic action stream | **Very high**: explicit time-in-position, detailed positional control, grappling outcomes, granular strike context | Highest-priority official/commercial live-data lead |
| IMG Arena MMA Fight Details / Fight Actions | **ACCESS REQUIRED; UFC ACTION ENDPOINT NOT YET VERIFIED** | timestamped event-by-event/action stream | **Yes** | **Very high**: position changes, strike attempts/results, takedown attempts/results, submissions, reversals, knockdowns | Confirm UFC entitlement/endpoint before depending on it |
| Text live blogs / prose play-by-play | Public but inconsistent | prose | Loosely | Low; hard to normalize, inconsistent action omission, editorial latency | Do not use as canonical simulator training data |
| Video-derived manual/computer-vision annotation | Potential fallback | frame/action level | Yes | Potentially maximal but expensive and validation-heavy | Fallback only if licensed sequential feeds cannot be obtained |

---

## 1. Greco1899 / UFCStats

### What we have

The exact Greco source revision is pinned in `provenance/greco1899.lock.json` and the six selected source files are stored under:

`data/raw/greco1899/8e40eb945e11/`

The round table supplies, per fighter and round:

- knockdowns
- significant strikes landed/attempted
- total strikes landed/attempted
- takedowns landed/attempted
- submission attempts
- reversals
- control time
- head/body/leg significant strikes landed/attempted
- distance/clinch/ground significant strikes landed/attempted

### What it does **not** have

It does not preserve the chronological order or timestamps of individual strikes, takedowns, position changes, submissions, or reversals inside a round.

### Markov implication

This is not a blocker to a first Markov simulator. Holmes, McHale and Zychaluk (International Journal of Forecasting, 2023; DOI `10.1016/j.ijforecast.2022.01.007`) estimated fighter skills from freely scraped historical fight indicators and then simulated fights as a Markov process. In other words, aggregate historical data can parameterize transition hazards/rates even without observing every historical transition directly.

However, empirical play-by-play would let UFC Edge estimate richer state-transition behavior instead of inferring all transitions from aggregate rates.

---

## 2. FightGeek PRECISION — strongest historical sequential lead found

Source pages:

- https://fightgeek.co/precision/
- https://fightgeek.co/our-data/
- https://fightgeek.co/help/

FightGeek describes PRECISION as a post-bout video-scrubbing system whose entries are time-stamped to source video. Its advertised advanced fields include:

- Critical Strikes
- Initiated / Counter Strikes
- Time In Position / Stance
- Stance Efficiency
- Combinations — Sets & Sequence
- Strike Source & Methods
- Durability Aptitude
- Illegal Strikes

FightGeek states that PRECISION is intended for deep analysis and predictive modelling. It is currently described as a managed-service product rather than an openly downloadable dataset.

### Independent evidence that historical UFC play-by-play exists

A 2025 RStudio project titled **“Analysing UFC play by play data”** states that its play-by-play data was supplied by FightGeek and came from nine elite promotions including UFC and ONE. The project loads:

- `Data/Precision_Data_NC_All.csv`
- `Data/Precision_Data_NC_All__BOUTS.csv`

The analyst explicitly uses the sequential data to explore Markov transition matrices. The UFC subset in that supplied dataset spans approximately 2007 through 2022. After that analyst further restricted the sample to fights decided by judges, 487 UFC bouts remained; that 487 figure is therefore **not** the size of the complete FightGeek UFC archive.

Public project:

https://rstudio-pubs-static.s3.amazonaws.com/1288698_cd551de2166f4fad9bd154f8853b9e62.html

### Access conclusion

The data **exists**. We did not find a legitimate public download of the two FightGeek Precision CSVs. UFC Edge must treat the historical Precision archive as access-gated until FightGeek explicitly provides/licences it.

Do not scrape or copy restricted FightGeek material into the repository without permission.

---

## 3. FightGeek SPEED

Source:

https://fightgeek.co/speed/

FightGeek describes SPEED as a real-time logging product designed for rapid combat sequences, with historical reports after bouts are archived. Their help materials state that SPEED can also be used for retroactive logging and currently offers a 30-day trial.

This is potentially useful for **future first-party collection**, but a SPEED subscription/trial should not be assumed to grant UFC Edge access to FightGeek's pre-existing historical UFC Precision archive.

---

## 4. Sportradar / IMG Arena — richest verified UFC live stats lead

Verified UFC documentation:

https://docs.sportradar.com/ufc/stream-endpoints-websocket/fight-stats

UFC Fight Stats uses an authenticated websocket:

`wss://dde-streams.data.imgarena.com/mma/fights/{id}/livestats`

Packets carry a sequence number and generation timestamp, and expose fight-level and round-level statistics. Particularly valuable fields include **Time In Position (TIP)**:

- back control time
- clinch time
- control time
- distance time
- ground control time
- ground time
- guard control time
- half-guard control time
- misc ground control time
- mount control time
- neutral time
- side-control time
- standing time

Grappling includes attempts/landed for:

- reversals
- standups
- submissions
- takedowns

The strike model is substantially richer than the base UFCStats table and includes context-specific attempt/land counts such as body, head, legs, distance, clinch, ground, significant/total strikes, and knockdowns.

### Why this matters

Even if we never obtain atomic Fight Actions, the TIP fields materially improve phase-duration modeling:

- standing / neutral duration
- distance vs clinch exposure
- ground exposure
- guard / half-guard / side / mount / back exposure
- escape/stand-up behavior

Those are directly relevant to the simulator states already contemplated by the master plan.

### Access conclusion

The UFC feed requires an API token. Public documentation does **not** establish that UFC Edge can retrieve a complete historical archive of old live packets. `startPosition` supports reconnecting/replaying packets within a stream, but should not be interpreted as proof of multi-year historical backfill.

Treat historical availability and pricing as unresolved commercial-access questions.

---

## 5. IMG Arena Fight Details / Fight Actions

Relevant combat-feed documentation currently visible under the PFL product describes three streams:

1. **Fight Details** — sub-second event-by-event information such as round start, takedown attempt/landed, submission attempt, reversal, knockdown.
2. **Fight Stats** — live aggregated statistics.
3. **Fight Actions** — detailed timestamped actions such as successful/unsuccessful strikes with significance, weapon/type, target, plus explicit position events such as DISTANCE and CLINCH.

Documentation:

https://docs.sportradar.com/pfl/stream-endpoints-websocket

This event vocabulary is almost exactly what UFC Edge would want for empirical Markov chains.

**Important:** the equivalent detailed UFC Fight Stats feed is directly verified. The same Fight Actions/Details behavior has not yet been independently verified in public UFC documentation. Do not assume UFC entitlement solely because the PFL product documents it.

---

## 6. ESPN public MMA API

A recent open-source audit of ESPN's public MMA Core API reports no-auth endpoints for UFC events, fighters, competitions, per-fight competitor statistics, officials, and a `/plays` endpoint.

The useful distinction is that the ESPN fight `plays` feed is reported as sparse and structural — approximately round/fight markers rather than a complete strike-by-strike narrative. It therefore does **not** solve the empirical action-transition requirement.

Potential additive fields to evaluate before ingestion include:

- ESPN fighter identity mapping
- gym / association
- fighter style labels
- officials/referees
- richer per-fight statistic fields, including reported position-advance information
- cross-source QA against UFCStats

Reference audit:

https://github.com/haroon427666/The-mma-app-verification/blob/2126d1cdb904f262238e68e087b908eb0fc40398/deliverables-2026-08-03/espn-mma-api-reference.md

Because ESPN is supplemental rather than a replacement for our verified UFCStats backbone, ingest only fields whose semantics and historical coverage we can validate.

---

# Markov-data requirements for UFC Edge

Before choosing a vendor-specific implementation, UFC Edge should reserve a canonical raw-normalized event grain capable of representing any legitimate sequential source.

Minimum information required to estimate empirical phase/action transitions:

- stable fight ID
- stable fighter ID
- round
- monotonic sequence number and/or round clock
- source timestamp when available
- action/event type
- actor fighter
- action outcome
- position/state before and after when known
- controller fighter when applicable
- raw vendor/source payload retained for audit

Desirable action detail:

- strike attempted / landed
- strike significant / total class
- strike weapon/type
- strike target
- initiated vs counter
- knockdown
- takedown attempted / landed
- submission attempted / completed
- reversal
- stand-up / escape
- explicit position transition
- control-position label: guard / half guard / side / mount / back / other
- round start/end and fight end

---

# Data-first decision

1. **Keep Greco/UFCStats as the historical backbone.** It already supports the core aggregate-rate version of the simulator and most model features.
2. **Do not pretend Greco is empirical play-by-play.** Preserve the distinction in schemas and validation.
3. **FightGeek PRECISION is the strongest demonstrated historical sequential-data lead.** Resolve legitimate archive access before final simulator state design.
4. **Sportradar/IMG Arena is the strongest verified live positional/stat feed.** Resolve UFC action-feed entitlement and historical backfill separately.
5. **ESPN is a free supplemental candidate, not the Markov solution.** Validate additive fields before ingestion.
6. **Freeze features only after the raw-source acquisition pass is complete.** Source availability should constrain the feature contract, not the other way around.
