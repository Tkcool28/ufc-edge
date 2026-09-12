# M0-MD0-R — The Odds API Historical Market Replication V1

Status: **AUTHORIZED_STAGE_2_IMPLEMENTATION** until the historical workflow completes.

This is a diagnostic replication of the frozen M0 market comparison. It does not retrain M0, alter F02, optimize a betting threshold, calculate ROI, or use market information as a model-training target.

## Frozen inputs

- M0 OOF rows: **5,626**
- M0 OOF logical SHA-256: `708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c`
- eligible OOF rows on/after 2020-06-06: **3,133**
- eligible UFC events: **268**

## Authorized market policy

- provider: The Odds API
- sport: `mma_mixed_martial_arts`
- market: `h2h`
- region: `us`
- one sport-level historical snapshot per eligible UFC event
- default timestamp: `00:00:00Z` on canonical event date
- provider-floor exception: `2020-06-06T10:05:00Z` for the first eligible date
- bookmaker aggregation: median fighter_1 no-vig probability across valid available US books
- de-vig: proportional normalization of both fighter implied probabilities
- fixed blend: exactly 50/50 M0 + market

## Authorized budget

- expected requests: **268**
- expected credits: **2,680**
- hard request ceiling: **300**
- hard credit ceiling: **3,000**
- retries in V1: **0**

The paid workflow has **workflow_dispatch only**. Routine push/PR CI is a separate zero-credit workflow using fixtures and static checks.

## Runtime output

Large raw API responses and normalized parquet tables remain GitHub Actions artifacts:

`artifacts/market_diagnostics/m0_md0r/` conceptually maps to the workflow artifact `m0-md0r-odds-api-replication-v1`.

Only compact reports are committed after successful authorized execution:

- `reports/retrieval_manifest.json`
- `reports/matching_report.json`
- `reports/diagnostic_result.json`

The API key is injected only from `secrets.THE_ODDS_API_KEY` and is never written to generated artifacts.
