# UFC EDGE — Project Status

Status: **AUTHORITATIVE**
Snapshot date: **2026-09-17**
Authoritative main at cleanup start: `7a7b50c2e1cdd20af8c7996e0c8460a35a693296`
Current phase: **repository organization before next model-development phase**

> Fresh sessions: read this file first, then `PROJECT_MAP.md`, `docs/MASTER_MILESTONES.md`, and `docs/DECISIONS.md`. Always verify current `main` before changing anything.

## Repository identity

Repository: `Tkcool28/ufc-edge`

The merge at the authoritative snapshot is PR #67, M1 missingness temporal leakage audit V1. Old draft PRs and old branches are historical evidence, not authority.

## Authoritative DATA

Status: `RECENT_PHYSICAL_PROFILE_COMPLETE_FROM_GOVERNED_PRIMARY_SOURCES`.

Physical-profile recovery order:

`existing canonical/governed source -> UFC Official null-fill -> pinned live UFCStats recovery -> governed supplemental recovery -> null`

Network acquisition is separated from canonical consumption. Live UFCStats recovery is pinned as evidence before deterministic/offline canonical consumption. Repository-local nulls do **not** prove the live source is null.

The committed canonical tree remains rooted at `data/canonical/v0/`; the corrected physical-profile reconciliation/replay workflow constructs the corrected canonical package deterministically at runtime from governed evidence. See `data/README.md`, `data/supplemental/`, `data/raw/ufcstats_live_recovery/`, and the physical-profile reconciliation pipeline/workflows.

## Authoritative feature stack

### F00 — feature contract/governance

Purpose: feature definitions, semantics, versioning, provenance and safety rules.
Methodology: **frozen unless an explicit feature-contract migration is authorized**.
Entry points: `features/FEATURE_CONTRACT.md`, `features/FEATURE_GOVERNANCE.md`, `features/README.md`.

### F01 — point-in-time fighter state

Purpose: materialize fighter state as known strictly before a target fight.
Methodology: **frozen for the corrected physical-profile experiment**.
Entry points: `features/F01_MATERIALIZER.md`, F01 tests/builders referenced by `features/README.md`.

### F02 — historical predictor replay

Purpose: deterministic historical replay of F01 across canonical fights:

`canonical fight -> strict pre-fight cutoff -> F01 states -> deterministic matchup predictors -> predictor artifact -> labels attached afterward`

F02 is **not a model**. It is the shared predictor surface consumed by models.
Replay schema used by M0/M1: `1.0.1`.

## Authoritative models

### M0

Status: **PERMANENT FROZEN SMALL EMPIRICAL BASELINE**.

M0 uses a small governed five-concept subset of F02 and remains the comparison/reference baseline. See `models/m0/README.md` and its committed completion/validation records.

### M1 — original historical model

Status: **HISTORICAL — TEMPORALLY CONTAMINATED BY REACH-AVAILABILITY LEAKAGE**.

The original M1 result must be preserved for audit history, but its performance is not the current authoritative performance estimate. The primary confirmed leakage surface was:

`pair::ctx__physical_size_profile__reach_cm::missing_diff`

The reach value itself was not the defect. Historical present/missing availability encoded future UFC career persistence/profile completeness.

### M1 — corrected physical-profile baseline

Status: **AUTHORITATIVE M1 BASELINE — READY FOR FORMAL FREEZE**.

Corrected aggregate metrics:

| Metric | Corrected M1 |
|---|---:|
| Log loss | `0.649120128` |
| Brier | `0.229025402` |
| Accuracy | `62.1045%` |
| ROC AUC | `0.665905862` |

2026 partial (`N=329`):

| Metric | Corrected M1 |
|---|---:|
| Log loss | `0.630602667` |
| Brier | `0.220613882` |
| Accuracy | `63.22%` |
| ROC AUC | `0.695153533` |

The controlled corrected rerun is PR #65; diagnostic follow-up is PR #66; missingness temporal-safety audit/governance is PR #67.

**Formal-freeze distinction:** the cleanup inventory found no committed corrected-M1 completion/freeze marker equivalent to the existing frozen-model conventions. Therefore current cleanup status is `CORRECTED_M1_READY_FOR_FREEZE_MARKER`. Do not invent a freeze during repository organization.

## Permanent major findings

1. Static attribute backfill does **not** make historical missingness safe.
2. Missingness/data availability must be audited independently for point-in-time safety.
3. `pair::ctx__physical_size_profile__reach_cm::missing_diff` was the primary confirmed original-M1 leakage surface.
4. Invalidated historical evidence is preserved, labeled, and never silently deleted.

Active rule: `governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md`.

## Open/deferred work

Not started/authorized in this cleanup:

- M1B;
- tree/boosted challengers;
- opponent adjustment;
- feature pruning/selection;
- hyperparameter tuning;
- betting simulation or market integration;
- new feature families.

## Open PR warning

Open draft PRs may predate the current authoritative stack. In particular, PRs #34, #60, #61 and #62 are historical/parallel work based on older main states. Inspect current `main` and this status file before reusing any branch or performance statement.

## Next approved action

After this repository-organization PR is reviewed/merged: **return to MASTER/PM for next-model planning**. Do not begin the next model from this cleanup branch.
