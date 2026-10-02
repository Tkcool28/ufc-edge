# UFC Fight Modeling Master Plan

## Purpose

Build a UFC modeling system that predicts the fight itself as cleanly as possible, then uses sportsbook prices only **afterward** as an external comparison layer.

The core philosophy is:

> **Predict the fight first. Price the bet second.**

The system is not intended to learn historical sportsbook prices or optimize directly for historical betting ROI. UFC outcomes are too noisy and the sportsbook already incorporates information that may not exist in public fight statistics.

Instead, the model should mechanically estimate:

- What fight environments each fighter can create
- How well the opponent can prevent those environments
- How well the opponent can survive once those environments occur
- How those dynamics change by round
- The resulting probabilities of KO/TKO, submission, decision, round of finish, and total fight duration

The sportsbook is then used as a **diagnostic layer**:

- Where does the market disagree with our modeled fight environment?
- Is that disagreement about winning probability, method concentration, durability, pace, or survivability?
- Which discrepancies deserve deeper matchup research?

---

# 1. Final System Vision

```text
RAW UFC DATA
    ↓
POINT-IN-TIME RECONSTRUCTION
    ↓
FIGHTER STATE / FEATURE ENGINE
    ├─ striking creation
    ├─ striking prevention
    ├─ wrestling creation
    ├─ wrestling prevention
    ├─ submission creation
    ├─ submission prevention
    ├─ durability
    ├─ pace/cardio
    ├─ environment tendencies
    └─ opponent-adjusted performance
           ↓
MATCHUP FEATURE ENGINE
    ├─ A creation vs B prevention
    ├─ B creation vs A prevention
    ├─ environment control
    ├─ method concentration
    └─ round-by-round persistence
           ↓
MODEL STACK
    ├─ Model 0: Historical baselines
    ├─ Model 1: Simple predictive baseline
    ├─ Model 2: Component / environment models
    └─ Model 3: Monte Carlo fight simulator
           ↓
FIGHT FORECAST
    ├─ win probabilities
    ├─ KO/TKO probabilities
    ├─ submission probabilities
    ├─ decision probabilities
    ├─ round finish probabilities
    ├─ totals probabilities
    └─ environment probabilities
           ↓
SPORTSBOOK COMPARISON
    ├─ de-vig prices
    ├─ method leakage
    ├─ survivability disagreement
    ├─ environment disagreement
    └─ alternate market confirmation
           ↓
HUMAN MATCHUP RESEARCH
           ↓
BETTING CARD
    ├─ High Hit Rate
    ├─ Balance
    ├─ Value
    └─ Sleeper
```

---

# 2. Non-Negotiable Design Rules

## 2.1 No future leakage

For every historical fight at time **T**, every feature must use only information available **before T**.

Never use:

- Current UFCStats career summaries to predict old fights
- Future wins or losses
- Future method outcomes
- Future opponent ratings
- Scaling parameters fit on future data
- Random train/test splits for final evaluation

Every historical fighter state must be rebuilt chronologically.

---

## 2.2 Sportsbook odds stay outside the core fight model

The primary model must be independent of betting-market prices.

Do not use:

- Moneyline
- Method-of-victory price
- Totals price
- Round props
- Closing odds

as predictive inputs to the core fight model.

Reason:

We want:

> UFC data → fight probability

then separately:

> fight probability vs sportsbook probability

A later market-aware challenger model may be useful, but it must never replace the independent core model.

---

## 2.3 Features before model complexity

A sophisticated model cannot rescue weak fighter-state construction.

Priority order:

1. Raw data integrity
2. Point-in-time reconstruction
3. Fighter-state features
4. Matchup interaction features
5. Simple predictive models
6. Component models
7. Simulator

---

## 2.4 Offensive creation must always be paired with opponent prevention

The system should never treat:

> Fighter A has great KO numbers

as sufficient.

Instead:

> How often can A create the environment required for a KO?

then:

> How well can B prevent that environment?

then:

> If the environment occurs, how well does B survive it?

