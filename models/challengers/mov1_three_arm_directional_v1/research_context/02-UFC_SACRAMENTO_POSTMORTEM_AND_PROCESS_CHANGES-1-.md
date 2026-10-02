# UFC Sacramento Postmortem and Process Changes

## Purpose

This document records the betting postmortem from UFC Sacramento and the process changes we want to carry forward into future UFC cards.

The main lesson from this card was not simply that the bets lost. The larger issue was a recurring handicap bias:

> We did a better job identifying what our preferred fighter could do than identifying what the opponent could do to break that path.

The goal going forward is to make opponent resistance, spoiler paths, and method sustainability first-class parts of the handicap rather than secondary checks after we already like a side.

---

# UFC Sacramento — Recommended Card

## High Hit / Floor — 25%

**Reinier de Ridder — Submission or Decision**

- Target: -300
- Play through: -320
- Pass if worse than -320

Original rationale:

- Roman Dolidze had never been KO/TKO'd professionally.
- The bet removed what appeared to be RdR's least likely winning method.
- It offered a better price than the moneyline.

### Result

**Loss — RdR won by Round 1 TKO.**

### What went wrong

The fighter read was correct, but the method tree was compressed too aggressively.

The mistake was treating Dolidze's historical absence of KO/TKO losses as evidence that RdR's TKO branch was nearly removable.

That ignored an important interaction:

- RdR's primary weapon is grappling.
- Dominant grappling can create more than submissions.
- It can also create ground-and-pound TKO outcomes.
- Therefore, RdR's TKO branch was not independent from his strongest skill.

### Lesson

A historical zero is not the same as a structural impossibility.

Before removing a method from a double-chance bet, ask:

> Can the fighter's primary offensive weapon naturally create the supposedly excluded outcome?

If yes, that outcome should not be treated as pure leakage.

---

# Balanced — 25%

**Mason Jones by Decision**

- Target: +100
- Play through: -105
- Pass if worse than -105

Original rationale:

- Jones was a substantial favorite.
- MarQuel Mederos had never been professionally finished.
- Every Mederos UFC fight had reached the scorecards.

### Result

**Loss — Mederos won by Round 2 TKO.**

### What went wrong

This was a more serious handicap miss.

The analysis put too much weight on:

- Jones being the favored fighter.
- Mederos' historical durability.
- The assumption that if Jones won, a decision was the most likely route.

The analysis did not sufficiently ask:

> How likely is Mederos to win the fight outright?

The method analysis became more developed than the underlying side analysis.

### Lesson

Before asking how Fighter A wins, first determine how confident we are that Fighter A wins at all.

Method probability should be thought of as:

**P(A wins by method) = P(A wins) × P(method | A wins)**

If the first term is wrong, the method handicap can look attractive for the wrong reason.

---

# Value — 25%

**Serghei Spivac Moneyline**

- Target: +124
- Play through: +110
- Pass below +110

Original rationale:

- Spivac's heavyweight grappling matchup looked favorable.
- His win could come by submission, ground-and-pound, or decision.
- At plus money there was no need to guess an exact method.

### Result

**Loss — Vitor Petrino won by unanimous decision.**

### What went wrong

This was not a method-selection error.

We deliberately avoided method overfitting and took the moneyline.

The underlying side was simply wrong.

That makes this one of the most important losses on the card because it points directly to opponent underestimation.

The analysis gave too much weight to Spivac's grappling upside and not enough weight to Petrino's ability to:

- keep the fight in favorable phases,
- defend or neutralize the grappling threat,
- win minutes,
- and sustain that resistance over the full fight.

### Lesson

Archetypes are useful starting points, not conclusions.

Examples:

- strong wrestler vs weaker grappler,
- submission specialist vs historically submitted opponent,
- cardio wrestler vs power puncher,
- durable underdog vs decision-heavy favorite.

These patterns can identify where to investigate, but they cannot substitute for a complete two-sided matchup evaluation.

---

# Sleeper — 8%

**Wes Schultz by Submission**

- Target: +275
- Play through: +250
- Pass below +250

Original rationale:

- 6 of Schultz's 9 wins were submissions.
- Both of Jackson McVey's professional losses were submissions.
- Schultz had submitted McVey in an earlier amateur meeting.

### Result

**Loss — McVey won by Round 1 TKO.**

### What went wrong

This was a compelling narrative that contained several true facts but did not sufficiently answer the central matchup question:

