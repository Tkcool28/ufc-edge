# MOV1 boosted-tree challenger V1 — first frozen run

**MOV1_BOOSTED_TREE_CHALLENGER_V1_COMPLETE**. Conditional challenger: **INCONCLUSIVE**. Composed system: **INCONCLUSIVE**. No model promotion and no automatic merge.

The preregistered nested family selector did not establish a convincing improvement over frozen linear MOV1-MIN. Its aggregate log-loss gains are tiny and uncertain. Better pooled calibration and seven favorable years are counterbalanced by 2023 and especially partial 2026, a slight composed Brier deterioration, and mixed pathway preservation. The fixed-family shadows look more promising descriptively, but selecting their outer winner would violate this experiment’s promotion rule.

## Identity and execution

- Starting main: `4ec01227a4a35872eed51ce7ce67c45b02e46ebd`; PR #120 confirmed merged.
- Branch: `feat/mov1-boosted-challenger-run-v1`; draft PR #121.
- Pre-fit pushed implementation freeze: `68d1c73a82ec9ae7e7374251b882b9e17179b1c4`.
- Contract manifest: `4593dc0056455356ea9e28191acd2fda109124ca9e18ccb07c09319e99a2849b`.
- Frozen F02, baseline contract/evidence, MOV0-MIN source, literal 35 columns, populations, exact folds and immutable references all pass identities.
- Python3.12.14, Linux x86_64, XGBoost2.1.4 / LightGBM4.6.0 / CatBoost1.2.8, full transitive lock; CPU, one thread, seed17.
- 972 inner +27 outer +9 repeat refits = **1008 fits**. Completed boosting rounds203178; zero ceiling hits, failed fits or exploratory fits.
- 5658 modern eligible bouts,2822 training-population finishes;4260 outer scores per surface and2115 conditional finishes. Decisions never entered fitting or preprocessing.
- Common raw-unit symmetric matrix, pooled training imputation and training-only division one-hot encoding. No numeric scaler, native CatBoost categories, extra crosses, calibration, odds or ROI/EV.
- Runtime274.6 seconds. All scoring precedes outer-label/diagnostic joins.

All implementation gates passed. Every saved prefix and all27 outer plus9 repeat models were regenerated without fitting: **1008 model checks, maximum prediction error0**, within atol1e−12/rtol0. Independent trace replay confirms earliest-best ties and100-round patience; pooled inner losses reconstruct the same configurations and refit counts. Outer native tree counts match requested counts. Composition is finite/in-bounds and sums to1 without renormalization. Swaps, asymmetric nulls, preprocessing restoration and label-removal/change checks pass; no dropped rows.

The full972-fit search was not repeated: that would exceed this execution’s frozen1008 budget. All inner saved predictions/traces were instead replayed, and SELECT was refitted once per year as contracted. No cross-platform bitwise equality is claimed. Packaging and the archive-aware zero-fit verifier were finalized after fitting; the fitted runner and scientific settings are unchanged.

## Primary conditional comparison

| Surface | Log loss | Brier | AUC | ECE | Calibration intercept | Slope | Mean KO |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MOV1-BOOST-SELECT | 0.614896 | 0.213543 | 0.663533 | 0.022994 | 0.010201 | 0.873607 | 65.71% |
| MOV1-CAT | 0.611210 | 0.211777 | 0.670908 | 0.022934 | -0.021467 | 0.920548 | 65.78% |
| MOV1-LGBM | 0.611886 | 0.212159 | 0.666430 | 0.019856 | -0.031574 | 0.967678 | 65.41% |
| MOV1-XGB | 0.611050 | 0.211944 | 0.667017 | 0.022657 | -0.053615 | 1.015144 | 65.29% |
| MOV1_MIN | 0.615366 | 0.213614 | 0.663563 | 0.031387 | 0.010552 | 0.830658 | 66.32% |

