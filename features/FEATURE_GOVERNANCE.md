# UFC Edge Feature Governance V1

Status: **AUTHORITATIVE GOVERNANCE PROCESS**

Governance version: **1.0.0**

This document defines how the shared feature system evolves without losing the meaning of old models or artifacts.

## 1. Core rule

Treat feature evolution like database/schema migration.

The lineage boundary is:

```text
SOURCE FACT
→ CANONICAL SEMANTIC
→ ELIGIBILITY / INTERPRETATION
→ FEATURE CONCEPT
→ MATERIALIZED VARIANT
→ HISTORICAL ARTIFACT
→ MODEL / SIMULATOR CONSUMER
```

Each layer has a different identity. A materialized column name is never the semantic identity of the concept.

## 2. Durable identities

Every catalog concept has one durable `feature_id` in `feature_governance.json`.

Rules:

- IDs are human-readable and never recycled.
- Durable shape is `<LAYER>_<CONCEPT>_V<SEMANTIC_MAJOR>`.
- The layer namespace appears exactly once. If a canonical name begins with the same layer prefix plus `_`, remove exactly that one redundant prefix from the concept token before constructing the ID.
- A pure rename keeps the same ID.
- A semantic change requires a new semantic identity/version; do not overwrite the old meaning.
- A methodology-only change bumps `methodology_version`.
- Old IDs remain in migration history when deprecated or superseded.
- Model consumers select shared IDs/tags; they do not redefine features privately.

Current durable layer prefixes are `FS`, `CTX`, `MX`, `OA`, `SIM`, `RES`, and `UNSUP`. Existing clean IDs are not renamed merely for stylistic consistency.

Example:

```text
SIM_TAKEDOWN_SUCCESS_PROBABILITY_V1
│   │                            │
│   │                            └─ semantic major generation 1
│   └─ semantic concept: takedown_success_probability
└─ simulator-layer concept
```

The terminal `_V1` means **semantic identity major 1**. It does **not** mean feature-contract version 1, methodology version 1, model version 1, consumer version, or implementation version. Those remain separate explicit metadata.

Because Governance V1 is still inside unmerged PR #31, malformed IDs discovered during review may be corrected directly and are not historical renames. Once PR #31 merges, durable feature IDs become immutable historical identities and any later replacement must follow the documented lifecycle/migration rules.

## 3. Concept vs materialized value

A concept is the semantic object.

A materialized value is:

```text
feature concept
+ component
+ window
+ round band where supported
+ estimator/shrinkage state
→ output column
```

Example: `FS_CONTROL_RATE_V1` is one concept. Career/last3/last5/EWMA, created/allowed, and round-specific outputs are variants of that concept.

## 4. Lifecycle

Governance lifecycle states:

- **ACTIVE** — approved for the current reviewed predictor surface.
- **DEFERRED** — defined, but methodology/implementation intentionally postponed.
- **RESEARCH_ONLY** — retained for research/human use, not production prediction.
- **SIMULATOR_REQUIRED** — explicitly needed by simulator architecture.
- **DATA_REQUIRED** — desired semantic blocked by missing canonical evidence.
- **PROXY_ONLY** — approximation allowed only with explicit non-equivalence.
- **DEPRECATED** — retained only for historical interpretation; unavailable to new consumers.
- **SUPERSEDED** — replaced by another durable ID.
- **UNSUPPORTED** — current canonical DATA cannot represent it safely.

Existing F00 contract statuses remain recorded separately as `contract_status`; governance does not silently rename them.

## 5. Change classification and replay

| Change | Identity/version action | Replay |
| --- | --- | --- |
| Documentation only | none | none |
| Display/canonical-name rename, same semantics | keep feature ID; add alias/migration | normally none |
| EWMA half-life/prior strength/estimator change | bump methodology version | affected variants |
| Numerator/denominator semantic change | new semantic identity/version | affected artifacts |
| Add a new window/materialized variant | same concept if meaning unchanged | new variant only |
| Add consumer tag | none if semantics unchanged | none |
| Change canonical source | DATA + semantic review | normally required |
| Replace proxy with exact data | new or explicitly migrated identity | replay required |

