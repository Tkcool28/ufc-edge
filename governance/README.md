# UFC EDGE — Governance Index

Status: **AUTHORITATIVE INDEX**

This directory contains cross-cutting rules that constrain how DATA, features, models, and historical evidence may be interpreted.

## Active governance

| Rule | Purpose |
|---|---|
| `M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1.md` | Governs missingness/data-availability PIT safety after the original M1 reach-availability leakage finding. |
| `../features/FEATURE_GOVERNANCE.md` | Feature definitions, lifecycle, semantics, provenance and evolution rules. |
| `../features/FEATURE_CONTRACT.md` | Current F00 feature contract. |
| `../features/MISSINGNESS_POINT_IN_TIME_SAFETY.md` | Feature-layer companion documentation for PIT-safe missingness. |
| `../provenance/data_sourcing_rules.md` | DATA/source evidence and sourcing rules. |
| `../provenance/data_phase_freeze_v0.json` | Durable DATA-phase freeze record. |

## Permanent missingness rule

The original M1 audit established that:

`pair::ctx__physical_size_profile__reach_cm::missing_diff`

could carry future-derived information through reach **availability**, even when reach itself is a static physical attribute that can be governed/backfilled.

Therefore:

> Missingness and data availability must be audited independently for point-in-time safety.

Do **not** assume that static-attribute backfill makes a missingness indicator historically safe.

## Freeze/version rule

A status statement such as `READY_FOR_FREEZE` is not equivalent to a durable freeze marker. Do not invent model/data freeze artifacts during unrelated work. Index the existing artifact or report the marker as pending.

## Historical evidence rule

Invalidated or superseded results are retained and labeled; they are not deleted merely because they are no longer authoritative.
