# UFC EDGE — Model Index

Status: **AUTHORITATIVE MODEL NAVIGATION**

Models consume the governed F02 historical predictor replay. F02 is shared predictor infrastructure, **not** a model.

## M0

Path: `models/m0/`

Purpose: permanent small empirical baseline/reference model.

Status: **FROZEN BASELINE**.

Start with `models/m0/README.md`. Its committed completion/freeze and validation records are retained under the same directory; large runtime OOF/model outputs remain Actions artifacts.

## M1

Path: `models/m1/`

Purpose: regularized shared-feature UFC winner-probability model over the broader governed F02 surface.

There are two performance states that must not be confused:

1. **Original M1** — `HISTORICAL — TEMPORALLY CONTAMINATED BY REACH-AVAILABILITY LEAKAGE`. Preserve its methodology/results as audit history, but do not quote its validation performance as the current clean estimate.
2. **Corrected physical-profile M1** — current clean M1 baseline. Status at repository-organization snapshot: `AUTHORITATIVE M1 BASELINE — READY FOR FORMAL FREEZE`.

Start with `models/m1/README.md` and `PROJECT_STATUS.md`.

## Not authoritative / not started

- M1B is not an authoritative model and has not been started by this cleanup.
- Tree/boosted challengers are not current authority.
- Opponent-adjusted models are not current authority.
- Betting/market models are outside the current model baseline.

Any future challenger must be a separately authorized project phase and must not silently rewrite M0/M1 history.