A worker must record the migration before old meaning becomes ambiguous.

## 6. Add a feature

Required sequence:

1. Identify the canonical source semantic.
2. Define the concept in the shared catalog.
3. Assign a stable feature ID.
4. Define unit and what the feature does **not** mean.
5. Define point-in-time eligibility.
6. Define missingness and zero semantics.
7. Define support/minimum sample.
8. Define formula, numerator, denominator, weighting, windows, and shrinkage.
9. Define consumers and simulator relevance.
10. Add dependency edges.
11. Implement only after the contract is explicit.
12. Add semantic regression tests.
13. Record migration/version impact.
14. Replay only the affected artifact surface.
15. Regenerate `FEATURE_REFERENCE.md` and `feature_inventory.json`.

## 7. Rename

For a semantic-preserving rename:

- retain `feature_id`;
- update `canonical_name`;
- record `renamed_from`;
- record the migration;
- retain old artifact interpretation;
- add a compatibility alias only where needed.

Do not mint a new ID simply because wording improved.

## 8. Change methodology

Examples: half-life, shrinkage strength, weighting, minimum-support calculation.

Required:

- keep semantic identity if the meaning is unchanged;
- bump `methodology_version`;
- record affected variants;
- update dependency/replay impact;
- rebuild affected historical artifacts before a consumer claims equivalence.

## 9. Change semantics

Examples: changing numerator meaning, turning generic control into top control, changing an attempt share into elapsed-time share.

Required:

- do **not** reuse the old identity;
- define a new semantic identity/version;
- deprecate/supersede the old concept as appropriate;
- document compatibility;
- replay all affected artifacts;
- update every consumer explicitly.

## 10. Deprecate / supersede

No concept disappears silently.

A deprecated concept keeps:

- feature ID;
- historical meaning;
- methodology/version;
- introduced/deprecated versions;
- old artifact interpretation.

A superseded concept also records `superseded_by`.

## 11. Add a consumer

Consumers select feature IDs/tags from the shared registry.

Adding a consumer does not create a new semantic concept.

If a model genuinely needs a different semantic, add it to the shared feature system first.

## 12. New data integration

New feature-enabling data cannot bypass DATA.

Required path:

```text
new raw source
→ immutable provenance
→ DATA contract decision
→ canonical/derived semantic
→ feature-source eligibility
→ feature concept or migration
→ dependency update
→ replay-impact decision
→ model/simulator consumer update
```

Example: a future exact top-position-duration feed must first establish source semantics and canonical representation. It cannot be substituted directly into `control_rate`.

## 13. Artifact compatibility

A persisted predictor artifact must carry enough metadata to interpret it without the current catalog:

- feature contract version;
- feature governance version/hash;
- feature catalog hash;
- feature schema hash;
- terminology/dependency hashes;
- per-concept feature IDs;
- semantic/methodology versions;
- DATA freeze;
- canonical manifest;
- ruleset registry hash where relevant;
- code commit;
- materialized column names;
- prediction cutoff;
- target schema/identity once labels are attached.

Bare column-name manifests are insufficient.

## 14. Dependency questions

`features/dependencies.json` is the programmatic answer surface for questions such as:

- What canonical field feeds this feature?
- What breaks if a feature changes?
- Which consumers use it?
- Which concepts depend on ruleset eligibility?
- Which simulator states are blocked by missing data?

Keep dependency edges current with the concept registry.

## 15. Simulator boundary

The simulator registry is intentionally stricter than generic predictor availability.

In particular:

**generic control rate ≠ positional ground/top duration**

Approximate predictors may be useful to a model while still being unsuitable as simulator state-duration evidence.

## 16. Repository hygiene

Authoritative contract/governance files stay shallow under `features/`; runtime implementation stays under `src/ufc_edge/features/`; tools stay under `tools/features/`; semantic provenance stays under `provenance/`.

Do not add committed replay matrices, model outputs, temporary runs, or generated feature stores to this governance milestone.

Quarantined pre-F00 work remains clearly marked and non-authoritative.
