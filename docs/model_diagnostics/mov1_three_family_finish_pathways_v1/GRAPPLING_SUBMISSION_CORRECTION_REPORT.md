# Grappling and submission correction

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

B1 distinguishes TD attempt pressure against opponent TD defense; B2 uses conversion success against defense; B3 requires submission pressure plus TD access (both high pressure and high conversion); B4 isolates pressure with poor access; B5 uses submission pressure against faced submission-attempt vulnerability. Faced attempts are not identical to historical submission losses. These concepts remain distinct and frozen.

**B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE**: 352 finishes (NORMAL); observed KO 49.7%, SUB 50.3%. XGB: KO 57.6%, SUB 42.4%, gap +7.88 pp; LL delta -0.016935, Brier delta -0.007276; absolute mean gap widens by 0.94 pp. LGBM: KO 57.7%, SUB 42.3%, gap +7.98 pp; LL delta -0.021277, Brier delta -0.009321; absolute mean gap widens by 1.03 pp. CAT: KO 57.4%, SUB 42.6%, gap +7.72 pp; LL delta -0.010008, Brier delta -0.004426; absolute mean gap widens by 0.77 pp.

**B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE**: 341 finishes (NORMAL); observed KO 54.3%, SUB 45.7%. XGB: KO 61.0%, SUB 39.0%, gap +6.71 pp; LL delta -0.016459, Brier delta -0.007447; absolute mean gap widens by 1.41 pp. LGBM: KO 61.0%, SUB 39.0%, gap +6.73 pp; LL delta -0.016292, Brier delta -0.007844; absolute mean gap widens by 1.43 pp. CAT: KO 60.5%, SUB 39.5%, gap +6.21 pp; LL delta -0.014846, Brier delta -0.007469; absolute mean gap widens by 0.91 pp.

**B3_TD_ACCESS_PLUS_SUB_PRESSURE**: 224 finishes (NORMAL); observed KO 46.0%, SUB 54.0%. XGB: KO 57.5%, SUB 42.5%, gap +11.50 pp; LL delta -0.010396, Brier delta -0.004135; absolute mean gap widens by 2.27 pp. LGBM: KO 57.1%, SUB 42.9%, gap +11.16 pp; LL delta -0.017031, Brier delta -0.007382; absolute mean gap widens by 1.93 pp. CAT: KO 57.2%, SUB 42.8%, gap +11.27 pp; LL delta -0.019306, Brier delta -0.008473; absolute mean gap widens by 2.04 pp.

**B4_SUB_PRESSURE_POOR_TD_ACCESS**: 861 finishes (NORMAL); observed KO 57.3%, SUB 42.7%. XGB: KO 59.6%, SUB 40.4%, gap +2.38 pp; LL delta -0.010425, Brier delta -0.004360; absolute mean gap narrows by 1.22 pp. LGBM: KO 59.5%, SUB 40.5%, gap +2.28 pp; LL delta -0.005741, Brier delta -0.002317; absolute mean gap narrows by 1.32 pp. CAT: KO 59.5%, SUB 40.5%, gap +2.28 pp; LL delta -0.003594, Brier delta -0.001315; absolute mean gap narrows by 1.32 pp.

**B5_SUB_PRESSURE_VS_SUB_VULNERABILITY**: 355 finishes (NORMAL); observed KO 45.1%, SUB 54.9%. XGB: KO 53.3%, SUB 46.7%, gap +8.20 pp; LL delta -0.018359, Brier delta -0.008405; absolute mean gap narrows by 0.78 pp. LGBM: KO 53.1%, SUB 46.9%, gap +8.02 pp; LL delta -0.016468, Brier delta -0.007538; absolute mean gap narrows by 0.96 pp. CAT: KO 52.6%, SUB 47.4%, gap +7.53 pp; LL delta -0.019270, Brier delta -0.008752; absolute mean gap narrows by 1.45 pp.

No mean-rate target was optimized. Improved loss with a wider group mean gap is possible when individual assignments improve despite residual aggregate bias.