SELECT−MIN log loss: **-0.000469595**. Fight paired95: [-0.008926885330868823, 0.0076463054761531195]; event-cluster paired95: [-0.009092972064072554, 0.007826487081917483]. Both span zero. Mean predicted KO falls from66.32% to65.71% versus64.35% actual; slope improves0.831→0.874 and ECE3.14%→2.30%. AUC is essentially unchanged.

## Annual evidence and nested selection

| Year | Family/config | Rounds | Inner pooled LL | Runner-up margin | Conditional LL delta | Composed LL delta |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | XGB_05 | 42 | 0.601954 | 0.003110 | -0.015786 | -0.008094 |
| 2019 | XGB_06 | 57 | 0.592411 | 0.000355 | -0.007200 | -0.003281 |
| 2020 | LGBM_06 | 56 | 0.593518 | 0.000205 | -0.004902 | -0.002435 |
| 2021 | CAT_06 | 152 | 0.600578 | 0.001810 | -0.000982 | -0.000477 |
| 2022 | LGBM_05 | 36 | 0.605931 | 0.000610 | -0.000241 | -0.000128 |
| 2023 | CAT_17 | 33 | 0.606895 | 0.001523 | 0.012535 | 0.006404 |
| 2024 | CAT_11 | 101 | 0.626749 | 0.000440 | -0.009519 | -0.004228 |
| 2025 | LGBM_06 | 40 | 0.621729 | 0.001551 | -0.003347 | -0.001674 |
| 2026 | LGBM_12 | 52 | 0.591882 | 0.002687 | 0.030516 | 0.016820 |

Family selections: XGB2, LGBM4, CAT3. This does not establish universal library superiority. All choices used only the two previous inner years. Seven favorable, two unfavorable, zero tied years. Median annual conditional delta−0.003347. Strongest year2018:−0.015786; worst partial2026:+0.030516. The2018 improvement is383% of the small net aggregate gain, showing substantial cancellation rather than robust persistence.2026 covers the frozen snapshot through August15 and is retained unchanged.

## Fixed-family shadows

**These fixed-family shadow results are descriptive. The experiment did not preregister choosing the production model by selecting the best outer-performing shadow family.**

XGB0.611050, LGBM0.611886 and CAT0.611210 pooled conditional log loss all improve descriptively on MIN0.615366 and SELECT0.614896. Their better outer scores suggest a possible cost from unstable nested family/configuration selection, but this explanation is not established by nine folds. No shadow family is promoted and no alternative significance tests are added.

## Preservation and correction panels

Preservation

| Cell | Finish N | Actual KO | MIN K | SELECT K | LL delta | Brier delta |
| --- | --- | --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 457 | 72.4% | 72.2% | 71.4% | 0.006041 | 0.001156 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 484 | 75.2% | 77.1% | 76.2% | -0.000799 | -0.001275 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 79 | 88.6% | 82.1% | 77.6% | 0.018567 | 0.005555 |
| Heavyweight | 187 | 77.5% | 76.9% | 77.8% | -0.019686 | -0.007453 |
| Light Heavyweight | 205 | 74.1% | 74.7% | 73.9% | 0.005657 | 0.000069 |
| Flyweight | 121 | 52.1% | 56.0% | 58.3% | 0.013872 | 0.007211 |

Correction

| Cell | Finish N | Actual KO | MIN K | SELECT K | LL delta | Brier delta |
| --- | --- | --- | --- | --- | --- | --- |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 224 | 46.0% | 55.2% | 56.8% | -0.011348 | -0.005137 |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 355 | 45.1% | 54.1% | 52.6% | -0.013938 | -0.006255 |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 352 | 49.7% | 56.7% | 57.2% | -0.013018 | -0.005637 |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 341 | 54.3% | 59.6% | 60.5% | -0.014236 | -0.007229 |
| Women's Strawweight | 94 | 44.7% | 50.6% | 51.0% | 0.023117 | 0.011493 |
| Women's Flyweight | 95 | 46.3% | 49.8% | 51.6% | 0.046576 | 0.022162 |