> Can Schultz force today's version of McVey into the grappling positions he needs before McVey imposes his own offense?

The old amateur result was particularly easy to overweight.

An amateur head-to-head result can be supporting evidence, but fighters can change substantially after years of development.

The professional submission-loss history was more relevant, but even that only described vulnerability after the correct positions were created.

It did not prove Schultz would reliably create them.

### Lesson

Do not confuse:

**opponent vulnerability once the fight enters a certain environment**

with:

**probability that the fight actually enters that environment.**

Those are separate variables.

---

# Parlay — 17%

## Leg 1
**Reinier de Ridder — Submission or Decision**

## Leg 2
**Mason Jones — KO/TKO or Decision**

## Leg 3
**Anthony Hernandez — KO/TKO or Decision**

- Target combined price: roughly +310
- Play through: +300 or better

### Result

**Loss.**

Multiple legs failed.

Rodrigues defeated Hernandez by unanimous decision.

### What went wrong

The Hernandez branch exposed the same structural issue seen elsewhere on the card.

The analysis spent significant effort deciding which Hernandez method to remove because Rodrigues had never been submitted professionally.

That was useful only if Hernandez's underlying win probability had already been evaluated correctly.

Instead, the opponent analysis should have been capable of reaching a more fundamental conclusion:

> Rodrigues may be live enough to win that we should not be building a method-based Hernandez leg at all.

### Lesson

Do not optimize a favorite's method tree before fully stress-testing the opponent's win case.

---

# Main Failure Pattern

## We underestimated opponent win probability and opponent resistance

This showed up most clearly in:

- Mason Jones vs MarQuel Mederos
- Serghei Spivac vs Vitor Petrino
- Anthony Hernandez vs Gregory Rodrigues

The common problem was not lack of information.

The problem was the order in which the information was used.

We tended to:

1. identify the fighter we liked,
2. identify that fighter's likely winning method,
3. check whether the opponent had vulnerabilities consistent with that method,
4. then price the bet.

That creates a natural confirmation bias.

Once a fighter is selected, opponent research can become a search for supporting vulnerabilities instead of a genuine attempt to disprove the play.

---

# Process Change Going Forward

## Old workflow

1. Identify the fighter we like.
2. Identify likely winning method.
3. Look for opponent vulnerabilities.
4. Compare to sportsbook price.
5. Bet if the price appears favorable.

## New workflow

### Step 1 — Build Fighter A's win case

Evaluate:

- offensive strengths,
- preferred environment,
- finishing routes,
- pace,
- cardio,
- durability,
- positional control,
- round-by-round sustainability.

### Step 2 — Independently build Fighter B's win case

Do not treat the opponent as a collection of weaknesses.

Evaluate the opponent as if we were trying to bet them.

Ask:

- What is their most credible path to victory?
- What happens if they survive the first dangerous phase?
- What skills directly interfere with Fighter A's strengths?
- Can they win minutes even without dominating?
- Are they stronger later than early?
- Do they possess a specific spoiler mechanism?

### Step 3 — Identify the strongest spoiler path for each fighter

Before choosing a side, write down the most dangerous failure mode for each.

Examples:

- defensive wrestling,
- get-up ability,
- submission survival,
- pace and attrition,
- counter power,
- clinch control,
- size,
- durability,
- late-round cardio,
- positional awareness.

### Step 4 — Determine the underlying win probability first

Do not move to method until the side itself is sufficiently established.

The key question:

> Is Fighter A actually mispriced to win, or are we merely attracted to one of Fighter A's possible methods?

### Step 5 — Only then split the win probability by method

Once the side is established, estimate:

- KO/TKO
- Submission
- Decision

For method props, think in two stages:

**P(method win) = P(fighter wins) × P(method | fighter wins)**

This prevents a strong-looking method share from masking an overestimated overall win probability.

### Step 6 — Check method leakage

Before excluding a method, ask whether the fighter's strongest weapon can naturally produce multiple finishing outcomes.

Example:

A dominant grappler may create:

- submission,
- ground-and-pound TKO,
- decision.

Therefore, a SUB/DEC double chance may still leak meaningful probability through TKO even against an opponent with strong historical durability.

### Step 7 — Evaluate method sustainability

For any finish-based play, ask:

- How easily can the fighter create the required position?
- How long can they maintain it?
- What happens if the first attempt fails?
- Does cardio materially decline?
- Does the opponent become more dangerous as the fight progresses?
- Is the method available in multiple rounds, or only during a narrow early window?

