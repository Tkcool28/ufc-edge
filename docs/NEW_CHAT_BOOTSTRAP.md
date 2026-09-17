# UFC EDGE — New Chat Bootstrap

Status: **AUTHORITATIVE BOOTSTRAP**

You are continuing UFC EDGE.

Read first:

1. `/PROJECT_STATUS.md`
2. `/PROJECT_MAP.md`
3. `/docs/MASTER_MILESTONES.md`
4. `/docs/DECISIONS.md`

Then verify current `main` before making changes. Do not treat an old draft PR, branch, handoff, runtime artifact, or remembered chat result as authoritative merely because it is newer-looking or detailed.

Current baseline at the 2026-09-17 cleanup snapshot:

- DATA: `RECENT_PHYSICAL_PROFILE_COMPLETE_FROM_GOVERNED_PRIMARY_SOURCES`
- F00: frozen feature contract/governance layer
- F01: point-in-time fighter state before target fight
- F02: deterministic historical predictor replay; **not a model**
- M0: permanent frozen small empirical baseline
- M1 original: **HISTORICAL — TEMPORALLY CONTAMINATED BY REACH-AVAILABILITY LEAKAGE**
- M1 corrected: **AUTHORITATIVE M1 BASELINE — READY FOR FORMAL FREEZE**

Permanent historical issue: `pair::ctx__physical_size_profile__reach_cm::missing_diff` exposed temporal leakage through historical availability/missingness. Missingness must independently satisfy point-in-time safety even when a static attribute may be safely backfilled.

Current project phase: **repository cleanup, then return to MASTER/PM for next-model planning**.

Do not begin M1B, a new model family, opponent adjustment, feature pruning, tuning, market integration, or betting simulation without a new explicit authorization.