Heavyweight is preserved/improved (77.8% predicted vs77.5% actual); A4 gap improves. A1’s mean remains close, but its loss/Brier worsen slightly. Light Heavyweight’s mean gap improves while loss worsens slightly. Flyweight moves away from observed KO52.1% (56.0%→58.3%) and loses performance. A2’s79 finishes are MODERATE_UNCERTAINTY: its underprediction increases, and loss/Brier worsen. These are mixed preservation findings, not uniform preservation.

B5 moves toward submission: KO54.1%→52.6% versus45.1% actual, with better loss/Brier. B3 does **not** achieve the intended mean correction: KO55.2%→56.8% versus46.0% actual, even though loss/Brier improve. A group’s mean calibration gap and individual predictive loss answer different questions. B1/B2 similarly improve loss but increase mean KO gaps. Women’s Strawweight and Flyweight worsen loss and mean gaps;94/95 finishes are moderate samples. Panels were never used for selection or tuning. Annual panel behavior, Wilson intervals and paired panel loss uncertainty are preserved.

## Fixed probability buckets

| Surface | Bucket | N | Mean KO | Actual KO | Gap pp | Wilson95 |
| --- | --- | --- | --- | --- | --- | --- |
| MOV1-BOOST-SELECT | <0.30 | 14 | 27.6% | 64.3% | -36.64 | [0.38764423103907397, 0.8365526824644587] |
| MOV1-BOOST-SELECT | 0.30–<0.40 | 74 | 36.3% | 40.5% | -4.26 | [0.3009056446255579, 0.5192416109359206] |
| MOV1-BOOST-SELECT | 0.40–<0.50 | 238 | 45.9% | 45.8% | +0.12 | [0.39585367001645827, 0.5214475235112055] |
| MOV1-BOOST-SELECT | 0.50–<0.60 | 438 | 55.4% | 54.1% | +1.27 | [0.49427361061297415, 0.5872035782775535] |
| MOV1-BOOST-SELECT | 0.60–<0.70 | 457 | 65.1% | 62.4% | +2.78 | [0.578357181607903, 0.6668464515226102] |
| MOV1-BOOST-SELECT | 0.70–<0.80 | 500 | 74.8% | 71.6% | +3.17 | [0.674944056876268, 0.7537622280443413] |
| MOV1-BOOST-SELECT | >=0.80 | 394 | 85.2% | 84.5% | +0.66 | [0.80614335899753, 0.8775460704708793] |
| MOV1_MIN | <0.30 | 32 | 25.1% | 50.0% | -24.90 | [0.33630882869327483, 0.6636911713067252] |
| MOV1_MIN | 0.30–<0.40 | 69 | 35.9% | 33.3% | +2.62 | [0.2335105070168671, 0.4507352457128168] |
| MOV1_MIN | 0.40–<0.50 | 208 | 45.5% | 47.6% | -2.13 | [0.40914326914496396, 0.5436516178631351] |
| MOV1_MIN | 0.50–<0.60 | 380 | 55.5% | 53.2% | +2.31 | [0.4813419457751135, 0.5811838691114206] |
| MOV1_MIN | 0.60–<0.70 | 495 | 65.1% | 63.6% | +1.50 | [0.5930867995415912, 0.6775402656569431] |
| MOV1_MIN | 0.70–<0.80 | 518 | 74.8% | 69.9% | +4.94 | [0.6579897929071928, 0.736766117183849] |
| MOV1_MIN | >=0.80 | 413 | 85.8% | 83.3% | +2.50 | [0.7939194363709641, 0.8658038089559656] |

SELECT’s ≥.80 tail is closer to observed frequency; the .70–<.80 gap also improves. The .60–<.70 gap worsens. SELECT’s <.30 cell has14 finishes and is INSUFFICIENT: no substantive tail conclusion. Baseline <.30 has32 and is THIN_EXPLORATORY. Buckets are not matched memberships across models; boundaries remain unchanged. Full table retains empty cells, fixed sample gates, annual coverage, division/archetype composition and separate all-fight score distributions.

