# UFC EDGE — Workflow Index

Status: **AUTHORITATIVE WORKFLOW NAVIGATION**

This directory contains a large historical and current workflow surface. Do not infer authority from workflow filename alone; first read `PROJECT_STATUS.md` and inspect the workflow trigger/paths.

## Current milestone workflow families

| Workflow family | Purpose | Network? | Authority note |
|---|---|---:|---|
| physical-profile reconciliation / recent recovery | governed recovery and corrected canonical/F01/F02 rebuild support | some acquisition: yes | consumes/pins governed evidence; do not rerun merely for cleanup |
| F00/F01/F02 validation | contract, PIT materialization and deterministic replay validation | no | frozen foundation checks |
| corrected M1 rerun / missingness audit | controlled corrected-M1 evidence and temporal-safety diagnosis | no | historical accepted evidence; corrected M1 is now formally frozen |
| Model Validation Bucket Contract V1 | build/validate immutable terrain and corrected-M1 calibration evidence | no | permanent model-independent V1 |
| MOV0 contract / frozen run | validate and execute frozen STANDARD_FINISH V1 | no | PR #73 result is accepted CLEAR_SUCCESS |
| MOV0 probability bucket diagnostic | descriptive frozen-OOF calibration buckets | no | post-freeze diagnostic only |
| MOV0 confidence terrain + feature behavior | explanatory diagnostic with guarded coefficient recovery | no | recovered predictions must reproduce frozen OOF exactly |
| MOV0 conditional interaction + archetype | descriptive interaction/archetype diagnostic | no | read-only workflow; durable evidence committed under `docs/model_diagnostics/` |

## Safety rules

- A workflow that performs network acquisition must be treated differently from deterministic canonical/model builds.
- Canonical/model consumers use pinned evidence, not mutable live responses.
- Old workflows may remain valuable historical machinery but are not automatically current instructions.
- Do not re-run expensive, network or credit-consuming workflows merely for repository cleanup.
- Do not treat retained Actions artifacts as repo-local freeze markers unless the relevant freeze convention explicitly does so.
- Post-freeze diagnostics do not authorize retraining, feature selection, threshold optimization or recalibration.
- Before moving a file referenced by a workflow, map every path reference and change the workflow/script/test in the same reviewed migration.

## Finding the exact workflow

Search by the milestone/model name, then read the trigger, referenced scripts and artifact identities before running it. For current model work, start from `PROJECT_STATUS.md` rather than filename chronology.
