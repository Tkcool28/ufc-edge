# UFC EDGE — Repository Organization V1 Report

Status: **CLEANUP AUDIT / REVIEW ARTIFACT**

Starting main: `7a7b50c2e1cdd20af8c7996e0c8460a35a693296`
Cleanup branch: `chore/repository-organization-v1`

## Inventory summary

Existing project roots were already structurally strong: `.github`, `data`, `features`, `governance`, `handicap`, `models`, `pipelines`, `provenance`, `schemas`, `src`, `tests`, `tools`.

Root also contained legacy phase/handoff continuity files: `DATA_PHASE_COMPLETE.md`, `DATA_PHASE_HANDOFF.md`, `DATA_PHASE_MASTER_HANDOFF.md`, `M1_MISSINGNESS_TEMPORAL_LEAKAGE_AUDIT_V1_HANDOFF.md`, and `UFC_PM_LOG.md`.

Organization strategy: **indexes first, minimal path churn**. Stable historical paths are retained until a separately reviewed path migration can prove all references are updated.

## Authority classification

- Current authority: `PROJECT_STATUS.md`, `PROJECT_MAP.md`, current governance/contracts/freeze records.
- Historical but valuable: old model results, old F02 artifacts required for comparisons, source-gap evidence, corrected-data comparisons, diagnostics, survivorship/leakage evidence.
- Invalidated as current performance: original M1 validation due to reach-availability temporal leakage.
- Superseded as current instruction: legacy root handoffs/PM logs; retained for history.
- Generated/runtime: large replay matrices, OOF predictions, coefficients and experiment outputs generally remain Actions artifacts unless explicitly promoted to a committed freeze/evidence record.

## Open PR review

| PR | Purpose | Base state | Classification | Superseded? | Recommended action |
|---|---|---|---|---|---|
| #34 | M0 bare-bones market diagnostic V0 | older M0-era main | historical diagnostic | not replaced by core model work, but outside current phase | keep only if future market-diagnostic archaeology is desired; otherwise close as historical after MASTER review |
| #60 | M0 Odds API market diagnostic replication | older M0-era main | historical/paused paid-market diagnostic | outside current phase | likely close after MASTER confirms no immediate market-diagnostic continuation |
| #61 | earlier M1 regularized winner implementation | older main | historical M1 implementation/performance | yes; superseded by later M1 methodology/corrected-data/audit stack | recommend close as superseded; preserve PR history/branch |
| #62 | broad regularized shared-feature M1 | older main | historical methodology source used by corrected rerun | performance superseded; methodology remains provenance | recommend close as superseded by merged #65/#66/#67 stack after MASTER review |

No PR is closed automatically by this cleanup.

## Branch review

Observed branches include `main`, feature/data/docs/handicap branches, M0/M1 drafts, physical-profile branches, and older fixes.

Recommended classes:

- keep: `main`, current cleanup branch;
- merged historical: F00/F01/F02/M0, physical-profile reconciliation/corrected rerun/diagnostic/leakage-audit branches;
- stale/paused: M0 market-diagnostic branches, older parallel M1 branches, older docs/handicap/fix branches unless still operationally needed;
- uncertain: any branch whose external consumer/deployment dependency has not been audited.

Do not delete branches automatically. After PR cleanup decisions, perform a separate branch-pruning task with exact merge/reachability checks.

## Files moved/archived

None in V1. This is intentional: current stable paths may be referenced by workflows, PR descriptions, old chats and provenance. Authority is made explicit through indexes/status documents rather than risky mass relocation.

New handoffs should follow `docs/handoffs/README.md` lifecycle policy. Legacy root handoffs are retained but explicitly non-authoritative.

## Corrected M1 freeze check

No committed corrected-M1 completion/freeze marker equivalent to existing model-freeze conventions was found during inventory.

Status: **`CORRECTED_M1_READY_FOR_FREEZE_MARKER`**.

The PR #65 controlled rerun/runtime evidence is authoritative experiment evidence, but repository cleanup does not silently promote it into a formal committed freeze marker.

## Remaining cleanup debt

1. Optional future path migration for legacy root handoffs/PM log after exact reference scanning.
2. Separate reviewed closure of superseded open PRs.
3. Separate reviewed branch-pruning pass after PR closure decisions.
4. Formal corrected-M1 freeze marker task, if/when MASTER authorizes it.

None of these require DATA/model methodology changes.
