# UFC EDGE — PM LOG

## Purpose

This is the durable project-management log for UFC EDGE.

Use it to preserve lessons from real betting cards, process corrections, model implications, staking rules, and decisions that should carry forward into future research and implementation.

This is not a raw pick log. It is a record of what changed in our thinking and why.

---

## Standing principles

1. **Handicap both fighters independently before choosing a side.**
2. **Opponent research must be capable of killing the original play.**
3. **Establish the side before narrowing to method.**
4. **Treat method probability as:**
   `P(method win) = P(fighter wins) × P(method | fighter wins)`
5. **Model method leakage explicitly.** A primary weapon can create multiple terminal outcomes.
6. **Evaluate method sustainability.** Ask whether the required environment persists after the first failed attempt or as cardio changes.
7. **Historical zeros are evidence, not impossibilities.**
8. **Do not confuse opponent vulnerability in a position with the probability that the fight reaches that position.**
9. **Try to kill every proposed bet before approving it.**
10. **Pass freely. Do not force four bets or a third parlay leg.**
11. **Track process quality separately from short-term results.**
12. **Keep bankroll sizing conservative until larger-sample calibration supports increasing it.**

---

# 2026-08-22 — UFC Sacramento

## Card result

The card failed across the recommended singles and parlay.

### Main lessons

#### 1. Opponent evaluation was too weak

The largest recurring error was overdeveloping the preferred fighter's win case while underdeveloping the opponent's ability to win or disrupt the expected route.

Most important examples:

- Mason Jones vs MarQuel Mederos
- Serghei Spivac vs Vitor Petrino
- Anthony Hernandez vs Gregory Rodrigues

The process was effectively:

1. identify the fighter we liked,
2. identify the likely winning method,
3. search for opponent vulnerabilities supporting that method,
4. price the bet.

That sequence encouraged confirmation bias.

### Process change

New order:

1. Build Fighter A's win case.
2. Independently build Fighter B's win case.
3. Identify the strongest spoiler mechanism for each.
4. Establish the underlying side.
5. Only then split win probability into KO/TKO, submission, and decision.
6. Compare those method probabilities to market prices.

#### 2. Method-tree leakage was underestimated

**Reinier de Ridder SUB/DEC** lost even though RdR won, because he won by TKO.

The mistake was treating Roman Dolidze's lack of prior KO/TKO losses as enough reason to nearly remove the TKO branch.

A grappler's dominant positions can produce:

- submission,
- ground-and-pound TKO,
- decision.

### Process change

Before removing a method from a double-chance market, ask:

> Can the fighter's primary weapon naturally generate the excluded outcome?

If yes, do not treat that outcome as negligible leakage.

#### 3. Historical narrative was overweighted

**Wes Schultz SUB** leaned on:

- Schultz's submission-heavy win record,
- McVey's submission-loss history,
- an old amateur submission result between them.

Those facts described potential vulnerability but did not prove Schultz could force the fight into that environment before McVey imposed his own offense.

### Process change

Old amateur results and small-sample method histories are supporting evidence only.

They should not create a play by themselves.

### Sacramento classification

**Primary failure:** opponent win probability / opponent resistance underestimated.

**Secondary failure:** method-tree leakage / overly aggressive method exclusion.

**Tertiary failure:** narrative and historical-pattern overweighting.

---

# 2026-09-05 — UFC Paris

## Recommended allocation

- Mario Pinto KO/TKO/DQ or Submission — **1.25% BR**
- Michael Page by Decision — **0.80% BR**
- Kurtis Campbell by Decision — **0.50% BR**
- Muhammad Naimov by Decision — **0.30% BR**
- Pinto KO/Sub + Page Decision parlay — **0.55% BR**

**Total risk: 3.40% BR**

## Result

- Pinto KO/Sub — **WIN**
- Page Decision — **WIN**
- Campbell Decision — **LOSS**; Campbell won by submission
- Naimov Decision — **LOSS**
- Pinto + Page parlay — **WIN**

At the posted prices and approximately +230 on the parlay:

- **Bankroll growth: about +2.03%**
- **ROI on wagered amount: about +59.7%**

Do not overfit to one profitable card; focus on whether the error profile improved.

---

## Paris lessons

### 1. Sacramento's method-leakage correction worked

Pinto was intentionally played as **KO/Sub**, not forced into one exact finish.

That mattered because he won by TKO.

This is the desired use of double-chance method markets:

- identify the dominant fight environment,
- preserve all major terminal outcomes naturally produced by that environment,
- eliminate only genuine leakage.

### 2. Page Decision was a strong opponent-specific method read

The decision case was supported by:

- Page's range-heavy minute-winning style,
- his UFC tendency to reach decisions,
- Ruziboev's durability,
- explicit acknowledgment that Page still had KO leakage.

The play did not depend on pretending the failure branch did not exist.

### 3. Campbell exposed a new method-concentration issue

The broad read was good:

- Campbell's wrestling/control advantage was real,
- Campbell won,
- the fight spent substantial time in the expected grappling environment.

The exact terminal method was too narrow.

Campbell eventually submitted Peek.

