# Frozen next-POC metrics, gates and handoff

Score only after mechanical/conservation/preflight gates pass and prediction-only artifacts are hashed. These thresholds are frozen now; no POC-B outer results exist or were inspected. Thresholds express scientific effect/preservation tolerances, not selected hazard constants.

Metrics: conditional LL/Brier on standard finishes; full multiclass LL and summed Brier; mean KO/SUB/DEC; B3/B5 conditional SUB and individual losses; A1/A2/A4; exact expected standing/actor-ground occupancy, TD/SUB/GnP rewards, return transitions and implicit multiplier distributions; every outer year, division and minimum-pair history support stratum. Fixed10 equal-width reliability bins; diagnostic calibration intercept/slope where N>=100 and>=25 positives/negatives. No calibration fit changes predictions. Point subgroup gates need>=25 finishes, otherwise unsupported/unmet, never silently passed.

Use paired event bootstrap2000 draws, seed164165, percentile2.5/97.5; contrasts B-A and B-C with rows/memberships fixed. Overall SUB means use all4260 fights; B3/B5 use their unchanged standard-finish cohorts. A1/A2/A4 losses likewise conditional. Report unfavorable years and uncertainty; no multiple-testing discovery claim.

For d_model=observed mean SUB-predicted mean SUB and d+=max(d,0): overall d+_B<=0.5*d+_A, absolute gap<=0.025 and KO absolute gap no more than A+0.005. Each B3/B5 d+_B<=0.75*d+_A and absolute gap no larger than A; both losses must not worsen; at least one improves LL by>=0.010 with event-bootstrap upper<0. Conditional overall LL improves by>=0.010 versus A with upper<0; Brier increase<=0.002. Full LL improves>=0.003; summed Brier increase<=0.003.

For A1/A4, max(LL_B-LL_C,0)<=0.5*max(LL_A-LL_C,0). Also every A1/A2/A4 LL_B<=LL_C+0.010 and Brier_B<=Brier_C+0.005. Thus repairing mean SUB cannot excuse A2 damage. Annual LL improves over A in>=6/9 years, no annual worsening>0.010. Require all reward tests; supported feasible share>=99% and100% outer rows for scoring. Original DEC is unchanged to numerical tolerance.

Arm C competitiveness is a separate gate: B-C LL<=-0.005 with event upper<0, Brier increase<=0.002 and LL improvement in>=6 years. Beating Arm C is not required to conclude the opportunity correction helped versus A.

| Machine gate | Frozen threshold |
|---|---|
| overall_SUB_positive_deficit_ratio_max_vs_A | 0.5 |
| overall_SUB_absolute_gap_max | 0.025 |
| overall_KO_absolute_gap_increase_max_vs_A | 0.005 |
| each_B3_B5_positive_deficit_ratio_max_vs_A | 0.75 |
| each_B3_B5_absolute_gap_increase_max_vs_A | 0.0 |
| each_B3_B5_LL_increase_max_vs_A | 0.0 |
| each_B3_B5_Brier_increase_max_vs_A | 0.002 |
| at_least_one_B3_B5_LL_improvement_min | 0.01 |
| at_least_one_B3_B5_event_CI_upper_required | 0.0 |
| conditional_LL_improvement_min_vs_A | 0.01 |
| conditional_LL_event_CI_upper_required_vs_A | 0.0 |
| conditional_Brier_increase_max_vs_A | 0.002 |
| multiclass_LL_improvement_min_vs_A | 0.003 |
| summed_Brier_increase_max_vs_A | 0.003 |
| each_A1_A4_positive_LL_gap_ratio_max_to_Arm_C | 0.5 |
| each_A1_A2_A4_LL_increase_max_vs_Arm_C | 0.01 |
| each_A1_A2_A4_Brier_increase_max_vs_Arm_C | 0.005 |
| annual_LL_improved_years_min_vs_A | 6 |
| annual_LL_increase_max_vs_A | 0.01 |
| subgroup_N_finish_min | 25 |
| competitive_LL_improvement_min_vs_Arm_C | 0.005 |
| competitive_LL_event_CI_upper_required | 0.0 |
| competitive_Brier_increase_max_vs_Arm_C | 0.002 |
| competitive_annual_LL_improved_years_min_vs_Arm_C | 6 |

## Failure interpretation and decision

D: certified reward/occupancy contradictions prevent the frozen generic-state mapping on supported contexts; this is relative to the selected proxy/entry architecture, not proof all coarse architectures fail. E: sparse support or numerical instability prevents construction; distinguish this from certified D. Both block scoring; do not use optimizer failure alone as D.

For valid scoring, C if the submission-deficit correction gates fail. B if opportunity correction works but full Arm C/preservation qualification remains incomplete; enumerate failed gates, even when individual aggregate losses improve. A only if all scientific success/preservation gates and competitiveness pass. No automatic next challenger, source purchase, production promotion or merge for any classification.

## Exact next execution handoff

**UFC_EDGE_OPPORTUNITY_CONSISTENT_GROUND_PATHWAY_POC_V2_IMPLEMENTATION_AND_FROZEN_RUN**. Begin only after this contract PR is merged and a separate execution instruction is given. Verify live main contains the exact frozen contract/config/manifest. Suggested branch feat/ground-opportunity-consistent-poc-v2. Open a draft PR; no automatic merge.

Read PR160/161/163/164 and this contract. Reuse immutable ability/source/reference artifacts. Implement only POC-B opportunity mapping in new isolated code; leave original code unchanged. Reproduce A/reference hashes. Run synthetic/chronology/order tests; reconstruct training-only targets and solve preflight without outcomes. If any outer row is unavailable, report BLOCKED_OPPORTUNITY_FEASIBILITY and stop before scoring. Otherwise save all4260 outcome-free predictions and support/hazard/reward records, hash them, then score once under these gates. Report both arms, Arm C, all years/cells, calibration, support, source manifest and completion marker. No extra variants, tuning, outer-selected constants or prospective confirmation access.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
