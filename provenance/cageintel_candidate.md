# Cage Intel — Historical Positional / Sparse Play-by-Play Evidence

Status date: 2026-08-19 (America/Denver)

Status: **REFERENCE ONLY — DOMAIN CURRENTLY INACTIVE / FOR SALE**

Cage Intel is **not a current UFC Edge acquisition source**. Current web search resolves `cageintel.com` to a domain-for-sale page. Search engines still retain indexed fight pages from when the project was active, and those historical pages are useful evidence about what FightMetric/IMG-style UFC data existed.

Do not design a production ingestion dependency around Cage Intel.

## Why the archived pages matter

Indexed Cage Intel fight pages display data materially richer than the Greco/UFCStats tables already ingested by UFC Edge.

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

## Sparse play-by-play evidence

Archived Cage Intel pages also contain a `Play-By-Play` timeline.

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

For newer fights, events include round clock and real-world UTC timestamps. Older timelines can contain UTC timestamps with `N/A` round clock.

Verified indexed examples during discovery:

- Michael Chiesa vs Tony Ferguson (2024): takedown attempt at R1 1:47, successful takedown at 1:45, submission attempt at 1:28; position-time fields include back control.
- Glover Teixeira vs Jan Blachowicz (2021): multiple timestamped takedown attempts, successful takedowns and submission attempts.
- Aljamain Sterling vs Pedro Munhoz (2019): timestamped takedown attempts.
- Curtis Blaydes vs Alistair Overeem (2018): successful takedowns, knockdown and submission attempt; timestamps exist even where source round clock is unavailable.
- Demetrious Johnson vs Ali Bagautinov (2014-06-14): timeline exists with successful takedowns and round markers.

Archived pages explicitly state that **Play-By-Play data started approximately mid-2014**. Pre-mid-2014 pages state no play-by-play is available.

## Important limitation

The archived timeline is **not strike-by-strike play-by-play**. Ordinary strikes are absent. It is best understood as a sparse high-value action feed for grappling/knockdown/round-state events, combined with rich aggregate positional exposure.

Therefore it demonstrates that a useful historical action layer existed, but it does not prove availability of fully atomic standing-strike sequences.

FightGeek PRECISION remains the strongest discovered source for truly rich sequential strike/action data.

## Historical positional coverage evidence

Cage Intel's indexed fight pages expose position-time fields on fights well before its play-by-play start, including UFC fights from the 2000s and early 2010s. This is consistent with academic work using the original FightMetric database.

Patrick Gift's study, “The impact of new judging criteria on 10-8 scores in MMA” (DOI `10.3233/JSA-200478`), states that FightMetric tracked over 100 round-level performance statistics including time in clinch, guard, half guard, side control, mount and back control. The paper notes that some older events lacked Time In Position (TIP), so historical missingness must be modeled as source coverage rather than interpreted as zero exposure.

## Provenance conclusion

When Cage Intel was active, its About page described it as a solo university-student project intended to collate deep UFC analysis data. The pages inspected did not identify a bulk-data license or clearly identify the upstream provider.

Because the domain is now inactive, and because the rich fields resemble FightMetric / IMG Arena data, UFC Edge should treat Cage Intel only as evidence pointing us toward the underlying data family—not as a dataset to reconstruct from search caches.

## UFC Edge decision

**REFERENCE ONLY.**

Use the archived evidence to define acquisition questions for FightGeek, Sportradar/IMG Arena, or another legitimate historical FightMetric export. Do not scrape search-engine caches or the inactive domain into UFC Edge.
