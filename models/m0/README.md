# M0 — Empirical UFC Winner Baseline V1

Status: **AUTHORITATIVE PERMANENT FROZEN SMALL BASELINE**

M0 is the deliberately simple empirical winner-probability truth test on the governed F02 historical predictor replay. It remains the permanent comparison/reference baseline even though corrected M1 is stronger and broader.

## Boundary

- UFC target fights only; binary winner-eligible rows only.
- Primary modeling era starts 2010-01-01.
- F02 is consumed as frozen; M0 does not rebuild/redefine historical features.
- No sportsbook data, ROI, random split, tree/boosting, feature hunting, or production deployment.
- Runtime fold models and OOF predictions stay outside git.

## Model progression

1. **M0-A**: constant 0.50.
2. **M0-B**: one-concept empirical experience baseline with Laplace smoothing.
3. **M0-C**: deterministic L2 logistic model on a compact career-state subset.

M0-C uses five governed concepts: prior fight count, age at fight, layoff days, career significant-strike accuracy/defense, and career takedown success/defense. Pair projections, pooled-median imputation, scale-only standardization and no-intercept construction preserve fighter-orientation antisymmetry.

## Validation

Expanding annual walk-forward: initial train 2010–2014, validate 2015, expand annually through 2026.

## Freeze and reproduction

The authoritative committed records are:

- `M0_EMPIRICAL_WINNER_BASELINE_V1_COMPLETE.json`
- `VALIDATION_REPORT_V1.md`

Verdict: **M0_SIGNAL_CONFIRMED**.

Runtime validation consumes the frozen F02 Actions artifact via `tools/models/run_m0.py`; runtime OOF/fold models remain outside git.

Do not modify M0 simply because later models exist. Any M0 methodology change would require a separately authorized baseline migration.
