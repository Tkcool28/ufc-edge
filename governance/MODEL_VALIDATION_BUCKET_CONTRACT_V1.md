# Model Validation Bucket Contract V1

Validation terrain is model-independent and pre-registered. Stage A accepts only allowlisted pre-fight F02 columns and rejects outcome or prediction column families. Its historical assignment is immutable within V1; future models join the frozen artifact rather than regenerating the historical terrain. Threshold/source changes require V2. Missing rich statistics are `UNASSIGNABLE_BY_CONTRACT`, never LOW. Outcome- and market-driven threshold selection are prohibited, and prediction files cannot affect bucket assignment.

## Frozen percentile reference

V1 percentile scoring is permanently anchored to:

`governance/model_validation_bucket_v1/MODEL_VALIDATION_PERCENTILE_REFERENCE_V1.json`

SHA256:

`c5a54e23e61c5b59f6e7c44c4de2c19652bdd664733001b126cddd41d66f89aa`

The artifact is a deterministic canonical JSON representation of the four exact corrected-F02 fighter-side empirical reference distributions used to create V1. Each distribution is losslessly run-length encoded as sorted `[float64 value, count]` pairs. Its source identities are corrected-F02 logical SHA256 `2d1a367416e105ed6fe546eb8590ae7b555dd044304ad0ba40c7945420599ba0` and corrected-F02 table SHA256 `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`. Generation method identity is `POOLED_UFC_2015_2026_FIGHTER_SIDE_MIDRANK_RLE_V1`.

The four frozen components are:

- `fs__knockdown_rate__created_per_15__career__shrunk`
- `fs__sig_strike_flow__landed_per_min__career__shrunk`
- `fs__submission_attempt_rate__created_per_15__career__shrunk`
- `fs__takedown_pressure__created_per_15__career__shrunk`

A V1 scorer must load and hash-verify this frozen artifact. It must never derive a replacement reference distribution from the incoming historical, future, or live scoring population. Missing, malformed, source-mismatched, or hash-mismatched reference data is a fail-closed error. The mid-rank empirical percentile method and 0.75 pressure threshold remain unchanged.

## Completeness tiers

The permanent V1 completeness contract remains:

- `LOW_MISSINGNESS`: all 8/8 rich-stat side-values present.
- `MODERATE_MISSINGNESS`: 6–7/8 present.
- `HIGH_MISSINGNESS`: 5/8 or fewer present.

`MODERATE_MISSINGNESS` is a valid permanent V1 contract state. The current frozen historical population happens to contain **N=0** fights in that tier. It must not be collapsed or removed because its present count is zero.

## Permanent sample-size governance

The V1 performance-interpretation gate applies to **every current and future model** evaluated on this frozen terrain:

- N ≥ 100 → `NORMAL`
- N 50–99 → `MODERATE_UNCERTAINTY`
- N 25–49 → `THIN_EXPLORATORY`
- N < 25 → `INSUFFICIENT_SAMPLE`; N-only reporting, with substantive performance interpretation suppressed.

Two currently populated joint cells are below N=25:

- `STRIKE_ONE_SIDED__GRAPPLE_TWO_SIDED` — N=17
- `STRIKE_TWO_SIDED__GRAPPLE_ONE_SIDED` — N=18

They remain `INSUFFICIENT_SAMPLE`. Future models may emit comparison rows for these same frozen fights, but the V1 governance label continues to suppress substantive performance interpretation while the cell N remains below 25. Thresholds must not be altered to enlarge these cells.
