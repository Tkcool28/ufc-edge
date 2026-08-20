# Stats Fight — Active Sequential / High-Dimensional MMA Data Candidate

Status date: 2026-08-19 (America/Denver)

Status: **ACTIVE PRODUCT; DATA EXPORT / LICENSING ACCESS NOT YET VERIFIED**

Stats Fight is an active 2026 MMA analytics platform with proprietary live-stat collection and a post-fight archive. It is a potentially important alternative/complement to FightGeek for simulator-oriented sequential data.

Sources:

- https://statsfight.com/stats/
- https://statsfight.com/analytics/
- https://statsfight.com/stream/
- https://statsfight.com/blog/g-fight/

## Advertised data richness

Stats Fight states that its team has years of experience collecting real-time combat-sports statistics and has proprietary UFC live-stat technology.

Observed/advertised capabilities include:

- live strike counts
- takedown attempts and successful takedowns
- submission attempts
- control information
- round-by-round data
- fight-flow / course-of-fight visualizations
- clinch exchanges
- ground-control shifts
- positional changes
- technical arsenal by Distance / Clinch / Ground
- post-fight archive
- 100+ live/performance parameters used in scoring/analytics
- comparison material claiming 282 MMA statistical indicators overall

Its current documentation/blog language says it tracks every strike, takedown and submission attempt as the fight unfolds.

## Potential Markov value

If raw event history/export is available, this source could potentially support:

- action-arrival rates
- strike sequences
- takedown attempt/success timing
- submission-attempt timing
- phase duration
- positional state changes
- pace/intensity changes through a round
- fatigue/persistence modeling

That would make it closer to the simulator's desired event stream than ordinary round aggregates.

## Critical semantic warning

Stats Fight explicitly uses definitions that differ from the official UFC/FightMetric convention.

Examples from its public glossary/explanation:

- It does not treat every probing/feint-like action as a thrown strike.
- It uses its own landed-strike/damage criteria.
- It considers a takedown successful when control or damage follows.
- It counts a submission attempt when a lock is fixed and pressure begins.

Therefore Stats Fight raw observations **must never be silently merged count-for-count with UFCStats/FightMetric observations**.

If acquired, preserve:

- `source_name = statsfight`
- exact Stats Fight definitions/version
- raw source labels
- source-specific action outcomes
- independent validation against FightMetric/UFCStats for overlap fights

Cross-source harmonization belongs downstream and must be explicit.

## Access status

The consumer app/site exposes live and archived analytics, but the acquisition pass did not find a documented public bulk historical API or downloadable raw action-event export.

Stats Fight publicly advertises partnerships and professional analytics. Its 2026 Jackson Wink partnership page lists a media/partnership contact, which suggests direct access discussions are plausible, but **UFC Edge should not assume raw-data licensing/export rights without confirmation**.

## UFC Edge decision

**HIGH-PRIORITY ACCESS INQUIRY.**

Questions to resolve before simulator state design:

1. Is historical UFC raw event-level data available for export or API access?
2. What dates and number of UFC bouts are covered?
3. Are ordinary strike attempts preserved as timestamped events, or only time-binned counts/graphs?
4. Are position changes timestamped as discrete events?
5. What exact position vocabulary is recorded?
6. Are stance, movement direction, strike type/weapon and combinations available historically?
7. May the data be stored in a private modeling repository/database?
8. Is commercial/predictive-model use permitted?
9. What is pricing and refresh access for future UFC cards?

Until those answers are obtained, treat Stats Fight as **known-to-exist high-value data, not owned data**.
