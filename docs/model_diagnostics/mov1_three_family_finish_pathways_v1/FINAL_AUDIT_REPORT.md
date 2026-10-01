# MOV1 three-family finish-pathway comparative audit V1

**MOV1_THREE_FAMILY_FINISH_PATHWAY_COMPARATIVE_AUDIT_V1_COMPLETE**

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

Main `4ec01227a4a35872eed51ce7ce67c45b02e46ebd`; source PR121 `859be9fad8a1a95cf35f3e5bb99107205734ddce` remains unmerged draft. Separate audit branch `audit/mov1-three-family-finish-pathways-v1` depends on its exact evidence head. All required manifest, archive, population, F02/MOV0, immutable membership and probability identities pass. Zero predictive fits, zero new scoring, zero frozen source modifications.

## Individual-family aggregate comparison

| model | finish_N | log_loss | brier | AUC | ECE | mean_KO | calibration_intercept | calibration_slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LINEAR_MIN | 2115 | 0.615366 | 0.213614 | 0.663563 | 0.031387 | 0.663152 | 0.010552 | 0.830658 |
| XGB | 2115 | 0.611050 | 0.211944 | 0.667017 | 0.022657 | 0.652944 | -0.053615 | 1.015144 |
| LGBM | 2115 | 0.611886 | 0.212159 | 0.666430 | 0.019856 | 0.654087 | -0.031574 | 0.967678 |
| CAT | 2115 | 0.611210 | 0.211777 | 0.670908 | 0.022934 | 0.657840 | -0.021467 | 0.920548 |
| SELECT | 2115 | 0.614896 | 0.213543 | 0.663533 | 0.022994 | 0.657083 | 0.010201 | 0.873607 |

XGBoost has the lowest observed aggregate conditional LL and strongest A1/A4 loss preservation among these shadows. It improves B1–B5 loss while B1/B2/B3 average KO bias widens. Its B5 submission shift is modest; Heavyweight improves, but men’s and women’s Flyweight deteriorate. LightGBM has the lowest pooled ECE and strong B1/B3 loss gains plus B5 improvement. A1/A4/HW improve, but LHW LL is slightly worse, Flyweight/women’s Flyweight worsen and partial2026 is its largest reversal. CatBoost has the highest observed AUC and lowest conditional Brier. It has the lowest observed B3/B5 losses and largest B5 submission movement, but B3 mean bias still worsens; A4 LL worsens slightly despite better Brier, A2 worsens, and Flyweight/women’s divisions remain limitations. All three are more promising descriptively than SELECT globally, with no confirmed or promoted winner.

## Central pathway evidence

| Environment | All N | Finish N | Gate | Actual KO | Actual SUB | LINEAR_MIN | XGB | LGBM | CAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.4% | 27.6% | 72.2% | 70.4% | 70.8% | 71.3% |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 88.6% | 11.4% | 82.1% | 76.3% | 76.8% | 77.1% |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 75.2% | 24.8% | 77.1% | 74.8% | 75.4% | 76.1% |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 49.7% | 50.3% | 56.7% | 57.6% | 57.7% | 57.4% |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 54.3% | 45.7% | 59.6% | 61.0% | 61.0% | 60.5% |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 46.0% | 54.0% | 55.2% | 57.5% | 57.1% | 57.2% |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 57.3% | 42.7% | 60.9% | 59.6% | 59.5% | 59.5% |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 45.1% | 54.9% | 54.1% | 53.3% | 53.1% | 52.6% |
| Heavyweight | 316 | 187 | NORMAL | 77.5% | 22.5% | 76.9% | 76.6% | 76.8% | 77.7% |
| Light Heavyweight | 319 | 205 | NORMAL | 74.1% | 25.9% | 74.7% | 73.1% | 73.5% | 74.0% |
| Flyweight | 252 | 121 | NORMAL | 52.1% | 47.9% | 56.0% | 57.4% | 57.8% | 58.4% |
| Women's Strawweight | 275 | 94 | MODERATE_UNCERTAINTY | 44.7% | 55.3% | 50.6% | 52.6% | 52.5% | 51.0% |
| Women's Flyweight | 266 | 95 | MODERATE_UNCERTAINTY | 46.3% | 53.7% | 49.8% | 54.0% | 53.4% | 51.7% |

