# Frozen POC V2 feasibility investigation

Read [DIAGNOSIS.md](DIAGNOSIS.md) for the findings and certificate equations.

Reproduce without scoring outcomes:

```sh
pip install -r docs/model_diagnostics/ground_poc_v2_feasibility_v1/requirements.txt
python docs/model_diagnostics/ground_poc_v2_feasibility_v1/verify.py --replay
python docs/model_diagnostics/ground_poc_v2_feasibility_v1/test_certificates.py
```

The lossless chunked archive contains per-row analytic bounds, exhaustive interval-cover ledgers, diagnostic root proposals and final row classifications. Hash verification restores both this archive and the unchanged original V2 prediction-only records. The replay regenerates proofs for every unavailable row and checks all accepted original rows against the analytic exclusion rule. Root proposals are discovery diagnostics; only interval certificates prove impossibility.

The original frozen run stays blocked. This directory provides a separate diagnosis; it does not amend the solver, targets, model arm, scoring population or original completion marker.
