# MOV1 directional feature representation + submission pathway feasibility audit V1

**Status: MOV1_DIRECTIONAL_FEATURE_REPRESENTATION_AUDIT_V1_COMPLETE — evidence/architecture feasibility only; no trained challenger, no promotion.**

Authoritative verified starting main: `6f92ce406af77758bacd2ce1f91fbbce0b4fc64b` (merged PRs #121/#122). Draft PR #123, `audit/mov1-directional-representation-v1`. Date boundary: through **2026-08-15**. No post-boundary fight outcomes were requested or inspected. Existing historical outer OOF results were already inspected and are not a fresh sealed holdout.

## Frozen source identity and execution

The **actual** corrected F02 artifact was downloaded in dedicated zero-fit GitHub Actions CI from run `35182939981` (`physical-profile-corrected-f02-v1/winner_modeling_table.parquet`) and its **physical SHA256 matches** `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`. Membership: 5,658 modern eligible UFC fights / 2,822 historical finishes, 1,812 KO/TKO and 1,010 submissions; the chronological outer evaluation retains 4,260 all-eligible fights / 2,115 conditional finishes. Saved boost prediction archive member SHA256 `d1899df12dc560e3633b37fee78c45a68246cfae16dcdb6de8627888bd423d02`, original linear MIN OOF SHA256 `f8841d5007d0dec1000ed3c93a1d397428b2e5668cfdeedca6d3afc7fe4f2b3a`. All diagnostics consume frozen predictions, never predict again.

See `EVIDENCE_MANIFEST.json`, generated deterministically in CI from 26 repository source identities and four independently reproducible evidence files. **Manifest SHA256: `e04409314831753ab00a218bc07f04273c73f19d28507581099f4e1adc5f6488`.** CI fails if a checked-in manifest does not exactly match regeneration. The supplemental machine-readable JSON and 224-row B3/B5 table are available as the 90-day `mov1-pr123-saved-only-diagnostics` artifact from the final audit workflow. Evidence archive retention is finite; preserve both that archive and the upstream frozen F02 outside Actions before expiry (PR #117 warned that upstream F02 expires around 2026-10-17).

## 35 literal MIN columns and all 17 frozen states

See `MOV1_EXACT_35_COLUMN_INVENTORY.csv` and `MOV1_STATE_CONCEPT_TO_FEATURE_MAP.csv`. The 35-column frozen literal allowlist consists of **3 shared fight-context fields**, **15 fighter-side pairs (30 fields)** and **1 pre-existing two-direction knockdown-creation × knockdown-vulnerability matchup pair**. Source pairs include prior experience, first-round finish history, career KO/SUB win and loss history, KD created/allowed, submission attempts created/faced, takedown pressure created/faced and takedown conversion success/defense. Of the 17 frozen PR #113 state concepts, 12 are directly measurable in MIN and five are available in F02/FULL but excluded by the preregistered MIN contract: `ground_share`, `strike_absorbed`, `strike_accuracy`, `strike_defense`, `strike_flow`. This is not a proposal to automatically enlarge MIN or reinterpret the negative FULL incremental result.

## Actual transformation audit and information loss

`models/mov1/implementation_v1.py::Preprocessor.unscaled` pools the **previous training-history fighter pair** for each null median, then emits `(f1+f2)/2` and `abs(f1-f2)` per pair. The linear numeric columns are training-standardized; the boosted challenger `TreeInputRepresentation` inherits precisely the same `unscaled` representation, leaving numeric values unscaled. Both retain one-hot training-only division, rounds/title and the already-directed KD cross-matchup pair. Thus neither generic linear terms nor downstream boosted trees can reconstruct submission-pressure/defensive-exposure **cross-concept fighter alignment** that this map discards. KD's own cross-matchup pair does not encode submission alignment.

The outcome-free pytest fixture proves a **synthetic exact collision**: pressure `(.9,.1)`, exposure A `(.1,.9)`, exposure B `(.9,.1)`. Both have pressure/exposure means `.5` and absolute gaps `.8` (all other MIN inputs can be held identical), while the symmetric directional submission sum `P1×V2+P2×V1` equals **.82 vs .18**. Simultaneous swap of both fighter IDs preserves this sum. GitHub Actions executes the regression; **no outcomes appear in fixture selection**.

To check real-world relevance without tuning to outcomes, the preregistered *descriptive proximity rule* bins four raw submission marginal coordinates (two pair means and two absolute gaps) separately at `floor(value / 0.10)`, requires at least two complete real matchups in one bin, then flags within-bin directional-sum range `>=0.20`. From actual F02: **4,561 complete fights; 680 bins with ≥2; 59 flagged bins comprising 171 fights (3.749% of complete); largest within-bin range .8238013**. This does **not** assert full-35-feature exact equality in observed history, feature importance, or predictive usefulness. The rule is outcome blind and fixed for this inspection; new thresholds must not be chosen from outcomes.

## Independently reconstructed source-lineage findings

The separate `verify_mov1_submission_lineage_v1.py` does **not** import F01 StateBuilder or its shrinkage helper. It re-sums canonical fighter round-stat sufficient statistics, target/earlier fight dates, and prior population sides, using the frozen elapsed-exposure registry solely for per-15-time family eligibility. Four independently defined measurements were checked on **six deterministic real fight fixtures × two oriented fighter sides = 48 numerical reconstructions**:

- `submission_attempt_rate.created_per_15`: 15 × own observed submission attempts / compatible eligible elapsed minutes.
- `submission_attempt_rate.faced_per_15`: 15 × opponent observed submission attempts / compatible eligible elapsed minutes.
- `takedown_pressure.created_per_15`: 15 × own observed takedown attempts / compatible eligible elapsed minutes.
- `takedown_conversion.defense`: (opponent attempted − landed) / opponent attempted on compatible observed rounds; **not** conditioned on elapsed-time eligibility.

For the first three the contract's `time_rate_v1` population-prior pseudo-exposure is 15; for TD defense `attempt_probability_v1` is 20. Independent population priors only use `prior_event_date < target_event_date` (both fighter sides); choose prior target division if it has ≥100 strict-prior fights, otherwise global. Both global and division prior cases were exercised. F01 withholds priors for zero canonical fights because true debut cannot be established. The numeric fixture pass is **48/48; maximum absolute error `4.440892098500626e-16`** against physical F02. Four additional real zero-history fighter-side fixtures verify **16 null F02 values**, not silent zeros/prior fills. Current fight and all same-date observations are excluded. Missing, observed zero and insufficient exposure are distinct; population shrinkage is never estimated from later fights. This is a sampled independent numerical reconstruction and existing full F02 reference/optimized replay governance, **not** independent reconstruction of every F02 row.

The independent audit script initially uncovered its *own* semantic mistake: it incorrectly required elapsed-time eligibility for TD-defense attempt conversion, producing a .002253 difference. It was repaired according to the original untouched F01 source; following CI passed 48/48. Frozen F01/F02/MOV1 were never edited.

## True training feasibility, including early folds

See verified `MOV1_FOLD_SAMPLE_SUPPORT.csv` and the 224-row `MOV1_DIVISION_TRAINING_COMPLETENESS.csv`. These use *actual strict-preyear KO/SUB training histories joined to physical F02*, not all-eligible scoring missingness:

| Outer year | Historical finishes (KO / SUB) | Complete four SUB-side inputs | Complete KO / SUB |
|---|---:|---:|---:|
| 2018 | 707 (451 / 256) | 561 (79.35%) | 361 / 200 |
| 2019 | 948 (602 / 346) | 751 (79.22%) | 484 / 267 |
| 2020 | 1179 (754 / 425) | 931 (78.97%) | 610 / 321 |
| 2021 | 1399 (892 / 507) | 1098 (78.48%) | 712 / 386 |
| 2022 | 1638 (1058 / 580) | 1297 (79.18%) | 848 / 449 |
| 2023 | 1906 (1229 / 677) | 1522 (79.85%) | 988 / 534 |
| 2024 | 2164 (1387 / 777) | 1721 (79.53%) | 1109 / 612 |
| 2025 | 2387 (1528 / 859) | 1904 (79.77%) | 1222 / 682 |
| 2026 | 2639 (1691 / 948) | 2103 (79.69%) | 1348 / 755 |

Complete submission + TD source counts happen to equal the four-submission complete counts in these histories, and complete existing directional KD counts also coincide. This reflects correlated source coverage, **not** absence of missingness (~20% of training histories). Division table retains every observed division, including thin cells and per-class completeness. First-fold 561 usable observations, including 200 submissions, provides meaningful *sample-size feasibility* for an isolated one-degree-of-freedom augmentation, but not proof of future convergence/robustness or a license for multiple specialists.

## B3/B5 saved historical diagnostics

The independent evaluation-only script joins frozen B3/B5 MATCH designations and all four saved conditional predictions, with annual, division, min fighter experience (0,1–2,3–7,8+ prior fights), and complete vs missing SUB source groups. It emits **224 rows** with true finish denominator, KO/SUB counts, observed and predicted conditional shares, gap, individual LL/Brier, and p10/p50/p90 where `N>=25`; pooled-only calibration intercept/slope where `N>=100` and both classes/variance permit. Standard sample statuses: `<25 INSUFFICIENT`, 25–49 `THIN_EXPLORATORY`, 50–99 `MODERATE_UNCERTAINTY`, ≥100 `NORMAL`. No sparse logistic calibration regression, no fitted/applied probability correction.

| Environment | Finish N (KO / SUB) | Observed KO | Linear MIN pred KO (gap) | XGB pred KO (gap) | LGBM pred KO (gap) | CAT pred KO (gap) |
|---|---:|---:|---:|---:|---:|---:|
| B3 TD access + SUB pressure | 224 (103 / 121) | 45.98% | 55.21% (+9.23pp) | 57.49% (+11.50pp) | 57.14% (+11.16pp) | 57.25% (+11.27pp) |
| B5 SUB pressure vs SUB vulnerability | 355 (160 / 195) | 45.07% | 54.05% (+8.98pp) | 53.27% (+8.20pp) | 53.09% (+8.02pp) | 52.60% (+7.53pp) |

Linear MIN B3 is KO-biased in **8/9** annual means (2019 differs), but only 6 years meet the 25-finish loss-reporting gate; partial 2026 has N13. B5 linear mean is KO-biased in **9/9** observed annual means, but partial 2026 N16 is insufficient, leaving eight reportable loss years. The three boosted families improve pooled individual B3 log loss/Brier while worsening mean KO gap, and reduce (but do not erase) B5's mean KO gap. These are different targets of description, **not** proof of interaction benefit. Previously published paired 95% intervals for B3/B5 family-minus-MIN conditional losses cross zero.

B3 has **206 complete /18 incomplete** submission-feature finishes; the latter cannot support loss conclusions under the frozen N gate. Complete-only linear B3 gap remains ~+8.93pp and boosted complete-only gaps remain ~+11.10–11.36pp. B3 minimum-experience distribution: 0=18, 1–2=56, 3–7=104, 8+=46. B5 has **355/355 complete** on four submission source measurements (missing N0), and min-experience distribution 0=0, 1–2=129, 3–7=134, 8+=92. Thus B5's pooled residual cannot be explained as the four submission inputs simply being unavailable. Each division/year/experience subgroup and sparse suppression is in the saved CI CSV. Division composition, years, experience and missingness remain potential correlates and should not be assigned causal shares; sparse subgroup inferences are withheld.

Pooled within-environment calibration *diagnostics* (intercept/slope) are, respectively, B3: MIN (−.294/.551), XGB (−.466/.923), LGBM (−.473/.982), CAT (−.471/.946); B5: MIN (−.290/.480), XGB (−.320/.850), LGBM (−.300/.742), CAT (−.284/.721). These are descriptive fits to old OOF only; **none changed any predictions**. Pooling heterogeneous years can mask chronological drift; do not substitute this for a forward-trained calibration wrapper.

## Striking preservation and alternative explanations

Existing #122 A1 has 457 finishes, observed KO 72.4%, individual-family mean KO 70.4/70.8/71.3%; A4 has 484 finishes, observed KO 75.2%, individual-family mean 74.8/75.4/76.1% (XGB/LGBM/CAT). The prior A1/A4 strict-prior 48/48 lineage is preserved separately, not silently transferred to submission. PR #117 division×round standardized pathway evidence warns against attributing all A1/A4 concentration to a causal alignment effect. Preserve all frozen KD, division and duration inputs. Missing information, erased directional relation, limited sample and probability-scale miscalibration are **distinct hypotheses**, and existing OOF cannot resolve their relative causal contributions.

## Feasibility conclusion and narrow future implementation contract

**Feasibility conclusion: YES, scientifically justified to preregister exactly ONE isolated directional submission representation challenger for future evaluation, not to claim it already predicts better.** Evidence supports that the governed point-in-time safe source quantities exist, their cross-side alignment is provably not recoverable from independent marginal symmetric inputs, real approximate-marginal groups can vary in directional sum, and even the first outer training history has 561 complete fights (361 KO /200 SUB). Historical outcomes do **not** authorize choosing a more complex library, adding an unrelated TD term, choosing optimal bin/formula thresholds, or assuming B3/B5 correction.

Recommended next task, strictly **contract creation only**: `MOV1_DIRECTIONAL_INTERACTION_CHALLENGER_V1`. Freeze original MOV1-MIN 35 literal F02 allowlist, same conditional KO/SUB labels and population, prior-year fold identities, preprocessor semantics, existing KD directional pair, existing division/duration/title controls, natural prevalence and regularized **L2 logistic**. Add one deterministic, fighter-swap-invariant numeric interaction computed from the already-governed fighter-side source pairs, after the **same training-only pooled median** missing-value policy:

`SUB_DIRECTIONAL_SUM = sub_created_f1 × sub_faced_f2 + sub_created_f2 × sub_faced_f1`.

Fix this sum mechanically in the new contract, without outcome-based evaluation of sum/max/min. Standardize its training-only numeric value with the existing linear training scaler workflow; record pre-imputation raw completeness and null flags for evaluation, not as new model predictors unless separately authorized. Preserve original MIN as unchanged comparator, regularization/hyperparameter choice by existing inner chronological history only, immutable archetypes/terrain, all divisions and years including thin ones, A1/A4 striking preservation, calibration reported separately and no posthoc B3/B5 tuning. No additional TD interaction or expanded FULL surface in the first isolating test. Any fresh forward-confirmation population after **2026-08-15** must have eligibility, leakage cutoff, label policy, metrics, divisions, sample gates and untouched outcome boundary frozen **before inspecting outcomes**. Historical 2018–partial-2026 outer OOF is extensively observed research data and cannot be rebranded as a new holdout.

A simple historical prior-year KO share given finish can later be preregistered as a separate strictly prior pooled reference (division/pathway tiny cells require predeclared support/shrinkage); no such reference was fit here. Calibration wrapper, if considered later, must train on prior predictions/outcomes and evaluate untouched subsequent years; no same-OOF calibration claim.

## Guardrail closeout

- Frozen F02/MOV0/MOV1, #113 archetypes and Validation Terrain remain unchanged.
- No feature added to current linear/boosted model matrices, no estimator training, no model rescoring, no calibrator application, no odds/ROI/simulator.
- Only pre-boundary saved prediction labels inspected. No production promotion; PR #123 remains draft and no merge performed.
- CI independently executes synthetic collision test, physical F02 hash and completeness/alignment script, source lineage reconstruction with null checks, saved B3/B5 diagnostics, evidence-manifest regeneration/hash gate, whitespace check.
- Limitations: sampled independent source reconstruction (48 numeric, 16 true-zero-history null), approximate real-marginal bins rather than full-feature exact historical collisions, ~20% source incompleteness, thin annual/weight-class subgroups, non-independent overlapping pathway memberships, heterogeneous pooled calibration and no untouched forward result.
