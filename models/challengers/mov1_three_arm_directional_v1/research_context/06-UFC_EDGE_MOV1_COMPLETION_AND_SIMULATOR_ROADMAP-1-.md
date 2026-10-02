# UFC EDGE — MOV1 Completion + Simulator Roadmap

**Status:** Active roadmap
**Purpose:** Preserve the intended next steps and long-term UFC EDGE direction so future work can re-anchor to this plan if context, tooling, or project focus is lost.

## Long-term objective

UFC EDGE is not being built as a collection of isolated prediction models. The long-term goal is a trustworthy pre-fight probability system that can eventually support a **hybrid UFC fight simulator**.

The simulator should ultimately help identify situations where model-derived probabilities differ meaningfully from sportsbook prices.

Conceptually:

**pre-fight fighter state**
→ **finish/survival probability**
→ **conditional finish pathway**
→ **KO/TKO vs submission**
→ later **round/state transitions and decision behavior**
→ **full outcome distribution**
→ compare with market prices
→ identify potential value opportunities

Core model development should remain independent of sportsbook prices and historical ROI optimization whenever possible. Build the probability engine first; market comparison belongs downstream.

---

## Current architecture

### MOV0 — Finish vs decision

MOV0 estimates:

`P(STANDARD_FINISH)`

where STANDARD_FINISH means KO/TKO or submission.

Therefore:

`P(DECISION) = 1 - P(STANDARD_FINISH)`

The evidence-supported current surface is **MOV0-MIN**.

### MOV1 — KO vs submission given finish

MOV1 estimates:

`P(KO/TKO | STANDARD_FINISH)`

with:

`P(SUBMISSION | STANDARD_FINISH) = 1 - P(KO/TKO | STANDARD_FINISH)`

The first frozen MOV1 run established that this decomposition contains real predictive signal.

The evidence-supported current surface is **MOV1-MIN**.

### Current composed three-way system

Let:

`F = P(STANDARD_FINISH)`

`K = P(KO/TKO | STANDARD_FINISH)`

Then:

`P(KO/TKO) = F × K`

`P(SUBMISSION) = F × (1 - K)`

`P(DECISION) = 1 - F`

This gives a complete pre-fight KO / Submission / Decision distribution.

---

## Current MOV1 result

### Conditional log loss

| Model | Conditional Log Loss |
|---|---:|
| Historical prevalence | 0.651593 |
| Context | 0.641605 |
| MOV1-MIN | **0.615366** |
| MOV1-FULL | 0.619689 |

MOV1-MIN improved over context in **all nine outer years**.

### Composed three-way log loss

| System | Three-Way Log Loss |
|---|---:|
| MOV0 + prevalence | 0.993740 |
| MOV0 + context | 0.988782 |
| MOV0 + MOV1-MIN | **0.975754** |
| MOV0 + MOV1-FULL | 0.977901 |

The MOV0 + MOV1-MIN architecture therefore improved the complete KO/SUB/DEC system. MOV1-FULL did not improve over MIN and is not the preferred surface.

---

## What MOV1 already does well

### KO-oriented striking pathways

**KD creation vs weak strike defense**

- predicted KO given finish: ~72.2%
- actual: ~72.4%

**KO history vs KO vulnerability**

- predicted: ~77.1%
- actual: ~75.2%

These results show method-specific striking signal rather than simple division memorization.

### Weight-class structure

**Heavyweight**

- predicted conditional KO: ~76.9%
- actual: ~77.5%

**Light Heavyweight**

- predicted: ~74.7%
- actual: ~74.1%

**Flyweight**

- predicted: ~56.0%
- actual: ~52.1%

The model captures broad method composition while still varying probabilities by fighter state and fold.

---

## Main known MOV1 weakness

The clearest weakness is **submission-pathway calibration**.

The model recognizes grappling/submission environments in the correct direction, but often does not move far enough toward submission.

### TD access + submission pressure

- MOV1-MIN predicted KO: ~55.2%
- actual KO: ~46.0%

Equivalent submission interpretation:

- predicted submission given finish: ~44.8%
- actual: ~54.0%

### Submission pressure vs submission vulnerability

- predicted KO: ~54.1%
- actual KO: ~45.1%