This applies equally to:

- KO/TKO
- submissions
- wrestling/control
- decision-heavy fights

---

# 3. Raw Data Requirements

## 3.1 Must-have fight-level fields

For every UFC fight:

- Fight ID
- Event ID
- Event date
- Fighter A
- Fighter B
- Winner
- Result
- Method
- Ending round
- Ending time
- Scheduled rounds
- Weight class
- Title fight indicator

---

## 3.2 Must-have fighter physical fields

- Fighter ID
- Name
- Date of birth
- Height
- Reach
- Weight
- Stance

---

## 3.3 Must-have fighter-round statistics

For each fighter in each round:

### General
- Knockdowns
- Control time
- Reversals
- Submission attempts

### Significant striking
- Significant strikes landed
- Significant strikes attempted

### Total striking
- Total strikes landed
- Total strikes attempted

### Takedowns
- Takedowns landed
- Takedowns attempted

### Strike target
- Head landed
- Head attempted
- Body landed
- Body attempted
- Leg landed
- Leg attempted

### Strike position
- Distance landed
- Distance attempted
- Clinch landed
- Clinch attempted
- Ground landed
- Ground attempted

---

# 4. Data Source Plan

## Historical backfill

Preferred initial historical source:

- Maintained UFCStats-derived dataset
- Store a local immutable copy in our own repo/database
- Normalize into our own canonical schema

The external source is only ingestion.

Once data enters our system, our model should not depend on that external source remaining online.

---

## Incremental updates

After each UFC event:

1. Query only new event/fight data
2. Insert unseen fights
3. Validate totals and fighter identities
4. Rebuild affected fighter states
5. Generate current-card features

A lightweight UFCStats JSON/API wrapper is preferred for incremental updates if reliable.

Scraping UFCStats directly remains the fallback.

---

# 5. Canonical Data Tables

Suggested minimum schema.

## `fighters`

- fighter_id
- name
- dob
- height_cm
- reach_cm
- weight_lbs
- stance

## `events`

- event_id
- event_name
- event_date
- location

## `fights`

- fight_id
- event_id
- fighter_a_id
- fighter_b_id
- winner_id
- result
- method
- finish_round
- finish_time_sec
- scheduled_rounds
- weight_class
- title_bout

## `fight_round_stats`

One row per fighter per round.

- fight_id
- round
- fighter_id
- opponent_id
- kd
- sig_landed
- sig_attempted
- total_landed
- total_attempted
- td_landed
- td_attempted
- sub_attempts
- reversals
- control_sec
- head_landed
- head_attempted
- body_landed
- body_attempted
- leg_landed
- leg_attempted
- distance_landed
- distance_attempted
- clinch_landed
- clinch_attempted
- ground_landed
- ground_attempted

---

# 6. Fighter State Engine

The fighter state engine is the center of the project.

For every historical fight, the engine must generate each fighter's state **before that fight occurs**.

Every major metric should ideally have multiple versions:

- Career
- Recent 3
- Recent 5
- Exponentially weighted recent form
- Opponent-adjusted version where feasible
- Round-specific version where meaningful

---

# 7. Feature Family A — Striking Environment

## 7.1 Striking opportunity / pace

Required features:

- Significant-strike attempts per minute
- Significant strikes landed per minute
- Significant strikes absorbed per minute
- Opponent significant-strike attempts faced per minute
- Distance attempts per minute
- Clinch attempts per minute
- Ground strike attempts per minute
- Exchange pace
- Significant-strike differential per minute

Purpose:

Estimate whether a fight will produce enough striking opportunities for a KO environment.

---

## 7.2 Striking creation

- Knockdowns per 15
- Knockdowns per significant strike landed
- Knockdowns per head strike landed
- Head significant strikes landed per minute
- Head strike accuracy
- Body strike rate
- Leg strike rate
- Distance strike rate
- Clinch strike rate
- Ground strike rate
- Significant-strike accuracy
- Damage creation proxy
- Early knockdown rate
- Late knockdown rate

