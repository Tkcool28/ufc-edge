#!/usr/bin/env python3
"""Model-independent, frozen-category historical target-structure audit."""
from __future__ import annotations
import argparse
import hashlib
import gzip
import importlib.util
import itertools
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'governance/finish_method_target_structure_v1'
CONTRACT = OUT / 'AUDIT_CONTRACT_V1.json'
STATUS = 'FINISH_METHOD_TARGET_STRUCTURE_AUDIT_V1_COMPLETE'
SPEC = importlib.util.spec_from_file_location('frozen_archetypes', ROOT / 'tools/diagnostics/run_mov0_conditional_feature_interaction_archetype_v1.py')
OLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OLD)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n')


def gate(n):
    return OLD.gate(n)


def interval(k, n):
    return OLD.wilson(k, n) if n else [None, None]


def summary(x, reference=None):
    n = len(x)
    counts = {m: int(x.method.eq(m).sum()) for m in ['KO_TKO', 'SUBMISSION', 'DECISION']}
    assert sum(counts.values()) == n
    f = counts['KO_TKO'] + counts['SUBMISSION']
    r = {'N': n, 'sample_status': gate(n), 'finish_N': f, 'finish_sample_status': gate(f), **{m+'_N': k for m,k in counts.items()}}
    for name,k,d in [('KO_TKO',counts['KO_TKO'],n),('SUBMISSION',counts['SUBMISSION'],n),('DECISION',counts['DECISION'],n),('FINISH',f,n),('KO_given_finish',counts['KO_TKO'],f),('SUB_given_finish',counts['SUBMISSION'],f)]:
        r[name+'_rate'] = k/d if d else None
        r[name+'_wilson_low'],r[name+'_wilson_high'] = interval(k,d)
        if reference is not None:
            rr = reference[name+'_rate']
            r[name+'_delta_pp'] = 100*(r[name+'_rate']-rr) if d and rr is not None else None
    return r


def states(x, side, thresholds):
    a = {}
    for name,t in thresholds.items():
        v = x[f'f{side}__{t["f02_suffix"]}'].astype(float)
        for level,flag in [('high',v.ge(t['high_p67'])),('low',v.le(t['low_p33']))]:
            a[name+'_'+level] = flag.astype('boolean').mask(v.isna(), pd.NA)
    a['td_access_high'] = a['td_pressure_high'] & a['td_conversion_high']
    a['damage_creation_high'] = a['kd_creation_high'] & a['strike_flow_high']
    a['finish_history_high'] = a['ko_win_history_high'] | a['sub_win_history_high'] | a['early_finish_high']
    return a


def archetypes(x, a, b):
    # Exact #113 known-state Boolean formulas; Kleene logic retains uncertainty.
    def either(c1,c2): return c1 | c2
    five = x.scheduled_rounds.eq(5)
    return {
        'A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE': either(a['kd_creation_high']&b['strike_defense_low'],b['kd_creation_high']&a['strike_defense_low']),
        'A2_BOTH_HIGH_DAMAGE_EXCHANGE': a['damage_creation_high']&b['damage_creation_high'],
        'A3_ACCURACY_VS_ABSORPTION': either(a['strike_accuracy_high']&b['strike_absorbed_high'],b['strike_accuracy_high']&a['strike_absorbed_high']),
        'A4_KO_HISTORY_VS_KO_VULNERABILITY': either(a['ko_win_history_high']&b['ko_loss_history_high'],b['ko_win_history_high']&a['ko_loss_history_high']),
        'B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE': either(a['td_pressure_high']&b['td_defense_low'],b['td_pressure_high']&a['td_defense_low']),
        'B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE': either(a['td_conversion_high']&b['td_defense_low'],b['td_conversion_high']&a['td_defense_low']),
        'B3_TD_ACCESS_PLUS_SUB_PRESSURE': either(a['td_access_high']&a['sub_pressure_high'],b['td_access_high']&b['sub_pressure_high']),
        'B4_SUB_PRESSURE_POOR_TD_ACCESS': either(a['sub_pressure_high']&~a['td_access_high'],b['sub_pressure_high']&~b['td_access_high']),
        'B5_SUB_PRESSURE_VS_SUB_VULNERABILITY': either(a['sub_pressure_high']&b['sub_vulnerability_high'],b['sub_pressure_high']&a['sub_vulnerability_high']),
        'C1_DAMAGE_PLUS_SUBMISSION_ACCESS': either(a['damage_creation_high']&a['td_access_high']&a['sub_pressure_high'],b['damage_creation_high']&b['td_access_high']&b['sub_pressure_high']),
        'C2_BOTH_HIGH_FINISH_HISTORY': a['finish_history_high']&b['finish_history_high'],
        'C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS': (a['finish_history_high']|b['finish_history_high'])&five,
        'D1_LOW_DAMAGE_STRONG_DEFENSE': a['kd_creation_low']&a['strike_defense_high']&b['kd_creation_low']&b['strike_defense_high'],
        'D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE': ~a['td_access_high']&a['sub_pressure_low']&~b['td_access_high']&b['sub_pressure_low'],
        'D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE': a['experience_high']&a['strike_defense_high']&b['experience_high']&b['strike_defense_high'],
    }


