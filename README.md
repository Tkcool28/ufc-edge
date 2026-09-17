# UFC Edge

UFC EDGE is a governed, chronological UFC modeling system that turns source evidence into deterministic canonical DATA, point-in-time features, shared historical predictor replay, and versioned winner models.

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
  ├── M0 permanent small baseline
  └── M1 corrected clean baseline
        ↓
future model families (only when separately authorized)
```

F02 is shared predictor infrastructure, **not a model**.

## Current snapshot

At authoritative `main` snapshot `7a7b50c2e1cdd20af8c7996e0c8460a35a693296`:

- recent physical-profile DATA gaps are complete through governed source recovery;
- F00/F01/F02 methodology is preserved;
- M0 remains the permanent frozen empirical baseline;
- original M1 is **historical and not authoritative for performance** because reach-availability missingness carried temporal leakage;
- corrected physical-profile M1 is the current clean baseline and is **ready for a formal freeze marker**;
- repository organization is the current work phase; next-model selection returns to MASTER/PM afterward.

The permanent governance lesson is simple: **a static attribute may be safely backfilled while its historical missingness/availability indicator is still unsafe. Missingness requires an independent point-in-time audit.**

## Repository map

- `PROJECT_STATUS.md` — current authority: DATA/features/models/findings/next action.
- `PROJECT_MAP.md` — where code, evidence, freezes and docs live.
- `data/` — raw, canonical, supplemental and derived DATA.
- `features/` — F00/F01/F02 semantic system and replay contracts.
- `models/` — M0/M1 model contracts and model-specific evidence.
- `governance/` — cross-cutting safety rules, especially missingness PIT safety.
- `provenance/` — source locks, DATA freeze records, audits and durable source evidence.
- `pipelines/` — deterministic acquisition/reconciliation/build logic.
- `tools/` — model/audit/operational runners.
- `tests/` — DATA/feature/model/regression checks.
- `.github/workflows/` — reproducible CI, acquisition, replay and controlled experiment workflows.
- `docs/` — durable milestones, decisions and zero-context chat bootstrap.

## Source/canonical boundary

Provider-specific vocabulary stops at the adapter/canonical boundary. A new source may add evidence or coverage; it must not silently redefine an existing canonical concept.

Live network acquisition is mutable. Canonical/model consumption must use governed pinned evidence and remain deterministic/offline where specified.

## Historical evidence

Do not delete important invalidated/superseded results. Original M1, old predictor artifacts, physical-profile gaps, corrected-data comparisons, survivorship probes, leakage diagnostics and freeze hashes are valuable audit history. Their **status** determines whether they are current authority.

## Before changing anything

1. read `PROJECT_STATUS.md`;
2. verify current `main` SHA;
3. inspect the task-specific contract/freeze/evidence;
4. do not assume an old draft PR or branch is authoritative;
5. preserve DATA/model methodology unless the task explicitly authorizes a migration.
