# Ground opportunity & competing finish-pathway data audit V1

Read `NEXT_EXPERIMENT_FEASIBILITY.md` first, then source lineage, coverage and the dedicated FightMetric decision. Conclusion B. Zero model fits; no frozen source changes.

Reproduce from the audit branch (Python 3.12 with the pinned numpy/pandas/scipy dependencies in `requirements.txt`):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python tools/audits/audit_ground_opportunity_competing_pathways_v1.py
PYTHONDONTWRITEBYTECODE=1 python tools/audits/report_ground_opportunity_competing_pathways_v1.py
```

Research-context documents are preserved source inputs (in the source manifest), not generated outputs. Both scripts support `--output-dir /tmp/ufc-ground-audit-reproduction`; run both with that same directory to compare all output hashes. Gzip outputs have deterministic timestamp metadata. Source pages and PR #125 archive parts are SHA-verified; only the saved evaluation member is decoded, not native models. No training packages or external data are used.

Tables preserve numerator/denominator/support/missingness and explicit zero opportunities. `boundary_coverage.csv`, `fold_state_coverage.csv`, `conversion_support_bins.csv` and `year_field_coverage.csv` are the primary coverage tables. `B3_B5_*` use frozen cell membership. State tables repeat prior observations across prediction times and must not be interpreted as independent samples. No numeric style classes were selected.

`STRICT_PRIOR_VERIFICATION.json` contains executable chronology and future-mutation gates; the evidence manifest seals source/code/report/table bytes. The completion marker records the manifest digest. Historical publication vintages and licensing are unresolved, not declared to pass by the retrospective event-date check.
