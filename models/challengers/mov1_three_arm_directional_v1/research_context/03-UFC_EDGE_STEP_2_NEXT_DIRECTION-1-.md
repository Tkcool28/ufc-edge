# UFC EDGE — STEP 2: WHAT COMES AFTER THE FROZEN BASELINE

## PURPOSE

This document records the project reset immediately after the corrected M1 V1 baseline and Validation Terrain V1 were formally frozen.

It exists to preserve the reasoning behind the next phase so future work does not drift into model-building for its own sake.

The key principle is:

> **Every new model should answer a specific, predeclared question that moves UFC EDGE closer to better fight-betting decisions.**

The project now has:

- a trustworthy corrected winner-model baseline;
- a permanent model-independent validation terrain;
- known historical failure modes;
- explicit calibration diagnostics;
- durable temporal-safety rules;
- a living modeling-reset checklist;
- enough structure to evaluate specialized models honestly.

That changes the next question from:

> “What model should come after M1?”

to:

> **“What prediction target gives us the most direct path from the data we actually have to an actionable betting decision?”**

---

## 1. WHAT WE ACCOMPLISHED

UFC EDGE now has a frozen authoritative winner-model baseline:

**Corrected M1 V1**

It is not perfect, and it is not intended to be.

Its purpose is to provide a trustworthy reference point against which future winner models can be compared.

UFC EDGE also has:

**Validation Terrain V1**

This gives every future model the same historical environments for evaluation.

The rule is:

> **Same historical terrain, different model.**

This means future work can ask not only whether a model improves globally, but also:

- where it improves;
- where it degrades;
- how confidence behaves;
- whether performance changes with experience;
- whether missingness matters;
- whether striking/grappling environments matter;
- whether the model should abstain or reduce confidence in some situations.

The project now has a known baseline and a known evaluation framework.

---

## 2. WHAT WE LEARNED FROM M1

Corrected M1 demonstrated something important:

A generalized winner model can be reasonably calibrated and useful without being the final answer to the betting problem.

M1 is valuable because it gives us:

- broad winner probabilities;
- a benchmark;
- a calibration reference;
- diagnostic weaknesses;
- a way to compare future challenger models.

But betting on UFC fights is not limited to asking:

> “Who wins?”

The project ultimately cares about probabilities such as:

- winner;
- KO/TKO;
- submission;
- decision;
- inside distance;
- goes distance;
- potentially round or timing outcomes later.

That means future progress does **not** require every new model to be a globally stronger version of M1.

A specialized model that answers one narrow wagering question extremely well may be more useful than a generalized model that improves aggregate log loss only slightly.

---

## 3. THE LONG-TERM ARCHITECTURE

The long-term north star remains a fight simulator.

Conceptually:

**Fight-state understanding → probability models → betting decisions**

A sufficiently strong simulator could eventually generate many useful probabilities from one underlying representation of a fight.

However, the project should not depend on obtaining perfect simulator-quality data.

If the required data never becomes available, UFC EDGE is now structured well enough to build specialized probability engines instead.

Examples include:

- winner probability;
- KO/TKO probability;
- submission probability;
- decision probability;
- inside-distance probability;
- goes-distance probability;
- finish timing;
- confidence/abstention models.

These models do not necessarily need:

- the same feature set;
- the same architecture;
- the same model family;
- the same training target.

They only need to be:

- temporally safe;
- reproducible;
- honestly validated;
- calibrated for their intended probability;
- useful for a clearly defined decision.

---

## 4. WHY WE SHOULD NOT AUTOMATICALLY START M1B

The corrected M1 foundation is frozen.

That does **not** mean the next automatic step is M1B.

Before building another winner model, the project should first ask:

> **What exact problem would M1B solve that corrected M1 does not solve well enough?**

If that question does not have a strong answer, M1B should wait.

The same applies to:

- trees;
- boosting;
- opponent adjustment;
- new feature families;
- aggressive feature selection;
- more complex generalized models.

Complexity should be earned by a specific unanswered question.

---

## 5. RECOMMENDED NEXT PHASE

The strongest next step is:

