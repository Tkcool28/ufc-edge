# Raw Data

Raw data is immutable and source-faithful.

## Rules

- Never hand-edit a raw source file.
- Never overwrite an existing snapshot when upstream changes.
- Versioned repositories use a pinned source revision; live/public APIs use an acquisition timestamp or other immutable snapshot identifier.
- Every imported snapshot must carry source identity, acquisition metadata, request/coverage information, and cryptographic hashes where practical.
- Raw files may contain post-fight or present-day information. They are **not** model features until transformed through the canonical and feature layers with no-look-ahead enforcement.
- Missing/404 source data is coverage evidence, not a zero-valued statistic.
- Provider namespaces stay separate in raw storage. Similar-looking UFCStats, UFC.com, ESPN, FightGeek, IMG, Stats Fight, market, or scorecard fields must not be silently mixed.

## Greco1899 layout

Pinned Greco UFCStats snapshots live at:

`data/raw/greco1899/<source-commit-prefix>/`

The active source revision and expected Git blob SHAs are in `provenance/greco1899.lock.json`.

## UFC.com layout

Point-in-time snapshots of the official UFC.com Drupal JSON:API live at:

`data/raw/ufc_com/<YYYYMMDDTHHMMSSZ>/`

The ingestion pass preserves the JSON:API resource catalog plus selected athlete, event and fight collections. Mutable career totals, rankings, streaks and status values are snapshot state and are unsafe for historical backfill.

## ESPN MMA layout

Point-in-time snapshots of ESPN's public UFC/MMA APIs live at:

`data/raw/espn_mma/<YYYYMMDDTHHMMSSZ>/`

The historical discovery pass stores yearly scoreboard payloads and additive fight surfaces such as event details, result status, officials, sparse plays and competitor statistics. The snapshot manifest records HTTP coverage and observed schema names so unavailable endpoints remain explicit.
