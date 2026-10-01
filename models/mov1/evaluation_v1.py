"""Descriptive evaluation of the frozen MOV1 ladder; no fitting of prediction models."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from implementation_v1 import (CONTRACT, ROOT, SURFACES, binary_loss, require,
                               sha, spec, write_csv, write_json)

SYSTEMS=['S0','S1','S2','S3']
METHODS=['KO_TKO','SUBMISSION','DECISION']


def gate(n):
    return 'NORMAL' if n>=100 else 'MODERATE_UNCERTAINTY' if n>=50 else 'THIN_EXPLORATORY' if n>=25 else 'INSUFFICIENT'


def wilson(k,n):
    if n==0:return [None,None]
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    width=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(center-width),float(center+width)]


def calibration(y,p):
    y=np.asarray(y,int);p=np.asarray(p,float)
    if len(y)==0:return {'intercept':None,'slope':None,'status':'EMPTY'}
    if len(np.unique(y))<2:return {'intercept':None,'slope':None,'status':'ONE_CLASS'}
    p=np.clip(p,1e-6,1-1e-6);x=np.log(p/(1-p))
    if np.ptp(x)<=1e-15:return {'intercept':None,'slope':None,'status':'CONSTANT_PREDICTION'}
    X=np.c_[np.ones(len(x)),x];beta=np.zeros(2)
    for i in range(100):
        eta=np.clip(X@beta,-30,30);q=1/(1+np.exp(-eta));w=np.clip(q*(1-q),1e-10,None)
        try:step=np.linalg.solve(X.T@(X*w[:,None]),X.T@(y-q))
        except np.linalg.LinAlgError:return {'intercept':None,'slope':None,'status':'SINGULAR'}
        beta+=step
        if not np.isfinite(beta).all() or np.max(abs(beta))>30:return {'intercept':None,'slope':None,'status':'SEPARATION_OR_NUMERICAL_INSTABILITY'}
        if np.max(abs(step))<1e-10:return {'intercept':float(beta[0]),'slope':float(beta[1]),'status':'CONVERGED','iterations':i+1}
    return {'intercept':None,'slope':None,'status':'NONCONVERGENT'}


def reliability(y,p):
    y=np.asarray(y,int);p=np.asarray(p,float);rows=[];ece=0.
    indices=np.minimum((p*10).astype(int),9)
    for index in range(10):
        mask=indices==index;n=int(mask.sum())
        actual=float(y[mask].mean()) if n else None;pred=float(p[mask].mean()) if n else None
        gap=pred-actual if n else None
        if n:ece+=n/len(y)*abs(gap)
        rows.append({'bin':index,'lower':index/10,'upper':(index+1)/10,'N':n,'mean_prediction':pred,
                     'actual_frequency':actual,'gap':gap,'Wilson95':wilson(int(y[mask].sum()),n)})
    return rows,float(ece) if len(y) else None


def binary_metrics(y,p):
    y=np.asarray(y,int);p=np.asarray(p,float)
    rel,ece=reliability(y,p)
    return {'N':len(y),'log_loss':float(binary_loss(y,p).mean()) if len(y) else None,
            'brier':float(np.mean((p-y)**2)) if len(y) else None,
            'calibration':calibration(y,p),'ECE':ece,'reliability':rel,
            'ROC_AUC':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
            'ROC_AUC_status':'DEFINED' if len(np.unique(y))==2 else 'EMPTY_OR_ONE_CLASS',
            'actual_KO_frequency':float(y.mean()) if len(y) else None,
            'mean_predicted_KO':float(p.mean()) if len(y) else None}


def multiclass_losses(method,p):
    idx=pd.Categorical(method,categories=METHODS).codes
    require((idx>=0).all(),'Unknown composed label')
    return -np.log(np.clip(p[np.arange(len(p)),idx],1e-15,1-1e-15))


def multiclass_metrics(method,p):
    method=np.asarray(method);p=np.asarray(p,float);n=len(method)
    indices=pd.Categorical(method,categories=METHODS).codes
    if n==0:return {'N':0,'log_loss':None,'brier':None,'classwise':{},'mean_assigned_probability_by_actual_outcome':{}}
    y=np.eye(3)[indices]
    classes={}
    for i,m in enumerate(METHODS):
        rel,ece=reliability(y[:,i],p[:,i])
        classes[m]={'observed_frequency':float(y[:,i].mean()),'mean_prediction':float(p[:,i].mean()),
                    'calibration':calibration(y[:,i],p[:,i]),'ECE':ece,'reliability':rel}
    matrix={m:{c:float(p[method==m,i].mean()) if (method==m).any() else None
               for i,c in enumerate(METHODS)} for m in METHODS}
    return {'N':n,'log_loss':float(multiclass_losses(method,p).mean()),
            'brier':float(np.mean(np.sum((p-y)**2,axis=1))),
            'classwise':classes,'mean_assigned_probability_by_actual_outcome':matrix}


def bootstraps(frame,delta):
    delta=np.asarray(delta,float);n=len(delta)
    intervals={}
    for kind in ['fight','event']:
        rng=np.random.default_rng(17);rep=[]
        if kind=='fight':
            for _ in range(2000):rep.append(float(delta[rng.integers(0,n,n)].mean()))
        else:
            events=np.array(sorted(frame.event_id.astype(str).unique()))
            groups={e:np.flatnonzero(frame.event_id.astype(str).to_numpy()==e) for e in events}
            sums=np.array([delta[groups[e]].sum() for e in events]);counts=np.array([len(groups[e]) for e in events])
            for _ in range(2000):
                ix=rng.choice(len(events),len(events),replace=True)
                rep.append(float(sums[ix].sum()/counts[ix].sum()))
        intervals[kind+'_paired_95']=np.quantile(rep,[.025,.975],method='linear').tolist()
    return intervals


def comparison(frame,candidate,baseline):
    delta=np.asarray(candidate)-np.asarray(baseline)
    annual=[]
    for year in range(2018,2027):
        mask=frame.outer_year.eq(year).to_numpy();value=float(delta[mask].mean())
        annual.append({'year':year,'N':int(mask.sum()),'delta':value,'summed_delta':float(delta[mask].sum()),
                       'direction':'TIED' if abs(value)<=1e-12 else 'FAVORABLE' if value<0 else 'UNFAVORABLE'})
    best=min(annual,key=lambda r:r['summed_delta']);total=float(delta.sum())
    return {'aggregate_delta':float(delta.mean()),'annual':annual,
            'favorable_years':sum(r['direction']=='FAVORABLE' for r in annual),
            'unfavorable_years':sum(r['direction']=='UNFAVORABLE' for r in annual),
            'tied_years':sum(r['direction']=='TIED' for r in annual),
            'median_annual_delta':float(np.median([r['delta'] for r in annual])),
            'strongest_favorable_year':min(annual,key=lambda r:r['delta']),
            'strongest_unfavorable_year':max(annual,key=lambda r:r['delta']),
            'strongest_year_share_of_net_improvement_percent':100*abs(best['summed_delta'])/abs(total) if total<0 else None,
            'replicates':2000,'seed':17,**bootstraps(frame,delta)}


def join_terrain(population):
    contract=spec('terrain_archetype_evaluation.json')['terrain']
    d=ROOT/'governance/model_validation_bucket_v1'
    assignment=d/'MODEL_VALIDATION_BUCKET_ASSIGNMENTS_V1.csv.gz'
    require(sha(d/'MODEL_VALIDATION_BUCKET_CONTRACT_V1.json')==contract['contract_sha256'],'Terrain contract mismatch')
    require(sha(d/'MODEL_VALIDATION_PERCENTILE_REFERENCE_V1.json')==contract['percentile_reference_sha256'],'Terrain percentile mismatch')
    with gzip.open(assignment,'rb') as stream:raw=stream.read()
    import hashlib
    require(hashlib.sha256(raw).hexdigest()==contract['assignment_physical_sha256'],'Terrain physical mismatch')
    terrain=pd.read_csv(assignment)
    require(not terrain.fight_id.duplicated().any(),'Duplicate terrain IDs')
    require(set(population.fight_id)<=set(terrain.fight_id),'Terrain join missing')
    dims=contract['diagnostics']
    check=population[['fight_id']+dims].merge(terrain[['fight_id']+dims],on='fight_id',validate='one_to_one',suffixes=('','_immutable'))
    for dim in dims:require(check[dim].eq(check[dim+'_immutable']).all(),'Audit/immutable terrain disagreement '+dim)
    return terrain


def cell_records(x,kind,label,ks,ps):
    n=len(x);finish=x.method.ne('DECISION').to_numpy();nf=int(finish.sum());out=[]
    for surface,system in zip(SURFACES,SYSTEMS):
        k=x[ks[surface]].to_numpy(float);p=x[ps[system]].to_numpy(float)
        actual={m:int(x.method.eq(m).sum()) for m in METHODS}
        cm= binary_metrics(x.loc[finish,'method'].eq('KO_TKO'),k[finish]) if nf>=25 else None
        tm= multiclass_metrics(x.method,p) if n>=25 else None
        r={'kind':kind,'cell':label,'surface':surface,'system':system,'N':n,'sample_status':gate(n),
           'finish_N':nf,'finish_sample_status':gate(nf),'year_counts':json.dumps(x.outer_year.value_counts().sort_index().to_dict(),sort_keys=True),
           'division_counts':json.dumps(x.division.value_counts().sort_index().to_dict(),sort_keys=True),
           **{m+'_N':actual[m] for m in METHODS},'F_all_mean':float(x.F.mean()) if n else None,
           'F_finish_mean':float(x.loc[finish,'F'].mean()) if nf else None,
           'K_all_mean':float(k.mean()) if n else None,'K_finish_mean':float(k[finish].mean()) if nf else None,
           'actual_KO_given_finish':actual['KO_TKO']/nf if nf else None,
           'conditional_gap':float(k[finish].mean())-actual['KO_TKO']/nf if nf else None,
           'conditional_Wilson95':json.dumps(wilson(actual['KO_TKO'],nf)),
           'conditional_log_loss':cm['log_loss'] if cm else None,'conditional_brier':cm['brier'] if cm else None,
           'conditional_ECE':cm['ECE'] if cm else None,
           'conditional_calibration_intercept':cm['calibration']['intercept'] if cm else None,
           'conditional_calibration_slope':cm['calibration']['slope'] if cm else None,
           'multiclass_log_loss':tm['log_loss'] if tm else None,'multiclass_brier':tm['brier'] if tm else None}
        for i,m in enumerate(METHODS):
            r['predicted_'+m]=float(p[:,i].mean()) if n else None
            r['actual_'+m]=actual[m]/n if n else None
            r['actual_'+m+'_Wilson95']=json.dumps(wilson(actual[m],n))
        out.append(r)
    return out


def evaluate(frame,population,mov0,all_scores,output):
    output=Path(output)
    terrain=join_terrain(population)
    x=population[population.event_date.ge('2018-01-01')].copy()
    x['outer_year']=x.event_date.str[:4].astype(int)
    x=x.sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
    # All scoring precedes this outcome/reference join. No table below enters a model.
    kcols={};pcols={};composed=[]
    F=mov0.set_index('fight_id').loc[x.fight_id].probability.to_numpy(float);x['F']=F
    for surface,system in zip(SURFACES,SYSTEMS):
        score=all_scores[all_scores.surface.eq(surface)].set_index('fight_id').loc[x.fight_id]
        k=score.P_KO_given_finish.to_numpy(float);col='K_'+surface;kcols[surface]=col;x[col]=k
        probs=np.c_[F*k,F*(1-k),1-F]
        require(np.isfinite(probs).all() and ((probs>=0)&(probs<=1)).all(),'Invalid composition')
        require(np.allclose(probs.sum(axis=1),1,atol=1e-12,rtol=0),'Composition sum failed')
        columns=['P_'+system+'_'+m for m in METHODS];pcols[system]=columns
        x[columns]=probs
        out=x[['fight_id','event_id','event_date','outer_year']].copy();out['system']=system
        out['frozen_MOV0_MIN_F']=F;out['MOV1_K']=k
        for i,m in enumerate(METHODS):out['P_'+m]=probs[:,i]
        out['actual_method']=x.method;composed.append(out)
    allcomposed=pd.concat(composed,ignore_index=True)
    allcomposed['system']=pd.Categorical(allcomposed.system,categories=SYSTEMS,ordered=True)
    allcomposed=allcomposed.sort_values(['event_date','event_id','fight_id','system'])
    require(len(allcomposed)==17040 and not allcomposed.duplicated(['fight_id','system']).any(),'Incomplete composition')
    write_csv(output/'composed_oof_all_eligible.csv',allcomposed)
    for system in SYSTEMS:write_csv(output/f'oof_{system}_composed.csv',allcomposed[allcomposed.system.eq(system)])
    regen=pd.read_csv(output/'composed_oof_all_eligible.csv',float_precision='round_trip')
    require(np.max(abs(regen[['P_'+m for m in METHODS]].to_numpy()-allcomposed[['P_'+m for m in METHODS]].to_numpy()))<=1e-12,'Composed serialization failed')
    finish=x[x.method.ne('DECISION')].copy();require(len(finish)==2115,'Conditional count')
    conditional={};threeway={};losses={};mlosses={}
    for surface in SURFACES:
        losses[surface]=binary_loss(finish.method.eq('KO_TKO'),finish[kcols[surface]])
        conditional[surface]={'aggregate':binary_metrics(finish.method.eq('KO_TKO'),finish[kcols[surface]]),
            'annual':{str(y):binary_metrics(q.method.eq('KO_TKO'),q[kcols[surface]])
                      for y in range(2018,2027) for q in [finish[finish.outer_year.eq(y)]]}}
    for system in SYSTEMS:
        mlosses[system]=multiclass_losses(x.method,x[pcols[system]].to_numpy())
        threeway[system]={'aggregate':multiclass_metrics(x.method,x[pcols[system]].to_numpy()),
            'annual':{str(y):multiclass_metrics(q.method,q[pcols[system]].to_numpy())
                      for y in range(2018,2027) for q in [x[x.outer_year.eq(y)]]}}
    # Algebraic gate before emitting/interpreting any performance report.
    max_identity_error=0.;clipping_exceptions=0
    for cand,base in [('S1','S0'),('S2','S1'),('S3','S2'),('S2','S0'),('S3','S0')]:
        a=SURFACES[SYSTEMS.index(cand)];b=SURFACES[SYSTEMS.index(base)]
        expected=np.zeros(len(x));mask=x.method.ne('DECISION').to_numpy()
        expected[mask]=losses[a]-losses[b]
        error=abs((mlosses[cand]-mlosses[base])-expected)
        max_identity_error=max(max_identity_error,float(error.max()))
        # Selected-class clipping can break the identity only at numerical boundaries.
        indices=pd.Categorical(x.method,categories=METHODS).codes
        for system in [cand,base]:
            selected=x[pcols[system]].to_numpy()[np.arange(len(x)),indices]
            clipping_exceptions+=int(((selected<1e-15)|(selected>1-1e-15)).sum())
        require(error.max()<=1e-12 or clipping_exceptions>0,'Composed/conditional loss identity failed')
    runtime=json.loads((output/'RUNTIME_VALIDATION.json').read_text())
    runtime.update({'composition_sum_max_error':float(np.max(abs(allcomposed[['P_'+m for m in METHODS]].sum(axis=1)-1))),
                    'composition_regenerated':True,'conditional_composed_loss_identity_max_error':max_identity_error,
                    'log_clip_exceptions_across_comparisons':clipping_exceptions,'terrain_one_to_one_immutable_join':True})
    write_json(output/'RUNTIME_VALIDATION.json',runtime)
    write_json(output/'conditional_metrics.json',conditional);write_json(output/'three_way_metrics.json',threeway)
    comparisons={};annual=[]
    for cand,base in spec('conditional_metrics.json')['comparisons']:
        r=comparison(finish,losses[cand],losses[base]);comparisons[cand+'_vs_'+base]={'kind':'conditional',**r}
        annual.extend({'comparison':cand+'_vs_'+base,**row} for row in r['annual'])
    for cand,base in [('S1','S0'),('S2','S1'),('S3','S2'),('S2','S0'),('S3','S0')]:
        r=comparison(x,mlosses[cand],mlosses[base]);comparisons[cand+'_vs_'+base]={'kind':'composed',**r}
        annual.extend({'comparison':cand+'_vs_'+base,**row} for row in r['annual'])
    write_json(output/'bootstrap_comparisons.json',comparisons);write_csv(output/'annual_comparisons.csv',pd.DataFrame(annual))
    buckets=[]
    for surface in SURFACES:
        for population_name,data in [('conditional_finishes',finish),('all_scoring_distribution',x)]:
            values=data[kcols[surface]].to_numpy();ix=np.searchsorted([.3,.4,.5,.6,.7,.8],values,side='right')
            for i,label in enumerate(spec('conditional_probability_buckets.json')['labels']):
                q=data.iloc[np.flatnonzero(ix==i)];n=len(q);k=int(q.method.eq('KO_TKO').sum())
                parts={a:{status:{'N':int(q[a].eq(status).sum()),'share':float(q[a].eq(status).mean()) if n else None}
                          for status in ['MATCH','NO_MATCH','UNASSIGNABLE']}
                       for a in spec('terrain_archetype_evaluation.json')['archetypes']}
                divisions={d:{'N':int(q.division.eq(d).sum()),'share':float(q.division.eq(d).mean()) if n else None}
                           for d in spec('terrain_archetype_evaluation.json')['normalized_weight_classes']}
                actual=k/n if n and population_name=='conditional_finishes' else None
                mean=float(q[kcols[surface]].mean()) if n else None
                buckets.append({'surface':surface,'population':population_name,'bucket':label,'N':n,'sample_status':gate(n),
                                'mean_predicted_KO':mean,'actual_KO_frequency':actual,'calibration_gap':mean-actual if actual is not None else None,
                                'Wilson95':json.dumps(wilson(k,n) if population_name=='conditional_finishes' else [None,None]),
                                'year_coverage':json.dumps(q.outer_year.value_counts().sort_index().to_dict(),sort_keys=True),
                                'division_composition':json.dumps(divisions,sort_keys=True),
                                'archetype_composition':json.dumps(parts,sort_keys=True)})
    write_csv(output/'conditional_probability_buckets.csv',pd.DataFrame(buckets))
    records=[];weight=[];arches=[];cross=[]
    for division in spec('terrain_archetype_evaluation.json')['normalized_weight_classes']:
        q=x[x.division.eq(division)];weight.extend(cell_records(q,'normalized_division',division,kcols,pcols))
    for dim in spec('terrain_archetype_evaluation.json')['terrain']['diagnostics']+['scheduled_rounds','era']:
        values=sorted(set(population[dim].astype(str))|set(terrain[dim].astype(str)) if dim in terrain else set(population[dim].astype(str)))
        if dim=='completeness_tier':values=sorted(set(values)|{'MODERATE_MISSINGNESS'})
        for value in values:records.extend(cell_records(x[x[dim].astype(str).eq(value)],dim,value,kcols,pcols))
    for archetype in spec('terrain_archetype_evaluation.json')['archetypes']:
        for status in ['MATCH','NO_MATCH','UNASSIGNABLE']:
            q=x[x[archetype].eq(status)];arches.extend(cell_records(q,'archetype',archetype+'::'+status,kcols,pcols))
            for division in spec('terrain_archetype_evaluation.json')['normalized_weight_classes']:
                cross.extend(cell_records(q[q.division.eq(division)],'division_archetype',division+'::'+archetype+'::'+status,kcols,pcols))
    write_csv(output/'terrain_performance.csv',pd.DataFrame(records))
    write_csv(output/'weight_class_method_composition.csv',pd.DataFrame(weight))
    write_csv(output/'archetype_composition.csv',pd.DataFrame(arches))
    write_csv(output/'weight_class_archetype_composition.csv',pd.DataFrame(cross))
    # Pair all systems within exact cells; no bootstrap battery or cell selection.
    differences=[]
    for r in records:
        if r['system']=='S0':
            peers=[v for v in records if v['kind']==r['kind'] and v['cell']==r['cell']]
            for cand,base in [('S1','S0'),('S2','S1'),('S3','S2')]:
                a=next(v for v in peers if v['system']==cand);b=next(v for v in peers if v['system']==base)
                differences.append({'kind':r['kind'],'cell':r['cell'],'N':r['N'],'sample_status':r['sample_status'],
                                    'comparison':cand+'_vs_'+base,'log_loss_delta':a['multiclass_log_loss']-b['multiclass_log_loss'] if a['multiclass_log_loss'] is not None else None,
                                    'brier_delta':a['multiclass_brier']-b['multiclass_brier'] if a['multiclass_brier'] is not None else None})
    write_csv(output/'terrain_comparisons.csv',pd.DataFrame(differences))
    coef=pd.read_csv(output/'coefficient_by_year.csv',float_precision='round_trip');stability=[]
    for (surface,feature),q in coef.groupby(['surface','feature'],sort=True):
        v=q.coefficient.to_numpy()
        stability.append({'surface':surface,'feature':feature,'folds_present':len(q),'positive_years':int((v>0).sum()),
                          'negative_years':int((v<0).sum()),'zero_years':int((v==0).sum()),
                          'mean_coefficient':float(v.mean()),'mean_abs_coefficient':float(abs(v).mean()),
                          'min':float(v.min()),'max':float(v.max()),'sd_population':float(v.std())})
    write_csv(output/'coefficient_stability.csv',pd.DataFrame(stability))
    coverage=[]
    for audit in json.loads((output/'TRAINING_AUDIT.json').read_text()):
        if audit['stage']!='outer':continue
        surface=audit['surface'];year=audit['outer_year'];q=frame[frame.outer_year.eq(year)]
        columns=audit['preprocessing']['literal_columns'];missing=q[columns].isna()
        mapping=json.loads((ROOT/spec('missingness_preprocessing.json')['weight_class']['literal_map_path']).read_text())['literal_map']
        unknown=q.ctx__weight_class.map(mapping).isin(audit['preprocessing']['division_categories'])
        coverage.append({'year':year,'surface':surface,'N':len(q),'rows_with_any_null':int(missing.any(axis=1).sum()),
                         'missing_values':int(missing.to_numpy().sum()),'known_but_unseen_training_division_N':int((~unknown).sum()),
                         'missing_by_column':json.dumps(missing.sum().to_dict(),sort_keys=True)})
    write_csv(output/'missingness_and_unknown_category_coverage.csv',pd.DataFrame(coverage))
    node={'finish_node':binary_metrics(x.method.ne('DECISION'),F),
          'weighted_finish_node_log_loss':float(binary_loss(x.method.ne('DECISION'),F).mean()),
          'weighted_method_node_log_loss':{s:float(losses[s].sum()/len(x)) for s in SURFACES},
          'identity':'composed LL = finish-node LL + finish-fraction times conditional LL before log clipping; terms have different targets and entropy, not comparable reducible-error budgets'}
    write_json(output/'node_error_decomposition.json',node)
    print('Complete conditional/composed evaluation; fixed reference tables written',flush=True)
    return conditional,threeway,comparisons
