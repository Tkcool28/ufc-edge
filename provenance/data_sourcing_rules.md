# UFC Edge — Data Sourcing Rules

Status: active acquisition policy
Status date: 2026-08-20 (America/Denver)

This document defines how UFC Edge discovers, acquires, stores, refreshes, audits, and promotes external data before feature engineering. It is intentionally stricter than a normal scraping notebook because silent source drift can contaminate historical model training.

## 1. Governing principle

**Raw source acquisition is evidence collection, not feature creation.**

No field becomes a model feature merely because it exists in a source. A desired data family must first be acquired or deliberately resolved, then normalized under a data contract, then tested for historical safety before feature definitions are frozen.

A feature specification may not depend on an unresolved promise that “we will find the data later.”

## 2. Source-status vocabulary

Every source or data family must be in exactly one acquisition state:

- **INGESTED AND AUDITED** — immutable raw bytes exist in-repo and basic coverage/schema/identity QA has passed.
- **INGESTED RAW / QA REQUIRED** — raw bytes exist, but source defects, identity mapping, semantic ambiguity, or coverage questions remain.
- **PIPELINE STARTED / RESULT UNVERIFIED** — ingestion code/workflow exists or has been triggered, but a valid raw artifact + manifest has not been verified.
- **PUBLIC / READY TO INGEST** — accessible without a commercial credential and technically suitable for acquisition, but not yet stored.
- **AVAILABLE BUT DELIBERATELY EXCLUDED** — source exists but is intentionally not part of the canonical data plane.
- **ACCESS / PERMISSION REQUIRED** — useful source exists but licensing, credentials, or explicit access is unresolved.
- **REFERENCE ONLY** — useful for research, benchmarking, or QA but not intended as canonical raw model data.
- **BLOCKED** — attempted acquisition failed for a concrete technical/access reason.
- **UNAVAILABLE** — no legitimate usable source was found.

`PIPELINE STARTED` is never equivalent to `INGESTED`.

## 3. Fail-closed rules

UFC Edge must prefer a visible failure over silently malformed data.

An ingestion job must fail closed, quarantine its output, or remain `QA REQUIRED` when any of the following occurs:

1. **Schema drift** — required fields disappear, types change unexpectedly, enums gain unknown values, or a provider renames/redefines a field.
2. **Coverage collapse** — recent periods return implausibly few events/fights/rows relative to expected source behavior.
3. **Pagination uncertainty** — termination, duplicate pages, cursor loops, or total-count semantics cannot be verified.
4. **Identity ambiguity** — a row cannot be mapped to a stable source identity without relying only on display-name equality.
5. **Historical leakage risk** — a current snapshot cannot be reconstructed as-of the target fight date.
6. **Missing-vs-zero ambiguity** — absent values cannot be proven to mean observed zero.
7. **Semantic conflict** — two fields with the same label appear to use different provider definitions.
8. **Access failure** — HTTP 401/403, entitlement errors, robots/permission constraints, or commercial terms prevent legitimate acquisition.
9. **Integrity mismatch** — expected hashes, pinned revisions, row counts, or downloaded byte counts do not match the manifest.
10. **Partial workflow success** — some endpoints succeed while others fail. Successful payloads may be preserved as evidence, but the source cannot be promoted as complete.
11. **Impossible values** — negative durations, impossible round/time combinations, duplicated fighter sides, self-fights, malformed score totals, or other domain-invalid rows appear above an accepted threshold.
12. **Unexpected source substitution** — a mirror, scrape, cached page, or derived dataset appears where an official/declared source was expected.

### Required behavior on failure

- Never coerce missing data to zero solely to keep a pipeline green.
- Never backfill a missing official field from a secondary source without preserving source provenance.
- Never silently discard malformed records without reporting counts and examples.
- Never treat an HTTP 404 as an observed zero statistic.
- Never use “nearest available” future state for historical rankings, records, streaks, rankings, totals, or status.
- Never promote a source because a single sample request worked; representative historical coverage must be measured.

## 4. Raw-data immutability

Raw provider responses are evidence and should be immutable after ingestion.

Preferred namespace patterns:

- versioned repository source: `data/raw/<source>/<pinned_revision>/`
- live API/web source: `data/raw/<source>/<snapshot_id>/`
- separately licensed/vendor source: its own provider namespace

Every raw snapshot should retain enough information to reproduce or audit acquisition:

- source name and canonical URL/endpoint
- acquisition timestamp in UTC
- pinned commit/version when available
- request parameters / date range / pagination policy
- response or file SHA-256 where practical
- row/page/request counts
- HTTP/status summary
- schema/attribute inventory
- known errors and missing endpoints
- code/workflow revision used for acquisition

A later canonical table must never overwrite the raw payload that produced it.

