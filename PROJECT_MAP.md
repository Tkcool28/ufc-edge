# UFC EDGE — Project Map

Status: **AUTHORITATIVE NAVIGATION INDEX**

This file answers: **where do I find things?** Current authority lives in `PROJECT_STATUS.md`.

| Area | Purpose | Start here |
|---|---|---|
| `data/` | Raw, canonical, supplemental and derived data evidence/products | `data/README.md` |
| `features/` | F00 contract/governance, F01 PIT state, F02 historical replay | `features/README.md` |
| `models/` | Model-family contracts, baselines and evaluation records | `models/README.md` |
| `governance/` | Cross-cutting safety/governance rules | `governance/README.md` |
| `pipelines/` | Deterministic data/reconciliation/build pipelines | inspect task-specific pipeline plus linked workflow |
| `tools/` | Audit/model/operational runners | task-specific tool entry point |
| `tests/` | DATA, feature, replay, model and regression checks | repository-specific test tree |
| `provenance/` | Source locks, freezes, audits and durable evidence | `provenance/README.md` |
| `.github/workflows/` | CI, manual acquisition and controlled experiment runners | `.github/workflows/README.md` |
| `schemas/` | Canonical and adapter contracts | relevant schema file |
| `handicap/` | Separate handicap-access surfaces retained from earlier work | inspect local README/contracts before use |
| `docs/` | Durable project continuity: milestones, decisions, chat bootstrap | `docs/NEW_CHAT_BOOTSTRAP.md` |

## Authority convention

Repository documentation uses these meanings:

- **AUTHORITATIVE** — current accepted state or current navigation/governance entry point.
- **HISTORICAL** — valid evidence from an older state; retained for context/reproducibility.
- **SUPERSEDED** — replaced by newer authoritative work and not current instruction.
- **INVALIDATED** — known data/methodology defect means the result must not be used as a current estimate.

A historical result may still be valuable evidence. Status is about authority, not whether the file should be deleted.

## DATA map

- `data/raw/` — immutable/source-faithful evidence.
- `data/canonical/` — governed source-neutral canonical package.
- `data/supplemental/` — governed recovery/enrichment inputs, including recent physical-profile completion.
- `provenance/` — locks, sourcing rules, audits and source-selection evidence.
- `pipelines/` — acquisition/reconciliation/build logic.

Important: mutable network acquisition is separated from deterministic canonical consumption.

## Feature map

- **F00** — `features/FEATURE_CONTRACT.md`, `features/FEATURE_GOVERNANCE.md`.
- **F01** — `features/F01_MATERIALIZER.md`; point-in-time fighter state before a target fight.
- **F02** — deterministic historical replay over F01; shared predictor dataset, **not a model**. Search `F02`, `f02`, and `historical predictor replay` in `features/`, `tools/`, `src/`, tests and workflows.
- Missingness PIT rule — `features/MISSINGNESS_POINT_IN_TIME_SAFETY.md` and `governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md`.

## Model map

- `models/m0/` — permanent small empirical baseline. Start at `models/m0/README.md`.
- `models/m1/` — regularized shared-feature winner model methodology. Start at `models/m1/README.md`.
- Original M1 performance: historical and temporally contaminated by reach-availability missingness.
- Corrected M1: current clean baseline candidate, ready for formal freeze marker.

## Evidence map

- Data freeze/source evidence: `provenance/`.
- M0 committed freeze/validation records: `models/m0/`.
- Original M1 methodology/config: `models/m1/`; large validation outputs are Actions artifacts.
- Corrected M1 controlled rerun: PR #65 / `physical-profile-corrected-m1-rerun-v1` workflow artifacts.
- Physical-profile diagnostic: PR #66.
- Missingness leakage audit/governance: PR #67, `governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md` and audit workflow artifacts.

## Handoffs and historical root files

Legacy root handoffs/logs are intentionally retained in place in this cleanup because older automation/conversations may reference their stable paths. They are **not** current instruction. New work should use `PROJECT_STATUS.md` and `docs/NEW_CHAT_BOOTSTRAP.md` instead.

## Fresh-session route

1. `PROJECT_STATUS.md`
2. `PROJECT_MAP.md`
3. `docs/MASTER_MILESTONES.md`
4. `docs/DECISIONS.md`
5. verify current `main`
6. only then inspect task-specific code/artifacts/PRs
