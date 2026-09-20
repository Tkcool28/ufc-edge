# FUTURE_SPECIALIZATION_HYPOTHESES

Status: **HYPOTHESES_ONLY — NOT AUTHORIZED FOR IMPLEMENTATION**

These candidates are retained because multiple forms of evidence point to possible environment-dependent behavior. They are not ranked and are not recommendations to deploy specialized models.

## Heavyweight

Evidence:

- NORMAL overall sample size: N=311.
- Frozen terrain had already identified Heavyweight as an unfavorable FULL-vs-B1 cell.
- FULL raises probabilities in 225/311 Heavyweight fights.
- Mean FULL-minus-MIN shift is about +2.0 percentage points.
- FULL worsens log loss and AUC relative to MIN.
- The broader strike-flow/efficiency surface changes confidence systematically without improving aggregate probability quality.

Uncertainty:

- Bucket-level Heavyweight cells are often moderate or thin.
- Correlated predictors can make individual logistic coefficients difficult to interpret mechanistically.

Future preregistered question:

> Do division-conditioned effects or hierarchical partial pooling improve finish-probability calibration/discrimination for Heavyweight without sacrificing global generalization?

## Light Heavyweight

Evidence:

- NORMAL overall sample size: N=319.
- Observed finish prevalence is high at 64.3%.
- B1 was better on frozen terrain log loss than MIN/FULL.
- MIN/FULL within-division AUC remains weak, about 0.545–0.553.
- High structural finish prevalence coexists with weak fighter-level ranking.

Uncertainty:

- A structural division baseline can appear strong even if no specialized fighter-state model can materially improve within-division ranking.

Future preregistered question:

> Should structural division finish prevalence and fighter-specific finish state be modeled with a hierarchical/interacted structure rather than one global coefficient surface?

## Flyweight

Evidence:

- NORMAL overall sample size: N=248.
- MIN/FULL log loss is approximately 0.696.
- AUC remains weak at roughly 0.549–0.560.
- Very few Flyweight fights reach the highest-confidence bin.
- Predictions are concentrated around the middle.

Uncertainty:

- High-confidence cells are too sparse for strong tail conclusions.
- Weak discrimination could represent genuinely weak available signal rather than a misspecified global model.

Future preregistered question:

> Is Flyweight weak separation caused by global coefficient averaging, or is the available pre-fight state simply insufficient for materially better STANDARD_FINISH discrimination?

## Long layoff: 18+ months

Evidence:

- Frozen Validation Terrain cell is NORMAL size (N=293).
- FULL log loss was approximately 0.7090 versus B1 approximately 0.7033.
- The frozen terrain record identifies this environment as unfavorable.
- Long layoffs plausibly alter how stale fighter-state summaries should be interpreted.

Uncertainty:

- This diagnostic cannot establish that decay/staleness treatment would improve prediction.
- Layoff effects may interact with experience and missingness.

Future preregistered question:

> Does strict-prior fighter-state information require explicit time-since-observation handling or interaction with layoff state?

## Finish-path environment

Evidence:

- STRIKE_TWO_SIDED and GRAPPLE_TWO_SIDED environments contain useful finish signal.
- They react differently to MIN/FULL feature expansion.
- Stable coefficients exist for both damage and submission-pressure variables.
- The long-term architecture already intends to decompose STANDARD_FINISH into KO/TKO versus submission.

Uncertainty:

- The current target collapses KO/TKO and submission, so pathway-specific interpretation is limited.

Future preregistered question:

> Conditional on STANDARD_FINISH, do striking- and grappling-oriented state variables support a stable KO/TKO-vs-submission model without contaminating the first-stage finish probability?

## Governance

No candidate above is authorized for implementation.

Any specialization must be separately preregistered with frozen target, feature, fold, preprocessing, evaluation, uncertainty, and comparison rules before training.
