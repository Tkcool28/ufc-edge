# UFC EDGE — Model Diagnostic Evidence Index

Status: **AUTHORITATIVE DIAGNOSTIC NAVIGATION**

This directory is for durable explanatory evidence produced **after** a model is frozen when that evidence should survive Actions artifact retention and remain easy for future work to locate.

Diagnostics do not silently redefine frozen model methodology.

## MOV0

### Conditional feature interaction + fight archetype diagnostic V1

Path:

`docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/`

Merged in PR #113 at main merge `0618a21e21002be9999d34f6997be659ca8ff224`.

Key files:

- `MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_REPORT.md`
- `MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_COMPLETE.json`
- `EVIDENCE_MANIFEST.json`
- `archetype_results.json`
- `bucket_to_archetype_mapping.json`
- `feature_state_thresholds.json`

The diagnostic reads/verifies the authoritative frozen MOV0 OOF evidence, uses fixed predictor-only state thresholds, applies preregistered symmetric archetypes, and joins immutable Validation Terrain V1.

## Related MOV0 diagnostics

Other committed post-freeze MOV0 diagnostics currently live under `models/mov0/diagnostics/` because those paths were established by their original merged PRs:

- probability bucket calibration V1 — PR #111;
- confidence terrain + feature behavior V1 — PR #112.

They are intentionally **not moved** by this continuity pass. A future consolidation would require a reference-complete migration plan first.

## Rule for future diagnostics

Prefer one clearly indexed directory per diagnostic milestone. If an existing script/workflow/test already depends on a path, preserve it unless relocation is explicitly reviewed with all references updated atomically.