| Environment | All N | Finish N | Gate | Actual KO | Actual SUB | LINEAR_MIN | XGB | LGBM | CAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 457 | NORMAL | 72.4% | 27.6% | 0.554185 | 0.549678 | 0.551361 | 0.553864 |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 79 | MODERATE_UNCERTAINTY | 88.6% | 11.4% | 0.350820 | 0.357951 | 0.356008 | 0.376912 |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 484 | NORMAL | 75.2% | 24.8% | 0.538524 | 0.528881 | 0.535453 | 0.539131 |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 352 | NORMAL | 49.7% | 50.3% | 0.691982 | 0.675047 | 0.670705 | 0.681974 |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 341 | NORMAL | 54.3% | 45.7% | 0.666875 | 0.650416 | 0.650582 | 0.652028 |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 224 | NORMAL | 46.0% | 54.0% | 0.702464 | 0.692068 | 0.685433 | 0.683159 |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 861 | NORMAL | 57.3% | 42.7% | 0.662289 | 0.651864 | 0.656548 | 0.658695 |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 355 | NORMAL | 45.1% | 54.9% | 0.706751 | 0.688393 | 0.690283 | 0.687481 |
| Heavyweight | 316 | 187 | NORMAL | 77.5% | 22.5% | 0.504301 | 0.490473 | 0.488332 | 0.494703 |
| Light Heavyweight | 319 | 205 | NORMAL | 74.1% | 25.9% | 0.555442 | 0.549355 | 0.556248 | 0.551027 |
| Flyweight | 252 | 121 | NORMAL | 52.1% | 47.9% | 0.643466 | 0.654030 | 0.664837 | 0.662539 |
| Women's Strawweight | 275 | 94 | MODERATE_UNCERTAINTY | 44.7% | 55.3% | 0.708423 | 0.706068 | 0.694157 | 0.719470 |
| Women's Flyweight | 266 | 95 | MODERATE_UNCERTAINTY | 46.3% | 53.7% | 0.691294 | 0.735787 | 0.737720 | 0.724300 |

The dedicated THREE_FAMILY_FINISH_PATHWAY_COMPARISON.md also provides Brier. Full gaps/deltas/uncertainty and annual coverage accompany every primary environment.

## Explicit scientific answers

1. **XGB observed finish-method information:** LL 0.611050, Brier 0.211944, ECE 0.022657, AUC 0.667017; 7/9 favorable outer years. Read the full pathway matrices for striking/grappling tradeoffs. “Learned” here means observed prediction behavior, not an identified causal mechanism.

2. **LGBM observed finish-method information:** LL 0.611886, Brier 0.212159, ECE 0.019856, AUC 0.666430; 7/9 favorable outer years. Read the full pathway matrices for striking/grappling tradeoffs. “Learned” here means observed prediction behavior, not an identified causal mechanism.

3. **CAT observed finish-method information:** LL 0.611210, Brier 0.211777, ECE 0.022934, AUC 0.670908; 7/9 favorable outer years. Read the full pathway matrices for striking/grappling tradeoffs. “Learned” here means observed prediction behavior, not an identified causal mechanism.

4. **Against linear MIN:** all three repeat the already-observed lower aggregate conditional losses/Brier and better pooled ECE; their uncertainty and nonuniform pathway changes remain material. Linear reference and SELECT remain unchanged.

5. **Useful striking-specific behavior:** XGB: lower observed LL in A1, A4; higher in A2. LGBM: lower observed LL in A1, A4; higher in A2. CAT: lower observed LL in A1; higher in A2, A4. These are descriptive environments, not validated specialist assignments.

6. **Useful grappling/submission behavior:** XGB: lower observed LL in B1, B2, B3, B4, B5; higher in none. LGBM: lower observed LL in B1, B2, B3, B4, B5; higher in none. CAT: lower observed LL in B1, B2, B3, B4, B5; higher in none. These are descriptive environments, not validated specialist assignments.

7. **B3:** **B3_TD_ACCESS_PLUS_SUB_PRESSURE**: 224 finishes (NORMAL); observed KO 46.0%, SUB 54.0%. XGB: KO 57.5%, SUB 42.5%, gap +11.50 pp; LL delta -0.010396, Brier delta -0.004135; absolute mean gap widens by 2.27 pp. LGBM: KO 57.1%, SUB 42.9%, gap +11.16 pp; LL delta -0.017031, Brier delta -0.007382; absolute mean gap widens by 1.93 pp. CAT: KO 57.2%, SUB 42.8%, gap +11.27 pp; LL delta -0.019306, Brier delta -0.008473; absolute mean gap widens by 2.04 pp.

8. **B5:** **B5_SUB_PRESSURE_VS_SUB_VULNERABILITY**: 355 finishes (NORMAL); observed KO 45.1%, SUB 54.9%. XGB: KO 53.3%, SUB 46.7%, gap +8.20 pp; LL delta -0.018359, Brier delta -0.008405; absolute mean gap narrows by 0.78 pp. LGBM: KO 53.1%, SUB 46.9%, gap +8.02 pp; LL delta -0.016468, Brier delta -0.007538; absolute mean gap narrows by 0.96 pp. CAT: KO 52.6%, SUB 47.4%, gap +7.53 pp; LL delta -0.019270, Brier delta -0.008752; absolute mean gap narrows by 1.45 pp.