---

## 7.3 Striking prevention

- Significant strikes absorbed per minute
- Head strikes absorbed per minute
- Opponent head-strike accuracy
- Significant-strike defense
- Knockdowns suffered per 15
- Knockdowns suffered per head strike absorbed
- KO/TKO losses
- KO/TKO loss rate
- Defensive pace suppression
- Distance defense
- Clinch defense proxy
- Ground-strike defense proxy

---

# 8. Feature Family B — Wrestling Environment

## 8.1 Wrestling creation

- Takedown attempts per 15
- Takedowns landed per 15
- Takedown accuracy
- Control time per 15
- Control share
- Repeated takedown attempt rate
- Wrestling-heavy fight rate

---

## 8.2 Wrestling prevention

- Takedown attempts faced per 15
- Takedown defense %
- Takedowns conceded per 15
- Control time allowed per 15
- Control share conceded
- Reversal rate
- Ground exposure allowed

---

# 9. Feature Family C — Submission Environment

## 9.1 Submission creation

- Submission attempts per 15
- Submission attempts per ground minute
- Submission wins
- Submission win rate
- Submission conversion
- Control-to-submission conversion
- Takedown-to-submission pipeline
- Ground exposure created

---

## 9.2 Submission prevention

- Submission attempts faced per 15
- Submission attempts faced per ground minute
- Submission losses
- Submission loss rate
- Submission-attempt survival rate
- Control time allowed
- Reversal/escape proxy
- Ground minutes per submission loss

---

# 10. Feature Family D — Durability

Durability should be modeled as a skill, not merely a loss count.

## Strike durability

- Minutes fought per knockdown suffered
- Head strikes absorbed per knockdown suffered
- Knockdowns suffered
- Knockdowns survived
- KO/TKO losses per damaging exposure
- Finish-loss rate
- Early finish-loss rate
- Late finish-loss rate

## Submission durability

- Submission attempts faced per submission loss
- Ground minutes per submission loss
- Control time allowed per submission loss
- Submission survival rate

## General durability

- Career minutes
- Average fight duration
- Decision reach rate
- Percentage surviving Round 1
- Percentage surviving Round 2
- Historical finish-loss rate

---

# 11. Feature Family E — Cardio / Persistence

Round-specific behavior is essential.

Build:

- R1 strike attempts/min
- R2 strike attempts/min
- R3 strike attempts/min
- R4/R5 where applicable
- Pace change R1 → R2
- Pace change R2 → R3
- Accuracy change by round
- Defense change by round
- TD attempt change by round
- TD success change by round
- Control-time change by round
- KD distribution by round
- Submission-attempt distribution by round

Potential derived features:

- Striking fade score
- Wrestling fade score
- Defensive fade score
- Late-fight persistence score
- Late-fight vulnerability score

---

# 12. Feature Family F — Finish Profile

For each fighter:

- KO win rate
- Submission win rate
- Decision win rate
- KO loss rate
- Submission loss rate
- Decision loss rate
- R1 finish rate
- R2 finish rate
- R3+ finish rate
- R1 finish-loss rate
- R2+ finish-loss rate

Important distinction:

## Explosive finisher

Finishes through immediate fight-ending events.

Possible indicators:

- High early KD rate
- High KD/strike ratio
- High R1 finish rate
- Low buildup requirement

## Pressure / cumulative finisher

Finishes by sustained volume and attritional damage.

Possible indicators:

- High pace
- High cumulative significant-strike differential
- Lower KD/strike ratio
- Higher R2/R3 finish share
- Opponent defense degradation

These should not be treated as the same type of KO threat.

---

# 13. Feature Family G — Context

- Age
- Age difference
- Reach
- Reach difference
- Height
- Height difference
- Stance
- Stance matchup
- Weight class
- Scheduled rounds
- Title fight
- UFC experience
- Days since last fight
- Recent activity
- Win streak
- Loss streak
- Recent 3 record
- Recent 5 record
- Weight-class change if obtainable
- Short-notice status if obtainable