### New process check: dominant-position finish leakage

When projecting a decision because an opponent is durable, ask:

> Does the expected control itself create repeated finishing opportunities over time?

For grapplers, do not assume:

`control → decision`

Instead estimate:

`control → decision / submission / ground-and-pound TKO`

Durability can sometimes mean the dominant fighter gets more time to accumulate finishing chances rather than guaranteeing a decision.

### 4. Naimov showed the sleeper still needs stricter gates

The Naimov decision thesis required:

1. survive Keita's explosive striking,
2. establish clinch/wrestling disruption,
3. sustain it long enough to win ugly rounds.

The handicap focused more on Gates 2 and 3 than Gate 1.

### New sleeper rule

For a long-shot method that requires surviving the opponent's strongest weapon first, the first gate must be independently supported.

A plausible script is not sufficient by itself.

---

# Current approval checklist

Before approving any UFC side or method, answer:

1. What is Fighter A's preferred winning environment?
2. What is Fighter B's preferred winning environment?
3. What is Fighter B's strongest path to beat or disrupt Fighter A?
4. Can Fighter B prevent Fighter A's preferred environment?
5. If not, can Fighter B survive it?
6. What happens after Fighter A's first failed attempt?
7. Who improves relatively as the fight gets longer?
8. Are we relying on a historical zero such as "never been finished"?
9. Are we relying on an old amateur result or thin sample?
10. Can the predicted dominant position produce multiple terminal methods?
11. Is the underlying side strong enough before method is considered?
12. What evidence argues most strongly that the bet is wrong?
13. Does the price still provide enough edge after uncertainty?
14. If one major gate is unsupported, should this simply be a pass?

---

# Betting-category guidance

## High Hit / Floor

Require:

- strong underlying win probability,
- strong method concentration,
- low method leakage,
- durable path across multiple rounds,
- limited opponent spoiler risk,
- sufficient sample/evidence quality.

Heavy favorite status alone is not enough.

## Balanced

Require:

- credible side,
- supported method path,
- manageable leakage,
- reasonable opponent resistance,
- worthwhile price.

## Value

Plus money is not value by itself.

Require a meaningful probability cushion over break-even after uncertainty is considered.

## Sleeper

Keep stake small.

Require more than an attractive narrative. If the route depends on clearing an early survival gate, verify that gate first.

## Parlays

### Core 2-leg parlay

Use only when the two strongest card plays both have independently supported sides and routes.

- No forced third leg.
- Rough working cap: **0.40%–0.60% BR**

### Flyer parlay

For 3+ legs or materially more speculative constructions.

- Entertainment/upside only.
- Rough working cap: **0.20% BR**

---

# Model implications

The model should reinforce the same two-sided discipline.

Important matchup concepts:

- Fighter A creation vs Fighter B prevention
- Fighter B creation vs Fighter A prevention
- environment control
- takedown creation and prevention
- submission creation and survival
- striking creation and durability
- cardio and persistence
- round-by-round decay
- method concentration
- method leakage
- opponent quality
- current fighter state
- uncertainty for low-sample fighters

The model should produce the matchup baseline first.

Research should interrogate that baseline rather than begin from a preferred fighter and search for confirmation.

---

# PM rule

After each UFC card, update this log with:

- recommended plays and bankroll allocation,
- actual outcomes,
- bankroll growth,
- ROI on wagered amount,
- correct reads,
- wrong reads,
- process failure tags,
- lessons worth carrying forward,
- any rule changed because of the evidence.

Do not change methodology because of one isolated loss or one isolated win.

Change the process when the same failure repeats, or when a result clearly exposes a structural flaw in the reasoning.


---

# 2026-09-12 — Noche UFC

## Recommended allocation

- Waldo Cortes-Acosta ML — **1.25% BR**
- Yousri Belgaroui KO/TKO/DQ or Submission — **1.25% BR**
- David Martinez by Decision — **1.00% BR**
- Edgar Chairez by Submission — **0.50% BR**
- McMillen/Rahiki Under 1.5 Rounds — **0.50% BR**
- Waldo Cortes-Acosta ML + David Martinez Decision parlay — **0.50% BR**

**Total planned exposure: 5.00% BR**

## Actual result

- Waldo Cortes-Acosta ML — **LOSS**
- Yousri Belgaroui KO/TKO/DQ or Submission — **WIN**
- David Martinez by Decision — **WIN**
- Edgar Chairez by Submission — **LOSS**
- McMillen/Rahiki Under 1.5 Rounds — **LOSS**
- Waldo + Martinez parlay — **LOSS**

Based on the actual tickets:

- total staked: **$4.90**
- net result: approximately **-$1.02**
- ROI on amount wagered: approximately **-20.8%**
- bankroll impact: approximately **-1.0% BR**

The negative result does not justify a broad framework change. The card exposed a few specific issues while also confirming that some recent method-construction improvements are working.

---

## Noche UFC lessons

### 1. Waldo vs Blaydes — surviving wrestling is not the same as neutralizing scoring

The Waldo thesis correctly identified Curtis Blaydes' wrestling as the major danger and expected Waldo to survive that route.

