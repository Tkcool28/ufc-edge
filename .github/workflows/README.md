# UFC EDGE — Workflow Index

Status: **AUTHORITATIVE WORKFLOW NAVIGATION**

This directory contains a large historical and current workflow surface. Do not infer authority from workflow filename alone; first read `PROJECT_STATUS.md` and inspect the workflow trigger/paths.

## Current model/data milestone workflows

| Workflow family | Purpose | Trigger type | Network acquisition? | Mutates committed DATA? | Artifact behavior |
|---|---|---|---|---|---|
| physical-profile reconciliation / recent recovery | governed recovery and canonical reconciliation of recent height/reach gaps | manual/PR depending on workflow | some acquisition workflows: **yes** | no direct mutation on `main`; evidence/build changes flow through PRs | pins evidence / emits audit outputs |
| UFCStats live recovery | query mutable live UFCStats for unresolved repository-local physical-profile gaps, then pin evidence | controlled/manual | **yes** | no; acquisition evidence is committed/reviewed separately | acquisition evidence / diagnostics |
| F00 feature contract/governance | validate feature contract/schema/governance | normal CI | no | no | validation output |
| F01 materializer | validate point-in-time fighter-state materialization | normal CI / task workflow | no | no | fixtures/runtime outputs as configured |
| F02 historical predictor replay | deterministic historical replay over F01 | controlled/CI | no | no | authoritative replay is a runtime artifact |
| M1 validation | validate frozen M1 methodology/config and produce historical validation artifacts | controlled/CI | no | no | OOF/results/coefficients as Actions artifacts |
| `physical-profile-corrected-m1-rerun-v1.yml` | controlled corrected-DATA F01/F02 rebuild + exact frozen M1 rerun comparison | PR-controlled | no live acquisition in canonical build; consumes pinned recovery evidence | no | corrected F02/M1/comparison artifacts |
| `m1-missingness-temporal-leakage-audit-v1.yml` | read-only old-vs-corrected missingness temporal-safety audit | PR-controlled | no | no | audit report/evidence artifact |

## Safety rules

- A workflow that performs network acquisition must be treated differently from deterministic canonical/model builds.
- Canonical/model consumers should use pinned evidence, not mutable live responses.
- Old workflows may remain valuable historical machinery but are not automatically current instructions.
- Do not re-run expensive/credit-consuming or network acquisition workflows merely for repository cleanup.
- Do not treat Actions retention artifacts as permanent repo-local freeze markers unless project freeze conventions explicitly say so.

## Finding the exact workflow

Search semantically for `physical-profile`, `ufcstats`, `f01`, `f02`, `m0`, `m1`, `missingness`, or `temporal-leakage`, then read the workflow trigger and referenced scripts before running it.
