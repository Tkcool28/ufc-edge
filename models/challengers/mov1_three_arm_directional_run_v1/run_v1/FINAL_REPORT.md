# Frozen three-arm historical experiment

All engineering gates passed with exactly 164 authorized fits: 144 inner, 18 outer and two 2021 reproduction fits. Arm A and MOV0 were not refitted. Both reproduction predictions are bit-identical; all 164 saved native model records regenerate their saved probabilities exactly. The original F02, MOV1 and MOV0 prediction bytes were verified. The published pre-fit implementation remains unchanged.

| Arm | Conditional log loss | Conditional Brier | Composed log loss | Composed Brier |
| --- | --- | --- | --- | --- |
| A | 0.615366 | 0.213614 | 0.975754 | 0.586206 |
| B | 0.615496 | 0.213621 | 0.975819 | 0.586200 |
| C | 0.607777 | 0.210100 | 0.971987 | 0.584547 |

B versus A is INCONCLUSIVE. Appending submission direction alone did not establish incremental probability improvement. C versus A and C versus B are SUPPORTED_IMPROVEMENT under the frozen aggregate criteria, for both conditional and complete-system comparisons. C−A conditional log-loss difference is −0.007589, with fight-level 95% interval [−0.012874, −0.002323] and event-cluster interval [−0.012643, −0.002577]. Eight of nine years improve; 2023 deteriorates by 0.002195. The median annual difference is −0.004842 and every leave-one-year-out pooled comparison remains favorable. Partial 2026 is included.

## B3: access plus submission pressure

224 finishes have 54.02% actual submission frequency. A/B/C predict 44.79%/44.61%/44.01% submission, with individual log losses 0.702464/0.703914/0.702832 and Brier scores 0.253128/0.253679/0.252792. C's absolute calibration gap grows from 9.23 to 10.01 percentage points. C−A is INCONCLUSIVE and B−A is NOT_SUPPORTED for this diagnostic. B3 remains unresolved; neither an overall improvement nor a small Brier reduction establishes pathway correction. 206 fights have complete submission and compact sources. All qualifying annual and completeness cells, distributions and paired uncertainty are preserved in the focused report and native evaluation tables.

## B5: submission pressure versus vulnerability

355 finishes have 54.93% actual submission frequency; all 355 have complete source measurements. A/B/C predict 45.95%/46.29%/48.06% submission. Individual log losses are 0.706751/0.706938/0.682100 and Brier scores 0.256122/0.256102/0.244638. C reduces the absolute calibration gap from 8.98 to 6.87 points. C−A and C−B meet SUPPORTED_CELL_IMPROVEMENT; B−A is INCONCLUSIVE. C−A log-loss intervals are [−0.041223, −0.008424] for fights and [−0.041893, −0.008209] for events. Submission remains underpredicted. This is developmental subgroup evidence.

## Preservation and divisions

A1 and A4 meet RETAINED_SUPPORTED for C−A. A2 is THIN_DESCRIPTIVE. Heavyweight and Light Heavyweight preservation are UNCERTAIN: Heavyweight log loss slightly worsens (0.504301→0.504632), while Light Heavyweight improves (0.555442→0.550590), without establishing every frozen preservation gate. Men's Flyweight worsens (0.643466→0.644570); women's Flyweight and Strawweight improve in point estimates (0.691294→0.684009 and 0.708423→0.682276), with moderate sample uncertainty. All 15 archetypes, 13 divisions, terrain, rounds, experience, completeness and chronological years retain their governed population and sample-size gates.

## Complete system and next milestone

C−A composed log loss improves by −0.003768; fight/event 95% intervals are [−0.006342, −0.001224] and [−0.006307, −0.001271]. Decision probabilities remain exactly identical. The model was not promoted. Historical results support prospective confirmation of the frozen compact representation, with explicit attention to unresolved B3 and preservation uncertainty. They do not identify a causal benefit from any particular removed predictor.

All three fixed 2026 MOV1 records are available, but prospective enrollment has not begun. It starts the next UTC day after the latest of October 2, contract merge and completion of all three model records; only pre-event predictions qualify. No post-August-15 outcomes were inspected. Prospective composition remains blocked pending recovery of the separate original frozen MOV0 fitted record; no substitute or retraining is authorized here.

## Publication verification

The frozen N<25 counts-only rule was applied to sparse annual subgroup fields before publication. This is a reporting-only correction, documented in SUBGROUP_SAMPLE_GOVERNANCE_VALIDATION.json and tools/directional_mov1/apply_sample_governance_v1.py. No probabilities, aggregate intervals, classifications, frozen modeling code or fit counts changed. The implementation-freeze manifest remains intact. Native models and larger evaluation tables are losslessly archived in SHA256-verified part files; verification restores and checks them without fitting.
