# UFC EDGE — Master Milestones

Status: **AUTHORITATIVE TIMELINE INDEX**

Concise continuity log. For current authority, always prefer `PROJECT_STATUS.md`.

| Date | Milestone | PR / merge | Final status | Authoritative evidence / finding |
|---|---|---|---|---|
| 2026-08 | DATA foundation | historical merged work | COMPLETE | `DATA_PHASE_COMPLETE.md`, `provenance/data_phase_freeze_v0.json`, source/provenance records |
| 2026-09 | F00 feature contract/governance | merged feature-governance work | FROZEN | `features/FEATURE_CONTRACT.md`, `features/FEATURE_GOVERNANCE.md` |
| 2026-09 | F01 PIT fighter state | merged F01 work | FROZEN METHODOLOGY | `features/F01_MATERIALIZER.md` |
| 2026-09 | F02 historical predictor replay | merged F02 work | FROZEN SHARED PREDICTOR SURFACE | replay schema `1.0.1`; F02 is not a model |
| 2026-09 | M0 empirical winner baseline | merged M0 work | PERMANENT FROZEN BASELINE | `models/m0/` completion/validation records |
| 2026-09 | Original M1 | historical M1 work | HISTORICAL / INVALIDATED AS CURRENT PERFORMANCE | later audit found missingness temporal contamination |
| 2026-09-17 | Physical-profile canonical completion | PR #64 | COMPLETE | governed source recovery closes recent physical-profile gaps |
| 2026-09-17 | Corrected F01/F02 + frozen M1 rerun | PR #65 | COMPLETE CONTROLLED EXPERIMENT | corrected M1 log loss `0.649120128`, Brier `0.229025402` |
| 2026-09-17 | M1 correction diagnostic | PR #66 | COMPLETE | isolated effect of corrected physical-profile evidence |
| 2026-09-17 | M1 missingness temporal-safety audit | PR #67 | COMPLETE | reach-availability missingness identified as primary original-M1 leakage |
| 2026-09-17 | Rich-stat/MOV bucket input temporal safety | pre-#70 audit stack | COMPLETE | candidate validation inputs audited before permanent terrain creation |
| 2026-09-17 | Permanent Validation Terrain V1 | PR #70 | FROZEN | immutable model-independent assignment + corrected-M1 calibration diagnostic |
| 2026-09-17 | Corrected M1 formal freeze + modeling reset checklist | PR #71, merge `df2692934565b905f3b53380ec86b01bd42408fc` | FROZEN | corrected M1 freeze marker committed |
| 2026-09-18 | MOV0 STANDARD_FINISH implementation contract | PR #72, merge `a796d594b1815b0313fcf795f5251554f42f531c` | FROZEN CONTRACT | no modeling discretion left for first run |
| 2026-09-19 | MOV0 first frozen run | PR #73, merge `71f982c60d0460292c099195f4fb5187daccf67a` | CLEAR_SUCCESS | MOV0-MIN adds persistent finish-vs-decision signal beyond B1 |
| 2026-09-19 | MOV0 probability-bucket calibration diagnostic | PR #111, merge `15d4beb4470098343b242d54e52c5970b49f4237` | COMPLETE DIAGNOSTIC | frozen OOF only; no retraining/tuning |
| 2026-09-20 | MOV0 confidence terrain + feature behavior diagnostic | PR #112, merge `cb7f66a8d348fef59870869601c5e0ec8fcf1a9f` | COMPLETE DIAGNOSTIC | guarded coefficient recovery reproduces frozen predictions before explanation |
| 2026-09-30 | MOV0 conditional feature interaction + archetype diagnostic | PR #113, merge `0618a21e21002be9999d34f6997be659ca8ff224` | COMPLETE DIAGNOSTIC | permanent merge-safe evidence under `docs/model_diagnostics/` |
| 2026-09-30 | Repository continuity refresh | `chore/repository-continuity-refresh-2026-09-30` | IN REVIEW | refresh authority/index docs; no DATA/model methodology or path moves |

## Current handoff

Review/merge the continuity refresh. Then return to MASTER/PM to define the exact next modeling question. No next model family is selected by this documentation task.