---

# 14. Feature Family H — Opponent Adjustment

Raw averages can be deceptive.

Eventually construct phase-specific performance relative to opponent expectation.

Examples:

## Striking creation over expectation

```text
fighter strikes landed
minus
opponent's typical strikes allowed
```

## Striking defense over expectation

```text
fighter strikes absorbed
minus
opponent's typical strikes landed
```

## Wrestling creation over expectation

```text
fighter TD performance
minus
opponent's typical TDs conceded
```

## Wrestling defense over expectation

```text
fighter TDs conceded
minus
opponent's typical TD production
```

## Submission creation over expectation

```text
fighter submission creation
relative to
opponent's usual submission resistance
```

These may ultimately become latent offensive and defensive ratings for each phase.

---

# 15. Matchup Interaction Engine

This layer converts fighter states into matchup-specific features.

Do not rely only on:

```text
A_stat - B_stat
```

Build explicit interactions.

---

## 15.1 KO environment

Components may include:

- A striking pace
- A standing-time tendency
- A KD creation
- A head-strike creation
- B standing exposure
- B head-strike absorption
- B KD susceptibility
- B KO durability
- B wrestling/clinch interruption ability
- A cardio persistence
- B defensive fade

Goal:

Estimate:

> Can A create and maintain an environment in which a KO becomes plausible?

---

## 15.2 Submission environment

Components:

- A TD attempt rate
- A TD success
- B TD susceptibility
- A control ability
- B control escape
- A submission-attempt rate
- B submission-attempt survival
- A submission conversion
- B late-round fatigue

---

## 15.3 Decision environment

Components:

- Low finish creation
- Strong opponent durability
- Low pace
- Strong defensive wrestling
- Limited submission exposure
- Low knockdown rates
- Strong round-to-round persistence
- Minute-winning ability

---

## 15.4 Environment control

Potential matchup questions:

- Who dictates standing vs grappling?
- Who forces the preferred phase?
- Who can prevent the opponent's preferred phase?
- Does one fighter possess a strong phase mismatch?
- Can that mismatch persist for three or five rounds?

---

# 16. Model Build Order

---

# Model 0 — Historical Baseline

No machine learning.

Purpose:

Create reference distributions and sanity checks.

Examples:

- KO rate by division
- Submission rate by division
- Decision rate by division
- Finish rate by round
- Finish rate by scheduled rounds
- Average duration
- Baseline KD rate
- Baseline TD rate

### Pass criteria

- Data counts reconcile
- Method categories are clean
- Round totals are internally consistent
- Historical rates look plausible
- No obvious data corruption

---

# Model 1 — Simple Predictive Baseline

Purpose:

Test whether the feature engine contains useful information.

Start simple.

Possible models:

- Regularized logistic regression
- Multinomial logistic regression

Potential targets:

- Fighter A wins
- Fight finishes
- Fighter A KO/TKO
- Fighter A submission
- Fighter A decision
- Fighter B KO/TKO
- Fighter B submission
- Fighter B decision

This model is a benchmark, not necessarily the final betting engine.

### Evaluation

Primary:

- Log loss
- Brier score
- Calibration

Secondary:

- Accuracy
- Class recall
- Confusion matrices

### Pass criteria

The engineered features must beat very simple historical/base-rate benchmarks out of sample.

If they do not:

**fix the feature engine before increasing model complexity.**

---

# Model 1B — Tree-Based Challenger

Once Model 1 works:

- XGBoost
- LightGBM
- CatBoost

Purpose:

Test whether nonlinear interactions materially improve prediction.

Possible hyperparameters to explore:

- learning rate
- tree depth
- number of leaves
- minimum child samples
- L1/L2 regularization
- feature fraction
- bagging fraction
- number of estimators

Use chronological validation.

Do not accept complexity unless it improves calibrated out-of-sample performance.

---

# Model 2 — Component / Environment Models

This is the bridge to the simulator.

Rather than one model trying to learn all of MMA, estimate individual components.

Potential models:

## Environment