9. **Individual loss rather than means:** LL/Brier deltas are computed on matched real fights; full primary-cell records and successful/unsuccessful disagreement examples are retained. Group mean correction and loss improvement are reported separately.

10. **Chronological persistence:** XGB improves LL in 7/9 years, Brier in 6/9; worst LL year 2026 (+0.016263). LGBM improves LL in 7/9 years, Brier in 6/9; worst LL year 2026 (+0.030516). CAT improves LL in 7/9 years, Brier in 6/9; worst LL year 2026 (+0.021219). A1 improves in 5/9 years for every family; A4 in 7/9 for XGB/LGBM and 3/9 for CAT. B3 loss improves in 3/6 gated years for XGB and 4/6 for LGBM/CAT; B5 in 6/8 for XGB and 5/8 for LGBM/CAT. Primary-cell annual results use the existing sample gates; all partial2026 rows remain.

11. **Thin/overlapping terrain:** important two-sided-grappling and low-strike/two-sided-grapple cells have 76/68 finishes, with overlapping membership. Other broadly populated panels are also inspected. Gains do not supply independent confirmations across overlapping groups.

12. **Why SELECT trails shadows:** verified annual composition is documented in WHY_SELECT_DIFFERS_FROM_SHADOWS.md; SELECT equals its selected family. The causal reason for inner/outer rank changes remains a hypothesis, not proven instability.

13. **Specialist research support:** recurring paired losses, pathway-specific residuals and family disagreements can motivate a later predefined confirmation of conditional method behavior. They do not supply a production routing rule.

14. **Missing confirmation:** new/sealed chronology, preregistered architecture and any specialist routing, sufficiently populated independent subgroup checks, robust calibration and complete-system validation. Reuse of these OOF outcomes is descriptive, even if an interval excludes zero.

15. **Simulator:** preserve F×K, F×(1−K), 1−F decomposition and frozen linear reference. Neither native feature importance nor group rates identify causal transitions or round mechanics. No simulator is built.

## Secondary complete-system results

| model | N | multiclass_log_loss | summed_brier | ll_delta_S2 | brier_delta_S2 |
| --- | --- | --- | --- | --- | --- |
| LINEAR_MIN | 4260 | 0.975754 | 0.586206 | 0.000000 | 0.000000 |
| XGB | 4260 | 0.973612 | 0.585540 | -0.002143 | -0.000666 |
| LGBM | 4260 | 0.974027 | 0.585662 | -0.001727 | -0.000544 |
| CAT | 4260 | 0.973691 | 0.585532 | -0.002063 | -0.000675 |
| SELECT | 4260 | 0.975521 | 0.586606 | -0.000233 | 0.000400 |

## Aggregate descriptive uncertainty

| model | N | event_N | delta | fight_paired_95 | event_paired_95 |
| --- | --- | --- | --- | --- | --- |
| XGB | 2115 | 361 | -0.004316 | [-0.013290130459958874, 0.00446178671906552] | [-0.013355325862407258, 0.00435335095273024] |
| LGBM | 2115 | 361 | -0.003479 | [-0.012101356557287906, 0.0050014209970317405] | [-0.012112039361026889, 0.004956306352141875] |
| CAT | 2115 | 361 | -0.004156 | [-0.012368996384505644, 0.003753551068450587] | [-0.012608658150661539, 0.004097285346796581] |

## Limitations

This is post-run evidence reuse, with many correlated comparisons and no independent family promotion test. Conditional bootstrap intervals condition on fitted OOF predictions and do not exhaust training/selection/repeated-fighter uncertainty. Groups overlap; unknown handling is immutable; small finish cells suppress performance interpretation. Partial2026 ends August15. Native importance/co-use cover SELECT folds rather than every shadow-year. Correlated predictors obscure attribution; no causal or isolated interaction claims. Existing chronology fixes all rows; no favorable-era filtering, recalibration or fit is performed.

## Evidence map

SOURCE_MANIFEST / EVIDENCE_VERIFICATION; aggregate/annual/configuration CSVs; all15 archetype statuses, division and terrain comparisons; focused B3/B5 and preservation/correction reports; primary-cell complete fight-level differences and deterministic representative examples; paired uncertainty; existing importance/co-use interpretation; composed classwise/annual results; future research implications; completion marker and SHA256 manifest. Native archives remain only in PR121. No automatic merge or promotion.
