# UFC EDGE — Modeling Reset Checklist

Status: **LIVING REFERENCE — NOT AN IMMUTABLE CONTRACT**

Purpose: provide a deliberate reset point whenever UFC EDGE model development becomes too abstract, too metric-driven, or disconnected from the actual project objective.

The objective is not to accumulate increasingly sophisticated models for their own sake.

The long-term objective is to make better, more defensible decisions about betting on UFC fights and method-of-victory markets using trustworthy pre-fight information, calibrated probabilities, and explicit uncertainty.

This document may change as the project learns. It should not silently override frozen DATA, feature, model, or validation contracts.

---

## A. Foundation / temporal-safety questions

Before trusting any new model result, ask:

1. **Is every model input available at the actual prediction cutoff?**
   - Are values point-in-time safe?
   - Is the *availability or missingness state itself* point-in-time safe?
   - Are we accidentally encoding future UFC career persistence, modern profile completeness, later rankings, later outcomes, or later source coverage?

2. **Did any source, backfill, reconciliation, or missing-data repair change the historical information set?**
   - Static values may be legitimate while historical present/missing status is not.
   - Missing must never silently become zero or “low.”

3. **Are era effects understood?**
   - Is a feature comparable across the historical period being modeled?
   - If not, is its limitation explicit rather than hidden in a pooled metric?

4. **Can the result be reproduced from pinned governed inputs?**
   - DATA identity
   - F00/F01/F02 identity
   - feature surface
   - model configuration
   - fold plan
   - seed/solver
   - runtime artifact identity

---

## B. Model-development discipline

5. **What exact question is this model trying to answer that the current frozen baseline does not answer well enough?**

6. **Is the proposed change a clean experiment?**
   - Ideally change one meaningful dimension at a time.
   - Avoid simultaneously changing DATA, features, model family, folds, hyperparameters, and evaluation logic.

7. **Are we improving a model, or merely increasing complexity?**
   - What new information or interaction can the challenger represent?
   - Is the complexity justified by out-of-sample evidence?

8. **Are we chasing one attractive subgroup or one bad cell?**
   - Named weak environments such as `GRAPPLE_TWO_SIDED` are diagnostic stress-tests.
   - They must not become isolated optimization targets that distort global selection.

9. **Are model-selection criteria still predeclared and market-blind?**
   - No odds, ROI, CLV, sportsbook residuals, or profitable-bucket mining should leak into winner/MOV model construction unless a later explicitly authorized market-model phase says otherwise.

---

## C. Calibration and permanent-terrain questions

10. **Does the model's stated confidence mean what it says historically?**
    - If the model says 60%, 70%, or 80%, does observed performance approximately follow?
    - Inspect reliability, ECE, calibration slope/intercept, and sample sizes.

11. **Does improvement survive the permanent validation terrain?**
    - Same historical terrain, different model.
    - Do not redefine Validation Terrain V1 because a challenger dislikes a bucket.

12. **Where does calibration degrade?**
    - experience
    - layoff
    - 3-round vs 5-round
    - title status
    - weight class
    - completeness
    - striking pressure
    - grappling pressure
    - joint MOV environment

13. **Are thin cells being treated honestly?**
    - N >= 100: normal
    - 50–99: moderate uncertainty
    - 25–49: thin/exploratory
    - <25: insufficient; N-only, no substantive performance interpretation

14. **Are frozen percentile/bucket references actually frozen?**
    - Validation Terrain V1 scoring must use its pinned percentile-reference artifact.
    - Incoming or future populations must not silently redefine V1 percentiles.

---

## D. Pre-freeze review questions

These are the questions preserved from the Validation Terrain V1 review and should be answered before a major model foundation is declared frozen:

