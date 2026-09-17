# UFC EDGE — Architecture Decision Log

Status: **AUTHORITATIVE DECISION INDEX**

Short ADR-style records for decisions future agents should not rediscover.

## D001 — Canonical/provider boundary

**Decision:** provider-specific vocabulary stops at adapters/canonicalization. Downstream features/models consume governed canonical meanings, not provider-specific redefinitions.

**Reason:** keeps source substitution/reconciliation from silently changing semantics.

## D002 — Static physical attributes may be backfilled under governed semantics

**Decision:** stable physical attributes such as height/reach may be recovered/backfilled when source semantics and identity are governed.

**Important limitation:** this decision applies to the attribute value, not automatically to historical missingness/availability indicators.

## D003 — Missingness requires independent point-in-time safety

**Decision:** missingness and data availability are predictive surfaces and must independently satisfy PIT safety.

**Permanent lesson:** `static attribute backfill` does **not** imply `historical missingness is safe`.

See `governance/M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md`.

## D004 — Live UFCStats acquisition is separated from canonical consumption

**Decision:** current/live UFCStats may be queried through a controlled network acquisition step when repository-local evidence is insufficient. Results must be pinned into governed evidence before deterministic canonical use.

**Reason:** network state is mutable; canonical rebuilds must be offline/deterministic from pinned inputs.

## D005 — Preserve invalidated historical model evidence

**Decision:** do not delete original M1 or other important invalidated/superseded experiments. Label their authority explicitly.

**Reason:** failed assumptions and leakage evidence are part of reproducibility and future governance.

## D006 — F02 is shared infrastructure, not a model

**Decision:** F02 is the deterministic historical replay/predictor surface shared by model families. M0/M1 consume it; they do not redefine it.

## D007 — M0 remains permanent small baseline

**Decision:** preserve M0 as a compact frozen empirical benchmark even when stronger models exist.

## D008 — Shared M1 feature representation stays frozen until explicit feature-selection work

**Decision:** repository cleanup and corrective DATA experiments do not prune, redesign, or outcome-shop the M1 feature representation. Any future feature-selection phase must be separately authorized and governed.

## D009 — Corrected M1 is not silently declared frozen

**Decision:** corrected M1 is the current clean baseline, but repository organization does not manufacture a formal freeze marker. Until an artifact consistent with model-freeze conventions is committed/approved, use `CORRECTED_M1_READY_FOR_FREEZE_MARKER`.

## D010 — Repository organization favors indexes over mass path churn

**Decision:** preserve stable code/artifact paths where relocation could break workflows, tests, historical references or provenance. Add authoritative indexes/status markers first; move only clearly safe material.