- P(fight remains standing-heavy)
- P(fight becomes wrestling-heavy)
- P(A controls preferred phase)
- P(B controls preferred phase)

## Wrestling

- P(A attempts TD)
- P(A TD succeeds | attempt)
- P(A establishes control | TD)
- P(B escapes control)

## Submission

- P(A creates submission attempt | ground)
- P(A converts submission | attempt)
- P(B survives submission attempt)

## Striking

- P(A produces high-volume striking environment)
- P(A creates KD | standing exposure)
- P(B suffers KD | standing exposure)
- P(finish occurs | KD/damage state)

## Persistence

- Expected pace by round
- Expected defensive fade
- Expected wrestling fade
- Expected late-fight finish risk

---

# Model 3 — Monte Carlo Fight Simulator

Initial simulator should be **round/state based**, not second-by-second.

Reason:

The available historical data is primarily round aggregates.

---

## 17.1 Suggested simulator states

```text
START ROUND
    ↓
DISTANCE STANDING
    ↓
possible transitions:
    ├─ continued distance striking
    ├─ pocket/clinch
    ├─ takedown attempt
    ├─ knockdown
    └─ finish

CLINCH
    ↓
possible transitions:
    ├─ break to distance
    ├─ clinch striking
    ├─ takedown attempt
    └─ finish

GROUND
    ↓
possible transitions:
    ├─ control
    ├─ ground strikes
    ├─ submission attempt
    ├─ reversal
    ├─ escape
    └─ finish
```

---

## 17.2 Persistent fight state

Each simulation should track:

- Round
- Time / exposure
- Cumulative damage
- Fatigue
- Control burden
- Knockdowns
- Ground exposure
- Possibly confidence/state momentum later

---

## 17.3 Simulator outputs

Run tens of thousands of simulations per matchup.

Minimum outputs:

### Winner
- Fighter A win
- Fighter B win

### Method
- A KO/TKO
- A Submission
- A Decision
- B KO/TKO
- B Submission
- B Decision

### Duration
- Fight reaches Round 2
- Fight reaches Round 3
- Fight reaches Round 4/5
- Over 1.5
- Under 1.5
- Over 2.5
- Under 2.5

### Finish round
- R1 finish
- R2 finish
- R3 finish
- R4 finish
- R5 finish

### Environment
- Standing-heavy %
- Wrestling-heavy %
- Ground-control-heavy %
- High-paced striking %
- Fighter A controls preferred environment %
- Fighter B controls preferred environment %

---

# 18. Model Agreement / Disagreement Layer

Because multiple models will exist, preserve all outputs.

Example:

```text
                Simple     Tree      Simulator
A wins           68%       72%        70%
A KO             24%       29%        31%
A SUB            13%       10%        11%
A DEC            31%       33%        28%
```

Useful derived signals:

- Model agreement
- Model dispersion
- Confidence band
- Method concentration
- Environment disagreement

Large disagreement should trigger research, not automatic betting.

---

# 19. Sportsbook Comparison Layer

Only after model predictions are frozen for the card.

Collect exact available prices for:

- Moneyline
- KO/TKO
- Submission
- Decision
- Double chance / method combinations
- Fight goes decision
- Fight doesn't go decision
- Round totals
- Over/Under 1.5
- Over/Under 2.5
- Round props where useful

---

## 19.1 De-vig

Convert opposing sportsbook prices into estimated market probabilities with vig removed.

The sportsbook comparison layer should identify:

- Model vs market probability difference
- Market disagreement about survivability
- Market disagreement about finish timing
- Market disagreement about method
- Method leakage

---

## 19.2 Diagnostic philosophy

Do not conclude:

> Model says KO, therefore bet KO.

Instead conclude:

> Model sees substantially more KO environment than the market appears to price.

Then investigate:

- opponent durability
- defensive wrestling
- striking exposure
- pace
- cardio
- recent form
- injuries
- weight cut
- camp changes
- matchup-specific tactical factors

---

# 20. Betting Output Layer