So some important grappling environments remain roughly **nine percentage points too KO-heavy**.

This is the primary known modeling weakness to attack next.

---

## Additional calibration limitation

MOV1-MIN is useful but not perfectly calibrated.

Current evidence includes:

- calibration slope around **0.831**
- some upper-tail KO overconfidence
- overall submission probability somewhat understated
- very low KO-probability tail remains thin and uncertain

Calibration and nonlinear interaction learning should be treated as separate scientific questions.

---

# Next Step 1 — Nonlinear MOV1 Challenger

The immediate next major modeling task should be a **nonlinear challenger to MOV1-MIN**.

Recommended first family: **gradient-boosted trees**.

Possible libraries include XGBoost, LightGBM, or another reproducible boosting implementation suitable for the repository. The exact implementation must be selected and frozen before evaluation.

## Scientific question

> Can nonlinear interaction learning improve KO-vs-submission probability estimation beyond frozen linear MOV1-MIN?

More specifically:

> Can it correct known grappling/submission interaction failures while preserving the strong striking and weight-class behavior already learned by MOV1-MIN?

## Keep frozen

The challenger should preserve:

- target definition;
- finish-only training population;
- all-eligible scoring population;
- 2015+ fitting history;
- 2018–2026 outer folds;
- corrected F02;
- governed predictor surface;
- division context;
- Validation Terrain;
- frozen archetypes;
- fixed probability buckets;
- three-way composition;
- complete KO/SUB/DEC evaluation.

The experiment should change **model family**, not the scientific target.

## Key success tests

### Aggregate

Does it improve:

- conditional log loss;
- Brier score;
- calibration;
- AUC?

### Complete system

When composed with frozen MOV0-MIN, does it improve:

- multiclass log loss;
- multiclass Brier;
- classwise calibration?

### Grappling correction

Especially test:

- TD access + submission pressure;
- submission pressure vs submission vulnerability;
- TD pressure vs weak TD defense;
- TD conversion vs weak TD defense.

### Preserve current strengths

Do not accept a model merely because aggregate log loss improves if it materially damages:

- KD creation vs weak strike defense;
- KO history vs KO vulnerability;
- Heavyweight;
- Light Heavyweight;
- other well-calibrated KO-heavy environments.

The goal is to fix interaction weaknesses **without destroying existing strengths**.

---

# Next Step 2 — Choose the Better Underlying MOV1 Model

After the nonlinear challenger, compare:

- frozen linear MOV1-MIN;
- nonlinear MOV1 challenger.

Use chronological out-of-fold evidence.

Select the preferred underlying model only after reviewing:

- aggregate metrics;
- annual persistence;
- calibration;
- terrain;
- division behavior;
- archetypes;
- composed three-way probabilities.

Do not select from one metric alone.

Possible outcomes:

- linear remains preferred;
- nonlinear clearly wins;
- nonlinear adds only limited or terrain-specific value.

All three outcomes are scientifically useful.

---

# Next Step 3 — Calibration Experiment

Once the preferred underlying MOV1 model is chosen, perform a **separate calibration experiment**.

Do not mix calibration tuning into the model-family comparison.

Potential methods:

- logistic / Platt recalibration;
- isotonic calibration if sample size and chronology justify it.

Calibration must be learned only from historical pre-validation predictions. No outer-year outcome may influence its own calibration mapping.

The question is:

> Given the best underlying ranking model, can the probability scale be improved so that predicted percentages correspond more closely to observed frequencies?

Focus on:

- overall conditional calibration slope;
- fixed probability buckets;
- KO-heavy upper tail;
- submission-heavy grappling environments;
- weight-class calibration;
- complete three-way classwise calibration.

---

# MOV1 completion criteria

MOV1 should be considered mature enough to freeze when:

1. **Preferred model family is established**
   Chronological evidence has selected either linear MOV1-MIN or a nonlinear challenger.

2. **Pathway behavior is understood**
   We understand behavior across striking, grappling, divisions, permanent terrain, and probability tails.

3. **Calibration is acceptable**
   Predicted percentages roughly correspond to observed frequencies over suitable historical samples.

4. **The composed system remains better**
   The final MOV1 node continues to improve the complete KO / SUB / DEC distribution.