1. Is the validation-bucket construction insulated from model predictions and outcomes?
2. Is percentile normalization appropriate for combining the selected rich-stat components?
3. Are elevated-pressure thresholds preregistered and performance-independent?
4. Is the MOV feature subset appropriately minimal and interpretable?
5. Is fighter-order invariance complete?
6. Is `UNASSIGNABLE_BY_CONTRACT` handled correctly and never conflated with low pressure?
7. Are sample-size gates appropriately conservative?
8. Do historical MOV outcome gradients support that the environments capture meaningful fight context without having been outcome-optimized?
9. Are there remaining temporal-leakage or era-comparability risks not covered by prior audits?
10. Is the current model's calibration record sufficient to serve as a baseline for future comparison?
11. What explicit cautions belong in the freeze record regarding weak environments, missing-data populations, or thin confidence cells?
12. Is there any reason the validation terrain or model should **not** be frozen before the next challenger begins?

---

## E. Reset to the actual goal: betting on fights

When the project starts to feel like an endless modeling exercise, ask these questions before adding another feature family or model:

1. **What decision will this eventually improve?**
   - winner probability?
   - KO/TKO probability?
   - submission probability?
   - decision probability?
   - confidence/abstention?
   - identifying when the model should not be trusted?

2. **Is the output a calibrated probability we could eventually compare to a market price?**
   A ranking or accuracy score alone is not enough for betting.

3. **Does the model tell us something useful about fight context, not just who wins?**
   For MOV betting, the system eventually needs to distinguish environments where the *way the fight is likely to end* changes meaningfully.

4. **Do we know where the model is weak?**
   A useful betting system should know when to reduce confidence or abstain, not only produce a pick for every fight.

5. **Are we separating predictive modeling from market evaluation?**
   First build and validate probabilities without market contamination. Later compare frozen predictions to real prices.

6. **Are we measuring value only after the predictive model is frozen?**
   Do not let historical sportsbook profitability determine feature engineering or model selection.

7. **Would this model still be considered an improvement if no betting odds existed?**
   If not, we may be fitting the market rather than improving the underlying fight model.

8. **When market integration begins, are we comparing like with like?**
   - winner model vs moneyline implied probability
   - KO probability vs KO price
   - submission probability vs submission price
   - decision probability vs decision price

9. **Are vig, liquidity, timing, limits, line movement, and stale prices treated separately from model probability?**

10. **What is the simplest real betting hypothesis supported by the model evidence?**
    Avoid building complicated betting rules before a simple hypothesis survives honest out-of-sample testing.

11. **Are we creating actionable confidence, or just more numbers?**

12. **If all current models disappeared, what evidence would we need to feel comfortable putting real money on a fight?**
    Use that answer to guide the next modeling priority.

---

## F. Current frozen-baseline reminders

As of the corrected M1 freeze:

- M0 remains the permanent small empirical baseline.
- Original M1 is historical and contaminated by reach-availability leakage.
- Corrected M1 V1 is the authoritative frozen broad winner baseline.
- Corrected M1 prediction artifact/content SHA256: `5eaa09e82787cae0e3a198d31b0c19573557c94f0faf9302a582023c44a39b78`.
- Corrected M1 OOF logical SHA256: `7e6a08a6a4013630239986360654ad0963a1f242dae9acd7b172ee5a321384e6`.
- Validation Terrain V1 is permanent for model comparison unless deliberately versioned to V2.
- `GRAPPLE_TWO_SIDED` is a named corrected-M1 stress-test, **not** a cell to optimize in isolation.
- High-missingness fights remain a harder population.
- Thin cells do not become meaningful simply because a new model is interesting there.

---

## G. When to use this document

Use this checklist:

- before authorizing a new major model family;
- before adding a large feature family;
- before changing validation methodology;
- before declaring a model frozen;
- before beginning market/ROI work;
- whenever several model iterations produce movement without a clear project-level gain;
- whenever the team cannot clearly explain how the current work eventually helps make a better betting decision.

If the answer to the last point is unclear, stop model proliferation and return to the project objective before proceeding.

---

## H. Review cadence

This file is intentionally revisable.

Revisit it when:

- a major model milestone is frozen;
- a new data source materially changes what can be modeled;
- the project transitions from predictive modeling into market evaluation;
- repeated experiments suggest the checklist itself no longer reflects the real decision problem.

Changes to this checklist do **not** rewrite frozen historical model or validation records.