The existing UFC betting framework remains downstream of the models.

Preferred categories:

## High Hit Rate

Most dependable playable method/combination.

## Balance

Best compromise between probability and payout.

## Value

Genuine plus-money / +EV proposition.

## Sleeper

Only when materially mispriced.

Never force four bets.

---

# 21. Parlay Framework

When feasible:

- One high-confidence floor/lock leg
- Two strong balanced legs

The floor may be:

- Double chance
- Broad method combination
- Another high-probability market

It does not need to be a pure method-of-victory bet.

---

# 22. Fastest-Finish Module — Later

Build only after the base simulator is trustworthy.

Needed outputs:

- Finish probability within first 60 sec
- Finish probability within first 90 sec
- Finish probability within first 120 sec
- R1 finish distribution
- KO vs submission early hazard
- Explosive-finish score
- Cumulative-finish score

Important distinction:

**explosive finishers** and **pressure/cumulative finishers** must be modeled separately.

---

# 23. Validation Philosophy

The model passes based on its ability to predict fights, not historical betting ROI.

Primary validation:

- Chronological walk-forward testing
- Multiclass log loss
- Brier score
- Calibration curves
- Reliability by probability bucket

Additional slicing:

- Weight class
- Men's vs women's divisions
- 3-round vs 5-round
- Debutants
- Fighters with <3 UFC fights
- Fighters with 3–5 UFC fights
- Experienced fighters
- Method class
- Round

---

# 24. Do Not Optimize For

Do not optimize the core model for:

- Historical sportsbook ROI
- Closing-line value
- Winning percentage alone
- Betting units won
- Maximum backtested profit
- A hand-picked subset of cards

Those can be reported later, but they are not model-training objectives.

---

# 25. Uncertainty / Sample Quality

Every current fighter state should include sample-quality metadata.

Examples:

- UFC fights observed
- UFC rounds observed
- Total UFC minutes
- Standing minutes proxy
- Ground/control exposure
- TD attempts observed
- Submission attempts observed
- Recent activity

Low-sample fighters should receive:

- Greater uncertainty
- More shrinkage toward division/population averages
- Lower model confidence

Later, Bayesian/hierarchical methods may improve this.

---

# 26. Recommended Build Sequence

## Phase 0 — Project foundation

- Create repo
- Define canonical schema
- Establish raw-data directories
- Add immutable-source rules
- Add data manifest/versioning
- Define method labels

**Deliverable:** reproducible empty project structure.

---

## Phase 1 — Historical ingestion

- Import historical UFCStats-derived data
- Normalize fighter identities
- Normalize events
- Normalize fights
- Normalize round stats
- Validate record counts

**Deliverable:** canonical raw database.

---

## Phase 2 — Point-in-time replay engine

- Sort fights chronologically
- Snapshot fighter state before each bout
- Update state after each bout
- Add strict leakage tests

**Deliverable:** historical pre-fight fighter snapshots.

---

## Phase 3 — Core feature engine

Build first:

1. Striking opportunity
2. Striking creation
3. Striking prevention
4. Wrestling creation
5. Wrestling prevention
6. Submission creation
7. Submission prevention
8. Durability
9. Cardio/persistence
10. Context

**Deliverable:** versioned fighter-state feature table.

---

## Phase 4 — Opponent-adjusted features

- Strike creation over expectation
- Strike defense over expectation
- Wrestling creation over expectation
- Wrestling defense over expectation
- Submission creation/resistance adjustments

**Deliverable:** opponent-adjusted fighter ratings.

---

## Phase 5 — Matchup interaction engine

- KO environment interactions
- Submission environment interactions
- Decision environment
- Phase-control features
- Persistence interactions

**Deliverable:** one matchup feature row per historical fight.

---

## Phase 6 — Model 0 baselines

- Historical class baselines
- Division baselines
- Round baselines
- Finish baselines

**Deliverable:** baseline scorecard.

---

## Phase 7 — Model 1 simple baseline