## Immutable terrain and all archetypes

All existing weight,round,title,experience,layoff,completeness,striking,grappling and joint MOV cells are retained with MATCH/NO_MATCH/UNASSIGNABLE handling and separate all-bout/finish gates. No category or threshold was created.

Notable conditional deltas: low missingness−0.005011 versus high missingness+0.017120; debut/unknown histories likewise+0.017120. Three rounds−0.001885 versus five rounds+0.011016. Title bouts+0.016461 (91 finishes,moderate). STRIKE_LOW−0.009810 versus STRIKE_ONE_SIDED+0.005212. GRAPPLE_LOW−0.007176, GRAPPLE_ONE_SIDED+0.009301, GRAPPLE_TWO_SIDED−0.056198 (76 finishes,moderate). The STRIKE_LOW__GRAPPLE_TWO_SIDED joint cell improves−0.066277 (68 finishes,moderate). Shared unknown/high-missingness populations overlap; these are not independent confirmations or winner-selection criteria.

| Archetype | All N | Finish N | Finish gate | MIN → SELECT K | Actual KO | LL delta |
| --- | --- | --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.2% → 71.4% | 72.4% | 0.006041 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 82.1% → 77.6% | 88.6% | 0.018567 |
| A3_ACCURACY_VS_ABSORPTION | 973 | 467 | NORMAL | 69.0% → 67.8% | 64.5% | 0.000040 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 77.1% → 76.2% | 75.2% | -0.000799 |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 56.7% → 57.2% | 49.7% | -0.013018 |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 59.6% → 60.5% | 54.3% | -0.014236 |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 55.2% → 56.8% | 46.0% | -0.011348 |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 60.9% → 59.4% | 57.3% | -0.002803 |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 54.1% → 52.6% | 45.1% | -0.013938 |
| C1_DAMAGE_PLUS_SUBMISSION_ACCESS | 29 | 19 | INSUFFICIENT | — | — | — |
| C2_BOTH_HIGH_FINISH_HISTORY | 1483 | 826 | NORMAL | 68.8% → 68.3% | 66.8% | -0.005454 |
| C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS | 417 | 232 | NORMAL | 76.2% → 72.8% | 73.7% | 0.011016 |
| D1_LOW_DAMAGE_STRONG_DEFENSE | 74 | 20 | INSUFFICIENT | — | — | — |
| D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE | 499 | 222 | NORMAL | 78.1% → 79.3% | 81.5% | 0.000622 |
| D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE | 124 | 39 | THIN_EXPLORATORY | 74.5% → 73.7% | 74.4% | -0.016181 |

C1 and D1 are insufficient for conditional interpretation; D3 is thin. Full tables include all three statuses, weight×archetype cells and annual coverage. Overlapping archetypes are descriptive, not independent tests.

## Composed complete system

| System | Multiclass LL | Summed Brier |
| --- | --- | --- |
| S2 | 0.975754 | 0.586206 |
| SB | 0.975521 | 0.586606 |

SB−S2 log loss **-0.000233144**; fight95 [-0.0043190330114718685, 0.0039715042944916635]; event95 [-0.004544835490310947, 0.0038671187137851375]. Seven favorable/two unfavorable years; uncertainty spans zero. Summed Brier increases+0.000400095. KO ECE1.76%→1.61%; SUB ECE2.47%→1.89%; DEC ECE3.29% remains identical. KO calibration slope0.836→0.844, SUB0.830→0.866; all classwise intercepts/slopes/reliability and annual metrics are retained.

SB mean probabilities: KO31.28%, SUB16.05%, DEC52.68%; observed31.95%,17.70%,50.35%. Frozen MOV0-MIN is unchanged, including its decision overprediction. Individual products are averaged; no products of group means. The composed log-loss delta equals finish-fraction times conditional delta (2115/4260); it is algebraically linked, not an independent confirmation. Multiclass Brier and classwise calibration expose additional tradeoffs.

