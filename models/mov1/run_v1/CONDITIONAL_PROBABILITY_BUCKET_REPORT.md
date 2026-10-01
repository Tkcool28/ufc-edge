# Frozen conditional probability buckets

| Frozen MIN bucket | N | Status | Mean predicted KO | Observed KO | Gap pp | Wilson95 |
|---|---|---|---|---|---|---|
| <0.30 | 32 | THIN_EXPLORATORY | 25.1% | 50.0% | -24.90 | [0.33630882869327483, 0.6636911713067252] |
| 0.30–<0.40 | 69 | MODERATE_UNCERTAINTY | 35.9% | 33.3% | 2.62 | [0.2335105070168671, 0.4507352457128168] |
| 0.40–<0.50 | 208 | NORMAL | 45.5% | 47.6% | -2.13 | [0.40914326914496396, 0.5436516178631351] |
| 0.50–<0.60 | 380 | NORMAL | 55.5% | 53.2% | 2.31 | [0.4813419457751135, 0.5811838691114206] |
| 0.60–<0.70 | 495 | NORMAL | 65.1% | 63.6% | 1.50 | [0.5930867995415912, 0.6775402656569431] |
| 0.70–<0.80 | 518 | NORMAL | 74.8% | 69.9% | 4.94 | [0.6579897929071928, 0.736766117183849] |
| >=0.80 | 413 | NORMAL | 85.8% | 83.3% | 2.50 | [0.7939194363709641, 0.8658038089559656] |

The >=.80 bucket has413 finishes and83.3% actual KO against85.8% predicted. The .70–<.80 bucket has518 and predicts74.8% versus69.9%, an overprediction of4.9 percentage points. The <.30 bucket has32 and is THIN_EXPLORATORY:50.0% actual versus25.1% predicted is a warning, not an established tail failure or a reason to change cutoffs. Keep these boundaries unchanged. Wilson intervals describe observed binomial frequencies; no simultaneous-interval or independent-fighter claim is made.

The complete CSV contains all models, empty buckets, annual coverage, division counts/shares and all15 archetype status counts/shares. Its all-scoring distribution rows do not calculate conditional outcome frequencies using decisions as negatives.
