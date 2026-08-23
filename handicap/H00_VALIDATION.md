# H00 Acceptance Validation

Generated entirely from frozen canonical DATA through the H00 access layer.

## Demonstration

- Fighter dossier: **Max Holloway**
- Matchup: **Max Holloway vs Dustin Poirier**
- Information cutoff: `2026-08-23T03:30:00Z`
- Direct prior meetings surfaced: **3**

## Data-family counts

| Family | Fighter A | Fighter B |
| --- | ---: | ---: |
| fights | 33 | 32 |
| fighter_round_rows | 112 | 81 |
| opponent_round_rows | 112 | 81 |
| fighter_position_rows | 74 | 61 |
| opponent_position_rows | 74 | 61 |
| ranking_rows | 885 | 668 |
| weigh_in_rows | 30 | 28 |
| profile_snapshot_rows | 1 | 1 |

Classic round validation confirms round >= 1 and presence of every H00-required classic field, including target/position strike splits, knockdowns, takedowns, submissions, reversals, and exact `control_sec`.

Positional/TIP evidence remains represented separately as canonical coarse bucket/bound fields and is never substituted for exact control seconds.

## Generated artifact sizes

| Path | Bytes | Lines |
| --- | ---: | ---: |
| `handicap/v0/index/fighters.json` | 5957122 | 161043 |
| `handicap/v0/fighters/6e36e3a7-7042-5958-b1ab-2c5683abc303.json` | 787772 | 23044 |
| `handicap/v0/matchups/6e36e3a7-7042-5958-b1ab-2c5683abc303__18fbdd6d-2d9a-501e-bcad-20672321fc30.json` | 1590929 | 43936 |
| `handicap/v0/matchups/6e36e3a7-7042-5958-b1ab-2c5683abc303__18fbdd6d-2d9a-501e-bcad-20672321fc30.md` | 315583 | 2754 |

## Unsupported / intentional exclusions

- Canonical judge-round scores: unavailable in DATA v0.
- Predictive/model features: intentionally excluded from H00.
- Sportsbook/market data: intentionally excluded from H00.
- Inferred weigh-in miss/catchweight/penalty semantics: intentionally excluded.
- Primitive field-provenance payloads: not duplicated; packets point to `data/canonical/v0/field_provenance.csv`.

## Integrity

The CI acceptance job separately runs the H00 tests and verifies no diff beneath frozen DATA paths/contracts after packet generation.

GitHub connector retrieval is verified externally after the generated files are committed to the feature branch.
