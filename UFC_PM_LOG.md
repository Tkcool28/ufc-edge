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