def status_labels(v):
    return v.map({True:'MATCH',False:'NO_MATCH'}).fillna('UNASSIGNABLE')


def standardize(x, col):
    # Descriptive MATCH - NO_MATCH contrast, common strata only; no modeling.
    z=x[x[col].isin(['MATCH','NO_MATCH'])]
    strata=[]
    for keys,v in z.groupby(['division','scheduled_rounds'],dropna=False):
        p=v[v[col].eq('MATCH')]; q=v[v[col].eq('NO_MATCH')]
        if len(p) and len(q):
            strata.append((len(v),summary(p),summary(q),keys))
    common=sum(n for n,_,_,_ in strata)
    r={'archetype':col,'assignable_N':len(z),'common_support_N':common,'common_support_fraction':common/len(z) if len(z) else None,'strata_N':len(strata),'thin_strata_N':sum(min(p['N'],q['N'])<25 for _,p,q,_ in strata)}
    p,q=summary(z[z[col].eq('MATCH')]),summary(z[z[col].eq('NO_MATCH')])
    for m in ['KO_TKO','SUBMISSION','DECISION','FINISH']:
        r[m+'_crude_delta_pp']=100*(p[m+'_rate']-q[m+'_rate']) if p['N'] and q['N'] else None
        r[m+'_standardized_delta_pp']=sum(n*(p[m+'_rate']-q[m+'_rate']) for n,p,q,_ in strata)/common*100 if common else None
    # Conditional shares require a common finish-stratum reference, not bout weights.
    fs=[(p['finish_N']+q['finish_N'],p,q) for _,p,q,_ in strata if p['finish_N'] and q['finish_N']]
    den=sum(n for n,_,_ in fs)
    r['conditional_common_finish_N']=den
    r['conditional_common_fraction']=den/(p['finish_N']+q['finish_N']) if p['finish_N']+q['finish_N'] else None
    r['common_support_sample_status']=gate(common)
    r['conditional_support_sample_status']=gate(den)
    r['interpretation']='DESCRIPTIVE_ONLY; inspect sparse strata and support coverage'
    for m in ['KO_given_finish','SUB_given_finish']:
        r[m+'_crude_delta_pp']=100*(p[m+'_rate']-q[m+'_rate']) if p['finish_N'] and q['finish_N'] else None
        r[m+'_standardized_delta_pp']=100*sum(n*(p[m+'_rate']-q[m+'_rate']) for n,p,q in fs)/den if den else None
    return r


