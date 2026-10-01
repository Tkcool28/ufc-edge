# Why SELECT differs from fixed-family shadows

This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.

## Verified behavior

SELECT equals the chosen family shadow prediction in each year, with identical within-family configuration and rounds. It chooses XGB twice, LightGBM four times, CatBoost three times, using pooled preceding two inner validation years. It performs no averaging. The table reconstructs those exact choices and their outer cost/benefit against each always-family procedure.

| year | family | N | selected_by_SELECT | family_outer_LL | SELECT_outer_LL | SELECT_minus_family_LL | inner_family_LL | SELECT_inner_LL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | XGB | 241 | True | 0.599788 | 0.599788 | 0.000000 | 0.601954 | 0.601954 |
| 2018 | LGBM | 241 | False | 0.601978 | 0.599788 | -0.002190 | 0.605343 | 0.601954 |
| 2018 | CAT | 241 | False | 0.599525 | 0.599788 | 0.000263 | 0.605416 | 0.601954 |
| 2019 | XGB | 231 | True | 0.605920 | 0.605920 | 0.000000 | 0.592411 | 0.592411 |
| 2019 | LGBM | 231 | False | 0.599337 | 0.605920 | 0.006583 | 0.592767 | 0.592411 |
| 2019 | CAT | 231 | False | 0.592519 | 0.605920 | 0.013401 | 0.597242 | 0.592411 |
| 2020 | XGB | 220 | False | 0.617205 | 0.629344 | 0.012139 | 0.595209 | 0.593518 |
| 2020 | LGBM | 220 | True | 0.629344 | 0.629344 | 0.000000 | 0.593518 | 0.593518 |
| 2020 | CAT | 220 | False | 0.623931 | 0.629344 | 0.005413 | 0.595321 | 0.593518 |
| 2021 | XGB | 239 | False | 0.605087 | 0.618465 | 0.013378 | 0.602972 | 0.600578 |
| 2021 | LGBM | 239 | False | 0.600801 | 0.618465 | 0.017663 | 0.602388 | 0.600578 |
| 2021 | CAT | 239 | True | 0.618465 | 0.618465 | 0.000000 | 0.600578 | 0.600578 |
| 2022 | XGB | 268 | False | 0.622028 | 0.622689 | 0.000661 | 0.607185 | 0.605931 |
| 2022 | LGBM | 268 | True | 0.622689 | 0.622689 | 0.000000 | 0.605931 | 0.605931 |
| 2022 | CAT | 268 | False | 0.613185 | 0.622689 | 0.009504 | 0.606852 | 0.605931 |
| 2023 | XGB | 258 | False | 0.650704 | 0.650498 | -0.000206 | 0.610977 | 0.606895 |
| 2023 | LGBM | 258 | False | 0.652145 | 0.650498 | -0.001647 | 0.611089 | 0.606895 |
| 2023 | CAT | 258 | True | 0.650498 | 0.650498 | 0.000000 | 0.606895 | 0.606895 |
| 2024 | XGB | 223 | False | 0.618653 | 0.612631 | -0.006022 | 0.628903 | 0.626749 |
| 2024 | LGBM | 223 | False | 0.605564 | 0.612631 | 0.007067 | 0.631167 | 0.626749 |
| 2024 | CAT | 223 | True | 0.612631 | 0.612631 | 0.000000 | 0.626749 | 0.626749 |
| 2025 | XGB | 252 | False | 0.591738 | 0.595219 | 0.003482 | 0.623280 | 0.621729 |
| 2025 | LGBM | 252 | True | 0.595219 | 0.595219 | 0.000000 | 0.621729 | 0.621729 |
| 2025 | CAT | 252 | False | 0.598400 | 0.595219 | -0.003181 | 0.626564 | 0.621729 |
| 2026 | XGB | 183 | False | 0.578090 | 0.592343 | 0.014253 | 0.594897 | 0.591882 |
| 2026 | LGBM | 183 | True | 0.592343 | 0.592343 | 0.000000 | 0.591882 | 0.591882 |
| 2026 | CAT | 183 | False | 0.583046 | 0.592343 | 0.009297 | 0.595849 | 0.591882 |

The all-year performance difference is a weighted sum of the years where SELECT chooses another family; no extra model was trained. A fixed-family shadow still selects configurations inside its family, so it is not one fixed hyperparameter model.

## Hypotheses, not established causes

Short inner windows, correlated near-tied candidates, changing method prevalence, configuration selection variability or family differences may explain why inner winners were less effective in some later years. Better aggregate shadows do not prove selector instability, overfitting or a universally superior library. Nine selections cannot disentangle these explanations. The audit preserves all years and does not select the outer-best family for production.
