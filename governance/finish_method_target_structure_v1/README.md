# Finish-method target structure V1

**Immutable descriptive reference; not a predictive feature table.**

Start with [FINISH_METHOD_TARGET_STRUCTURE_AUDIT_V1_REPORT.md](FINISH_METHOD_TARGET_STRUCTURE_AUDIT_V1_REPORT.md), then the MOV1, partial-pooling and hybrid-simulator implication files. `AUDIT_CONTRACT_V1.json` was committed before outcome aggregation. Future work may read this directory but must not silently modify V1; corrections or extensions require a separately reviewed version.

| Artifact | Purpose |
|---|---|
| `population_manifest.csv.gz` | Exact eligible bout identities, methods, raw/normalized division, era, rounds, immutable terrain and pre-existing state memberships |
| `excluded_fights.csv` / `POPULATION_AND_EXECUTION.json` | Exact 71 exclusions, 5,658 population reconciliation, cutoff and pinned input hashes |
| `canonical_weight_class.csv` | All 46 raw-label mappings using the existing governed literal map |
| `weight_class_finish_method.csv` | All twelve divisions, Catch Weight and UFC-wide counts/rates/Wilson intervals |
| `weight_class_era.csv` / `weight_class_rounds.csv` / `weight_class_era_rounds.csv` | Fixed era and scheduled-round views with matched-reference pp differences |
| `striking_pathway.csv` / `grappling_pathway.csv` / `mixed_survival_pathway.csv` | All 15 exact #113 archetypes, MATCH/NO_MATCH/UNASSIGNABLE |
| `state_pathways.csv` / `state_era.csv.gz` / `state_rounds.csv.gz` | All 17 existing concepts, ten unordered LOW/MID/HIGH/MISSING pairs each |
| `pathway_weight_composition.csv.gz` | Division composition for every archetype status and state-pair cell |
| `weight_class_archetype.csv.gz` / `weight_class_terrain.csv.gz` | Bounded all-division cross-tabs, including zero/small cells |
| `terrain_pathways.csv` | All eight existing permanent terrain dimensions |
| `archetype_era.csv` / `archetype_rounds.csv` | Pathway persistence and exposure views |
| `pathway_standardized_contrasts.csv` / `pathway_standardized_era.csv` / `pathway_standardized_rounds.csv` | Descriptive MATCH−NO_MATCH common-support contrasts standardized by division/rounds; no causal claim |
| `pathway_standardization_strata.csv.gz` | Underlying division × fixed-round counts, intervals and gates; sparse support stays visible |
| `SAMPLE_GOVERNANCE_METADATA.json` | Separate bout and conditional-finish gates, unknown states, marginal interval limits |
| `EVIDENCE_MANIFEST.json` | SHA256/byte counts for every durable artifact and runner |

Gzip is deterministic; pandas reads it directly. Rates are proportions, deltas percentage points, absent denominators blank. Each conditional share uses `finish_N` and `finish_sample_status`. Archetypes overlap and cannot be summed.

Reproduce using Python 3.12, numpy 1.26.4, pandas 2.2.3 and pyarrow 17.0.0:

```bash
python tools/diagnostics/run_finish_method_target_structure_v1.py \
  --f02-table /path/to/frozen/winner_modeling_table.parquet \
  --output-dir /tmp/finish-method-audit
```

The authoritative corrected F02 was produced by workflow run `35182939981`, artifact `physical-profile-corrected-f02-v1`; its table hash must equal `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`. The runner checks every contract-pinned source. It does not download, materialize features, fit/retrain models, consume predictions or generate simulator behavior. Human-authored report/implication files are reviewed interpretations of the generated tables; they are not rewritten by reproduction. CI compares all reproduced table bytes and execution metadata and verifies committed hashes.

The upstream F02 Actions artifact is currently available but expires 2026-10-17. The committed target/membership reference remains durable; a later full source-level rerun needs an archived copy with the same pinned hash, not a silently rebuilt F02.
