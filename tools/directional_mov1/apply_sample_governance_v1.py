"""Publication-only correction: enforce the already-frozen N<25 annual subgroup suppression.

No fit, feature, threshold, probability, paired interval or scientific classification changes.
The pre-fit implementation is preserved verbatim; this records a report-format correction.
"""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[2]
D=R/'models/challengers/mov1_three_arm_directional_run_v1/run_v1'
p=D/'PATHWAY_UNCERTAINTY.json';data=json.loads(p.read_text());corrected=[]
for cell,report in data.items():
    if not report['comparisons']:continue
    for pair,row in report['comparisons'].items():
        suppressed=False
        for annual in row['annual']:
            n=annual['N'];annual['sample_gate']='NORMAL' if n>=100 else 'MODERATE_UNCERTAINTY' if n>=50 else 'THIN_EXPLORATORY' if n>=25 else 'INSUFFICIENT'
            if n<25:
                for key in ['log_loss_delta','brier_delta','summed_LL_delta']:annual[key]=None
                annual['direction']='SUPPRESSED_N_LT25';corrected.append({'cell':cell,'comparison':pair,'year':annual['year'],'N':n});suppressed=True
        if suppressed:
            for key in ['favorable_years','unfavorable_years','tied_years','median_annual_delta','strongest_favorable_year','strongest_unfavorable_year','single_best_year_share_of_net_improvement_percent']:row[key]=None
            row['annual_persistence_reporting_status']='SUPPRESSED_MIXED_ANNUAL_SAMPLE_GATES; no alternative qualifying-year success definition introduced'
p.write_text(json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+'\n')
(D/'SUBGROUP_SAMPLE_GOVERNANCE_VALIDATION.json').write_text(json.dumps({'status':'PASS','scope':'publication-only annual subgroup reporting correction','frozen_N_lt25_suppression_applied':corrected,'no_new_thresholds':True,'primary_and_secondary_aggregate_comparisons_unchanged':True,'all_fit_records_and_probabilities_unchanged':True,'paired_aggregate_intervals_and_scientific_classifications_unchanged':True,'additional_fits':0,'original_implementation_freeze_preserved':True},sort_keys=True,indent=2)+'\n')
