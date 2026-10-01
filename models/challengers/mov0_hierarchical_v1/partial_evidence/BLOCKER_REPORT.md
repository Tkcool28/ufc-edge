# MOV0 hierarchical / partial-pooling challenger V1 — BLOCKED

Status: **BLOCKED_CONVERGENCE**. This is not a completed challenger evaluation.

Starting main: `378ba0576426cd01bd73cbaff774b782c8fb2f6b`.
Branch: `feat/mov0-hierarchical-partial-pooling-v1`.
Draft PR: #115. Do not merge.
Specification freeze commit: `bc5f9df5436402915915aa34da304bbfa46cbccb`, before challenger fitting or performance interpretation.

## Exact implementation

PyMC 5.18.2 Bayesian Bernoulli logistic likelihood with four NUTS chains, 1,000 tuning + 1,000 posterior draws per chain, target_accept=.95, max tree depth=12, noncentered zero-mean group deviations, proper Normal global priors and learned HalfNormal scales. Full dependency lock is committed.

H1 replaces MIN's weight one-hot coefficients with global intercept + partially pooled categorical division deviations; all numeric/title slopes are global. H2 adds exactly seven existing transformed MIN slopes across striking, submission, takedown entry, and experience families. See exact literal maps in the specification directory. Training-only frozen MIN preprocessing is reused unchanged. No FULL-only predictors are trained. Interim/tournament wrappers normalize to their explicit governed division; Catch Weight is separate.

## Execution and convergence

Seven fits passed: H1/H2 for 2018, 2019, and 2020, plus H1 for 2021. H2 for 2021 failed. The remaining ten planned fits were not attempted. No full H1/H2 OOF files were produced.

The failure is in the shared weight-class intercept scale `tau_intercept`:

| Check | H2 / 2021 | Frozen requirement | Status |
|---|---:|---:|---|
| Minimum bulk ESS | 397.521795 | >=400 | FAIL |
| Minimum tail ESS | 351.557475 | >=400 | FAIL |
| Maximum rank R-hat | 1.004427 | <=1.01 | PASS |
| Divergences | 0 | 0 | PASS |
| Minimum chain BFMI | 0.761102 | >=0.3 | PASS |
| Maximum-tree-depth hits | 0 | 0 | PASS |

The contract requires all checks to pass and preregisters **no retry**. Gates were not relaxed, draws were not increased, priors were not tuned, and no alternative family was substituted.

First-fold H1 repeated under identical environment and seed produced identical posterior arrays and predictions. Passed folds also satisfied fighter-order invariance within 1e-12. This establishes local reproducibility for the tested repeat; cross-platform bitwise identity is not asserted. Implementation/regression checks passed locally and the first GitHub CI run passed.

The initial local compilation attempt failed before sampling because the runtime's Python shared-library symlink was broken. A task-local link to the existing library repaired compilation; specification and inference settings were unchanged. Exact executed code hashes and software are recorded in execution_identity.json.

## Scientific interpretation withheld

The incomplete ladder does not support the requested aggregate log-loss comparison, nine-year persistence, fight/event paired bootstrap, permanent terrain comparison, broad-band calibration, or PR #113 archetype preservation analysis. None was interpreted from a selectively completed subset.

Heavyweight, Light Heavyweight, and Flyweight performance findings: **not evaluated**. Credible varying effects and empirical shrinkage findings: **not established**. Partial posterior summaries are retained as inference-audit evidence only, not accepted scientific results. They must not be used to claim a slope is stable, a class improves, or a small group shrinks appropriately across the completed experiment.

HELPED/HURT/UNCHANGED tradeoffs: **not evaluated**. The immutable panels and evaluation runner are implemented, but the runner refuses to evaluate without 18 passed fits and the reproducibility gate.

No model-selection classification is assigned. In particular, convergence failure is not evidence for CURRENT_SPECIFICATION_NOT_SUPPORTED on probability quality, and no claim is made that hierarchical modeling has failed. The required COMPLETE marker has intentionally not been emitted.

## Implications and limits

MOV1 architecture remains undecided. This partial execution supplies no defensible choice between global coefficients, hierarchical intercepts, or selected hierarchical slopes. MOV1 was not started.

Environment-conditioned finish hazards and survival effects remain hypotheses. The incomplete execution does not establish simulator relevance; logistic coefficients must not be copied into hazard transitions. No causal claim or simulator implementation is present.

Any future inference attempt requires an explicitly versioned, pre-result inference contract; this execution does not silently authorize a longer run or post-result changes. No final challenger performance was read, so the scientific feature/prior choices remain protected from performance-driven selection.

## Preserved evidence

Partial fold predictions for the seven accepted fits, eight fit diagnostic records, all four preprocessing records, accepted and failed posterior summaries, original BLOCKED marker, executed-source identity, repeat proof, and trace hashes are persisted. Raw posterior draws are a separate supplemental archive. Frozen MOV0/M1/F02/Validation Terrain and archetype/band artifacts remain unchanged.

This report stops at the preregistered inference blocker.
