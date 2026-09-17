# UFC EDGE — Provenance & Freeze Index

Status: **AUTHORITATIVE INDEX**

Use this directory for durable source locks, acquisition status, source-selection evidence, DATA freezes, audits and run evidence.

## DATA provenance

- `data_phase_freeze_v0.json` — committed DATA-phase freeze marker.
- `data_source_manifest.md` — source inventory/status.
- `data_sourcing_rules.md` — source-governance rules.
- `audits/` — generated QA/audit outputs tied to specific evidence/snapshots.
- `runs/` — machine run logs/terminal diagnostics where present.
- source-specific `*.lock.json`, closeout and audit records — pinned source identity/evidence.

## Physical-profile correction

Recent physical-profile completion is governed by repository evidence under `data/supplemental/`, pinned live-recovery evidence under `data/raw/ufcstats_live_recovery/`, and the physical-profile reconciliation pipeline/workflows. Live network acquisition is not itself canonical authority; pinned evidence consumed by deterministic/offline reconstruction is.

## Feature freezes

F00/F01/F02 methodology and versioning live primarily under `features/` plus associated tests/workflows. `PROJECT_STATUS.md` is the current authority index; do not infer current feature authority from timestamp alone.

## Model freezes

### M0

Committed completion/freeze evidence lives under `models/m0/`, including `M0_EMPIRICAL_WINNER_BASELINE_V1_COMPLETE.json` and its validation report. Runtime OOF artifacts remain GitHub Actions artifacts.

### Original M1

Its methodology/configuration remains under `models/m1/` and historical runtime validation artifacts are preserved. Its historical performance estimate is **not current authority** because missingness temporal leakage was later confirmed.

### Corrected M1

The controlled corrected rerun is preserved through PR #65 and its workflow/runtime artifacts. PR #66 supplies the correction diagnostic; PR #67 supplies the full missingness audit/governance.

At the repository-organization snapshot there is **no committed corrected-M1 completion/freeze marker equivalent to the M0 convention**. Status: `CORRECTED_M1_READY_FOR_FREEZE_MARKER`.

## Authority rule

When evidence conflicts, prefer the explicit current authority declared in `PROJECT_STATUS.md`, then the relevant immutable/frozen artifact and its provenance. Historical artifacts remain evidence but do not become current merely because they contain a complete result.
