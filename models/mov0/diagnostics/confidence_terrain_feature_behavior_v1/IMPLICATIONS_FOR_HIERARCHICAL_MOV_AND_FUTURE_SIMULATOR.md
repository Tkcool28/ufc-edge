# IMPLICATIONS_FOR_HIERARCHICAL_MOV_AND_FUTURE_SIMULATOR

Status: **ARCHITECTURE NOTES ONLY — NO IMPLEMENTATION AUTHORIZED**

## Hierarchical MOV

The diagnostic supports preserving the intended hierarchy:

`P(STANDARD_FINISH)`

then:

`P(KO_TKO | STANDARD_FINISH)`

then compose:

- `P(DECISION)`
- `P(KO_TKO)`
- `P(SUBMISSION)`

Why this remains sensible:

- Direct finish-history variables show stable relationships with the first-stage STANDARD_FINISH target.
- Striking and grappling state variables appear to contribute through different pathways.
- Some FULL-only additions alter confidence without improving first-stage aggregate performance, suggesting that richer state may be more useful conditionally than when all mechanisms are forced into one global first-stage model.
- STRIKE_TWO_SIDED and GRAPPLE_TWO_SIDED terrain behave differently enough to justify preserving pathway identity for future conditional modeling.

This diagnostic does not authorize MOV1.

## Candidate state variables for later simulator research

Predictive variables with comparatively stable behavior include:

- prior first-round finish wins/losses;
- KO/TKO creation/vulnerability history;
- submission attempts created/faced;
- knockdown production and knockdown-creation efficiency;
- significant strikes absorbed;
- significant-strike defense;
- ground significant-strike share;
- scheduled rounds / available fight duration.

These are candidate state descriptors, not causal transition parameters.

## Survival / round exposure

Scheduled rounds is a stable finish-increasing predictor, and 5-round fights are much more likely to occupy high finish-confidence bins than 3-round fights.

That is consistent with a future simulator explicitly representing:

pre-fight state
→ round exposure
→ competing finish hazards
→ survival to later rounds
→ decision conditional on survival.

MOV0 itself does not estimate round-level hazards, and its scheduled-round coefficient must not be copied into a simulator transition probability.

## Environments potentially poorly represented by one global model

The diagnostic identifies several environments where one global coefficient surface may be inadequate:

- Heavyweight: richer FULL state raises confidence but worsens probability quality versus MIN.
- Light Heavyweight: high structural finish prevalence, weak within-division discrimination.
- Flyweight: weak overall separation and almost no confident tail.
- Long layoffs: frozen terrain weakness suggests fighter-state staleness may matter.
- Specific strike/grapple environments: local calibration and confidence ordering differ from the global pattern.

These are hypotheses for later preregistered architecture tests, not evidence to branch the simulator now.

## Calibration implication

Global probability buckets are monotonic, but local terrain families can show reversals and overconfidence.

A future simulator or hierarchical MOV system should therefore be evaluated not only on aggregate probability quality but also on permanent terrain calibration, especially where transition/hazard assumptions differ structurally.

## Causality warning

Recovered logistic coefficients are predictive associations after regularization and correlated feature adjustment.

They do not establish:

- causal finish mechanisms;
- causal round-transition probabilities;
- independent hazard effects;
- fighter-specific latent traits;
- optimal simulator parameters.

Any future simulator must estimate and validate its own state-transition/hazard structure prospectively and chronologically.

## Current architecture takeaway

MOV0 established that a global first-stage STANDARD_FINISH probability contains reproducible signal.

This diagnostic adds that the signal has interpretable state structure, but its calibration and discrimination vary by environment.

That supports a future hierarchical/hybrid architecture in principle while arguing against directly turning MOV0 coefficients into simulator mechanics.
