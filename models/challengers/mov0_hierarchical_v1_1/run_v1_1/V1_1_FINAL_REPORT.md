# V1.1 inference amendment and completed challenger

Status: MOV0_HIERARCHICAL_PARTIAL_POOLING_CHALLENGER_V1_1_COMPLETE.
Inference: V1_1_CONVERGENCE_VALIDATED.
Scientific classification: CURRENT_SPECIFICATION_NOT_SUPPORTED for both tested challengers versus frozen MOV0-MIN; H2 versus H1 is INCONCLUSIVE.

Starting main: 378ba0576426cd01bd73cbaff774b782c8fb2f6b. Draft PR #116, branch feat/mov0-hierarchical-partial-pooling-v1-1. No merge.
PR #115 remains the permanent BLOCKED_CONVERGENCE record. Scientific freeze bc5f9df5436402915915aa34da304bbfa46cbccb; V1 blocked head 454ae18ea28ad8086aed1024941b831295d67d91. V1.1 amendment freeze 30b14dc5b355e9356dbdd80c793ab6d6feedf861 preceded inference and performance interpretation. Executed implementation published at 3194d899a69b5cb3bfd12ac6a5e47b891644343c; execution_identity.json records the executed bytes.

Only tune and retained draws changed, from 1000/1000 to 2000/2000 per chain for every fit. Four chains, PyMC 5.18.2, jitter+adapt_diag, target_accept .95, max_treedepth 12, seeds, proper priors, likelihood, noncentered hierarchy, seven slopes, categorical normalization, training-only preprocessing and prior-history folds remain fixed. Source hash and AST checks demonstrate unchanged scientific functions and unchanged evaluator. SCIENTIFIC_SPECIFICATION_PROOF.json, amendment.json and the byte-identical V1 contract/lock/maps make the comparison reviewable.

All 18 fits passed before evaluation began. H1/2018 identical-environment repeat produced identical posterior arrays and predictions (maximum delta zero). All 18 fighter-order swaps had zero probability change; reloaded traces reproduce persisted probabilities within 1.12e-16. Cross-platform bitwise identity is not claimed. Full parameter diagnostics, preprocessing and posterior summaries accompany the evidence.

## All convergence results

| Surface | Year | Min bulk ESS | Min tail ESS | Max rank R-hat | Min BFMI | Divergences | Depth hits | Passed |
|---|---|---|---|---|---|---|---|---|
| H1 | 2018 | 3041.117 | 3793.764 | 1.001356 | 0.852701 | 0 | 0 | True |
| H2 | 2018 | 2072.647 | 2751.759 | 1.002305 | 0.890431 | 0 | 0 | True |
| H1 | 2019 | 2524.936 | 2992.599 | 1.001320 | 0.811863 | 0 | 0 | True |
| H2 | 2019 | 1583.724 | 1505.975 | 1.002822 | 0.776975 | 0 | 0 | True |
| H1 | 2020 | 1872.196 | 1562.605 | 1.001417 | 0.755415 | 0 | 0 | True |
| H2 | 2020 | 1314.443 | 1748.261 | 1.002342 | 0.819752 | 0 | 0 | True |
| H1 | 2021 | 2028.687 | 1926.825 | 1.001895 | 0.798208 | 0 | 0 | True |
| H2 | 2021 | 1190.722 | 1223.903 | 1.003446 | 0.788288 | 0 | 0 | True |
| H1 | 2022 | 1477.224 | 1343.362 | 1.002862 | 0.739459 | 0 | 0 | True |
| H2 | 2022 | 2086.328 | 2780.994 | 1.003764 | 0.825834 | 0 | 0 | True |
| H1 | 2023 | 1461.233 | 1440.293 | 1.001863 | 0.702640 | 0 | 0 | True |
| H2 | 2023 | 1189.330 | 1219.663 | 1.002306 | 0.758068 | 0 | 0 | True |
| H1 | 2024 | 1854.794 | 2481.976 | 1.001572 | 0.777311 | 0 | 0 | True |
| H2 | 2024 | 1364.328 | 1482.906 | 1.003151 | 0.775257 | 0 | 0 | True |
| H1 | 2025 | 1741.110 | 2728.464 | 1.002699 | 0.784892 | 0 | 0 | True |
| H2 | 2025 | 1655.027 | 2746.628 | 1.002218 | 0.778100 | 0 | 0 | True |
| H1 | 2026 | 2206.277 | 3889.199 | 1.001972 | 0.835059 | 0 | 0 | True |
| H2 | 2026 | 1859.693 | 1726.415 | 1.003097 | 0.807525 | 0 | 0 | True |

