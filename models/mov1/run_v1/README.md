# Frozen MOV1 V1 run evidence

Read [the final report](MOV1_KO_VS_SUBMISSION_GIVEN_FINISH_V1_REPORT.md) and [separate interpretation](INTERPRETATION.md). The numerical implementation was frozen before fitting; no feature/fold/threshold changes followed results.

Reproduce with `tools/experiments/run_mov1_conditional_v1.py` in the pinned environment and exact corrected F02/frozen MOV0-MIN inputs. Verify persisted predictions with `tools/experiments/verify_mov1_saved_run_v1.py`. `EVIDENCE_MANIFEST.json` inventories hashes; `RUN_MANIFEST.json` pins source identities. V1 is an immutable first-run record and must not silently change.