## 5. Provenance and identity rules

Every normalized row must be traceable back to a raw provider record.

Stable IDs are preferred in this order:

1. provider-owned immutable entity ID
2. provider URL containing a stable entity identifier
3. official FightMetric/UFC identifier
4. explicit crosswalk to another stable source ID
5. deterministic composite key only when no stable provider ID exists

Display names alone are not stable fighter identities. Corner/color/order is transport context, not a semantic fighter identity.

When two sources disagree, retain both raw values and resolve the conflict under an explicit canonicalization rule. Do not overwrite evidence.

## 6. Historical-safety / no-look-ahead rules

A field is eligible for historical training only if its value can be proven to have existed at or before the prediction cutoff.

Examples:

- dated ranking snapshots: use the latest observation strictly before the cutoff
- current UFC athlete totals: **not** safe for old fights unless historical reconstruction exists
- career record: rebuild chronologically from completed fights rather than injecting a modern snapshot
- streak/status/gym/weight class: treat as time-varying unless provider history proves otherwise
- weigh-in data: available only after the official weigh-in; do not use for earlier prediction-time experiments

Every feature family will later declare an explicit `available_as_of` rule in its data contract.

## 7. Missingness semantics

Canonical contracts must distinguish at least:

- **observed zero** — source explicitly reports zero
- **missing from source** — source record exists but field is absent/null
- **endpoint unavailable** — request failed or source does not expose the field
- **not applicable** — field is structurally irrelevant for that row
- **not yet mapped** — raw value exists but identity/normalization is unresolved

These states must not be collapsed merely for modeling convenience.

## 8. Source trust dimensions

Do not use one vague “trust score.” Each source is evaluated on separate dimensions from 1 (weak) to 5 (strong):

### Semantic authority
How close is the source to the official stat producer / event record?

- **5** — official UFC/FightMetric or official data partner feed
- **4** — major first-party sports publisher or licensed specialist with documented methodology
- **3** — established independent archive/scrape with identifiable upstream
- **2** — derived/community dataset with known transformations or OCR
- **1** — unclear provenance, crowd data, prose extraction, or unverified mirror

### Historical completeness
How well does the source cover the needed eras and fields?

- **5** — broad historical coverage with measured near-completeness
- **4** — strong coverage with known bounded gaps
- **3** — useful partial era/field coverage
- **2** — small, selective, or record-book-like subset
- **1** — sample/current-only/unknown

### Refresh reliability
How confidently can UFC Edge obtain fresh future snapshots in the same semantics?

- **5** — documented/stable API or versioned release with reliable refresh path
- **4** — public structured endpoint with repeatable acquisition but no formal stability contract
- **3** — public site/community repo that may drift or lag
- **2** — irregular/manual/archive-only update path
- **1** — blocked, abandoned, one-off snapshot, or access unresolved

### Canonical-use class
Scores do not automatically decide use. Each source is assigned one of:

- **PRIMARY** — preferred source for that data family
- **SECONDARY / QA** — cross-check or gap-fill after explicit reconciliation
- **ADDITIVE** — unique fields/context outside the primary source
- **RAW-ONLY** — retained but blocked from canonical use pending QA
- **REFERENCE** — research/benchmark only

## 9. Official-source preference

When two legitimate sources expose equivalent semantics and coverage, UFC Edge should prefer the source closest to the official producer.

Current intended hierarchy where coverage supports it:

1. official UFC/FightMetric
2. official/licensed data partner
3. major structured publisher such as ESPN
4. reproducible independent UFCStats mirror/scrape such as Greco1899
5. derived/community datasets

This is a preference, not permission to ignore evidence. An official endpoint with poor historical coverage can coexist with a more complete independent historical archive.

## 10. Promotion gate before canonicalization

A newly ingested source cannot move from raw storage into canonical tables until the following are documented:

- exact grain (fighter, fight, fighter-round, action, ranking-date, etc.)
- stable identity fields
- units and clock semantics
- observed schema and types
- missingness behavior
- duplicate behavior
- historical coverage
- latest/freshness behavior
- no-look-ahead rule
- source-conflict rule
- known defects
- provenance/license/access status

## 11. Gate before feature freezing

Before feature engineering begins, each desired data family must be explicitly resolved as one of:

- available and contract-ready
- available but intentionally excluded
- access-gated/deferred
- unavailable

Only after that inventory is closed do we freeze canonical data contracts and then feature families.

## 12. Operational rule for future runs

Every recurring acquisition job should produce a machine-readable manifest that lets us answer:

- What did we request?
- What did we receive?
- How much did we receive?
- What changed in schema/coverage?
- What failed?
- Is the snapshot safe to promote?

A green GitHub Actions job is not sufficient evidence by itself. **The manifest is the evidence.**
