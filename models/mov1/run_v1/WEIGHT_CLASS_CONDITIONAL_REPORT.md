# Weight-class conditional MOV1 evaluation

Every division is retained. Rates are matching 2018–2026 OOF outcomes, not the longer 2015+ audit population. The immutable PR117 rates remain structural context only. Mean K here uses actual finishes; all-bout scoring and composition are separate columns in `weight_class_method_composition.csv`. Thin/insufficient rows are retained for transparency, not substantive conclusions.

| Division | All N | Finish N | Finish status | Actual KO \| finish | C1 mean K | MIN mean K | FULL mean K |
|---|---|---|---|---|---|---|---|
| Flyweight | 252 | 121 | NORMAL | 52.1% | 53.5% | 56.0% | 55.5% |
| Bantamweight | 488 | 213 | NORMAL | 61.5% | 59.4% | 64.7% | 65.0% |
| Featherweight | 502 | 239 | NORMAL | 66.5% | 63.6% | 65.5% | 65.7% |
| Lightweight | 576 | 311 | NORMAL | 66.6% | 64.1% | 66.8% | 67.0% |
| Welterweight | 546 | 283 | NORMAL | 67.8% | 66.5% | 69.3% | 69.2% |
| Middleweight | 476 | 270 | NORMAL | 65.9% | 68.9% | 68.9% | 68.2% |
| Light Heavyweight | 319 | 205 | NORMAL | 74.1% | 70.5% | 74.7% | 73.5% |
| Heavyweight | 316 | 187 | NORMAL | 77.5% | 75.7% | 76.9% | 75.8% |
| Women's Strawweight | 275 | 94 | MODERATE_UNCERTAINTY | 44.7% | 44.0% | 50.6% | 51.0% |
| Women's Flyweight | 266 | 95 | MODERATE_UNCERTAINTY | 46.3% | 49.3% | 49.8% | 51.6% |
| Women's Bantamweight | 158 | 56 | MODERATE_UNCERTAINTY | 51.8% | 56.9% | 58.0% | 56.2% |
| Women's Featherweight | 27 | 12 | INSUFFICIENT | 50.0% | 63.3% | 58.0% | 56.3% |
| Catch Weight | 59 | 29 | THIN_EXPLORATORY | 44.8% | 60.3% | 65.5% | 65.6% |

HW is appropriately KO-heavy: MIN76.9% versus actual77.5%, much closer than C0’s64.0%. LHW MIN74.7% versus actual74.1%. Men’s Flyweight remains closer to balanced at56.0% versus52.1%; context alone is closer at53.5%. The model does not simply hard-code a static audit percentage: coefficients and preprocessing are fitted on prior finish histories, and probabilities vary by fighter state and outer fold.

Women’s Strawweight is a limitation: MIN50.6% versus actual44.7%, while C1 is44.0%. Women’s Flyweight MIN49.8% versus46.3%; C1 is49.3%. Both have only94/95 conditional finishes and MODERATE_UNCERTAINTY. MIN does not fully preserve submission concentration in these environments. Women’s Bantamweight also overpredicts KO among56 finishes. Women’s Featherweight has12 finishes and cannot support conditional interpretation. Catch Weight has29 finishes and is THIN_EXPLORATORY, not a standard division.

No division-specific rule or interaction was created, no historical prior was encoded and no subgroup result changed the model.
