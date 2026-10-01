# Complete-system secondary check

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

With frozen F=MOV0-MIN and family K: P(KO)=F×K; P(SUB)=F×(1−K); P(DEC)=1−F. All 4,260 outer fights participate.

| model | N | multiclass_log_loss | summed_brier | ll_delta_S2 | brier_delta_S2 |
| --- | --- | --- | --- | --- | --- |
| LINEAR_MIN | 4260 | 0.975754 | 0.586206 | 0.000000 | 0.000000 |
| XGB | 4260 | 0.973612 | 0.585540 | -0.002143 | -0.000666 |
| LGBM | 4260 | 0.974027 | 0.585662 | -0.001727 | -0.000544 |
| CAT | 4260 | 0.973691 | 0.585532 | -0.002063 | -0.000675 |
| SELECT | 4260 | 0.975521 | 0.586606 | -0.000233 | 0.000400 |

| model | method | ECE | mean_prediction | actual_frequency | intercept | slope | calibration_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LINEAR_MIN | KO_TKO | 0.017642 | 0.314690 | 0.319484 | -0.096482 | 0.835968 | CONVERGED |
| LINEAR_MIN | SUBMISSION | 0.024725 | 0.158551 | 0.176995 | -0.131681 | 0.829915 | CONVERGED |
| LINEAR_MIN | DECISION | 0.032872 | 0.526759 | 0.503521 | -0.080259 | 0.832109 | CONVERGED |
| XGB | KO_TKO | 0.017369 | 0.310182 | 0.319484 | -0.020870 | 0.911747 | CONVERGED |
| XGB | SUBMISSION | 0.015249 | 0.163059 | 0.176995 | 0.010279 | 0.940452 | CONVERGED |
| XGB | DECISION | 0.032872 | 0.526759 | 0.503521 | -0.080259 | 0.832109 | CONVERGED |
| LGBM | KO_TKO | 0.021600 | 0.310907 | 0.319484 | -0.037852 | 0.893354 | CONVERGED |
| LGBM | SUBMISSION | 0.015641 | 0.162334 | 0.176995 | -0.010284 | 0.923810 | CONVERGED |
| LGBM | DECISION | 0.032872 | 0.526759 | 0.503521 | -0.080259 | 0.832109 | CONVERGED |
| CAT | KO_TKO | 0.018161 | 0.313087 | 0.319484 | -0.063985 | 0.870978 | CONVERGED |
| CAT | SUBMISSION | 0.018866 | 0.160154 | 0.176995 | -0.028274 | 0.901832 | CONVERGED |
| CAT | DECISION | 0.032872 | 0.526759 | 0.503521 | -0.080259 | 0.832109 | CONVERGED |
| SELECT | KO_TKO | 0.016119 | 0.312762 | 0.319484 | -0.082891 | 0.843739 | CONVERGED |
| SELECT | SUBMISSION | 0.018905 | 0.160479 | 0.176995 | -0.087523 | 0.865623 | CONVERGED |
| SELECT | DECISION | 0.032872 | 0.526759 | 0.503521 | -0.080259 | 0.832109 | CONVERGED |

DEC predictions are byte-identical numerically across all surfaces; their calibration is unchanged. Composed LL gains equal 2115/4260 times conditional LL gains, so they are algebraically linked evidence. Summed Brier and classwise calibration expose additional tradeoffs. Annual complete-system results retained in CSV.
