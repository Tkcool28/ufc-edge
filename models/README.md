# UFC EDGE — Model Index

Status: **AUTHORITATIVE MODEL NAVIGATION**

Models consume the governed F02 historical predictor replay. F02 is shared predictor infrastructure, **not** a model.

## M0 — winner baseline

Path: `models/m0/`

Status: **PERMANENT FROZEN SMALL EMPIRICAL BASELINE**.

Use as the compact winner-probability reference model. Start with `models/m0/README.md`.

## M1 — winner model

Path: `models/m1/`

Status: **AUTHORITATIVE FROZEN CORRECTED M1 V1 BASELINE**.

Do not confuse:

1. **Original M1** — historical performance is invalidated as current evidence by reach-availability temporal leakage.
2. **Corrected physical-profile M1** — authoritative frozen clean winner baseline, pinned by `M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_CORRECTED_FROZEN.json`.

Start with `models/m1/README.md` and `PROJECT_STATUS.md`.

## MOV0 — STANDARD_FINISH probability

Path: `models/mov0/`

Status: **FROZEN FIRST RUN COMPLETE — CLEAR_SUCCESS**.

Target: `P(STANDARD_FINISH)` where KO/TKO or submission = 1 and governed decision outcomes = 0.

- Contract: PR #72.
- First frozen implementation/run: PR #73.
- Closeout: root `MOV0_STANDARD_FINISH_PROBABILITY_V1_REPORT.md` and completion JSON.
- Probability-bucket and confidence/terrain/feature-behavior diagnostics: `models/mov0/diagnostics/`.
- Conditional interaction/archetype evidence: `docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/`.

MOV0-MIN is the surface that clearly established incremental signal beyond B1. MOV0-FULL remained better than B1 overall but did not establish meaningful incremental value beyond MIN.

## Not automatically authorized

- M1B
- MOV1
- tree/boosted challengers
- opponent-adjusted models
- feature-selection/pruning experiments
- post-hoc recalibration
- simulator models
- sportsbook/ROI/EV model selection

Any future challenger requires a separately defined question, frozen evaluation plan and explicit authorization. It must not silently rewrite M0/M1/MOV0 history.
