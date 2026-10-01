# MOV0 hierarchical challenger V1.1

Identity: `MOV0_HIERARCHICAL_PARTIAL_POOLING_CHALLENGER_V1_1`.
Amendment: `INFERENCE_BUDGET_AMENDMENT_ONLY`.
Draft PR #116. Do not merge automatically.

V1 draft PR #115 remains the permanent blocked record. Its specification freeze is `bc5f9df5436402915915aa34da304bbfa46cbccb`, blocked evidence head `454ae18ea28ad8086aed1024941b831295d67d91`.

V1.1 began from authoritative main `378ba0576426cd01bd73cbaff774b782c8fb2f6b`. The preregistration commit is `30b14dc5b355e9356dbdd80c793ab6d6feedf861`.

The only inference change is **2,000 tuning + 2,000 retained posterior draws per chain** for every fit and the repeat. Four chains, same seed rule, jitter+adapt_diag, target_accept=.95, maximum tree depth=12, exact original software lock, and all original convergence gates remain fixed. There are no retries.

The four scientific files under `../mov0_hierarchical_v1/` are byte-identical copies from the original V1 freeze, not a redefinition of V1. `amendment.json` pins those files and the exact V1 runner/evaluator snapshots. AST regression checks require all scientific functions to match and compare both sampling calls after removing only tune/draws. The evaluator is byte-identical to V1.

Execute with Python 3.12:

```bash
python -m pip install -r models/challengers/mov0_hierarchical_v1/requirements.lock
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tools/models/run_mov0_hierarchical_v1_1.py --f02-dir /path/to/pinned-f02 --mov0-run-dir /path/to/frozen-mov0 --output-dir /path/to/new-v11-evidence
```

The runner creates only separate V1.1 outputs. It verifies amendment ancestry, exact specification hashes, frozen inputs, chronology, and each fit's full convergence diagnostics. It repeats H1/2018 under identical V1.1 settings and requires exact posterior/prediction equality within that environment. Fighter swaps must preserve predictions within 1e-12.

Any failed gate produces `V1_1_BLOCKED_CONVERGENCE` and stops without performance interpretation. Only after `V1_1_CONVERGENCE_VALIDATED` may the unchanged evaluator run:

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tools/models/evaluate_mov0_hierarchical_v1.py --f02-dir /path/to/pinned-f02 --mov0-run-dir /path/to/frozen-mov0 --evidence-dir /path/to/new-v11-evidence
```

Convergence alone establishes no superiority. The original chronological comparisons, uncertainty, terrain, six bands, archetypes, sample-size governance, and scientific interpretation rules remain fixed. No odds, ROI/EV, new features, MOV1, or simulator implementation is authorized.

## Completed evidence

All 18 fits passed the unchanged gates: V1_1_CONVERGENCE_VALIDATED. The identical-environment H1 repeat and all-fold fighter-order invariance passed. Evaluation is complete: CURRENT_SPECIFICATION_NOT_SUPPORTED for H1/H2 versus frozen MIN; H2 versus H1 is INCONCLUSIVE. PR #115 is unchanged and remains the blocked V1 record.

See [V1.1 final report](run_v1_1/V1_1_FINAL_REPORT.md), [full frozen evaluation panels](run_v1_1/REPORT.md), [varying effects](run_v1_1/VARYING_EFFECTS_AND_SHRINKAGE.md), [tradeoffs](run_v1_1/HELPED_HURT_UNCHANGED.md), [MOV1 implications](run_v1_1/IMPLICATIONS_FOR_MOV1.md) and [simulator implications](run_v1_1/IMPLICATIONS_FOR_HYBRID_SIMULATOR.md). The evidence manifest hashes every persisted compact artifact. Large JSON/CSV files use lossless deterministic gzip. POSTERIOR_ARCHIVE.json hashes each raw trace and the separately preserved posterior/input ZIP. No merge or deployment is authorized by this result.