# UFC EDGE — BETTING TARGET FEASIBILITY + MODEL ARCHITECTURE AUDIT V1

This should be an audit only.

Do not train a new model yet.

Do not use sportsbook odds.

Do not analyze ROI.

Do not optimize betting thresholds.

The purpose is to answer:

> **Given the data UFC EDGE actually has today, what fight-betting probability targets can we build honestly and validate properly right now?**

---

## 6. CANDIDATE TARGETS TO AUDIT

The audit should examine at least:

| Target | Potential betting use |
|---|---|
| Winner | Moneyline |
| KO/TKO | KO/TKO method market |
| Submission | Submission market |
| Decision | Decision market |
| Inside distance | Broad finish market |
| Goes distance | Distance market |
| Early vs late finish | Potential timing/round markets |
| Exact round | Only if label quality and sample size support it |

For every target, answer:

1. Do we have a clean historical label?
2. Is that label consistently available across the historical period?
3. Is the label definition stable across eras?
4. How many usable historical fights exist?
5. How imbalanced is the target?
6. Which current F01/F02 predictors are plausibly relevant?
7. Are those predictors point-in-time safe?
8. Are there important missing variables that UFC EDGE currently cannot observe?
9. Can the target be evaluated on Validation Terrain V1?
10. What should the simplest frozen baseline be?
11. What evaluation metrics matter?
12. What would constitute meaningful improvement?
13. What calibration diagnostics should be required?
14. Are there environments where abstention or reduced confidence may matter?
15. Is the target useful enough for betting to justify a dedicated model?

---

## 7. WHY MOV DESERVES SPECIAL ATTENTION

Validation Terrain V1 already produced an important observation:

Historical fight outcomes shift meaningfully with striking and grappling pressure environments.

Examples from the frozen terrain include:

- higher striking-pressure environments showing materially higher KO/TKO rates;
- higher grappling-pressure environments showing materially higher submission rates;
- two-sided grappling being a relative weakness for M1 winner discrimination.

These findings do **not** prove a profitable betting edge.

They do show that the current data appears to contain information about **how fights end**, not just who wins.

That makes method-of-victory modeling a legitimate next research direction.

---

## 8. POSSIBLE PATHS AFTER THE AUDIT

The audit should choose among several legitimate directions rather than assuming one in advance.

### PATH A — M1B / BETTER GENERALIZED WINNER MODEL

Choose this if:

- winner probability remains the highest-value foundational target;
- corrected M1 has identifiable representational limitations;
- a new model family or feature treatment has a specific reason to improve them;
- better winner estimates are needed before later conditional MOV models.

M1B should not exist merely because “M1 comes before M1B.”

---

### PATH B — FIRST MOV SPECIALIST

Build one narrow probability model first.

Example:

> **P(KO/TKO | pre-fight state)**

This would directly test whether a specialized model can answer one wagering question better than a generalized architecture.

Other first-specialist candidates could be:

- submission probability;
- decision probability;
- goes-distance probability.

The target should be selected from the feasibility audit, not preference.

---

### PATH C — HIERARCHICAL MOV ARCHITECTURE

Instead of immediately training one three-class KO/submission/decision model, consider decomposing the problem.

Example:

1. **P(finish)**
2. Conditional on finish:
   - **P(KO/TKO | finish)**
   - **P(submission | finish)**
3. Decision becomes the complement of finish.

This may be statistically easier and more interpretable than forcing one model to solve all outcomes simultaneously.

The audit should determine whether this decomposition fits the available labels and data.

---

### PATH D — SIMULATOR DATA-GAP ANALYSIS

Instead of training immediately, perform a dedicated audit of what the eventual simulator still lacks.

Candidate concepts may include:

- positional transitions;
- strike pace changes;
- control-state transitions;
- takedown chains;
- submission threat state;
- damage proxies;
- fatigue;
- momentum/pressure changes;
- round-to-round state persistence;
- finish hazard.

For each missing concept, determine:

- whether it can be sourced historically;
- whether it can be sourced reliably;
- whether it can be made point-in-time safe;
- whether coverage is sufficient;
- whether the cost is justified.