H2/2021 now has bulk ESS 1190.722 and tail ESS 1223.903, versus V1's 397.522 and 351.557. The authorized budget therefore removed the observed blocker for this environment and seed policy. No selective retries or gate exceptions were used.

## Scientific conclusion and tradeoffs

Across 4260 untouched chronological OOF fights, H1 log loss is worse by +.002349 and H2 by +.002346. Both fight and event-cluster 95% intervals lie above zero. H1 improves only two of nine years; H2 improves three. Both worsen Brier, fixed-bin ECE and calibration slope versus MIN. H2 and H1 are effectively tied in aggregate, with uncertainty spanning improvements and regressions. The strongest adverse annual mean contribution is 2018 for both; favorable H1 is 2025 and favorable H2 annual mean is 2026 (largest favorable summed contribution is 2025). Annual and paired_uncertainty files retain every delta and contribution.

Heavyweight (N311) log loss rises from .656784 to .657028/.659281; Light Heavyweight (N319) from .660121 to .662068/.663492; Flyweight (N248) from .696083 to .699976/.700578. Their NORMAL-sized immutable terrain cells do not support improvement. H2 helps Bantamweight and both models help Women's Bantamweight, but Lightweight and most other divisions worsen. Do not combine interim labels into evaluation cells: model normalization and immutable terrain labels serve distinct preregistered purposes.

Three-round and five-round log loss worsen for both models. Long layoffs worsen, especially H2 at 18+ months (+.008367). High missingness improves log loss modestly (H1 -.000347, H2 -.001289), while its ECE and calibration slope worsen. All three striking and all three grappling environments worsen log loss; two-sided grappling worsens particularly. Full terrain metrics include prevalence, mean prediction, calibration, discrimination, uncertainty and governance.

Probability tails expand rather than compress: N below .30 moves 383 -> 425/436; N at least .70 moves 212 -> 246/263. Top-band overconfidence grows from 7.554 percentage points to 9.278/9.078. Low-tail underprediction also grows. Observed finish rates remain monotonic across all six immutable bands for H0/H1/H2. H2 has smaller absolute gaps in .30–<.40, .50–<.60 and .60–<.70, but worse tails and .40–<.50; this does not establish useful new tails. probability_buckets.json also retains fixed-H0-membership comparisons so movement between bands is visible.

The exact PR #113 archetypes are evaluation panels only. KD-creation/weak-defense and KO-history/vulnerability calibration are essentially retained by H1 and modestly worsened by H2. Takedown-access/submission-pressure worsens slightly for both; submission-pressure/vulnerability improves slightly but remains underpredicted by about 6.4 percentage points. High-finish-pressure/five-round overprediction worsens. Experience/strong-defense overprediction improves from 11.545 to 10.914/10.923 percentage points, leaving a large miss. Low-damage/strong-defense also improves, with limited N74. No claim is based on N-only cells, and archetypes overlap. Historical FULL strengths quoted in the motivation are context; this experiment's primary reference remains immutable MIN.

## Interpretation boundaries

The larger inference budget succeeded computationally; the tested scientific specification did not improve generalization. This does not reject hierarchical modeling broadly. H1 versus H0 also changes Bayesian global regularization and normalized label pooling relative to frozen ridge; it is not an isolated causal estimate of intercept hierarchy. H2 versus H1 more directly isolates the added slope hierarchy and provides no convincing aggregate benefit. 2026 is incomplete. Paired bootstraps condition on fitted OOF predictions and exclude refit uncertainty. Repeated fighters, correlated events, overlapping subgroup panels, conditional feature collinearity and one prior specification limit subgroup inference. No outcome-driven tuning, recalibration or architecture selection occurred.

See REPORT.md for complete annual metrics, terrain log loss, six-band N/means/prevalence/Wilson95/year coverage and every archetype's probabilities and gaps. Machine evidence retains all secondary metrics and posterior intervals. HELPED_HURT_UNCHANGED.md records directional costs and gains without an arbitrary success cutoff.
