# Reproduction

Install the frozen PR163 requirements in Python3.12. From repository root:

```bash
python -c "import sys; sys.path.insert(0,'models/challengers/ground_pathway_simulator_poc_v1'); import publication; publication.restore(publication.OUT)"
OPENBLAS_NUM_THREADS=1 python docs/model_diagnostics/ground_pathway_measurement_hazard_v1/audit.py
python docs/model_diagnostics/ground_pathway_measurement_hazard_v1/supplement.py
python docs/model_diagnostics/ground_pathway_measurement_hazard_v1/report.py
OPENBLAS_NUM_THREADS=1 python docs/model_diagnostics/ground_pathway_measurement_hazard_v1/verify.py
python docs/model_diagnostics/ground_pathway_measurement_hazard_v1/publication.py --verify
```

For a new authorized publication, package and seal only after validation. Existing publication verification checks original hashes and archived plain CSV contents. Regenerated .csv.gz files contain identical plain CSV data; compare decompressed oracle bytes against RECORDS_MANIFEST.json; the primary archive table projects out duplicated reference columns (the exact column list is in publication.py). REPRODUCIBILITY.json records two independent full runs with 24 byte-identical artifacts. PREREGISTRATION.bundle retains the original local pre-scoring commits with the starting main as prerequisite; the GitHub protocol commit was published later and is not asserted to precede local scoring.

This audit imports the frozen engine and descriptive priors; no predictive training or new model artifact exists. The source verifier ran in isolation and reproduced the PR163 evidence manifest. Read FROZEN_SOURCE_VERIFICATION.txt for all canonical/chronology/directional checks.
