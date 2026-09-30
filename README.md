# UFC Edge

UFC EDGE is a governed, chronological UFC modeling system that turns source evidence into deterministic canonical DATA, point-in-time features, shared historical predictor replay, and versioned probability models.

**Start here:** [`PROJECT_STATUS.md`](PROJECT_STATUS.md) is the single authoritative current-state document. Use [`PROJECT_MAP.md`](PROJECT_MAP.md) to find implementation/evidence. Fresh ChatGPT sessions should then read [`docs/NEW_CHAT_BOOTSTRAP.md`](docs/NEW_CHAT_BOOTSTRAP.md).

## Architecture

```text
RAW / SOURCE DATA
        ↓
CANONICAL DATA
        ↓
F00 FEATURE CONTRACT / GOVERNANCE
        ↓
F01 POINT-IN-TIME FIGHTER STATE
        ↓
F02 HISTORICAL PREDICTOR REPLAY
        ↓
MODELS
  ├── M0 permanent small winner baseline
  ├── M1 corrected frozen winner baseline
  └── MOV0 frozen STANDARD_FINISH probability model
        ↓
future model families (only when separately authorized)
```

F02 is shared predictor infrastructure, **not a model**.

## Current snapshot

At authoritative `main` snapshot `0618a21e21002be9999d34f6997be659ca8ff224` (2026-09-30):

- recent physical-profile DATA gaps are complete through governed source recovery;
- F00/F01/F02 methodology remains frozen;
- M0 remains the permanent frozen empirical winner baseline;
- original M1 is **historical and not authoritative for performance** because reach-availability missingness carried temporal leakage;
- corrected physical-profile M1 is the **authoritative frozen M1 V1 baseline**;
- Validation Terrain V1 is permanent and model-independent;
- MOV0 STANDARD_FINISH V1 is merged and classified **CLEAR_SUCCESS**;
- MOV0 probability-bucket, confidence/terrain/feature-behavior, and conditional interaction/archetype diagnostics are merged as post-freeze descriptive evidence;
- the current task is repository continuity/documentation refresh before selecting or authorizing another model type.

The permanent governance lesson remains: **a static attribute may be safely backfilled while its historical missingness/availability indicator is still unsafe. Missingness requires an independent point-in-time audit.**

## Repository map

- `PROJECT_STATUS.md` — current authority: DATA/features/models/findings/next action.
- `PROJECT_MAP.md` — where code, evidence, freezes and docs live.
- `data/` — raw, canonical, supplemental and derived DATA.
- `features/` — F00/F01/F02 semantic system and replay contracts.
- `models/` — M0/M1/MOV0 contracts and model-specific evidence.
- `governance/` — cross-cutting safety rules and permanent Validation Terrain V1.
- `provenance/` — source locks, DATA freeze records, audits and durable source evidence.
- `pipelines/` — deterministic acquisition/reconciliation/build logic.
- `tools/` — model, diagnostic, audit and operational runners.
- `tests/` — DATA/feature/model/regression checks.
- `.github/workflows/` — reproducible CI, acquisition, replay, model and diagnostic workflows.
- `docs/model_diagnostics/` — durable post-freeze diagnostic evidence/index.
- `docs/` — milestones, decisions, handoff policy and zero-context chat bootstrap.

## Historical evidence

Do not delete important invalidated/superseded results. Original M1, old predictor artifacts, corrected-data comparisons, leakage diagnostics, freeze hashes and post-freeze diagnostics are valuable audit history. Their **status** determines whether they are current authority.

Legacy root handoffs remain in place because old automation/chats may reference those paths. They are historical, not current instructions.

## Before changing anything

1. read `PROJECT_STATUS.md`;
2. verify current `main` SHA;
3. inspect the task-specific contract/freeze/evidence;
4. do not assume an old draft PR or branch is authoritative;
5. preserve DATA/model methodology unless the task explicitly authorizes a migration;
6. do not move path-coupled files until every workflow/script/test/reference has been mapped and updated in one reviewed migration.
