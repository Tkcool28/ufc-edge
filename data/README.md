# Data Directory

This directory has three intentionally simple layers.

## `raw/`

Immutable source snapshots exactly as acquired. Each provider gets one namespace; each changing source gets a pinned revision or timestamped snapshot. Source-specific layout rules live in `raw/README.md`.

## `canonical/`

Normalized UFC entities and histories created only after source identity, duplicate/conflict, units, clocks, null semantics, and provenance rules are audited.

Current acquisition-phase rule: **do not rush raw sources into canonical tables merely because they were successfully downloaded.**

## `features/`

Reserved for the later feature-design phase.

**Do not populate or redesign feature data in the current data-acquisition phase.**

## Navigation rule

Raw bytes live here; explanations do not.

- source locks/status/research conclusions -> `../provenance/`
- data contracts -> `../schemas/`
- acquisition/audit code -> `../pipelines/`
- machine diagnostics -> `../provenance/runs/`

Do not create additional nested documentation trees under `data/`.
