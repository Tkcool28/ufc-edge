# Cage Intel — Historical Positional / Sparse Play-by-Play Candidate

Status date: 2026-08-19 (America/Denver)

Status: **PUBLIC WEB DATA; BULK-USE PERMISSION / PROVENANCE NOT YET RESOLVED**

This note records a potentially high-value historical data source discovered during the Markov-data acquisition pass. Do **not** bulk ingest it until source provenance and acceptable use are clarified.

## Why it matters

Cage Intel publicly displays fight-level and round-level UFC data that goes materially beyond the Greco/UFCStats tables already ingested by UFC Edge.

Observed fields include:

- neutral time
- standing time
- distance time
- clinch time
- ground time
- control time
- ground control time
- miscellaneous ground control time
- guard control time
- half-guard control time
- side-control time
- mount control time
- back-control time
- takedowns attempted/landed
- reversals
- submission attempts
- detailed strike splits
- fight-specific weigh-in values
- exact finish technique / finish position on many bouts
- judge scorecards when available

These time-in-position fields closely resemble the richer FightMetric / current IMG Arena UFC stat vocabulary and directly address a known limitation of the Holmes-McHale-Zychaluk Markov simulator, which did not have time spent in specific ground positions.

## Sparse play-by-play

Cage Intel also exposes a fight timeline under `Play-By-Play`.

Observed event types include:

- Fight opens
- walkouts
- Tale of the Tape
- staredown
- round start/end
- takedown attempt
- successful takedown
- submission attempt
- knockdown
- pause / round paused / round continues
- fight over
- outcome announced
- fight complete

For newer fights, events may include both round clock and real-world UTC timestamp. Older timelines may have UTC timestamps but `N/A` round clock.

### Verified examples

- Michael Chiesa vs Tony Ferguson (2024): takedown attempt at R1 1:47, successful takedown at 1:45, submission attempt at 1:28; same page reports back-control time and other positional durations.
- Glover Teixeira vs Jan Blachowicz (2021): multiple timestamped takedown attempts, successful takedowns and submission attempts.
- Aljamain Sterling vs Pedro Munhoz (2019): timestamped takedown attempts.
- Curtis Blaydes vs Alistair Overeem (2018): successful takedowns, knockdown, submission attempt; the page has timestamps even where the source round clock is unavailable.
- Demetrious Johnson vs Ali Bagautinov (2014-06-14): timeline exists with successful takedowns and round markers.

Cage Intel pages explicitly state on older fights that **Play-By-Play data started approximately mid-2014**.

## Important limitation

The public timeline is **not strike-by-strike play-by-play**. Ordinary strikes are absent. It is best understood as a sparse high-value action feed for grappling/knockdown/round-state events, combined with rich aggregate positional exposure.

Therefore:

- it can help estimate takedown-attempt → takedown-success timing and some submission/knockdown hazards;
- it can anchor phase-duration / position-occupancy models through TIP fields;
- it cannot, by itself, empirically estimate every standing-strike transition or combination sequence.

FightGeek PRECISION remains the strongest discovered source for truly rich sequential strike/action data.

## Historical positional coverage

Cage Intel exposes position-time fields on fights well before its play-by-play start. Examples found during discovery include UFC fights from 2007 and 2011 with guard / half-guard / side / mount / back-control time.

Academic work using the original FightMetric database confirms that FightMetric historically tracked over 100 round-level performance statistics, including time in clinch, guard, half guard, side control, mount and back control. That research notes that some older events did not have Time In Position (TIP) tracked, so missingness must be treated as source coverage rather than zero exposure.

Reference:

Patrick Gift, “The impact of new judging criteria on 10-8 scores in MMA,” Journal of Sports Analytics, DOI `10.3233/JSA-200478`.

## Provenance / access problem

Cage Intel's About page describes it as a solo university-student project intended to collate deep UFC analysis data. The public pages inspected during discovery did not state the upstream data provider or a bulk-data license.

Because many fields strongly resemble FightMetric / IMG Arena data and the play-by-play structure resembles provider fight-detail feeds, UFC Edge must **not infer redistribution or bulk-scraping rights from public page visibility alone**.

Before ingestion, resolve:

1. What upstream source(s) generated the position-time and play-by-play data?
2. Does Cage Intel have authority to redistribute/export it?
3. May UFC Edge store a private historical copy for modeling?
4. Is there an API/export or preferred respectful acquisition method rather than crawling HTML?
5. What is the true historical field-coverage matrix by fight/year?

Cage Intel's public contact address is listed on its About page. If we pursue this source, requesting a direct export/permission is preferable to bulk crawling.

## UFC Edge decision

**High-priority candidate pending permission/provenance.**

If legitimate private-modeling access can be obtained, this could fill much of the position-time gap at far lower friction than a commercial live-data contract, while FightGeek PRECISION would remain the higher-ceiling option for fully sequential strike/action transitions.
