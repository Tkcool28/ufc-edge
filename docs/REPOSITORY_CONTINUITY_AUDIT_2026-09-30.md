# UFC EDGE — Repository Continuity Audit — 2026-09-30

Status: **CLEANUP / CONTINUITY REVIEW ARTIFACT**

Audit baseline: `main@0618a21e21002be9999d34f6997be659ca8ff224`

Purpose: make the repository easy for a future fresh session to understand before another model type is selected, without risky path churn or accidental methodology changes.

## Overall finding

The repository is structurally sound. Core domains are already separated into `data/`, `features/`, `models/`, `governance/`, `pipelines/`, `provenance/`, `src/`, `tests/`, `tools/` and workflows.

The main continuity problem was **documentation drift**, not a broken directory architecture.

Several authoritative indexes stopped at the 2026-09-17 corrected-M1 phase even though the repository had since merged:

- corrected M1 formal freeze (#71);
- MOV0 implementation contract (#72);
- MOV0 first frozen run (#73);
- MOV0 probability-bucket diagnostic (#111);
- MOV0 confidence/terrain/feature-behavior diagnostic (#112);
- MOV0 conditional interaction/archetype diagnostic (#113).

This branch refreshes navigation/status documentation to match current main.

## Path-move decision

**No existing file or directory is moved in this pass.**

Reason: the repository contains many historical workflows, scripts, tests, PR descriptions and chat handoffs that may reference stable paths. Tidiness alone is not enough reason to risk breaking reproducibility.

If a future move is desirable:

1. identify the exact source path and proposed destination;
2. search code, workflows, tests, docs and generated-reference checks for every source-path consumer;
3. determine whether artifact hashes/manifests or external instructions pin the path;
4. update all consumers in one branch;
5. add/adjust regression tests for the new path;
6. run affected workflows/tests;
7. preserve a redirect/index note where historical readers would otherwise be stranded;
8. only then merge the relocation.

## Current model continuity

- M0 — permanent frozen small empirical winner baseline.
- Corrected M1 — authoritative frozen M1 V1 winner baseline.
- Original M1 — historical/temporally contaminated performance evidence.
- Validation Terrain V1 — permanent, immutable and model-independent.
- MOV0 STANDARD_FINISH V1 — first frozen run complete, CLEAR_SUCCESS.
- MOV0 diagnostics #111/#112/#113 — explanatory post-freeze evidence; no retraining/tuning authority.

## Open PR inventory

At audit time:

- #34 — paused/historical M0 market diagnostic.
- #60 — paused/historical M0 The Odds API market diagnostic replication.
- #61 — superseded original-M1 draft.
- #62 — superseded broad original-M1 draft/methodology provenance.

No PR is closed by this continuity branch.

Recommended separate follow-up: close #61/#62 as superseded after review; leave #34/#60 only if deliberate future market-diagnostic archaeology/resumption is wanted.

## Branch inventory

The repository retains many merged historical feature/diagnostic branches. That is not a functional problem, but it makes branch search noisy.

Obvious cleanup candidates include temporary/copy names such as:

- `tmp-ignore`
- `tmp-ignore-2`
- `docs/corrected-m1-freeze-v1-copy`
- already-merged MOV0 diagnostic branches
- already-merged contract/model branches

No branch is deleted here. A separate prune should verify each branch is merged/reachable and has no external dependency before deletion.

## Root continuity files

Legacy root handoffs (`DATA_PHASE_*.md`, the M1 audit handoff, PM log) remain intentionally in place. They are historical continuity records and may have stable external references.

Current authority is explicitly:

1. `PROJECT_STATUS.md`
2. `PROJECT_MAP.md`
3. `docs/MASTER_MILESTONES.md`
4. `docs/DECISIONS.md`
5. task-specific freeze/contract/evidence

## Remaining debt after this refresh

1. Review/merge this documentation-only continuity refresh.
2. Optional separate PR/branch cleanup for superseded PRs and merged temporary branches.
3. If a directory consolidation is still desired, prepare a reference-complete migration plan before moving anything.
4. Define the next modeling question only after continuity review; repository cleanup itself does not authorize a new model family.