def run(f02_path, output):
    c=json.loads(CONTRACT.read_text())
    if sha(f02_path)!=c['f02_sha256']: raise ValueError('F02 hash mismatch')
    for p,h in c['source_sha256'].items():
        if sha(ROOT/p)!=h: raise ValueError('Frozen source mismatch: '+p)
    thresholds=json.loads((ROOT/'docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/feature_state_thresholds.json').read_text())
    predictors=pd.read_parquet(f02_path)
    if predictors.fight_id.duplicated().any(): raise ValueError('Duplicate F02 ID')
    predictors.event_date=pd.to_datetime(predictors.event_date)
    modern=predictors[predictors.promotion.eq('UFC')&predictors.event_date.ge('2015-01-01')].copy()
    raw=pd.read_csv(ROOT/'data/canonical/v0/fights.csv')
    events=pd.read_csv(ROOT/'data/canonical/v0/events.csv')
    canon=raw.merge(events[['event_id','event_date']],on='event_id',validate='many_to_one')
    canon.event_date=pd.to_datetime(canon.event_date)
    canon=canon[canon.promotion.eq('UFC')&canon.event_date.ge('2015-01-01')].copy()
    def valid(r):return (r.result=='win_loss' and r.method in ['KO_TKO','SUBMISSION']) or (r.result in ['win_loss','draw'] and r.method=='DECISION')
    canon['label_eligible']=canon.apply(valid,axis=1)
    missing_ids=set(canon[canon.label_eligible].fight_id)-set(modern.fight_id)
    if missing_ids: raise ValueError('Canonical eligible IDs absent from frozen F02')
    x=modern.merge(canon[['fight_id','event_date','result','method','weight_class','scheduled_rounds','label_eligible']],on='fight_id',validate='one_to_one',suffixes=('','_canonical'),how='left',indicator=True)
    if not x._merge.eq('both').all():raise ValueError('F02 canonical join loss')
    if not x.event_date.eq(x.event_date_canonical).all() or not x.scheduled_rounds.eq(x.scheduled_rounds_canonical).all() or not x.ctx__weight_class.eq(x.weight_class).all():raise ValueError('Context mismatch')
    excluded=x[~x.label_eligible].copy()
    x=x[x.label_eligible].copy().sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
    expected=json.loads((ROOT/'models/mov0/target_contract_v1.json').read_text())['governed_modern_label_population']['exact_counts']
    for m,n in [('KO_TKO',expected['KO_TKO']),('SUBMISSION',expected['SUBMISSION']),('DECISION',expected['DECISION_0'])]:
        if int(x.method.eq(m).sum())!=n:raise ValueError('Population mismatch '+m)
    if len(x)!=5658 or int(x.result.eq('draw').sum())!=45:raise ValueError('Population mismatch')
    wc=json.loads((ROOT/'models/challengers/mov0_hierarchical_v1/weight_class_map.json').read_text())['literal_map']
    x['division']=x.weight_class.map(wc)
    if x.division.isna().any() or not set(x.division).issubset(c['weight_classes']):raise ValueError('Unmapped division')
    if not x.scheduled_rounds.isin([3,5]).all():raise ValueError('Unexpected rounds')
    x['era']=x.event_date.dt.year.map(lambda y:next(f'{lo}–{hi}' for lo,hi in c['eras'] if lo<=y<=hi))
    terrain=pd.read_csv(ROOT/'governance/model_validation_bucket_v1/MODEL_VALIDATION_BUCKET_ASSIGNMENTS_V1.csv.gz')
    x=x.merge(terrain[['fight_id']+c['terrain_dimensions']],on='fight_id',validate='one_to_one',how='left')
    if x[c['terrain_dimensions']].isna().any().any():raise ValueError('Terrain join loss')
    a,b=states(x,1,thresholds),states(x,2,thresholds)
    flags=archetypes(x,a,b)
    swapped=archetypes(x,b,a)
    if any(not flags[k].equals(swapped[k]) for k in flags):raise ValueError('Order dependence')
    old=OLD.qualify(x,OLD.side_state(x,1,thresholds),OLD.side_state(x,2,thresholds))
    changes={}
    for k,v in flags.items():
        x[k]=status_labels(v)
        known=v.notna()
        changed=int((v[known].astype(bool)!=old[k][known]).sum())
        if changed:raise ValueError('Known-state formula differs from #113')
        changes[k]={'known_matches_old_exactly':True,'unassignable_N':int(v.isna().sum()),'old_match_on_unassignable_N':int(old[k][v.isna()].sum())}
    state_pairs={}
    for name,t in thresholds.items():
        labels=[]
        for side in [1,2]:
            v=x[f'f{side}__{t["f02_suffix"]}']
            labels.append(pd.Series(np.select([v.isna(),v.le(t['low_p33']),v.ge(t['high_p67'])],['MISSING','LOW','HIGH'],default='MID'),index=x.index))
        col='state__'+name
        x[col]=[' / '.join(sorted(pair)) for pair in zip(*labels)]
        state_pairs[name]=col
    output.mkdir(parents=True,exist_ok=True)
    files={}
    def save(name,rows):
        data=pd.DataFrame(rows).to_csv(index=False,float_format='%.10f',lineterminator='\n').encode()
        p=output/(name+('.csv.gz' if len(data)>100000 else '.csv'))
        if len(data)>100000: data=gzip.compress(data,mtime=0)
        p.write_bytes(data); files[p.name]=len(rows)
    overall=summary(x)
    save('weight_class_finish_method',[{'division':'UFC-wide',**overall}]+[{'division':w,**summary(x[x.division.eq(w)],overall)} for w in c['weight_classes']])
    save('canonical_weight_class',[{'raw_label':w,'division':wc[w],'N':len(z),'sample_status':gate(len(z))} for w,z in x.groupby('weight_class',sort=True)])
    save('weight_class_era',[{'division':w,'era':e,**summary(x[x.division.eq(w)&x.era.eq(e)],summary(x[x.era.eq(e)]))} for w,e in itertools.product(c['weight_classes'],[f'{lo}–{hi}' for lo,hi in c['eras']])]+[{'division':'UFC-wide','era':e,**summary(x[x.era.eq(e)])} for e in x.era.unique()])
    save('weight_class_rounds',[{'division':w,'scheduled_rounds':r,**summary(x[x.division.eq(w)&x.scheduled_rounds.eq(r)],summary(x[x.scheduled_rounds.eq(r)]))} for w,r in itertools.product(c['weight_classes'],c['rounds'])]+[{'division':'UFC-wide','scheduled_rounds':r,**summary(x[x.scheduled_rounds.eq(r)])} for r in c['rounds']])
    save('weight_class_era_rounds',[{'division':w,'era':e,'scheduled_rounds':r,**summary(x[x.division.eq(w)&x.era.eq(e)&x.scheduled_rounds.eq(r)],summary(x[x.era.eq(e)&x.scheduled_rounds.eq(r)]))} for w,e,r in itertools.product(c['weight_classes'],x.era.unique(),c['rounds'])])
    pathrows=[]; compositions=[]; cross=[]; eras=[]; rounds=[]
    for k,family,definition in OLD.ARCHETYPES:
        for st in ['MATCH','NO_MATCH','UNASSIGNABLE']:
            z=x[x[k].eq(st)]
            pathrows.append({'archetype':k,'family':family,'definition':definition,'membership':st,**summary(z,overall)})
            for w in c['weight_classes']:
                v=z[z.division.eq(w)]
                compositions.append({'archetype':k,'membership':st,'division':w,'N':len(v),'sample_status':gate(len(v)),'composition_rate':len(v)/len(z) if len(z) else None})
                cross.append({'archetype':k,'family':family,'membership':st,'division':w,**summary(v,summary(x[x.division.eq(w)]))})
            for e in x.era.unique():eras.append({'archetype':k,'family':family,'membership':st,'era':e,**summary(z[z.era.eq(e)],summary(x[x.era.eq(e)]))})
            for r in c['rounds']:rounds.append({'archetype':k,'family':family,'membership':st,'scheduled_rounds':r,**summary(z[z.scheduled_rounds.eq(r)],summary(x[x.scheduled_rounds.eq(r)]))})
    save('striking_pathway',[r for r in pathrows if r['family']=='striking'])
    save('grappling_pathway',[r for r in pathrows if r['family']=='grappling'])
    save('mixed_survival_pathway',[r for r in pathrows if r['family'] in ['mixed','survival']])
    save('weight_class_archetype',cross)
    save('archetype_era',eras);save('archetype_rounds',rounds)
    save('pathway_standardized_contrasts',[standardize(x,k) for k in flags])
    save('pathway_standardized_era',[{'era':e,**standardize(x[x.era.eq(e)],k)} for e,k in itertools.product(x.era.unique(),flags)])
    save('pathway_standardized_rounds',[{'scheduled_rounds':r,**standardize(x[x.scheduled_rounds.eq(r)],k)} for r,k in itertools.product(c['rounds'],flags)])
    save('pathway_standardization_strata',[{'archetype':k,'division':w,'scheduled_rounds':r,'membership':st,**summary(x[x[k].eq(st)&x.division.eq(w)&x.scheduled_rounds.eq(r)])} for k,w,r,st in itertools.product(flags,c['weight_classes'],c['rounds'],['MATCH','NO_MATCH','UNASSIGNABLE'])])
    sr=[];se=[];sround=[]
    for concept,col in state_pairs.items():
        for pair in itertools.combinations_with_replacement(['HIGH','LOW','MID','MISSING'],2):
            st=' / '.join(sorted(pair));z=x[x[col].eq(st)]
            sr.append({'concept':concept,'state_pair':st,**summary(z,overall)})
            for w in c['weight_classes']:compositions.append({'archetype':col,'membership':st,'division':w,'N':len(z[z.division.eq(w)]),'sample_status':gate(len(z[z.division.eq(w)])),'composition_rate':len(z[z.division.eq(w)])/len(z) if len(z) else None})
            for e in x.era.unique():se.append({'concept':concept,'state_pair':st,'era':e,**summary(z[z.era.eq(e)],summary(x[x.era.eq(e)]))})
            for r in c['rounds']:sround.append({'concept':concept,'state_pair':st,'scheduled_rounds':r,**summary(z[z.scheduled_rounds.eq(r)],summary(x[x.scheduled_rounds.eq(r)]))})
    save('state_pathways',sr);save('state_era',se);save('state_rounds',sround);save('pathway_weight_composition',compositions)
    tr=[];wt=[]
    for dim in c['terrain_dimensions']:
        for label in sorted(x[dim].unique()):
            z=x[x[dim].eq(label)];tr.append({'dimension':dim,'state':label,**summary(z,overall)})
            for w in c['weight_classes']:wt.append({'division':w,'dimension':dim,'state':label,**summary(z[z.division.eq(w)],summary(x[x.division.eq(w)]))})
    save('terrain_pathways',tr);save('weight_class_terrain',wt)
    cols=['fight_id','event_id','event_date','result','method','weight_class','division','scheduled_rounds','era']+c['terrain_dimensions']+list(flags)+list(state_pairs.values())
    save('population_manifest',x[cols].astype({'event_date':str}).to_dict('records'))
    save('excluded_fights',excluded[['fight_id','event_id','event_date','result','method']].astype({'event_date':str}).to_dict('records'))
    metadata={'status':STATUS,'starting_main':c['starting_main'],'contract_sha256':sha(CONTRACT),'freeze_commit':'6264fc89e9c493f0fd5a6d2cdbde87f98c9598f0','population_N':len(x),'modern_F02_candidates_N':len(modern),'canonical_modern_N':len(canon),'canonical_absent_from_F02_N':len(set(canon.fight_id)-set(modern.fight_id)),'exclusions':{str(k):int(v) for k,v in excluded.groupby(['result','method']).size().items()},'date_min':str(x.event_date.min().date()),'date_max':str(x.event_date.max().date()),'decision_draws_N':int(x.result.eq('draw').sum()),'aggregate':overall,'membership_missingness_review':changes,'tables':files,'inputs':{'F02':sha(f02_path),**c['source_sha256']},'software':{'numpy':np.__version__,'pandas':pd.__version__},'guardrails':c['guardrails']}
    write_json(output/'SAMPLE_GOVERNANCE_METADATA.json',{'bout_N':c['sample_governance'],'conditional_share_denominator':'finish_N','conditional_sample_gate_separate':True,'zero_denominator':'blank/JSON null; never zero rate','insufficient_policy':'counts and intervals retained transparently; no substantive interpretation','missingness':c['missingness'],'overlap':'archetypes and state panels overlap; not additive','wilson':'marginal binomial intervals; repeated fighters/events not independent; no causal/predictive interpretation'})
    write_json(output/'POPULATION_AND_EXECUTION.json',metadata)
    write_json(output/'EVIDENCE_MANIFEST.json',{'status':STATUS,'starting_main':c['starting_main'],'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(output.iterdir()) if p.is_file() and p.name!='EVIDENCE_MANIFEST.json'},'runner_sha256':sha(__file__)})
    print(json.dumps({'status':STATUS,'N':len(x),'exclusions':metadata['exclusions'],'tables':files},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--f02-table',type=Path,required=True);ap.add_argument('--output-dir',type=Path,default=OUT);args=ap.parse_args();run(args.f02_table,args.output_dir)