## Interpretability and simulator implications

Five seed17 held-out permutations per transformed column per SELECT model were completed with zero extra fits. Across folds the strongest mean loss increases involve submission pressure, KO win history, submission pressure faced, KD vulnerability and takedown defense. Native XGB weight/gain/total-gain, LGBM split/gain and CatBoost PredictionValuesChange retain their distinct meanings. Do not compare these scales as interchangeable importance.

The three preregistered split co-use hypotheses are checked on selected native trees only. Co-use around submission pressure×TD access, submission pressure×vulnerability, and KD creation×vulnerability is descriptive nonlinear structure, not causality or an isolated interaction-effect estimate. It does not establish that boosting repaired B3/B5. SHAP is explicitly deferred by V1. No variables were removed or refitted.

For the future simulator roadmap, retain frozen linear MOV1-MIN/S2 as the current reference pending a separate decision. This run supports neither replacing them with SELECT nor automatically freezing the best outer shadow. Fight-level probabilities and split importance do not identify round hazards, causal transitions or action/position mechanics. No simulator code is produced.

## Separate classifications and limitations

**Conditional: INCONCLUSIVE.** Tiny primary gain, uncertain intervals, near-identical AUC, seven favorable years but severe partial2026 reversal. Better ECE/slope and B5 loss/correction are supporting evidence; B3 mean correction fails and women/Flyweight/preservation findings are mixed.

**Composed: INCONCLUSIVE.** Tiny uncertain log-loss gain, annual reversal and slightly worse Brier. Better KO/SUB ECE is real descriptive support but does not establish complete-system superiority. DEC limitations are unchanged.

Bootstrap conditions on fitted OOF predictions and does not capture every training-selection uncertainty. Repeated fighters and overlapping histories remain dependence limitations.2026 is partial. Early-stopping/selection reuse inner validation, so inner minima are selection evidence rather than unbiased scores. Nine family selections, thin/moderate cells, correlated predictors and overlapping panels limit interpretation. No full-search refit or cross-platform bitwise claim. No later seed/grid/features/calibration changes, odds, ROI/EV or auto-promotion.

## Reproduction and artifact map

`RUN_MANIFEST.json`, `INPUT_VALIDATION.json`, `ENVIRONMENT_LOCK.json`, `FOLD_IDENTITIES.json`, `FIT_LEDGER.json`, `FIT_BUDGET.json`, `PREPROCESSING.json`, `INNER_CANDIDATES.json`, `SELECTED_BY_YEAR.json`, `REPRODUCIBILITY.json`, `SAVED_RUN_VERIFICATION.json`, `RUNTIME_VALIDATION.json`, aggregate/annual metrics, family/shadow reports, uncertainty, importances and completion marker are retained.

Every native prefix/model, effective parameter dump, stopping trace and inner prediction is preserved in `NATIVE_MODELS.tar.xz.part*`; concatenate numerically and extract to restore3987 files under MODELS. `NATIVE_MODEL_MANIFEST.json` gives member SHA256 hashes. All prediction, bucket, terrain,archetype,panel and matched-difference CSVs are preserved in `EVALUATION_TABLES.tar.xz`, with member SHA256 hashes in `EVALUATION_TABLE_MANIFEST.json`. The saved-run verifier restores both archives automatically without estimator fits.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
python tools/experiments/verify_mov1_boosted_saved_v1.py \
  --f02-table /path/to/winner_modeling_table.parquet \
  --mov0-min-oof /path/to/oof_MOV0_MIN.csv \
  --run-dir models/challengers/mov1_boosted_v1/run_v1
```

`EVIDENCE_MANIFEST.json` hashes all persisted run artifacts except itself and records code/test/workflow hashes, the unchanged training implementation freeze and archive member manifests. The completion marker is emitted only after implementation and saved-model gates pass. Review draft PR #121; do not merge automatically.
