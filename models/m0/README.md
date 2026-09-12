# M0 — Empirical UFC Winner Baseline V1

M0 is the first deliberately simple winner-probability truth test on the frozen F02 historical predictor replay.

## Boundaries

- UFC target fights only.
- Binary winner-eligible rows only.
- Primary modeling era starts 2010-01-01.
- F02 is consumed as frozen; M0 does not rebuild or redefine historical features.
- No sportsbook data, ROI, random split, tree/boosting, feature hunting, or production deployment.
- Runtime fold models and OOF predictions stay outside git.

## Predeclared progression

1. **M0-A**: constant 0.50.
2. **M0-B**: one-concept empirical experience baseline. The training fold estimates, with Laplace smoothing, how often the fighter with more prior canonical fights wins. Equal experience returns 0.50.
3. **M0-C**: deterministic L2 logistic regression on a compact career-state subset.

M0-C uses five governed feature concepts: prior fight count, age at fight, layoff days, career significant-strike accuracy/defense, and career takedown success/defense. Each paired fighter concept is projected to an antisymmetric f1-minus-f2 value after training-fold-only pooled-median imputation, plus an antisymmetric missingness difference. Training-fold standardization is scale-only (no mean centering), which preserves that antisymmetry. This keeps the linear model invariant to the arbitrary canonical fighter presentation. The model has no intercept.

Shared fight context (weight class, scheduled rounds, title) is retained for predefined slices but intentionally not used as an orientation-direction predictor in M0-C.

## Validation

Expanding annual walk-forward:

- initial train: 2010–2014;
- validate: 2015;
- expand one year at a time;
- final fold: 2026.

The 2010 era start was chosen from F02 population/coverage inspection before any M0 outcome metrics were computed.

## Reproduce

Full validation consumes the frozen F02 Actions artifact and writes runtime output only:

`python tools/models/run_m0.py validate --f02-dir <f02-artifact-dir> --output-dir <runtime-dir>`

Routine CI validates contracts and focused deterministic fixtures rather than rerunning the entire historical validation.