This should be especially important for:

- explosive KO fighters,
- aggressive submission hunters,
- low-sample prospects,
- fighters with questionable cardio,
- fighters whose entire edge depends on early physical dominance.

### Step 8 — Try to kill the bet

Before approval, actively search for evidence that the play is wrong.

Ask:

> What is the strongest evidence against this bet?

A play should survive adversarial review, not merely accumulate supporting evidence.

---

# Opponent-First Review Checklist

Before approving any UFC method or side, answer all of the following:

1. What is our fighter's preferred winning environment?
2. What is the opponent's preferred winning environment?
3. How does the opponent prevent our fighter's preferred environment?
4. If the opponent cannot prevent it, how well do they survive it?
5. What happens after the first failed attempt?
6. Who benefits as the fight gets longer?
7. What is the opponent's strongest spoiler mechanism?
8. Has the opponent shown that mechanism against comparable competition?
9. Are we relying too heavily on a historical zero such as "never been finished"?
10. Are we relying too heavily on an old amateur result or small sample?
11. Can the fighter's primary weapon naturally create more than one finish type?
12. Are we confident in the fighter's overall win probability before choosing a method?
13. Does the sportsbook price still offer a meaningful edge after accounting for uncertainty?
14. What evidence would make us pass?

If several answers remain uncertain, the correct action is often:

**PASS.**

---

# Betting Category Changes

## High Hit / Floor

A high-hit-rate method bet should require all of the following:

- strong underlying win probability,
- strong method concentration,
- low method leakage,
- durable path across multiple rounds,
- limited opponent spoiler risk,
- sufficient evidence quality.

Heavy favorite status alone is not enough.

## Balanced

Balanced plays should combine:

- solid underlying side,
- reasonable method concentration,
- meaningful price,
- manageable opponent resistance.

## Value

Plus-money value plays should not be approved simply because the implied probability is low.

They should require a clear probability cushion after accounting for uncertainty.

## Sleeper

Sleeper plays may use thinner or more specialized angles, but narrative evidence should be heavily discounted.

Examples of weak standalone evidence:

- old amateur head-to-head result,
- opponent has only two losses and both were submissions,
- fighter has a high percentage of wins by one method,
- opponent has never been finished.

These can support a play but should not create one by themselves.

---

# Evidence Weighting Changes

## Stronger evidence

Prioritize:

- recent professional fights,
- opponent-adjusted performance,
- positional success,
- defensive success,
- get-up ability,
- submission survival,
- pace under resistance,
- cardio over multiple rounds,
- results against similar archetypes,
- age/current-form context,
- weight-class context.

## Weaker evidence

Treat with caution:

- amateur head-to-head results,
- small sample historical zeros,
- raw finish percentages without opponent context,
- records built against weak competition,
- one-dimensional statistics without positional context.

---

# Model Implications

The future UFC model should reinforce this process mechanically.

It should not begin by deciding which fighter we like and then projecting a method.

The model should first produce an independent matchup distribution using both fighters' offensive and defensive components.

Important concepts to model include:

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
- uncertainty for low-sample fighters
- opponent quality
- current fighter state

The research layer should then interrogate the model rather than anchor it.

---

# Sacramento Card Classification

The card should be logged as:

## Primary failure tag
**Opponent evaluation / opponent win probability underestimated**

Applies especially to:

- Jones vs Mederos
- Spivac vs Petrino
- Hernandez vs Rodrigues

## Secondary failure tag
**Method-tree leakage / overly aggressive method exclusion**

Applies especially to:

- RdR SUB/DEC vs Dolidze

## Tertiary failure tag
**Narrative / historical-pattern overweighting**

Applies especially to:

- Schultz SUB vs McVey

---

# Going Forward

The central change is simple:

> Do not research the opponent merely to refine our fighter's winning method. Research the opponent strongly enough that the correct conclusion can be that our original fighter should not be bet at all.

For every future UFC card:

1. Evaluate both fighters independently.
2. Build both win cases.
3. Identify both spoiler paths.
4. Establish the side first.
5. Only then estimate method.
6. Stress-test method leakage.
7. Evaluate sustainability.
8. Try to kill the play.
9. Price it.
10. Pass freely when the evidence is not strong enough.

The goal is not to eliminate losses.

The goal is to stop making losses that come from the same avoidable reasoning error.
