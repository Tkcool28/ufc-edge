# M0-MD0 — Bare-Bones Market Comparison V0

Status: diagnostic implementation. Market data are not UFC Edge canonical DATA and are never an M0 training target.

## Question

Does the frozen M0 OOF winner signal merely reproduce the historical UFC market, clearly trail it, or retain measurable information after market probability is known?

## Frozen M0

- authoritative merged main at task start: `4cd9bb9a51b0c8cd225c6a9bed91b9c5933ec1e3`
- M0 freeze: `1.0.0`
- OOF rows: `5,626`
- OOF logical SHA-256: `708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c`
- runtime artifact ID: `10292502486`

The diagnostic consumes `m0_oof_predictions.parquet` exactly. It does not call the M0 fitting code.

## Market source decision

The Odds API was investigated first. Its MMA key and historical `h2h` endpoint are suitable in principle, but the current GitHub connector cannot read the user's external/VPS API credential. An authenticated probe therefore cannot be performed from this execution context without moving or exposing a secret.

The V0 diagnostic uses a pinned public fallback instead:

- repository: `theGholland/ufc-data_with_random_forests`
- pinned commit: `e22124fe43285f3a7018b5c2674e31441797ca9d`
- file: `data/cleaned_odds.csv`
- upstream market source documented by that repository: `betmma.tips`
- listed rows: 4,452
- observed date range: 2014-11-07 through 2023-12-16

The public dataset documents extraction timestamps, not the historical instant represented by each price. Therefore V0 calls these **historical listed odds**. It does not call them opening or closing lines.

No license file was observed at the pinned public repository root. That is a provenance/licensing limitation. The odds are technically usable for this bounded diagnostic only and are not promoted into governed UFC Edge DATA.

## Construction

The source odds are decimal prices. V0 converts each side to raw implied probability as `1 / decimal_odds` and removes vig by proportional normalization across the two sides. There is one listed market source, so there is no cross-book price selection. The fixed blend is exactly `0.5 * M0 + 0.5 * market`.

## Matching

Market display names are normalized only to resolve a unique UFC Edge canonical fighter ID. Any normalized name that maps to multiple canonical IDs fails closed. A resolved market row then matches M0 by exact event date plus the unordered canonical fighter-ID pair. Prices are finally reoriented to F02/M0 canonical `fighter_1`.

Conflicting duplicate market rows for the same date/fighter-ID pair fail closed. Identical duplicates collapse deterministically.

## Incremental-information test

The diagnostic fits only:

- market-only: `target ~ logit(market)`
- market + M0: `target ~ logit(market) + logit(M0)`

Evaluation is expanding-year chronological walk-forward. The first matched year is training-only; every scored year is predicted from earlier matched years only. No random split, additional feature, blend-weight tuning, or outcome-driven parameter search exists.

## Runtime artifacts

The matched diagnostic table and full machine result are generated in GitHub Actions and uploaded as runtime artifacts. Large odds/prediction tables are not committed.

## Explicit exclusions

No ROI, profit, units, Kelly, edge threshold, profitable disagreement bucket, bookmaker-specific profitability, feature reaction, M0 retraining, or M1 work is part of V0.