This keeps the simulator path alive without forcing it prematurely.

---

## 9. SPECIALIZED MODELS ARE ALLOWED TO BE SPECIALIZED

A future model does not have to beat corrected M1 everywhere.

Example:

Suppose a future grappling-specialist model is designed only for fights classified by the frozen terrain as:

- `GRAPPLE_ONE_SIDED`
- `GRAPPLE_TWO_SIDED`

If that model answers a preregistered question materially better on a sufficiently large historical population, it can be useful even if it has no purpose on most UFC fights.

That is acceptable.

The objective is not:

> “Find one model that dominates every fight.”

The objective is:

> **Build trustworthy probability tools that answer specific betting-relevant questions where the data supports them.**

A future UFC EDGE system may therefore contain:

- a generalized winner baseline;
- specialized winner challengers;
- KO specialists;
- submission specialists;
- decision specialists;
- abstention models;
- environment-specific tools;
- eventually a simulator.

These can coexist if each has a clear contract and purpose.

---

## 10. THE THREE PRIMARY WAGERING OUTCOMES

At the practical method-of-victory level, UFC EDGE is fundamentally interested in three broad outcome families:

1. **KO/TKO**
2. **Submission**
3. **Decision**

Because these represent the dominant method-of-victory wagering structure, relatively small but reliable changes in the estimated probability of one or two of these outcomes can matter substantially.

That creates room for highly specialized models.

A model does not necessarily need to understand the entire fight equally well.

It may only need to identify one or two pieces of pre-fight information that materially shift:

- KO/TKO probability;
- submission probability;
- decision probability.

Those shifts can later be compared to sportsbook implied probabilities after the predictive model is frozen.

---

## 11. MARKET DISCIPLINE REMAINS IMPORTANT

Predictive modeling and betting evaluation must remain separate.

The sequence should remain:

**build probability → freeze probability model → evaluate against market**

Not:

**search historical sportsbook results → engineer model until it finds profitable pockets**

Future market evaluation may include:

- implied probabilities;
- vig removal;
- market timing;
- line movement;
- closing prices;
- liquidity;
- betting limits;
- EV;
- ROI;
- staking.

But those belong after the predictive target/model is frozen.

---

## 12. THE RESET QUESTION FOR EVERY FUTURE MODEL

Before authorizing any future major modeling task, answer:

> **What exact betting-relevant probability or decision will this work improve, and what evidence would prove that improvement?**

If that cannot be answered clearly, do not build the model yet.

Other useful reset questions include:

- What information can this model represent that the frozen baseline cannot?
- Is the question globally useful or intentionally specialized?
- Is the target cleanly labeled?
- Can it be validated without market information?
- Is calibration measurable?
- Can we identify when the model should abstain?
- Does the expected output correspond to an actual market we could eventually compare against?
- Would we still consider the model useful if sportsbook odds did not exist?

---

## 13. RECOMMENDED IMMEDIATE NEXT ACTION

Do **not** begin M1B automatically.

Do **not** begin MOV model training automatically.

First perform:

# BETTING TARGET FEASIBILITY + MODEL ARCHITECTURE AUDIT V1

The audit should inventory:

- available labels;
- historical coverage;
- target balance;
- point-in-time predictor availability;
- missing critical information;
- appropriate baselines;
- appropriate metrics;
- calibration requirements;
- Validation Terrain compatibility;
- likely modeling architectures;
- simulator dependencies.

Then return to MASTER/PM and choose the next model deliberately.

---

## FINAL DIRECTION

UFC EDGE has moved beyond:

> “Build a generic prediction model and see if it works.”

The project can now operate as:

> **Identify a betting-relevant question → define the probability target → freeze the evaluation contract → build the simplest model capable of answering it → validate it on permanent historical terrain → understand where it works and where it fails → only then compare the frozen probabilities to the market.**

The fight simulator remains the long-term ideal.

But it is no longer the only path to a useful UFC betting system.

If simulator-quality data proves unavailable, UFC EDGE is now positioned to build a collection of narrower, disciplined, purpose-built probability machines.

That is the direction for Step 2.
