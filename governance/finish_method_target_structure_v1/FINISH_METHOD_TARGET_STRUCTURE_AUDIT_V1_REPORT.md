# FINISH-METHOD TARGET STRUCTURE + WEIGHT-CLASS ENVIRONMENT AUDIT V1

Status: **FINISH_METHOD_TARGET_STRUCTURE_AUDIT_V1_COMPLETE**

## Scope, freeze, and sources

Starting exact main: `44aa8dc97b57192ae90e847767051a03f38acd3d` (merged #116). Branch: `audit/finish-method-target-structure-v1`. No automatic merge.

The audit contract was published at commit `6264fc89e9c493f0fd5a6d2cdbde87f98c9598f0` before outcome aggregation. It fixes the population policy, all divisions, four eras, rounds, all 15 #113 archetypes, all 17 existing state concepts, terrain dimensions, comparisons, missingness and sample governance. No categories or thresholds were changed after observing outcomes.

Read context: PROJECT_STATUS, PROJECT_MAP, MODELING_RESET_CHECKLIST, MASTER_MILESTONES, DECISIONS; frozen MOV0 contracts/report; merged #111/#112/#113; completed #116. The attached master plan, Sacramento postmortem, Step 2 direction, target-feasibility audit and simulator-feasibility research informed interpretation boundaries. #116 predictive results were not used to choose audit categories. Neither its predictions nor MOV0 probabilities are inputs to this audit.

This is a descriptive audit of observed outcomes, not an out-of-sample performance estimate, causal analysis, model-selection test or feature build. Wilson intervals are marginal binomial intervals; repeated fighters/events and simultaneous inspection mean they are not independent, simultaneous or causal uncertainty guarantees.

## Exact population and exclusions

Canonical UFC, 2015+; same frozen corrected F02 identity and MOV0 standard-method label policy. Canonical and F02 modern candidates reconcile one-to-one at **5,729**; **5,658** eligible; no eligible canonical bout is lost at the F02 or terrain join. Date coverage: **2015-01-03 through 2026-08-15**, not all of 2026. This is the full modern label population; the older #113 diagnostic used only the 4,260 outer OOF bouts in 2018–2026. Different N here reflects the authorized population expansion, not a new label taxonomy.

- KO_TKO: **1,812**; SUBMISSION: **1,010**; DECISION: **2,836**.
- Decision draws included: **45**, as in MOV0.
- Excluded: `win_loss|DQ` 13; `no_contest|NO_CONTEST` 32; `no_contest|OTHER` 25; `draw|NO_CONTEST` 1. Total **71**. No coercion of ambiguous results.
- Pre-2015 and non-UFC rows are outside the candidate population, not hidden label exclusions.
- The prior governed literal weight-class map strips interim/tournament wrappers. All **46** observed modern raw labels remain in `canonical_weight_class.csv`. Twelve canonical divisions are reported; 70 Catch Weight bouts remain a separate reference and in the UFC-wide denominator. No missing labels were imputed.
- All scheduled rounds reconcile between F02 and canonical data: 5,102 three-round and 556 five-round fights.

Sample gates: N≥100 NORMAL; 50–99 MODERATE_UNCERTAINTY; 25–49 THIN_EXPLORATORY; <25 INSUFFICIENT. Every table retains small and zero cells. Conditional shares use **finish_N**, with their own gate. A large bout N does not make a conditional share precise when few bouts finish. Zero denominators produce missing rates, not artificial zeroes.

## All-division method distribution

Rates below include Wilson 95% intervals in brackets. Counts are outcomes, not rankings.

| Division | N | KO N | SUB N | DEC N | KO rate [95%] | SUB rate [95%] | DEC rate [95%] |
|---|---|---|---|---|---|---|---|
| UFC-wide | 5658 | 1812 | 1010 | 2836 | 32.0% [30.8%, 33.3%] | 17.9% [16.9%, 18.9%] | 50.1% [48.8%, 51.4%] |
| Flyweight | 338 | 77 | 75 | 186 | 22.8% [18.6%, 27.5%] | 22.2% [18.1%, 26.9%] | 55.0% [49.7%, 60.2%] |
| Bantamweight | 604 | 161 | 108 | 335 | 26.7% [23.3%, 30.3%] | 17.9% [15.0%, 21.1%] | 55.5% [51.5%, 59.4%] |
| Featherweight | 651 | 201 | 105 | 345 | 30.9% [27.4%, 34.5%] | 16.1% [13.5%, 19.2%] | 53.0% [49.2%, 56.8%] |
| Lightweight | 831 | 280 | 153 | 398 | 33.7% [30.6%, 37.0%] | 18.4% [15.9%, 21.2%] | 47.9% [44.5%, 51.3%] |
| Welterweight | 799 | 277 | 136 | 386 | 34.7% [31.4%, 38.0%] | 17.0% [14.6%, 19.8%] | 48.3% [44.9%, 51.8%] |
| Middleweight | 641 | 254 | 116 | 271 | 39.6% [35.9%, 43.5%] | 18.1% [15.3%, 21.3%] | 42.3% [38.5%, 46.1%] |
| Light Heavyweight | 421 | 198 | 72 | 151 | 47.0% [42.3%, 51.8%] | 17.1% [13.8%, 21.0%] | 35.9% [31.4%, 40.6%] |
| Heavyweight | 420 | 200 | 56 | 164 | 47.6% [42.9%, 52.4%] | 13.3% [10.4%, 16.9%] | 39.0% [34.5%, 43.8%] |
| Women's Strawweight | 360 | 49 | 72 | 239 | 13.6% [10.5%, 17.5%] | 20.0% [16.2%, 24.4%] | 66.4% [61.4%, 71.1%] |
| Women's Flyweight | 277 | 46 | 55 | 176 | 16.6% [12.7%, 21.4%] | 19.9% [15.6%, 25.0%] | 63.5% [57.7%, 69.0%] |
| Women's Bantamweight | 216 | 43 | 39 | 134 | 19.9% [15.1%, 25.7%] | 18.1% [13.5%, 23.7%] | 62.0% [55.4%, 68.2%] |
| Women's Featherweight | 30 | 7 | 6 | 17 | 23.3% [11.8%, 40.9%] | 20.0% [9.5%, 37.3%] | 56.7% [39.2%, 72.6%] |
| Catch Weight | 70 | 19 | 17 | 34 | 27.1% [18.1%, 38.5%] | 24.3% [15.8%, 35.5%] | 48.6% [37.2%, 60.0%] |

| Division | Finish N | Finish rate [95%] | KO share of finishes [95%] | SUB share of finishes [95%] | Bout / finish gate |
|---|---|---|---|---|---|
| UFC-wide | 2822 | 49.9% [48.6%, 51.2%] | 64.2% [62.4%, 66.0%] | 35.8% [34.0%, 37.6%] | NORMAL / NORMAL |
| Flyweight | 152 | 45.0% [39.8%, 50.3%] | 50.7% [42.8%, 58.5%] | 49.3% [41.5%, 57.2%] | NORMAL / NORMAL |
| Bantamweight | 269 | 44.5% [40.6%, 48.5%] | 59.9% [53.9%, 65.5%] | 40.1% [34.5%, 46.1%] | NORMAL / NORMAL |
| Featherweight | 306 | 47.0% [43.2%, 50.8%] | 65.7% [60.2%, 70.8%] | 34.3% [29.2%, 39.8%] | NORMAL / NORMAL |
| Lightweight | 433 | 52.1% [48.7%, 55.5%] | 64.7% [60.1%, 69.0%] | 35.3% [31.0%, 39.9%] | NORMAL / NORMAL |
| Welterweight | 413 | 51.7% [48.2%, 55.1%] | 67.1% [62.4%, 71.4%] | 32.9% [28.6%, 37.6%] | NORMAL / NORMAL |
| Middleweight | 370 | 57.7% [53.9%, 61.5%] | 68.6% [63.8%, 73.2%] | 31.4% [26.8%, 36.2%] | NORMAL / NORMAL |
| Light Heavyweight | 270 | 64.1% [59.4%, 68.6%] | 73.3% [67.8%, 78.3%] | 26.7% [21.7%, 32.2%] | NORMAL / NORMAL |
| Heavyweight | 256 | 61.0% [56.2%, 65.5%] | 78.1% [72.7%, 82.8%] | 21.9% [17.2%, 27.3%] | NORMAL / NORMAL |
| Women's Strawweight | 121 | 33.6% [28.9%, 38.6%] | 40.5% [32.2%, 49.4%] | 59.5% [50.6%, 67.8%] | NORMAL / NORMAL |
| Women's Flyweight | 101 | 36.5% [31.0%, 42.3%] | 45.5% [36.2%, 55.2%] | 54.5% [44.8%, 63.8%] | NORMAL / NORMAL |
| Women's Bantamweight | 82 | 38.0% [31.8%, 44.6%] | 52.4% [41.8%, 62.9%] | 47.6% [37.1%, 58.2%] | NORMAL / MODERATE_UNCERTAINTY |
| Women's Featherweight | 13 | 43.3% [27.4%, 60.8%] | 53.8% [29.1%, 76.8%] | 46.2% [23.2%, 70.9%] | THIN_EXPLORATORY / INSUFFICIENT |
| Catch Weight | 36 | 51.4% [40.0%, 62.8%] | 52.8% [37.0%, 68.0%] | 47.2% [32.0%, 63.0%] | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |

Heavyweight: KO rate **47.6%**, +15.6 percentage points versus UFC-wide 32.0%; finish rate **61.0%**, +11.1 pp; KO share among finishes **78.1%**, +13.9 pp. Both components contribute. A symmetric arithmetic decomposition of the 15.6 pp KO-rate difference attributes about **7.9 pp** to finish prevalence and **7.7 pp** to conditional KO share: Δ(F×K) = ΔF×mean(K) + ΔK×mean(F). This identity is descriptive, not a causal attribution.

Light Heavyweight: KO **47.0%**, finish **64.1%**, conditional KO **73.3%**. It has a higher generic finish rate than Heavyweight but a lower conditional KO share. The two divisions therefore share a KO-heavy environment without being identical.

Flyweight: KO **22.8%**, SUB **22.2%**, decision **55.0%**. Its 152 finishes are almost evenly split: 50.7% KO and 49.3% submission; UFC-wide is 64.2% / 35.8%. This is a method-composition difference, not merely a lower overall finish rate.

Women's Strawweight (59.5% SUB among finishes) and Women's Flyweight (54.5%) are submission-majority in the aggregate. Relative submission enrichment is more defensible than a claim of permanent majority in each era. Women's Bantamweight and men's Flyweight are also more submission-weighted than UFC-wide; Women's Bantamweight has only 82 finishes and much less stable conditional mix. Women's Featherweight's 13 finishes are insufficient for substantive conclusions. Catch Weight is heterogeneous, not a model division.

Decision-heavy aggregate environments include Women's Strawweight 66.4%, Women's Flyweight 63.5%, Women's Bantamweight 62.0%, men's Bantamweight 55.5%, and men's Flyweight 55.0%. The era table qualifies persistence rather than treating every aggregate majority as permanent.

## Fixed time-stability view

No windows were merged, split or selected using outcomes. The last window ends at the data cutoff in August 2026. Table shows all divisions and the UFC-wide reference; conditional denominator gates are explicit. Full Wilson intervals and era-matched absolute pp deltas are in `weight_class_era.csv`.

| Division | Era | N / finishes | KO | SUB | DEC | KO / finish | SUB / finish | Bout / finish gate |
|---|---|---|---|---|---|---|---|---|
| Flyweight | 2015–2017 | 86 / 31 | 16.3% | 19.8% | 64.0% | 45.2% | 54.8% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Flyweight | 2018–2020 | 60 / 29 | 26.7% | 21.7% | 51.7% | 55.2% | 44.8% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Flyweight | 2021–2023 | 92 / 47 | 26.1% | 25.0% | 48.9% | 51.1% | 48.9% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Flyweight | 2024–2026 | 100 / 45 | 23.0% | 22.0% | 55.0% | 51.1% | 48.9% | NORMAL / THIN_EXPLORATORY |
| Bantamweight | 2015–2017 | 116 / 56 | 25.9% | 22.4% | 51.7% | 53.6% | 46.4% | NORMAL / MODERATE_UNCERTAINTY |
| Bantamweight | 2018–2020 | 161 / 78 | 29.8% | 18.6% | 51.6% | 61.5% | 38.5% | NORMAL / MODERATE_UNCERTAINTY |
| Bantamweight | 2021–2023 | 170 / 84 | 34.1% | 15.3% | 50.6% | 69.0% | 31.0% | NORMAL / MODERATE_UNCERTAINTY |
| Bantamweight | 2024–2026 | 157 / 51 | 15.9% | 16.6% | 67.5% | 49.0% | 51.0% | NORMAL / MODERATE_UNCERTAINTY |
| Featherweight | 2015–2017 | 149 / 67 | 28.2% | 16.8% | 55.0% | 62.7% | 37.3% | NORMAL / MODERATE_UNCERTAINTY |
| Featherweight | 2018–2020 | 174 / 76 | 27.6% | 16.1% | 56.3% | 63.2% | 36.8% | NORMAL / MODERATE_UNCERTAINTY |
| Featherweight | 2021–2023 | 171 / 76 | 29.8% | 14.6% | 55.6% | 67.1% | 32.9% | NORMAL / MODERATE_UNCERTAINTY |
| Featherweight | 2024–2026 | 157 / 87 | 38.2% | 17.2% | 44.6% | 69.0% | 31.0% | NORMAL / MODERATE_UNCERTAINTY |
| Lightweight | 2015–2017 | 255 / 122 | 28.6% | 19.2% | 52.2% | 59.8% | 40.2% | NORMAL / NORMAL |
| Lightweight | 2018–2020 | 195 / 96 | 32.8% | 16.4% | 50.8% | 66.7% | 33.3% | NORMAL / MODERATE_UNCERTAINTY |
| Lightweight | 2021–2023 | 202 / 120 | 40.1% | 19.3% | 40.6% | 67.5% | 32.5% | NORMAL / NORMAL |
| Lightweight | 2024–2026 | 179 / 95 | 34.6% | 18.4% | 46.9% | 65.3% | 34.7% | NORMAL / MODERATE_UNCERTAINTY |
| Welterweight | 2015–2017 | 253 / 130 | 33.6% | 17.8% | 48.6% | 65.4% | 34.6% | NORMAL / NORMAL |
| Welterweight | 2018–2020 | 207 / 103 | 34.3% | 15.5% | 50.2% | 68.9% | 31.1% | NORMAL / NORMAL |
| Welterweight | 2021–2023 | 181 / 93 | 30.4% | 21.0% | 48.6% | 59.1% | 40.9% | NORMAL / MODERATE_UNCERTAINTY |
| Welterweight | 2024–2026 | 158 / 87 | 41.8% | 13.3% | 44.9% | 75.9% | 24.1% | NORMAL / MODERATE_UNCERTAINTY |
| Middleweight | 2015–2017 | 165 / 100 | 46.1% | 14.5% | 39.4% | 76.0% | 24.0% | NORMAL / NORMAL |
| Middleweight | 2018–2020 | 132 / 70 | 34.1% | 18.9% | 47.0% | 64.3% | 35.7% | NORMAL / MODERATE_UNCERTAINTY |
| Middleweight | 2021–2023 | 172 / 100 | 38.4% | 19.8% | 41.9% | 66.0% | 34.0% | NORMAL / NORMAL |
| Middleweight | 2024–2026 | 172 / 100 | 39.0% | 19.2% | 41.9% | 67.0% | 33.0% | NORMAL / NORMAL |
| Light Heavyweight | 2015–2017 | 102 / 65 | 45.1% | 18.6% | 36.3% | 70.8% | 29.2% | NORMAL / MODERATE_UNCERTAINTY |
| Light Heavyweight | 2018–2020 | 118 / 77 | 45.8% | 19.5% | 34.7% | 70.1% | 29.9% | NORMAL / MODERATE_UNCERTAINTY |
| Light Heavyweight | 2021–2023 | 106 / 62 | 45.3% | 13.2% | 41.5% | 77.4% | 22.6% | NORMAL / MODERATE_UNCERTAINTY |
| Light Heavyweight | 2024–2026 | 95 / 66 | 52.6% | 16.8% | 30.5% | 75.8% | 24.2% | MODERATE_UNCERTAINTY / MODERATE_UNCERTAINTY |
| Heavyweight | 2015–2017 | 104 / 69 | 52.9% | 13.5% | 33.7% | 79.7% | 20.3% | NORMAL / MODERATE_UNCERTAINTY |
| Heavyweight | 2018–2020 | 114 / 72 | 47.4% | 15.8% | 36.8% | 75.0% | 25.0% | NORMAL / MODERATE_UNCERTAINTY |
| Heavyweight | 2021–2023 | 107 / 64 | 47.7% | 12.1% | 40.2% | 79.7% | 20.3% | NORMAL / MODERATE_UNCERTAINTY |
| Heavyweight | 2024–2026 | 95 / 51 | 42.1% | 11.6% | 46.3% | 78.4% | 21.6% | MODERATE_UNCERTAINTY / MODERATE_UNCERTAINTY |
| Women's Strawweight | 2015–2017 | 85 / 27 | 8.2% | 23.5% | 68.2% | 25.9% | 74.1% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Women's Strawweight | 2018–2020 | 88 / 26 | 10.2% | 19.3% | 70.5% | 34.6% | 65.4% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Women's Strawweight | 2021–2023 | 99 / 40 | 23.2% | 17.2% | 59.6% | 57.5% | 42.5% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Women's Strawweight | 2024–2026 | 88 / 28 | 11.4% | 20.5% | 68.2% | 35.7% | 64.3% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Women's Flyweight | 2015–2017 | 11 / 6 | 18.2% | 36.4% | 45.5% | 33.3% | 66.7% | INSUFFICIENT / INSUFFICIENT |
| Women's Flyweight | 2018–2020 | 93 / 35 | 15.1% | 22.6% | 62.4% | 40.0% | 60.0% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Women's Flyweight | 2021–2023 | 109 / 43 | 20.2% | 19.3% | 60.6% | 51.2% | 48.8% | NORMAL / THIN_EXPLORATORY |
| Women's Flyweight | 2024–2026 | 64 / 17 | 12.5% | 14.1% | 73.4% | 47.1% | 52.9% | MODERATE_UNCERTAINTY / INSUFFICIENT |
| Women's Bantamweight | 2015–2017 | 58 / 26 | 24.1% | 20.7% | 55.2% | 53.8% | 46.2% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Women's Bantamweight | 2018–2020 | 53 / 16 | 22.6% | 7.5% | 69.8% | 75.0% | 25.0% | MODERATE_UNCERTAINTY / INSUFFICIENT |
| Women's Bantamweight | 2021–2023 | 51 / 17 | 13.7% | 19.6% | 66.7% | 41.2% | 58.8% | MODERATE_UNCERTAINTY / INSUFFICIENT |
| Women's Bantamweight | 2024–2026 | 54 / 23 | 18.5% | 24.1% | 57.4% | 43.5% | 56.5% | MODERATE_UNCERTAINTY / INSUFFICIENT |
| Women's Featherweight | 2015–2017 | 3 / 1 | 33.3% | 0.0% | 66.7% | 100.0% | 0.0% | INSUFFICIENT / INSUFFICIENT |
| Women's Featherweight | 2018–2020 | 12 / 8 | 41.7% | 25.0% | 33.3% | 62.5% | 37.5% | INSUFFICIENT / INSUFFICIENT |
| Women's Featherweight | 2021–2023 | 14 / 4 | 7.1% | 21.4% | 71.4% | 25.0% | 75.0% | INSUFFICIENT / INSUFFICIENT |
| Women's Featherweight | 2024–2026 | 1 / 0 | 0.0% | 0.0% | 100.0% | — | — | INSUFFICIENT / INSUFFICIENT |
| Catch Weight | 2015–2017 | 11 / 7 | 54.5% | 9.1% | 36.4% | 85.7% | 14.3% | INSUFFICIENT / INSUFFICIENT |
| Catch Weight | 2018–2020 | 13 / 6 | 7.7% | 38.5% | 53.8% | 16.7% | 83.3% | INSUFFICIENT / INSUFFICIENT |
| Catch Weight | 2021–2023 | 28 / 15 | 28.6% | 25.0% | 46.4% | 53.3% | 46.7% | THIN_EXPLORATORY / INSUFFICIENT |
| Catch Weight | 2024–2026 | 18 / 8 | 22.2% | 22.2% | 55.6% | 50.0% | 50.0% | INSUFFICIENT / INSUFFICIENT |
| UFC-wide | 2015–2017 | 1398 / 707 | 32.3% | 18.3% | 49.4% | 63.8% | 36.2% | NORMAL / NORMAL |
| UFC-wide | 2018–2020 | 1420 / 692 | 31.1% | 17.7% | 51.3% | 63.7% | 36.3% | NORMAL / NORMAL |
| UFC-wide | 2021–2023 | 1502 / 765 | 33.0% | 18.0% | 49.1% | 64.7% | 35.3% | NORMAL / NORMAL |
| UFC-wide | 2024–2026 | 1338 / 658 | 31.8% | 17.4% | 50.8% | 64.6% | 35.4% | NORMAL / NORMAL |

The UFC-wide mix is quite stable: KO 31.1–33.0%, submission 17.4–18.3%, conditional KO 63.7–64.7%. This does not imply every division is stable.

Heavyweight KO rates remain above era-matched UFC-wide in all four windows (52.9%, 47.4%, 47.7%, 42.1%); conditional KO remains 75.0–79.7%. Generic finish declines from 66.3% to 53.7%, so a fixed numerical division prevalence is not timeless. Light Heavyweight KO rates remain 45.1–52.6%, with conditional KO 70.1–77.4%; both exceed the era reference throughout. Men's Middleweight also retains elevated KO and finish prevalence across windows, without establishing an ordinal weight trend or separate slope structure.

Flyweight's conditional KO stays 45.2–55.2%, below every era reference, with only 29–47 finishes per era: repeated direction but THIN_EXPLORATORY era-level conditional precision. Its overall finish prevalence varies from 36.0% to 51.1%; a universal decision-heavy claim is weaker than the composition finding.

Women's Strawweight and Women's Flyweight remain more submission-weighted than the UFC reference in adequately covered eras, but Women's Strawweight reverses its own majority in 2021–2023 (57.5% KO). Women's Flyweight has only 11 bouts in 2015–2017 and 17 finishes in 2024–2026; those cells remain insufficient. Women's Bantamweight's conditional KO varies 41.2–75.0%, with 16–26 finishes per era: no stable submission-majority claim. Its decision rate remains above era reference throughout. Women's Strawweight and post-2017 Women's Flyweight are persistently decision-heavy.

Men's Bantamweight is strongly decision-heavy in 2024–2026 (67.5%) but nearer 50/50 earlier. Featherweight changes from decision-majority in the first three eras to finish-majority in the last. Welterweight conditional KO reaches 75.9% late versus 59.1% in 2021–2023. These patterns argue against hard-coded permanent per-division probabilities.

## Round-structure view

Scheduled rounds are associated with selection into title/main-event environments; the table does not identify the effect of adding two rounds. Full Wilson intervals and round-matched deltas are in `weight_class_rounds.csv`; division × era × rounds is also retained.

| Division | Rounds | N / finishes | KO | SUB | DEC | KO / finish | SUB / finish | Bout / finish gate |
|---|---|---|---|---|---|---|---|---|
| Flyweight | 3 | 302 / 131 | 21.5% | 21.9% | 56.6% | 49.6% | 50.4% | NORMAL / NORMAL |
| Flyweight | 5 | 36 / 21 | 33.3% | 25.0% | 41.7% | 57.1% | 42.9% | THIN_EXPLORATORY / INSUFFICIENT |
| Bantamweight | 3 | 562 / 250 | 26.0% | 18.5% | 55.5% | 58.4% | 41.6% | NORMAL / NORMAL |
| Bantamweight | 5 | 42 / 19 | 35.7% | 9.5% | 54.8% | 78.9% | 21.1% | THIN_EXPLORATORY / INSUFFICIENT |
| Featherweight | 3 | 595 / 276 | 29.2% | 17.1% | 53.6% | 63.0% | 37.0% | NORMAL / NORMAL |
| Featherweight | 5 | 56 / 30 | 48.2% | 5.4% | 46.4% | 90.0% | 10.0% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Lightweight | 3 | 771 / 388 | 32.6% | 17.8% | 49.7% | 64.7% | 35.3% | NORMAL / NORMAL |
| Lightweight | 5 | 60 / 45 | 48.3% | 26.7% | 25.0% | 64.4% | 35.6% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Welterweight | 3 | 724 / 377 | 34.5% | 17.5% | 47.9% | 66.3% | 33.7% | NORMAL / NORMAL |
| Welterweight | 5 | 75 / 36 | 36.0% | 12.0% | 52.0% | 75.0% | 25.0% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Middleweight | 3 | 567 / 333 | 39.7% | 19.0% | 41.3% | 67.6% | 32.4% | NORMAL / NORMAL |
| Middleweight | 5 | 74 / 37 | 39.2% | 10.8% | 50.0% | 78.4% | 21.6% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Light Heavyweight | 3 | 366 / 231 | 46.4% | 16.7% | 36.9% | 73.6% | 26.4% | NORMAL / NORMAL |
| Light Heavyweight | 5 | 55 / 39 | 50.9% | 20.0% | 29.1% | 71.8% | 28.2% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Heavyweight | 3 | 352 / 199 | 43.5% | 13.1% | 43.5% | 76.9% | 23.1% | NORMAL / NORMAL |
| Heavyweight | 5 | 68 / 57 | 69.1% | 14.7% | 16.2% | 82.5% | 17.5% | MODERATE_UNCERTAINTY / MODERATE_UNCERTAINTY |
| Women's Strawweight | 3 | 329 / 108 | 12.8% | 20.1% | 67.2% | 38.9% | 61.1% | NORMAL / NORMAL |
| Women's Strawweight | 5 | 31 / 13 | 22.6% | 19.4% | 58.1% | 53.8% | 46.2% | THIN_EXPLORATORY / INSUFFICIENT |
| Women's Flyweight | 3 | 255 / 95 | 16.5% | 20.8% | 62.7% | 44.2% | 55.8% | NORMAL / MODERATE_UNCERTAINTY |
| Women's Flyweight | 5 | 22 / 6 | 18.2% | 9.1% | 72.7% | 66.7% | 33.3% | INSUFFICIENT / INSUFFICIENT |
| Women's Bantamweight | 3 | 193 / 69 | 18.7% | 17.1% | 64.2% | 52.2% | 47.8% | NORMAL / MODERATE_UNCERTAINTY |
| Women's Bantamweight | 5 | 23 / 13 | 30.4% | 26.1% | 43.5% | 53.8% | 46.2% | INSUFFICIENT / INSUFFICIENT |
| Women's Featherweight | 3 | 22 / 9 | 18.2% | 22.7% | 59.1% | 44.4% | 55.6% | INSUFFICIENT / INSUFFICIENT |
| Women's Featherweight | 5 | 8 / 4 | 37.5% | 12.5% | 50.0% | 75.0% | 25.0% | INSUFFICIENT / INSUFFICIENT |
| Catch Weight | 3 | 64 / 33 | 26.6% | 25.0% | 48.4% | 51.5% | 48.5% | MODERATE_UNCERTAINTY / THIN_EXPLORATORY |
| Catch Weight | 5 | 6 / 3 | 33.3% | 16.7% | 50.0% | 66.7% | 33.3% | INSUFFICIENT / INSUFFICIENT |
| UFC-wide | 3 | 5102 / 2499 | 30.9% | 18.1% | 51.0% | 63.0% | 37.0% | NORMAL / NORMAL |
| UFC-wide | 5 | 556 / 323 | 42.6% | 15.5% | 41.9% | 73.4% | 26.6% | NORMAL / NORMAL |

In three-round bouts, UFC-wide KO is 30.9%, finish 49.0%, conditional KO 63.0%. Heavyweight remains KO-heavy: **43.5% KO**, **56.5% finish**, **76.9% conditional KO** (N352 / 199 finishes). Light Heavyweight remains **46.4%, 63.1%, 73.6%** (N366 / 231). Thus their structural differences survive three-round restriction; five-round exposure amplifies Heavyweight's aggregate but does not account for it entirely.

Flyweight remains nearly even among three-round finishes (49.6% KO / 50.4% SUB; N302 / 131 finishes). Women's Strawweight and Women's Flyweight remain more submission-weighted and decision-heavy in three-round bouts. Five-round division cells are generally moderate/thin; several women's cells are insufficient.

Not every five-round environment is more finish-heavy: Middleweight 50.0% vs 58.7% in three-round bouts; Welterweight 48.0% vs 52.1%. The aggregate five-round association must not become a universal causal rule.

The C3 high-finish-history/five-round archetype looks finish-heavy against the whole population (58.9% vs 49.9%) but is **58.9% versus 58.1%** within all five-round bouts. Almost every five-round fight qualifies (545/556). The striking/defense archetype A3 is also close to its round-matched baseline (three-round KO 29.7% vs 30.9%, five-round finish 58.2% vs 58.1%). These are examples where an apparent broad association is mostly exposure/composition rather than a distinct finish environment. C3 standardization has only 3.1% common bout support and 13 common finishes: its extreme adjusted contrasts are not interpretable.

## Existing striking and grappling pathways

Definitions and thresholds are byte-pinned from #113. The following table contains MATCH bouts. NO_MATCH and UNASSIGNABLE rows, counts, all rates, intervals, pp deltas, era/round views and division compositions are retained in the machine tables. Membership overlaps; totals must not be added across archetypes. No actor-specific winner/method inference is made.

| Archetype | N / finishes | KO [95%] | SUB [95%] | DEC | KO / finish | SUB / finish | Bout / finish gate |
|---|---|---|---|---|---|---|---|
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 943 / 571 | 43.3% [40.1%, 46.4%] | 17.3% [15.0%, 19.8%] | 39.4% | 71.5% | 28.5% | NORMAL / NORMAL |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 153 / 86 | 49.0% [41.2%, 56.9%] | 7.2% [4.1%, 12.4%] | 43.8% | 87.2% | 12.8% | NORMAL / MODERATE_UNCERTAINTY |
| A3_ACCURACY_VS_ABSORPTION | 1070 / 516 | 31.6% [28.9%, 34.4%] | 16.6% [14.5%, 19.0%] | 51.8% | 65.5% | 34.5% | NORMAL / NORMAL |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 1039 / 633 | 45.9% [42.9%, 48.9%] | 15.0% [13.0%, 17.3%] | 39.1% | 75.4% | 24.6% | NORMAL / NORMAL |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 963 / 494 | 26.3% [23.6%, 29.1%] | 25.0% [22.4%, 27.9%] | 48.7% | 51.2% | 48.8% | NORMAL / NORMAL |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 996 / 489 | 27.1% [24.4%, 30.0%] | 22.0% [19.5%, 24.7%] | 50.9% | 55.2% | 44.8% | NORMAL / NORMAL |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 574 / 315 | 27.0% [23.5%, 30.8%] | 27.9% [24.4%, 31.7%] | 45.1% | 49.2% | 50.8% | NORMAL / NORMAL |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 2302 / 1214 | 29.9% [28.1%, 31.8%] | 22.8% [21.1%, 24.6%] | 47.3% | 56.8% | 43.2% | NORMAL / NORMAL |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 923 / 533 | 26.8% [24.0%, 29.7%] | 31.0% [28.1%, 34.0%] | 42.3% | 46.3% | 53.7% | NORMAL / NORMAL |
| C1_DAMAGE_PLUS_SUBMISSION_ACCESS | 36 / 23 | 33.3% [20.2%, 49.7%] | 30.6% [18.0%, 46.9%] | 36.1% | 52.2% | 47.8% | THIN_EXPLORATORY / INSUFFICIENT |
| C2_BOTH_HIGH_FINISH_HISTORY | 1998 / 1107 | 36.7% [34.6%, 38.8%] | 18.7% [17.1%, 20.5%] | 44.6% | 66.2% | 33.8% | NORMAL / NORMAL |
| C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS | 545 / 321 | 43.1% [39.0%, 47.3%] | 15.8% [13.0%, 19.1%] | 41.1% | 73.2% | 26.8% | NORMAL / NORMAL |
| D1_LOW_DAMAGE_STRONG_DEFENSE | 105 / 31 | 15.2% [9.6%, 23.3%] | 14.3% [8.9%, 22.2%] | 70.5% | 51.6% | 48.4% | NORMAL / THIN_EXPLORATORY |
| D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE | 561 / 251 | 37.1% [33.2%, 41.1%] | 7.7% [5.7%, 10.2%] | 55.3% | 82.9% | 17.1% | NORMAL / NORMAL |
| D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE | 182 / 62 | 23.6% [18.0%, 30.3%] | 10.4% [6.8%, 15.7%] | 65.9% | 69.4% | 30.6% | NORMAL / MODERATE_UNCERTAINTY |

### Striking specificity

A1 (KD creation vs weak strike defense) has KO 43.3% versus 32.0% overall, while submission is 17.3% versus 17.9%. Its higher finish rate is principally KO-oriented. KO is 42.4–44.3% in every era, above each era reference. A4 (KO history vs KO vulnerability) has KO 45.9%, SUB 15.0%, conditional KO 75.4%; its raw KO direction also repeats across eras. Both survive three-round restriction.

To expose composition, `pathway_standardized_contrasts.csv` compares MATCH with NO_MATCH among assignable fights, directly standardizing both to the same **division × scheduled-round** weights over common support. A1's crude KO difference is +15.0 pp, adjusted +9.0 pp; A4 +18.9 pp, adjusted +9.2 pp. Conditional KO differences attenuate to +5.5 and +8.7 pp. These descriptive adjusted estimates have sparse constituent cells and are not fitted parameters or causal effects. A1 adjusted KO remains positive in all fixed eras, but its conditional KO contrast is near zero/slightly negative in 2018–2020. A4's earliest adjusted KO contrast is -0.7 pp, so uniform independent temporal effect is not established.

A2 (both high damaging exchange) is strongly KO-concentrated in aggregate (87.2% of 86 finishes) but has only 10 and 21 bouts in its first two eras and thin conditional cells later. This is a promising hypothesis, not a supported permanent interaction. A3 (accuracy vs absorption) does not show a stable specific KO uplift; high striking activity alone is not interchangeable with KD/damage state.

### Grappling specificity

B1 TD pressure vs weak TD defense: SUB **25.0%**, finish **51.3%**, SUB share **48.8%**. B2 TD conversion vs weak TD defense: SUB **22.0%**, finish **49.1%**, SUB share **44.8%**. B2 is particularly informative: method composition shifts although generic finish prevalence remains near the overall reference.

B3 TD access plus submission pressure: SUB **27.9%**, KO **27.0%**, SUB share **50.8%**. B5 submission pressure vs attempts-faced vulnerability: SUB **31.0%**, KO **26.8%**, SUB share **53.7%**. B3 and B5 submission rates exceed the same-era UFC reference in all four windows; conditional submission enrichment also repeats. Their composition-standardized MATCH-minus-NO_MATCH submission differences are **+10.3 pp** and **+17.9 pp**, respectively; conditional SUB differences are **+17.4 pp** and **+23.4 pp**. B1/B2/B3/B5 adjusted submission contrasts stay positive in each era, despite sparse strata.

These observations support distinguishing submission environments from generic finish pressure. They do not imply that takedowns only produce submissions: substantial KO/TKO rates remain in every grappling archetype. B4 high submission pressure without high TD access still has elevated submission prevalence (22.8%); direct B3-vs-B4 causal access effects are not identified. “Vulnerability” here means historical submission attempts faced, not measured inability to survive a submission, and KD/TKO labels cannot locate the finish in standing vs ground phases.

### Primitive states and permanent terrain

All 17 frozen concepts are included as unordered two-fighter LOW/MID/HIGH/MISSING pairs; they are descriptive slices, not new features. Examples below compare two predeclared corners without choosing outcome-optimized cutoffs. The complete 170-cell panel, including mixed and missing pairs, is retained.

| Concept | Pair | N / finishes | KO | SUB | DEC | KO / finish | SUB / finish |
|---|---|---|---|---|---|---|---|
| early_finish | HIGH / HIGH | 673 / 434 | 44.6% | 19.9% | 35.5% | 69.1% | 30.9% |
| early_finish | LOW / LOW | 753 / 288 | 20.2% | 18.1% | 61.8% | 52.8% | 47.2% |
| experience | HIGH / HIGH | 1062 / 521 | 34.0% | 15.1% | 50.9% | 69.3% | 30.7% |
| experience | LOW / LOW | 1400 / 721 | 32.0% | 19.5% | 48.5% | 62.1% | 37.9% |
| ground_share | HIGH / HIGH | 555 / 319 | 34.4% | 23.1% | 42.5% | 59.9% | 40.1% |
| ground_share | LOW / LOW | 589 / 249 | 28.4% | 13.9% | 57.7% | 67.1% | 32.9% |
| kd_creation | HIGH / HIGH | 677 / 409 | 48.0% | 12.4% | 39.6% | 79.5% | 20.5% |
| kd_creation | LOW / LOW | 694 / 273 | 20.0% | 19.3% | 60.7% | 50.9% | 49.1% |
| kd_vulnerability | HIGH / HIGH | 510 / 294 | 38.8% | 18.8% | 42.4% | 67.3% | 32.7% |
| kd_vulnerability | LOW / LOW | 700 / 259 | 17.7% | 19.3% | 63.0% | 47.9% | 52.1% |
| ko_loss_history | HIGH / HIGH | 740 / 456 | 43.2% | 18.4% | 38.4% | 70.2% | 29.8% |
| ko_loss_history | LOW / LOW | 822 / 320 | 21.9% | 17.0% | 61.1% | 56.2% | 43.8% |
| ko_win_history | HIGH / HIGH | 812 / 491 | 47.8% | 12.7% | 39.5% | 79.0% | 21.0% |
| ko_win_history | LOW / LOW | 809 / 318 | 19.3% | 20.0% | 60.7% | 49.1% | 50.9% |
| strike_absorbed | HIGH / HIGH | 655 / 323 | 34.5% | 14.8% | 50.7% | 70.0% | 30.0% |
| strike_absorbed | LOW / LOW | 637 / 306 | 28.6% | 19.5% | 52.0% | 59.5% | 40.5% |
| strike_accuracy | HIGH / HIGH | 625 / 337 | 36.3% | 17.6% | 46.1% | 67.4% | 32.6% |
| strike_accuracy | LOW / LOW | 556 / 249 | 28.6% | 16.2% | 55.2% | 63.9% | 36.1% |
| strike_defense | HIGH / HIGH | 677 / 266 | 27.0% | 12.3% | 60.7% | 68.8% | 31.2% |
| strike_defense | LOW / LOW | 632 / 378 | 38.3% | 21.5% | 40.2% | 64.0% | 36.0% |
| strike_flow | HIGH / HIGH | 680 / 313 | 32.5% | 13.5% | 54.0% | 70.6% | 29.4% |
| strike_flow | LOW / LOW | 560 / 287 | 28.2% | 23.0% | 48.8% | 55.1% | 44.9% |
| sub_pressure | HIGH / HIGH | 558 / 314 | 27.8% | 28.5% | 43.7% | 49.4% | 50.6% |
| sub_pressure | LOW / LOW | 644 / 287 | 36.6% | 7.9% | 55.4% | 82.2% | 17.8% |
| sub_vulnerability | HIGH / HIGH | 504 / 289 | 28.6% | 28.8% | 42.7% | 49.8% | 50.2% |
| sub_vulnerability | LOW / LOW | 675 / 291 | 32.9% | 10.2% | 56.9% | 76.3% | 23.7% |
| sub_win_history | HIGH / HIGH | 632 / 343 | 27.1% | 27.2% | 45.7% | 49.9% | 50.1% |
| sub_win_history | LOW / LOW | 616 / 297 | 38.5% | 9.7% | 51.8% | 79.8% | 20.2% |
| td_conversion | HIGH / HIGH | 618 / 293 | 28.2% | 19.3% | 52.6% | 59.4% | 40.6% |
| td_conversion | LOW / LOW | 569 / 251 | 28.5% | 15.6% | 55.9% | 64.5% | 35.5% |
| td_defense | HIGH / HIGH | 663 / 307 | 36.7% | 9.7% | 53.7% | 79.2% | 20.8% |
| td_defense | LOW / LOW | 563 / 298 | 28.6% | 24.3% | 47.1% | 54.0% | 46.0% |
| td_pressure | HIGH / HIGH | 633 / 317 | 26.7% | 23.4% | 49.9% | 53.3% | 46.7% |
| td_pressure | LOW / LOW | 633 / 313 | 38.9% | 10.6% | 50.6% | 78.6% | 21.4% |

High/high KD creation: KO 48.0% and conditional KO 79.5%; low/low: 20.0% and 50.9%. High/high KD vulnerability similarly differs from low/low (KO 38.8% vs 17.7%). High/high submission pressure: SUB 28.5% vs low/low 7.9%; high/high attempts-faced vulnerability: 28.8% vs 10.2%. TD pressure, conversion and opponent defense have distinct gradients; conversion alone is much less separated than submission pressure. State-pair era/round tables qualify these raw comparisons. They do not establish nonlinear effects, independent slopes or outcome attribution.

Permanent terrain also separates method mix: STRIKE_LOW/ONE_SIDED/TWO_SIDED KO rates 27.8/40.2/43.6%, conditional KO 59.1/73.6/82.3%; GRAPPLE_LOW/ONE_SIDED/TWO_SIDED SUB rates 14.8/23.2/30.5%, conditional SUB 31.0/45.0/51.8%. All eight existing terrain dimensions are reported, including 1,097 UNASSIGNABLE_BY_CONTRACT bouts. These assignments are unchanged; missing does not mean low.

## Weight class × pathway findings

`weight_class_archetype.csv.gz` retains all 585 division × archetype × MATCH/NO_MATCH/UNASSIGNABLE cells. `weight_class_terrain.csv.gz` retains 429 cells over each existing terrain dimension. `pathway_standardization_strata.csv.gz` adds fixed-round cells, N and both sample gates, without searching new interactions. Zero and insufficient cells are visible.

A1 has NORMAL bout N in Lightweight, Welterweight, Middleweight, Light Heavyweight and Heavyweight. Its KO difference versus each division's whole population is about +8.9, +8.9, +6.6, +7.5 and +0.4 pp, respectively. Heavyweight A1 is not a large further uplift above an already high baseline. Conditional shares in many of these cells remain only moderately supported.

A4 is heavily concentrated in the larger men's divisions: Heavyweight contributes 295/1,039 bouts; Light Heavyweight 220; Middleweight 191. Within Heavyweight its KO uplift is only +0.5 pp, versus +11.9 Lightweight, +10.3 Welterweight and +7.5 Middleweight. This explains part of the aggregate A4 association and prevents treating its raw rate as a division-independent effect.

B5 has NORMAL N in Bantamweight, Featherweight, Lightweight, Welterweight and Middleweight; SUB rates exceed their division references by about +9.5 to +12.5 pp. Flyweight B5 N99 shows +10.1 pp. Heavyweight B5 N8 is insufficient, and Light Heavyweight N36 is thin. B3 spans multiple divisions but has **no NORMAL division-specific MATCH cell**; its pooled structure is better supported than division-specific interactions. No “heavyweight grappling exception” or division-specific slope rule is established.

## STRUCTURAL FACTS SUPPORTED BY THE DATA

1. **Heavyweight historically shows a higher KO/TKO rate and KO/TKO share conditional on finish than the UFC-wide modern-era population.** Both directions recur across fixed eras and remain in three-round-only fights. Numerical prevalence changes over time.
2. **Light Heavyweight has a similar KO-heavy structure with higher generic finish prevalence and a less KO-concentrated finish mix than Heavyweight.** It is not solely a five-round-exposure artifact.
3. **Men's Flyweight has a more balanced KO/submission mix among finishes than UFC-wide.** The aggregate and three-round denominators are adequate; era-level conditional cells are thin, so persistence is directional evidence rather than precise era estimation.
4. **Women's Strawweight and post-2017 Women's Flyweight are decision-heavy and relatively submission-weighted among finishes.** Permanent submission-majority in every era is not established. Women's Flyweight has important thin/insufficient conditional-era cells.
5. **A1 and A4 describe KO-oriented rather than merely generic finish-heavy aggregate environments.** Time and three-round views support the raw relationship; composition accounts for a material part. Uniform independent interactions/slopes are not established.
6. **The existing takedown-access/submission-pressure and pressure/attempts-faced archetypes describe submission-enriched environments across eras and rounds.** B2's near-neutral generic finish rate alongside submission enrichment shows why FINISH vs DECISION and KO vs SUB are different target questions. Composition-standardized direction reinforces the pooled association, with sparse-stratum caveats.
7. **Scheduled duration and division must be kept distinct in interpretation.** Several strong division differences survive three-round restriction; C3's apparent general finish uplift mostly disappears against a five-round reference.

These are bounded historical associations with plausible mechanisms, not predictions, biological laws, causal effects or frozen future model coefficients.

## Explicit answers to the twelve audit questions

1. **Higher Heavyweight KO rate?** Yes, against UFC-wide in all four fixed eras and in three-round fights.
2. **Generic finish or conditional KO share?** Both: +11.1 pp finish and +13.9 pp conditional KO overall.
3. **Light Heavyweight similar or distinct?** Similar high KO; higher finish prevalence but lower conditional KO than Heavyweight.
4. **Flyweight different?** Yes, near-even KO/SUB among finishes with lower KO prevalence; conditional era cells are thin.
5. **Submission-heavy divisions?** Aggregate majority in Women's Strawweight/Flyweight; relative enrichment in men's Flyweight and Women's Bantamweight. Persistent per-era majority is not established.
6. **Decision-heavy divisions?** Women's Strawweight, post-2017 Women's Flyweight, Women's Bantamweight consistently relative to UFC; men's Bantamweight/Flyweight in aggregate with temporal qualifications.
7. **Striking specifically KO?** A1/A4 yes descriptively; A2 promising but temporally sparse; A3 not established.
8. **Grappling specifically submission?** Yes for the pooled existing panels, especially B3/B5; not exclusive to submission.
9. **Stable across time?** Broad HW/LHW method directions and pooled grappling enrichment recur; exact rates and several lighter-division/archetype claims vary. Adjusted conditional striking contrasts are less uniformly stable.
10. **Weight differences survive three-round-only?** HW/LHW high KO and Flyweight balanced mix do; women's decision/submission enrichment also remains.
11. **Strong relationships disappear after round accounting?** C3 nearly loses its finish uplift within five-round fights; A3 has little distinct signal. D1's raw survival association almost disappears after division/round standardization, but common-support and tiny-stratum issues prevent declaring absence. HW/LHW differences persist.
12. **Structural enough for MOV1 preregistration?** A method-conditional target, categorical division context and bounded striking/grappling state hypotheses are justified to test. No specific hierarchical parameterization, optimized threshold or division-specific slope is proven.

## Unsupported, uncertain and open relationships

A2 early-era sparsity; C1 combined damage/access N36; D1/D3 small era cells; Women's Featherweight; Catch Weight; most five-round division cells; specific weight-class × B3/B5 slope differences; independent causal TD-access effects; standing-vs-ground KO pathways; hard-coded constant division priors; guaranteed out-of-sample benefit. D1 has only 31 finishes; its apparent survival association is composition-sensitive. A4 adjusted KO is not uniformly positive across eras. Individual state correlations do not prove independent predictive value.

## Implications and limitations

Read the three companion implication files. The target evidence makes division structure worth preregistering for KO-vs-SUB conditional on finish, but it does not show the earlier hierarchy was “simply aimed at the wrong target,” nor that a future hierarchy will generalize. All modeling choices must be frozen before training and evaluated chronologically; composed KO/SUB/decision calibration needs direct evaluation.

The descriptive outcomes are intentionally visible here. The audit is not holdout evidence. Coverage is frozen to August 2026, some divisions began later, fighter histories and missingness are incomplete, archetypes overlap, categories discard continuous information, observed method lacks exact finish phase, and repeated fighters/events weaken naive interval independence. Direct standardization retains common support only and has many thin component cells; it does not adjust for every confounder or warrant causal interpretation. No transition hazards are learned. The upstream F02 Actions artifact expires 2026-10-17; later full source-level reproduction requires a retained copy with the pinned hash. The committed outcome/membership reference and its tables remain durable.

## Artifact manifest and reproducibility

All durable reference artifacts live in `governance/finish_method_target_structure_v1/`. `EVIDENCE_MANIFEST.json` hashes every artifact (including this report and companions) and the runner. `POPULATION_AND_EXECUTION.json` pins canonical inputs, F02, terrain, thresholds, source runner, dates, exact counts and exclusions. `population_manifest.csv.gz` lists each eligible bout, raw/normalized division, method, era, rounds and existing state memberships; it is explicitly not a predictive feature table. `excluded_fights.csv` lists all 71 rejected IDs. Gzip files are deterministic and can be read by pandas or decompressed with `gzip -dc`.

Runner: `tools/diagnostics/run_finish_method_target_structure_v1.py --f02-table <verified frozen winner_modeling_table.parquet>`. It rejects changed source bytes, population/context mismatch, duplicate IDs, missing joins, unmapped divisions and fighter-order differences. Known-state archetype flags exactly reproduce #113; nullable Boolean logic makes unresolved states UNASSIGNABLE. This audit changes neither #113 evidence nor its thresholds. The missingness review records every old match on unresolved input (zero in this population).

Reference policy: future tasks may read V1 but must not silently edit it or automatically import it as model features. Corrections/extensions require a separately reviewed version and identity. F02, MOV0, all model code and existing governed artifacts remain byte-unchanged. No retraining, odds, ROI/EV, MOV1, hierarchy or simulator code was run or built. No merge.
