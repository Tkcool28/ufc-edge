# FightMetric `round=0` research note

Status: **high-confidence source fight summary; explicit vendor sentence not found**

This note exists so the project does not repeatedly re-investigate the same question.

## Question

What does `round=0` mean in the official UFC.com `fight_stat` resource?

## External research result

A targeted web search on 2026-08-20 did **not** find an official UFC/FightMetric document that explicitly says `round=0 = fight total`.

A surviving historical FightMetric API manual does establish the old source's fight/fighter identity model and fight-level result fields. It documents FightMetric FightID/FighterID, ending round/time, and importantly a per-fight `WeighIn` value. It does not document the modern Drupal `fight_stat` round encoding.

Reference:
- https://paperzz.com/doc/7368033/api-fight-detail-%23%23%23.json---fightmetric-logo-api

A public 2017 modeling dataset attributed directly to FightMetric exposes **fight-total statistics and round-specific statistics side-by-side**. Examples include:

- `F1SigStr` and `F1R1SigStr`
- `F1TotStr` and `F1R1TotStr`
- `F1TD` and `F1R1TD`
- `F1SubAtt` and `F1R1SubAtt`

Reference:
- https://ledgerw.github.io/UFC/index.html

This externally corroborates that historical FightMetric data had a distinct fight-total statistical layer in addition to R1-R5 statistics. A plausible migration interpretation is that UFC's later Drupal table stored the old fight-total record in the same resource as round rows and used `round=0` as the sentinel. That migration mechanism is an inference, not a documented vendor statement.

## Internal full-snapshot evidence

The repository audit over the complete official UFC FightMetric snapshot supports `round=0` as a per-fighter fight summary:

- 15/16 tested count families support additive fight-summary semantics at the audit threshold;
- all 13 tested time families support summary semantics once source rounding tolerance is applied;
- round 0 is therefore excluded from canonical fighter-round grain and retained separately as source summary/QA.

Generated evidence:
- `provenance/audits/fightmetric_semantics_latest.md`
- `provenance/audits/fightmetric_semantics_latest.json`

## Current contract decision

Treat `round=0` as **source-provided fight summary** with high confidence.

- Do not model it as a real round.
- Preserve it in raw data.
- Do not silently discard it.
- Derive canonical fight totals from real rounds where appropriate and compare them against the source summary.
- Re-open this conclusion only if stronger primary documentation or contradictory source evidence appears.

## Related acquisition lead

The historical FightMetric manual explicitly states that fight detail included `WeighIn`: the fighter's weigh-in weight **for that specific fight**, not generic roster weight. This should be investigated as a potential historical fight-specific weigh-in source before relying on article scraping.
