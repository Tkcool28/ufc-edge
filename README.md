# UFC Edge

One repository for the full UFC modeling system: source acquisition, canonical data, features, models, simulation, backtests, reports, and later sportsbook diagnostics.

## Current project phase: data foundation

The **current work phase** is data acquisition, validation, identity resolution, source reconciliation, canonicalization, and data-contract design.

Do **not** freeze or engineer model features during this phase. Once the agreed data-source checklist is complete and the canonical data contracts are ready, this phase closes and feature work begins as a separate project/chat phase in the same repository.

## Repository map

Keep the repository shallow and traceable:

- `data/README.md` — one-page map of data storage.
- `data/raw/` — immutable, source-faithful snapshots. Never hand-edit.
- `data/canonical/` — source-neutral UFC entities and histories that satisfy the canonical data contract.
- `data/derived/` — later reproducible non-feature data products built from canonical data when needed.
- `provenance/` — source locks, acquisition status, source notes, durable research conclusions, and source-selection evidence.
- `provenance/audits/` — generated QA/audit outputs tied to specific snapshots.
- `provenance/runs/` — machine run logs and terminal diagnostics.
- `pipelines/` — deterministic acquisition, normalization, reconciliation, and audit code.
- `schemas/` — canonical data contracts, source-adapter contracts, enums, units, and acquisition schemas.
- `features/` — later feature definitions/builders. Reserved during the current data phase.
- `models/` — later predictive/component models and simulator code.
- `backtests/` — later chronological evaluation/replay code.
- `reports/` — human-readable generated outputs and scorecards.
- `tests/` — source, schema, canonical, leakage, and later model-quality gates.
- `.github/workflows/` — reproducible runners for acquisition, audits, and later build stages.

Avoid parallel documentation trees or deeply nested folders that repeat names such as `data/docs/data/...`. A durable conclusion should have one obvious home and be linked from the nearest top-level README or manifest.

## Data architecture rule

Provider-specific vocabulary stops at the adapter boundary.

```text
RAW SOURCE SNAPSHOT
    ↓
SOURCE ADAPTER
    ↓
CANONICAL DATA CONTRACT
    ↓
CANONICAL TABLES
    ↓
FEATURES / MODELS / SIMULATOR
```

UFC.com, UFCStats/Greco, ESPN, rankings, scorecards, weigh-ins, and external-MMA sources may all name or encode the same concept differently. Adapters must convert those observations into one canonical name, type, unit, null meaning, identity rule, and provenance model before downstream code can consume them.

A new source may add coverage or evidence. It must **not** create a new definition for an already-defined canonical concept merely because the provider uses a different field name.

## Source truth hierarchy

When numbers disagree:

1. immutable raw source response/file;
2. raw snapshot manifest/hash;
3. generated audit tied to that snapshot;
4. canonical reconciliation decision + field provenance;
5. source/provenance summary;
6. conversational notes.

Do not overwrite a higher-trust source with a remembered or paraphrased value.

## Non-negotiable leakage rule

Any future training feature for a fight must be computable using only information available strictly before that fight. Current snapshots may contain post-fight or present-day fields; acquisition does not make them historically safe.

## Historical backbone

Greco1899's UFCStats scrape remains a pinned historical backbone while official UFC FightMetric and other additive sources are audited. The pinned Greco revision is `8e40eb945e1127bf0ef172ab211a34787948f312` under `data/raw/greco1899/8e40eb945e11/`.

## Data-phase completion rule

This phase ends only when every material data family identified in the acquisition plan is one of:

- **INGESTED + AUDITED**;
- **ACCESS-GATED / DEFERRED BY DECISION**; or
- **REJECTED WITH A RECORDED REASON**.

The canonical data contract and identity/provenance rules must also be stable enough that the next feature phase consumes data without redefining source semantics.
