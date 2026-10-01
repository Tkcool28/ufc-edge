#!/usr/bin/env python3
"""Evaluate only after all preregistered fit/reproducibility gates pass."""
import argparse,json,hashlib,importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from ufc_edge.models import mov0
ROOT=Path(__file__).resolve().parents[2]
SPEC=ROOT/'models/challengers/mov0_hierarchical_v1'
sp=importlib.util.spec_from_file_location('archetypes',ROOT/'tools/diagnostics/run_mov0_conditional_feature_interaction_archetype_v1.py');arch=importlib.util.module_from_spec(sp);sp.loader.exec_module(arch)

def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n')
def sign(d):return 'UNCHANGED' if abs(d)<=1e-12 else ('HELPED' if d<0 else 'HURT')
def cell(frame):
    n=len(frame);r={'N':n,'governance':mov0.sample_gate(n),'years':sorted(map(int,frame.year.unique()))}
    if n>=25:
        r.update(mov0.full_metrics(frame));r['wilson95']=arch.wilson(int(frame.target.sum()),n);r['gap_observed_minus_predicted']=float(frame.target.mean()-frame.probability.mean())
    return r

def panel(frame,ids):return cell(frame[frame.fight_id.isin(ids)])
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=Path,required=True);ap.add_argument('--mov0-run-dir',type=Path,required=True);ap.add_argument('--f02-dir',type=Path,required=True);a=ap.parse_args();out=a.evidence_dir
    assert (out/'FIT_COMPLETE.json').exists() and not (out/'BLOCKED.json').exists()
    diagnostics=json.loads((out/'fit_diagnostics.json').read_text());assert len(diagnostics)==18 and all(d['passed'] for d in diagnostics)
    repro=json.loads((out/'reproducibility.json').read_text());assert repro['posterior_arrays_identical'] and repro['predictions_identical']
    ref=a.mov0_run_dir/'oof_MOV0_MIN.csv';assert mov0.file_sha256(ref)==json.loads((SPEC/'contract.json').read_text())['frozen_MIN_OOF_sha256']
    frames={'H0':pd.read_csv(ref),'H1':pd.read_csv(out/'oof_H1.csv'),'H2':pd.read_csv(out/'oof_H2.csv')}
    for s,f in frames.items():
        assert len(f)==4260 and not f.fight_id.duplicated().any()
        base=frames['H0'].set_index('fight_id').loc[f.fight_id]
        assert np.array_equal(base.target,f.target) and np.array_equal(base.year,f.year) and np.array_equal(base.event_id,f.event_id)
    aggregate={s:mov0.full_metrics(f) for s,f in frames.items()};write(out/'aggregate_metrics.json',aggregate)
    annual=[{'surface':s,'year':int(y),**mov0.full_metrics(f)} for s,x in frames.items() for y,f in x.groupby('year')];write(out/'annual_metrics.json',annual)
    reliability={s:mov0.reliability(f.target.to_numpy(),f.probability.to_numpy())[0] for s,f in frames.items()};write(out/'reliability_10_bins.json',reliability)
    comparisons={};paired={}
    for s,b in [('H1','H0'),('H2','H0'),('H2','H1')]:
        k=f'{s}_vs_{b}';comparisons[k]={**mov0.comparison(frames[s],frames[b]),'fight_bootstrap':mov0.paired_bootstrap(frames[s],frames[b],False),'event_bootstrap':mov0.paired_bootstrap(frames[s],frames[b],True)};paired[k]=mov0.paired_loss_delta(frames[s],frames[b])
    write(out/'paired_uncertainty.json',comparisons)
    terrain=mov0.load_terrain_assignment(ROOT/'governance/model_validation_bucket_v1/MODEL_VALIDATION_BUCKET_ASSIGNMENTS_V1.csv.gz')
    terrain_rows=[]
    for dimension in mov0.TERRAIN_COLUMNS:
        for label,t in terrain[terrain.fight_id.isin(frames['H0'].fight_id)].groupby(dimension,dropna=False):
            ids=set(t.fight_id);r={'dimension':dimension,'label':str(label),'models':{s:panel(f,ids) for s,f in frames.items()}}
            if len(ids)>=25:r['paired_log_loss_deltas']={k:float(d.loc[d.fight_id.isin(ids),'delta'].mean()) for k,d in paired.items()}
            terrain_rows.append(r)
    write(out/'validation_terrain.json',terrain_rows)
    bucket_rows=[]
    for name,_,_ in arch.BUCKETS:
        r={'band':name,'models':{s:cell(f[f.probability.map(arch.bucket).eq(name)]) for s,f in frames.items()}}
        ids=set(frames['H0'].loc[frames['H0'].probability.map(arch.bucket).eq(name),'fight_id'])
        r['fixed_H0_membership']={s:panel(f,ids) for s,f in frames.items()}
        r['paired_log_loss_deltas_fixed_H0_membership']={k:float(d.loc[d.fight_id.isin(ids),'delta'].mean()) for k,d in paired.items()}
        bucket_rows.append(r)
    monotonic={s:[bucket_rows[i]['band']+' -> '+bucket_rows[i+1]['band'] for i in range(5) if 'prevalence' in bucket_rows[i]['models'][s] and 'prevalence' in bucket_rows[i+1]['models'][s] and bucket_rows[i]['models'][s]['prevalence']>bucket_rows[i+1]['models'][s]['prevalence']] for s in frames}
    write(out/'probability_buckets.json',{'bands':bucket_rows,'observed_monotonicity_reversals':monotonic,'paired_quality_population':'fixed H0 membership; own-model reliability bands have changing membership'})
    f02=pd.read_parquet(a.f02_dir/'winner_modeling_table.parquet');thresholds=json.loads((ROOT/'docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/feature_state_thresholds.json').read_text())
    x=frames['H0'][['fight_id','target','year']].merge(f02,on='fight_id',validate='one_to_one');flags=arch.qualify(x,arch.side_state(x,1,thresholds),arch.side_state(x,2,thresholds))
    expected=json.loads((ROOT/'docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/archetype_results.json').read_text());expected={r['name']:r['N'] for r in expected}
    archetypes=[]
    for name,family,definition in arch.ARCHETYPES:
        ids=set(x.loc[flags[name],'fight_id']);assert len(ids)==expected[name]
        r={'name':name,'family':family,'definition':definition,'models':{s:panel(f,ids) for s,f in frames.items()}}
        if len(ids)>=25:r['paired_log_loss_deltas']={k:float(d.loc[d.fight_id.isin(ids),'delta'].mean()) for k,d in paired.items()}
        archetypes.append(r)
    write(out/'archetype_comparison.json',archetypes)
    effects=[]
    for p in sorted(out.glob('effects_H*.json')):
        _,surface,year=p.stem.split('_');effects.extend([{'surface':surface,'year':int(year),**r} for r in json.loads(p.read_text())])
    write(out/'varying_effects_and_shrinkage.json',effects)
    stability=[]
    for col in sorted({r['column'] for r in effects if r['surface']=='H2'}):
        for group in sorted({r['group'] for r in effects if r['surface']=='H2'}):
            rr=[r for r in effects if r['surface']=='H2' and r['column']==col and r['group']==group]
            stability.append({'column':col,'group':group,'years_present':len(rr),'positive_deviation_means':sum(r['deviation']['mean']>0 for r in rr),'negative_deviation_means':sum(r['deviation']['mean']<0 for r in rr),'credible_positive_years':[r['year'] for r in rr if r['deviation']['ci95'][0]>0],'credible_negative_years':[r['year'] for r in rr if r['deviation']['ci95'][1]<0],'last_fold':rr[-1]})
    write(out/'effect_stability.json',stability)
    # Same fitted effect, real largest/smallest training groups; uncertainty and conditional pooling displayed without assuming N guarantees shrinkage.
    last=[r for r in effects if r['surface']=='H2' and r['year']==2026]
    sanity=[]
    for col in sorted({r['column'] for r in last}):
        rr=sorted([r for r in last if r['column']==col],key=lambda r:r['train_n']);small,large=rr[0],rr[-1]
        sanity.append({'column':col,'small':small,'large':large,'smaller_more_pooled':small['approximate_pooling_weight']['mean']>large['approximate_pooling_weight']['mean'],'smaller_more_uncertain':small['deviation']['sd']>large['deviation']['sd'],'caution':'conditional information includes predictor magnitude and prevalence; not N alone; diagnostic approximation, not causal or an independently fitted contrast'})
    write(out/'shrinkage_sanity.json',sanity)
    trade=[]
    for k,c in comparisons.items():
        trade.append(['aggregate',k,4260,c['aggregate_log_loss_delta'],sign(c['aggregate_log_loss_delta'])]);trade.extend(['year '+str(r['year']),k,r['N'],r['log_loss_delta'],sign(r['log_loss_delta'])] for r in c['per_year'])
    for category,panel_rows in [('terrain',terrain_rows),('archetype',archetypes)]:
        for r in panel_rows:
            for k,d in r.get('paired_log_loss_deltas',{}).items():trade.append([category+' '+r.get('name',r.get('dimension','')+':'+r.get('label','')),k,r['models']['H0']['N'],d,sign(d)])
    for r in bucket_rows:
        for k,d in r['paired_log_loss_deltas_fixed_H0_membership'].items():trade.append(['fixed H0 bucket '+r['band'],k,r['fixed_H0_membership']['H0']['N'],d,sign(d)])
    (out/'HELPED_HURT_UNCHANGED.md').write_text('# HELPED / HURT / UNCHANGED\n\nDescriptive paired log-loss directions; no subgroup success threshold. Thin cells remain exploratory; cells below 25 are suppressed. Correlated overlapping panels are not independent tests. Own-model bucket calibration is separately reported because membership changes.\n\n'+table(['Population','Comparison','N','Delta log loss','Direction'],[[p,k,n,f'{d:+.6f}',s] for p,k,n,d,s in trade]))
    def classification(c):
        bounds=[c['fight_bootstrap']['ci95'],c['event_bootstrap']['ci95']]
        if all(b[0]>0 for b in bounds):return 'CURRENT_SPECIFICATION_NOT_SUPPORTED'
        # favorable uncertainty does not by itself clear panel tradeoffs; review explicitly.
        return 'INCONCLUSIVE'
    classes={k:classification(v) for k,v in comparisons.items()};write(out/'classification_review.json',{'automatic_conservative_classification':classes,'CLEAR_SUCCESS':'requires documented panel/generalization review; never solely a significant aggregate delta'})
    report=['# MOV0 hierarchical / partial-pooling challenger V1','', 'All 18 chronological fits passed preregistered convergence gates. First H1 repeat verified posterior and prediction equality. Frozen reference was read, never refit.','',f'Contract commit: `{json.loads((out/"execution_identity.json").read_text())["contract_commit"]}`.','', '## Aggregate', '',table(['Surface','Log loss','Brier','AUC','ECE','Cal intercept','Cal slope'],[[s]+[f'{v[k]:.6f}' for k in ['log_loss','brier','roc_auc','ece_10_fixed','calibration_intercept','calibration_slope']] for s,v in aggregate.items()]),'## Paired uncertainty','']
    for k,c in comparisons.items():report += [f"- {k}: delta {c['aggregate_log_loss_delta']:+.6f}; years better/worse/tied {c['better_years']}/{c['worse_years']}/{c['tied_years']}; fight CI {c['fight_bootstrap']['ci95']}; event CI {c['event_bootstrap']['ci95']}."]
    report += ['', '## Annual metrics','',table(['Year','Surface','N','Log loss','Brier','AUC','ECE','Cal intercept','Cal slope'],[[r['year'],r['surface'],r['N']]+[f'{r[k]:.6f}' if r[k] is not None else 'NA' for k in ['log_loss','brier','roc_auc','ece_10_fixed','calibration_intercept','calibration_slope']] for r in annual]),'## Terrain probability quality','',table(['Dimension / label','N','H0 LL','H1 LL','H2 LL'],[[r['dimension']+' / '+r['label'],r['models']['H0']['N']]+[f"{r['models'][s]['log_loss']:.6f}" if 'log_loss' in r['models'][s] else 'N-only' for s in frames] for r in terrain_rows]),'## Fixed probability bands','',table(['Band','Model','N','Mean prediction','Observed finish','Gap','Wilson95','Years'],[[r['band'],s,c['N']]+([f"{c['mean_prediction']:.3%}",f"{c['prevalence']:.3%}",f"{c['gap_observed_minus_predicted']:+.3%}",str(c['wilson95']),str(c['years'])] if 'mean_prediction' in c else ['N-only']*5) for r in bucket_rows for s,c in r['models'].items()]),f'Observed monotonicity reversals: {monotonic}.','', '## Exact PR #113 panel','',table(['Archetype','N','Actual','H0 mean/gap','H1 mean/gap','H2 mean/gap'],[[r['name'],r['models']['H0']['N'],f"{r['models']['H0']['prevalence']:.3%}"]+[f"{r['models'][s]['mean_prediction']:.3%} / {r['models'][s]['gap_observed_minus_predicted']:+.3%}" for s in frames] for r in archetypes]),'## Limitations','', 'Correlated repeated fighters/events, one preregistered prior specification, differing Bayesian global regularization from frozen ridge, normalized rare labels, incomplete 2026, posterior inference uncertainty, overlapping exploratory subgroup tests. Bootstrap intervals condition on fitted OOF predictions; they do not incorporate refit or model-selection uncertainty. Effects are conditional predictive associations; no causal or hazard interpretation. H1 vs H0 changes prior/inference and label pooling as well as hierarchical intercepts; H2 vs H1 isolates the added slope hierarchy more directly. All probabilities remain uncalibrated posterior predictive means; no outcome-selected recalibration.','']
    (out/'REPORT.md').write_text('\n'.join(report))
    print(json.dumps({'aggregate':aggregate,'comparisons':comparisons,'classification':classes},indent=2))
if __name__=='__main__':main()
