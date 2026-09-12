# F02 — Deterministic Historical Predictor Replay V1

F02 converts the governed F01 point-in-time materializer into one shared historical predictor surface for later model families. It does **not** train models, select features with outcomes, consume sportsbook data, perform opponent adjustment, or implement simulator states.

## Contract

- **Row grain:** one canonical target fight.
- **Target universe:** canonical `data/canonical/v0/fights.csv`, ordered by `(event_date, event_id, fight_id)`.
- **Prediction cutoff:** target event date at `00:00:00Z`. F01 history eligibility is date-only and requires `event_date < cutoff_date`, so the target and every other same-date fight are excluded. F02 never invents bout order.
- **Orientation:** F01/F00 orientation is authoritative: lexicographically smaller canonical fighter ID is fighter 1; larger ID is fighter 2.
- **Shared surface:** all currently active V1 F01 concepts are replayed with `consumer=None`. Model-specific selection happens later from governance metadata.
- **Namespacing:** fighter-state/context values are `f1__<F01 materialized name>` / `f2__<F01 materialized name>`. Matchup values remain exactly one `mx__` namespace.
- **Predictor/target separation:** predictor chunks and their manifest are frozen first. Winner labels are attached afterward into a derived modeling table and a separate target manifest.

Current governed surface at F02 V1 is 60 durable concepts, 24 active V1 concepts, 104 F01 materialized definitions (99 fighter-state/context plus 5 matchup interactions), and **203 row-level predictor columns** after fighter orientation is expanded across both sides.

## Semantic authority

F02 does not implement feature formulas. `V1Materializer` / `StateBuilder` remain the semantic authority for:

- strict point-in-time history;
- recent/career/EWMA windows;
- same-day ambiguity handling;
- shrinkage and minimum support;
- semantic missingness;
- external-promotion history;
- target context;
- matchup interactions;
- elapsed-exposure eligibility through `ruleset_registry_v1` only.

`DR_EXACT_POSITIONAL_DURATION_V1` remains `DATA_REQUIRED` / `SIMULATOR_REQUIRED`. F02 does not infer top, ground, back-control, clinch, transition, or other exact positional duration from generic control, strike locations, takedown timing, or coarse FightMetric buckets.

## Reference and optimized replay

The untouched F01 path is the reference. Full-history replay may use `ExactReplayStateBuilder`, whose only optimization is a population-prior index. For each feature/component/cutoff it applies scalar contributions in the same canonical fight order and fighter-A/fighter-B order as F01. It does not change formulas, windows, shrinkage, or cutoff semantics.

Before optimized replay is accepted, F02 runs a representative bounded fixture through both reference and optimized materializers and compares the complete predictor row **and** F01 audit projection for exact Python equality. Any difference is a hard failure; the optimized path is not allowed to continue.

## Artifacts

Runtime output belongs under `artifacts/features/f02/v1/` (gitignored) or another caller-supplied output directory. Full matrices are not committed to git.

A replay directory contains:

```text
manifest.json
schema.json
coverage.json
exclusions.json
equivalence.json
target_contract.json
summary.json
chunks/
  <five-year-range>.parquet
  <five-year-range>.manifest.json
winner_modeling_table.parquet   # only when --attach-targets is requested
target_manifest.json            # only when --attach-targets is requested
```

Five-year event-date ranges provide deterministic, bounded restart points without creating one file per fight or fighter. `--resume` verifies target-membership, Parquet-byte, and logical-content hashes before reusing a chunk.

Parquet is the production storage format. The core feature package remains importable without PyArrow/NumPy; those dependencies are installed only for optimized replay / Parquet writing. Artifact identity is based on a canonical logical row hash, not solely on Parquet bytes. Parquet hashes are recorded separately.

## Schema and missingness

The runtime `schema.json` explicitly records ordered columns, types, nullability, roles, and F01 source materialized names. Missing predictor values remain null. No zero/mean/population fill is introduced outside F01's governed shrinkage.

F01 semantic states (`observed_positive`, `observed_zero`, `missing_observation`, `not_applicable`, `insufficient_exposure`) are retained in replay QA while producing coverage diagnostics. They are not duplicated into hundreds of model-matrix columns.

## Target contract

F02 V1 attaches only the minimum winner-model target fields:

- `target_state`
- `binary_winner_eligible`
- `fighter_1_win`
- `winner_id`

Canonical `win_loss` rows are binary eligible only when `winner_id` is one of the oriented participants. `draw`, `no_contest`, `other`, and `unknown` remain explicit and receive `fighter_1_win = null`. The current canonical DATA contract has no separate `overturned` result enum, so F02 does not infer one from `other`.

## Reproduction

Inspect contracts/universe:

```bash
PYTHONPATH=src python tools/features/replay_f02.py inspect
```

Run exact reference/optimized equivalence:

```bash
PYTHONPATH=src python tools/features/replay_f02.py equivalence --equivalence-targets 16
```

Bounded modern replay (default: first 300 deterministic 2024 targets):

```bash
PYTHONPATH=src python tools/features/replay_f02.py bounded \
  --output-dir /tmp/ufc-edge-f02-bounded \
  --attach-targets
```

Full replay after bounded validation passes:

```bash
PYTHONPATH=src python tools/features/replay_f02.py full \
  --output-dir /tmp/ufc-edge-f02-full \
  --attach-targets --resume
```

Use `--reference` only when deliberately running the unoptimized F01 path.

## Leakage/determinism gates

Focused tests cover target exclusion, target-label mutation invariance, future-result/stat mutation invariance, date truncation, orientation reversal, same-date exclusion, external-history/no-round-stat behavior, target-state handling, elapsed-feature auditability, schema uniqueness/counts, and optimized/reference exact equivalence.

Two runs over the same code/contracts/DATA and target selection must produce the same target set, ordering, schema, values/nulls, chunk logical hashes, final logical artifact hash, and deterministic manifest hash. Runtime timestamps and elapsed resource measurements live outside deterministic manifest content.

## Coverage diagnostics and known limits

Coverage is reported by year, promotion, fighter-history depth, active materialized feature/missingness state, elapsed-feature state, external-history slice, UFC rules-reference era, and scheduled-round count. Frozen canonical `fighters.csv` has no governed sex/gender field; F02 therefore does not fabricate a male/female split.

The next task after F02 is **M0 — empirical baseline / first model-family validation**. F02 does not start M0.
