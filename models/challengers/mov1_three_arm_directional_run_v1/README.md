# MOV1 three-arm directional challenger V1 — frozen execution

Executes merged PR124 from main a638fc1c9a66986875e1929949886c3ef6bf6621. The original contract and all source artifacts remain unchanged. No ArmA/MOV0/boosted fitting, no post-Aug15 outcomes, no additional candidates, no promotion or automatic merge.

Implementation is frozen before first fit via PRE_FIT_IMPLEMENTATION_MANIFEST.json and a published Git commit recorded with the run. Pre-fit evidence includes20 outcome-free tests, the exact frozen source/fold validator and a full synthetic-label/constant-probability reporting fixture. Code consumes the original feature-specification operations/order and common source-pair medians. Original numerical family/settings/grid and164-fit budget are enforced.

Run only once in a new evidence directory with the pinned environment:

```bash
python -W ignore::FutureWarning tools/directional_mov1/run_v1.py --f02 /path/to/verified/winner_modeling_table.parquet --mov0 /path/to/frozen/oof_MOV0_MIN.csv --output models/challengers/mov1_three_arm_directional_run_v1/run_v1 --implementation-freeze PUBLISHED_PREFIT_SHA
```

The runner first launches the no-training contract validator in a separate process, verifies original A and F identities, records source evidence, then fits144 inner +18 outer +2 preregistered2021 reproduction models. It saves all fitted/preprocessing/native prediction records, selects C from inner history only, and persists prediction-only outer tables before joining outcomes. Evaluation implements shared paired bootstrap draws and original success/pathway/preservation rules. Unexpected fitting/convergence/source/dimension/identity failures produce INVALID_INCOMPLETE without assigning scientific failure.

Saved-only verification reconstructs all164 fitted records and8520 challenger outer predictions, independently recovers inner selection, aggregate losses and10,000-draw paired uncertainty/classifications without fitting:

```bash
python -W ignore::FutureWarning tools/directional_mov1/verify_v1.py --f02 /path/to/verified/winner_modeling_table.parquet --output models/challengers/mov1_three_arm_directional_run_v1/run_v1
```

Native records and large evidence tables are retained in hashed, deterministic tar.xz part bundles, with exact member names/hashes. Concatenate parts lexically and extract to recover every original file. The verifier restores large tables automatically. GitHub uploads the complete verified evidence as a90-day Actions artifact. ArmA original evidence is referenced rather than duplicated as standalone models/prediction files.

Forward conditional2026 records are preserved but no cohort is enrolled here. Prospective complete-system enrollment remains BLOCKED_MISSING_FROZEN_MOV0_RECORD. Historical composition consumes frozen OOF F unchanged; no recovery or refitting of MOV0 is attempted. All historical scientific conclusions are developmental evidence, not independent forward confirmation.