- Logistic/multinomial models
- Walk-forward testing
- Calibration
- Feature diagnostics

**Deliverable:** first honest predictive benchmark.

### Gate

Do not proceed to sophisticated models until the feature engine shows genuine out-of-sample predictive value.

---

## Phase 8 — Tree-model challenger

- LightGBM/XGBoost/CatBoost
- Conservative tuning
- Compare with simple baseline
- Calibrate probabilities

**Deliverable:** nonlinear challenger.

---

## Phase 9 — Component/environment models

Train separate models for:

- Environment control
- Striking exposure
- KD creation
- TD attempts
- TD success
- Ground control
- Submission creation
- Submission survival
- Round persistence

**Deliverable:** simulator transition probabilities.

---

## Phase 10 — Simulator V1

- Round/state Monte Carlo
- Standing/clinch/wrestling/ground states
- Damage
- Fatigue
- Control
- Finish transitions

**Deliverable:** full simulated fight distribution.

---

## Phase 11 — Simulator validation

Compare simulated distributions to actual historical outcomes.

Check:

- Winner calibration
- Method calibration
- Finish calibration
- Round calibration
- Total-duration calibration
- Division-specific behavior

**Deliverable:** simulator scorecard.

---

## Phase 12 — Current-card pipeline

For a new card:

1. Update data
2. Build current fighter states
3. Build matchup features
4. Run all models
5. Run simulator
6. Freeze predictions
7. Output forecast file/report

**Deliverable:** card-level model forecast before sportsbook analysis.

---

## Phase 13 — Sportsbook diagnostic layer

- Enter current DraftKings prices
- Convert to implied probabilities
- De-vig
- Compare model vs market
- Surface largest disagreements
- Check alternate markets
- Check method leakage

**Deliverable:** research-priority report.

---

## Phase 14 — Human research layer

Research only after the mechanical forecast exists.

Focus research on model-market disagreements and model uncertainty:

- durability
- style matchup
- recent changes
- injuries
- camp changes
- weigh-ins
- short notice
- weight changes
- tactical tendencies
- sample quality

---

## Phase 15 — Betting card output

Produce:

- High Hit Rate
- Balance
- Value
- Sleeper only if deserved
- Optional floor + balanced-leg parlay

Include:

- Model probability
- Market de-vigged probability
- Price
- Break-even
- Research conclusion
- Confidence
- Stake

---

# 27. Future Extensions

Only after core simulator is trustworthy.

## Bayesian / hierarchical shrinkage

Useful for:

- Debutants
- Low UFC sample
- Division-specific priors
- Uncertainty bands

## Time-to-event / survival model

Useful for:

- Round totals
- Finish timing
- Fastest-finish promo

## Markov-chain refinement

Useful for:

- More realistic phase transitions
- Standing → clinch → wrestling → ground
- Round-by-round state persistence

## Market-aware challenger

Optional separate model that includes current market probabilities.

Must remain separate from the independent core model.

---

# 28. Project Success Definition

The project is successful if it creates a repeatable process where:

1. Raw fight data is trustworthy.
2. Historical features are leakage-safe.
3. Fighter states represent creation, prevention, survivability, and persistence.
4. Simple models demonstrate that those features predict real fights.
5. Component models estimate fight-environment mechanics.
6. The simulator produces calibrated winner/method/timing distributions.
7. Current sportsbook prices are compared only after the fight forecast is frozen.
8. Model-market disagreements tell us **where to research**.
9. Final wagers still require matchup-specific human validation.
10. The system helps us avoid researching every market blindly and then rationalizing a pick afterward.

---

# 29. Immediate Next Task

Before writing prediction models:

## Lock the canonical feature specification.

For every proposed feature, document:

- Name
- Exact mathematical definition
- Required raw fields
- Minimum sample requirement
- Career/recent/EWMA variants
- Round-specific variants
- Opponent-adjusted variant
- Missing-data behavior
- Leakage rule

Then compare that feature specification against the available historical data source.

Only after confirming that the raw data can support the feature engine should model implementation begin.
