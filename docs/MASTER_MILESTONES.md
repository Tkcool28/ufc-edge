# UFC EDGE — Master Milestones

Status: **AUTHORITATIVE TIMELINE INDEX**

Concise continuity log. For current authority, always prefer `PROJECT_STATUS.md`.

| Date | Milestone | PR / merge | Final status | Authoritative evidence / finding |
|---|---|---|---|---|
| 2026-08 | DATA foundation | historical merged work | COMPLETE | `DATA_PHASE_COMPLETE.md`, `provenance/data_phase_freeze_v0.json`, source/provenance records |
| 2026-09 | F00 feature contract/governance | merged feature-governance work | FROZEN | `features/FEATURE_CONTRACT.md`, `features/FEATURE_GOVERNANCE.md` |
| 2026-09 | F01 PIT fighter state | merged F01 work | FROZEN METHODOLOGY | `features/F01_MATERIALIZER.md`; state must be knowable strictly before target fight |
| 2026-09 | F02 historical predictor replay | merged F02 work | FROZEN SHARED PREDICTOR SURFACE | replay schema `1.0.1`; F02 is not a model |
| 2026-09 | M0 empirical baseline | merged M0 work | PERMANENT FROZEN BASELINE | `models/m0/M0_EMPIRICAL_WINNER_BASELINE_V1_COMPLETE.json`, validation report, frozen runtime artifact |
| 2026-09 | Original M1 | historical M1 work | HISTORICAL / INVALIDATED AS CURRENT PERFORMANCE | broad regularized shared-feature model; later audit found missingness temporal contamination |
| 2026-09 | Physical-profile canonical completion | PR #64, reviewed head `59660c9086384c9388a82a4ac4ecb4e6efd40593`; merged before #65 | COMPLETE | recent physical-profile gaps resolved through governed source recovery; acquisition pinned before deterministic consumption |
| 2026-09-17 | Corrected physical-profile F01/F02 + frozen M1 rerun | PR #65; merge `27b09a094bbe9ddb34326fc29f1b6be366e4de86` | COMPLETE CONTROLLED EXPERIMENT | Corrected M1: log loss `0.649120128`, Brier `0.229025402`, accuracy `62.1045%`, AUC `0.665905862` |
| 2026-09-17 | M1 physical-profile correction diagnostic | PR #66; merge `8b20b34458777b74edb6e7925452faf35443bcf0` | COMPLETE | isolated why original M1 changed after physical-profile correction |
| 2026-09-17 | Full M1 missingness temporal-leakage audit + governance | PR #67; merge `7a7b50c2e1cdd20af8c7996e0c8460a35a693296` | COMPLETE / CURRENT MAIN SNAPSHOT | primary confirmed leakage surface: `pair::ctx__physical_size_profile__reach_cm::missing_diff`; missingness requires independent PIT audit |
| 2026-09-17 | Repository organization + durable handoff architecture | this cleanup PR | IN REVIEW | entry-point hierarchy, authority classification, zero-context bootstrap; no model/data methodology changes |

## Current handoff

After repository organization is reviewed and merged, return to MASTER/PM. The next model-development phase has **not** been selected here.
