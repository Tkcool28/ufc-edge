# F00 — Feature Contract / Governance Layer

Status: **AUTHORITATIVE LAYER GUIDE**

F00 defines what feature concepts mean, how they are versioned, which inputs they depend on, how missingness/orientation/eligibility are interpreted, and how future changes must be governed.

## Authority

- semantic contract: `FEATURE_CONTRACT.md`
- machine-readable definitions: `feature_catalog.yaml`
- lifecycle/version governance: `feature_governance.json`
- contributor rules: `FEATURE_GOVERNANCE.md`
- terminology/leakage/dependency registries: adjacent governed files listed in `README.md`

## Methodology status

F00 methodology is frozen unless an explicit feature-contract migration is authorized. Repository cleanup does not alter feature semantics.

## Downstream

F01 materializes point-in-time fighter state under F00 semantics. F02 replays that state historically. Models consume F02 rather than creating private semantic definitions for shared features.
