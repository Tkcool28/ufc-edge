# MOV0 hierarchical / partial-pooling challenger V1

Controlled challenger; frozen MOV0 remains authoritative. Draft PR #115. Do not merge automatically.

Specification was committed before fitting at `bc5f9df5436402915915aa34da304bbfa46cbccb`.

- H0 reads hash-verified frozen MOV0-MIN OOF probabilities.
- H1 uses the existing MIN numeric/title columns and replaces weight-class one-hot coefficients with global intercept plus learned, partially pooled class intercepts.
- H2 adds exactly seven existing transformed MIN slopes. The four semantic families share four learned scales. All other slopes remain global.
- Every fold uses only 2015+ eligible prior-year history; no inner tuning, outcome-selected features, odds, MOV1, or simulator implementation.

`contract.json`, `varying_effect_map.json`, `weight_class_map.json`, and `requirements.lock` are immutable preregistration. Implementation safeguards compare their bytes to the freeze commit. Existing frozen artifacts and diagnostic panel identities are hash-checked.

Run with Python 3.12 and the exact lock:

```bash
python -m pip install -r models/challengers/mov0_hierarchical_v1/requirements.lock
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tools/models/run_mov0_hierarchical_v1.py --f02-dir /path/to/corrected-f02 --mov0-run-dir /path/to/frozen-mov0-run --output-dir /path/to/new-evidence
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tools/models/evaluate_mov0_hierarchical_v1.py --f02-dir /path/to/corrected-f02 --mov0-run-dir /path/to/frozen-mov0-run --evidence-dir /path/to/new-evidence
```

The workflow performs implementation tests on PRs. Its optional manual execution fits all 18 models and repeats first H1 under identical settings. Convergence failure stops evaluation; it does not trigger prior/sampler tuning. Existing Actions input artifacts must still be available for manual execution.

Posterior group effects are conditional associations in standardized predictor units. Reported pooling weights are a preregistered local-information approximation, not a ratio against an independent class model. Smaller N does not automatically mean more shrinkage: predictor information and finish prevalence also matter.

H0-to-H1 comparisons also change global regularization/inference and normalize semantic label wrappers. H2-to-H1 is the more direct test of varying slopes. One fixed specification cannot resolve the whole hierarchical model family.
