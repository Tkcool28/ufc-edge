# UFC EDGE — Project Map

Status: **AUTHORITATIVE NAVIGATION INDEX**

This file answers: **where do I find things?** Current authority lives in `PROJECT_STATUS.md`.

| Area | Purpose | Start here |
|---|---|---|
| `data/` | Raw, canonical, supplemental and derived data evidence/products | `data/README.md` |
| `features/` | F00 contract/governance, F01 PIT state, F02 historical replay | `features/README.md` |
| `models/` | Model-family contracts, frozen baselines and evaluation records | `models/README.md` |
| `governance/` | Cross-cutting safety rules and permanent validation terrain | `governance/README.md` |
| `pipelines/` | Deterministic data/reconciliation/build pipelines | task-specific pipeline plus linked workflow |
| `tools/` | Audit/model/diagnostic/operational runners | task-specific tool entry point |
| `tests/` | DATA, feature, replay, model and regression checks | repository-specific test tree |
| `provenance/` | Source locks, freezes, audits and durable evidence | `provenance/README.md` |
| `.github/workflows/` | CI, manual acquisition, model and diagnostic runners | `.github/workflows/README.md` |
| `schemas/` | Canonical and adapter contracts | relevant schema file |
| `handicap/` | Separate handicap-access surfaces retained from earlier work | inspect local README/contracts before use |
| `docs/model_diagnostics/` | Durable post-freeze model diagnostic evidence | `docs/model_diagnostics/README.md` |
| `docs/` | Durable project continuity: milestones, decisions, handoff policy, bootstrap | `docs/NEW_CHAT_BOOTSTRAP.md` |

## Authority convention

- **AUTHORITATIVE** — current accepted state or current navigation/governance entry point.
- **FROZEN** — accepted identity/methodology that must not be silently changed.
- **HISTORICAL** — valid evidence from an older state; retained for context/reproducibility.
- **SUPERSEDED** — replaced by newer authoritative work and not current instruction.
- **INVALIDATED** — known data/methodology defect means the result must not be used as a current estimate.
- **DIAGNOSTIC** — explanatory/post-freeze evidence; it does not redefine the frozen model unless separately authorized.

## Feature map

- **F00** — `features/FEATURE_CONTRACT.md`, `features/FEATURE_GOVERNANCE.md`.
- **F01** — `features/F01_MATERIALIZER.md`; point-in-time fighter state before a target fight.
- **F02** — deterministic historical replay over F01; shared predictor dataset, **not a model**.
- Missingness PIT rule — `features/MISSINGNESS_POINT_IN_TIME_SAFETY.md` and `governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md`.

## Model map

- `models/m0/` — permanent frozen small empirical winner baseline.
- `models/m1/` — corrected frozen regularized shared-feature winner baseline plus preserved historical original-M1 evidence.
- `models/mov0/` — frozen STANDARD_FINISH V1 contract/implementation. Current run classification: **CLEAR_SUCCESS**.
- Root `MOV0_STANDARD_FINISH_PROBABILITY_V1_REPORT.md` and completion JSON — accepted first frozen MOV0 run closeout.
- `models/mov0/diagnostics/` — probability-bucket and confidence/terrain/feature-behavior post-freeze diagnostics.
- `docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/` — durable merge-safe archetype/interaction diagnostic evidence.

## Validation / governance map

- `governance/model_validation_bucket_v1/` — immutable permanent Validation Terrain V1 assignments, percentile reference and calibration evidence.
- `governance/MODEL_VALIDATION_BUCKET_CONTRACT_V1.md` — terrain contract.
- `governance/MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE.json` — prerequisite rich-stat temporal-safety audit.
- `governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md` — permanent missingness availability rule.

## Historical root files

Legacy root handoffs/logs are intentionally retained in place because old automation/conversations may reference their stable paths. They are **not** current instruction. New work should use `PROJECT_STATUS.md` and `docs/NEW_CHAT_BOOTSTRAP.md`.

Do not relocate one merely for tidiness. A relocation requires a separate migration that first maps and updates every code/workflow/test/doc reference.

## Stale-work map

As of 2026-09-30, open PRs #34 and #60 are paused market diagnostics. Open PRs #61 and #62 are superseded original-M1 drafts and must not be treated as current M1 authority.

Merged historical branches remain numerous. Obvious temporary/stale branch names also exist. Branch pruning is intentionally separate from documentation cleanup and requires exact reachability/dependency review before deletion.

## Fresh-session route

1. `PROJECT_STATUS.md`
2. `PROJECT_MAP.md`
3. `docs/MASTER_MILESTONES.md`
4. `docs/DECISIONS.md`
5. `docs/MODELING_RESET_CHECKLIST.md`
6. verify current `main`
7. inspect task-specific contract/freeze/evidence
