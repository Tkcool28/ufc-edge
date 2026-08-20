# Official UFC FightMetric duplicate-version audit

Snapshot: `data/raw/ufc_fightmetric_official/20260820T123046Z`
Conflicting fighter/round keys: **714** across **109 FightMetric fight IDs**.

## Newest Drupal row vs oldest row

- More non-null metric fields: 672 (94.12%)
- Equal non-null metric fields: 0 (0.00%)
- Fewer non-null metric fields: 42 (5.88%)
- More TIP fields: 672 (94.12%)
- Equal TIP fields: 42 (5.88%)
- Fewer TIP fields: 0 (0.00%)

## Decision

**No automatic newest-row-wins rule is frozen yet.** Drupal internal-ID ordering is useful version evidence, but the duplicated rows must be tied to actual fights and cross-checked against Greco/shared statistics before one version is selected for canonical use.

The raw contract remains fail-closed: preserve every conflicting row; never arbitrary first/last-row dedupe.