Waldo did survive. The problem was that survival alone was not enough.

Blaydes did not need sustained domination or a finish. Takedowns, mat returns, defensive reactions, clinch work, and time spent forcing Waldo to defend were enough to affect round scoring and suppress Waldo's offense.

### Process change: wrestling survival vs scoring denial

Against control-oriented wrestlers, explicitly separate:

- probability of being finished or held down for long stretches,
- probability of repeatedly conceding takedowns or control moments,
- offensive opportunity cost created by wrestling defense,
- round-winning equity created by even intermittent control.

Do not convert "can survive the wrestling" into "has neutralized the wrestling enough to win" without separately evaluating scoring and minute-loss risk.

---

### 2. Belgaroui KO/Sub — method-family construction worked again

Belgaroui won inside the distance by strikes.

The bet intentionally preserved both KO/TKO and submission branches because the incremental price relative to a narrower finish prop was small.

This continues the positive pattern first highlighted after Sacramento and Paris:

> When the expected dominant environment can naturally produce multiple terminal outcomes, preserve those branches unless the market charges too much for them.

No process change is needed here.

---

### 3. Martinez Decision — strong side-plus-method fit

Martinez won by decision as projected.

The play combined:

- a credible underlying side,
- demonstrated ability to win decisions against UFC-level veterans,
- an opponent whose UFC losses had overwhelmingly reached the scorecards,
- a method price that remained acceptable.

This is the type of method bet the framework should continue prioritizing.

No process change is needed here.

---

### 4. Chairez Submission — submission-loss counts need an exposure denominator

The Chairez case leaned partly on Elliott's history of UFC submission losses and his willingness to create grappling exchanges.

The missing context is that a long-career, grappling-heavy fighter can accumulate submission losses partly because he has spent an unusually large number of minutes and exchanges in dangerous grappling positions.

A raw count such as "five UFC submission losses" does not by itself tell us the conditional probability of being submitted in a given grappling exchange or fight.

### Process change: exposure-adjusted submission vulnerability

When using opponent submission history, distinguish:

- raw number of submission losses,
- total grappling-heavy fight exposure,
- submission attempts faced,
- survival/escape frequency,
- recency of those losses,
- quality and style of the submission threats faced.

The goal is to separate true vulnerability from simple opportunity volume.

---

### 5. McMillen/Rahiki Under 1.5 — process was supported; result should not be mislabeled as a research failure

This loss should **not** be logged as a failure to research finish timing.

The pre-fight work explicitly examined both fighters' historical finish times, not just raw finish percentages.

The combined professional history reportedly contained only about **three finishes occurring after the Round 2 2:30 cutoff**, which was part of the reason the Under 1.5 at plus money was approved.

The fight itself still produced meaningful finishing danger but survived past the betting cutoff and ultimately reached decision.

### PM classification

**Outcome variance / durability realization**, not an identified process flaw.

Do not create a new methodology rule simply because this particular Under lost.

The existing requirement remains:

> For Under 1.5 props, research actual finish-time distribution and opponent survival history rather than relying only on aggregate finish rate.

That work was done here.

Future samples should determine whether the historical timing signal is actually predictive enough to keep using, but one loss does not justify changing the method.

---

### 6. Parlay — duplicated exposure should be visible before approval

The parlay paired:

- Waldo ML,
- Martinez Decision.

Martinez hit; Waldo did not.

Because Waldo also carried the largest single stake, the parlay increased total exposure tied to the same underlying Waldo win thesis.

This is not inherently wrong, but the concentration should be explicit before betting.

### Process change: total fighter-thesis exposure

Before approving a core parlay, calculate each fighter's total bankroll exposure across:

- singles,
- same-fighter method derivatives,
- parlays.

A core parlay may duplicate a strong single, but the total correlated exposure should be visible and consciously accepted.

Do not evaluate the parlay stake in isolation.

---

## Noche UFC classification

### Positive confirmations

- **Method-family construction:** Belgaroui KO/Sub correctly protected against unnecessary exact-method risk.
- **Opponent-specific decision handicapping:** Martinez Decision matched the expected route.
- **Finish-time research:** McMillen/Rahiki Under was based on actual timing distribution; the loss does not invalidate the process by itself.

### Process issues

- **Wrestling scoring equity underestimated:** Waldo vs Blaydes.
- **Submission-loss denominator/context missing:** Chairez vs Elliott.
- **Correlated exposure not made explicit enough:** Waldo single + Waldo/Martinez parlay.

### Not a process issue

- **McMillen/Rahiki Under 1.5:** classify as a researched plus-money total that lost, not as evidence that finish-time distribution was ignored.

---

# Additions to current approval checklist

For future cards, add the following checks:

15. Against a wrestler, are we distinguishing survival from actual scoring denial and offensive opportunity cost?
16. When citing submission-loss history, are we adjusting mentally for total grappling exposure and survival volume?
17. What is the total bankroll exposure to each underlying fighter thesis across singles and parlays?
18. For round totals, was actual finish-time distribution researched? If yes, do not rewrite the process solely because one outcome missed.