5. **A governed final version is frozen**
   Future changes require a separate preregistered challenger.

---

# Possible Later Challenger — Direct Three-Way Model

After the hierarchical architecture is mature, consider an independent direct multiclass challenger:

`P(KO), P(SUB), P(DECISION)`

This should not automatically replace the current architecture.

Its purpose is to compare:

### Hierarchical decomposition

`P(FINISH) × P(METHOD | FINISH)`

versus

### Direct multiclass modeling

`P(KO, SUB, DECISION)` jointly.

If the hierarchy wins, that supports the simulator architecture. If direct multiclass wins, that is also useful evidence.

Do this only after the current MOV architecture is mature enough to be a fair benchmark.

---

# Longer-term simulator direction

MOV0/MOV1 are the beginning, not the final simulator.

A future hybrid simulator may need:

## Pre-fight latent state

Examples:

- striking threat;
- grappling access;
- submission threat;
- defensive durability;
- experience;
- pace;
- cardio;
- scheduled rounds;
- weight class.

## Round-level state evolution

Potential future concepts:

- round-specific finish probability;
- accumulated damage;
- changing pace;
- takedown/control state;
- fatigue;
- survival into later rounds.

## Competing finish pathways

Conceptually:

`pre-fight state`

→ round state

→ KO hazard

→ submission hazard

→ survival

→ next round

→ eventual decision state

Predictive logistic coefficients must **not** be treated as causal hazard or transition parameters. A separate simulator-design audit will be needed before translating predictive models into round/state mechanics.

---

# Relationship to sportsbook analysis

The simulator and probability system are ultimately intended to help identify possible market inefficiencies.

Future workflow:

1. generate trustworthy pre-fight probabilities;
2. produce full outcome distributions;
3. compare those probabilities with sportsbook prices;
4. convert prices to implied probabilities with appropriate vig handling;
5. estimate model-vs-market differences;
6. account for uncertainty and model reliability;
7. only then evaluate whether a price represents a usable betting opportunity.

The preferred direction is:

> **Build the strongest trustworthy probability engine first, then test whether the market misprices its information.**

Do not shape core predictive models merely to maximize historical sportsbook ROI.

---

# Project guardrails

If project direction becomes unclear, return to these rules.

## Do

- preserve point-in-time integrity;
- freeze experiments before outcomes;
- use chronological validation;
- retain negative experiments;
- distinguish structural audits from predictive evaluation;
- compare complete probability systems;
- keep calibration visible;
- preserve interpretable diagnostic surfaces;
- document limitations;
- retain reproducible evidence.

## Do Not

- chase isolated historical wins;
- optimize core features directly against sportsbook ROI;
- rewrite experiments after seeing results;
- silently change folds or targets;
- treat descriptive associations as causal laws;
- assume more complex models are automatically better;
- turn every historical pattern into a feature;
- confuse classification accuracy with probability quality;
- allow the simulator goal to drift away from validated pre-fight probabilities.

---

# Immediate roadmap

1. **MOV0 frozen finish-vs-decision model** — COMPLETE
2. **MOV0 diagnostics** — COMPLETE
3. **MOV0 hierarchical challenger** — COMPLETE / NOT SUPPORTED
4. **Finish-method structural audit** — COMPLETE
5. **MOV1 linear contract** — COMPLETE
6. **MOV1 first frozen linear run** — COMPLETE / CLEAR SUCCESS
7. **Nonlinear MOV1 challenger** — NEXT
8. **Choose preferred MOV1 model**
9. **Chronological calibration experiment**
10. **Freeze mature MOV1**
11. **Re-evaluate final KO/SUB/DEC architecture**
12. **Consider direct multiclass challenger**
13. **Design next simulator-oriented target/state layer**
14. **Eventually integrate model probabilities with sportsbook-market comparison**

---

# Anchor principle

> **Build a trustworthy, chronologically validated UFC probability engine that can eventually drive a realistic hybrid fight simulator and identify situations where model probabilities differ meaningfully from sportsbook prices.**

Every new model should answer a clearly defined probability question.

Every simulator component should be grounded in validated evidence.

Every betting application should sit **downstream** of the probability model rather than dictate its construction.
